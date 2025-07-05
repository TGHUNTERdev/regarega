import requests
import json
from Core import Log as log
from Core.SmsServices.Classes import Phone
from Core.SmsServices.SmsService import SmsService

PHONE_ERROR_CODES = {
    "-2":"Token does not exist",
    "-3":"The service does not exist",
    "-4":"The country is error",
    "-5":"The service not audit",
    "-6":"The service disabled",
    "-7":"The token disabled",
    "-8":"Your balance is insufficient, please recharge",
    "-9":"Too many numbers, please supplement the balance",
    "-10":"The service does not allow specifying the number"
}

class FirefoxFunService(SmsService):
    name="firefoxfun"
        
    def load(self,config):
##        self.url = f"http://www.firefox.fun"
        self.token = config.getstring("token")
        self.iid = config.getstring("iid")
##        self.maxPrice = config.getstring("maxPrice")
        self.maxPrice = self.MaxPrice

    def GetCountries(self):
        raise ValueError("firefoxfun сервис не поддерживает проверку стран")
        
    def GetPhone(self,country):
        url = f"/yhapi.ashx?act=getPhone&token={self.token}&iid={self.iid}&country={country.code}&maxPrice={self.maxPrice}&dock=1"
        response = self.request(url)
##        log.d(response.request.url,level=log.level.debug)
##        log.d(response.text,level=log.level.debug)
        
        text = response.text
        if text.startswith("1"):
##            log.d(text)
            text = text.split("|")
            phone_id = text[1]
            number = text[4] + text[7]
##            log.d(response.request.url,level=log.level.debug)
            return Phone(phone_id, number)
        if text.startswith("0"):
            text = text.split("|")
            if text[1] == '-1':
                return None
            else:
                raise RuntimeError(
                    "ошибка получения номера: "+PHONE_ERROR_CODES.get(text[1],text[1])
                )
     
    def GetSms(self,phone): 
        url = f"/yhapi.ashx?act=getPhoneCode&token={self.token}&pkey={phone.id}"

        response = self.request(url)
        text = response.text

##        log.d(text)
        
        if text[0] == "1":
            text = text.split("|")
            return text[1]
        if text[0] == "0":
            if text[1] == '-1':
                log.e("Не верный API ключ")
                return None
            if text[1] == '-2':
                log.w("pkey недействителен")
                return None
            else:
                return None
        else:
            return None
            
    def SetBan(self,phone):
        url = f"/yhapi.ashx?act=addBlack&token={self.token}&pkey={phone.id}&reason=used"
        response = self.request(url)
    def SetFinish(self,phone):
        pass
