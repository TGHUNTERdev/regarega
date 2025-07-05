import requests
from Core import Log as log
from Core.SmsServices.Classes import Phone
from Core.SmsServices.SmsService import SmsService

class SmsAcktiwator(SmsService):
    name="smsacktiwator"
        
    def load(self,config):
        self.api_key = config.getstring("api key")
##        self.host = config.getstring("host")
##        self.url = f"{self.host}/api/"
##        self.url2 = f"{self.host}/stubs/handler_api.php?"
        self.service = config.getstring("service")
        
    def GetCountries(self):
        raise ValueError("smsacktiwator сервис пока не поддерживает проверку стран")
    
##    def GetPhone(self,country): ##Заказ номера
##        url = f"{self.url}getnumber/{self.api_key}?id={self.service}&code={country.code}"
####        log.d(url)
##        response = requests.get(url)
##        data = response.json()
##
##        if data.get("name") == "error":
##            code = data["code"]
##            if code == 103:
##                return None
##            else:
##                error = data["message"]
##                raise RuntimeError(f"ошибка: {code} {error}")
##        else:
##            phone_id = data["id"]
##            number = data["number"]
##            return Phone(phone_id, number)

    def GetPhone(self,country): ##Заказ номера
##        return Phone(0,"89115859736")
        url = f"/stubs/handler_api.php?action=getNumber&api_key={self.api_key}\
&service={self.service}&country={country.code}&maxPrice={self.MaxPrice}"
##        log.d(url)
        response = self.request(url)

        text = response.text
        if text == "NO_NUMBERS":
##            log.w("Нет номеров, попробуйте позднее")
            return None
        if text == "BAD_KEY":
            raise RuntimeError("не верный API ключ")
        if text == "NO_BALANCE":
            raise RuntimeError("низкий баланс")
        if text.startswith("ACCESS_NUMBER"):
##            log.i("Номер успешно арендован")
            text = text.split(":")
            phone_id = text[1]
            number = text[2]
            return Phone(phone_id, number)
        else:
            raise RuntimeError("сервер вернул "+str([text[:22]+"..."]))
            
##    def GetSms(self,phone): ##Получить состояние активации
##        url = f"getlatestcode/{self.api_key}?id={phone.id}"
##        response = self.request(url)
##        data = response.text
##        
##        if data.isdigit():
##            return data
##        elif data:
##            raise RuntimeError(f"Непредвиденная ошибка {data}")
##        else:
##            return None

    def GetSms(self,phone): ##Получить состояние активации
        url = f"/getstatus/{self.api_key}?id={phone.id}"
        response = self.request(url)
        data = response.json()
        if data:
            if data.get("name") == "error":
                error = data["message"]
                raise RuntimeError(f"ошибка: {code} {error}")
            else:
                sms = data.get("small")
                if sms:
                    return sms
        
    def SetFinish(self,phone):
        pass

    def SetBan(self,phone):
        pass
