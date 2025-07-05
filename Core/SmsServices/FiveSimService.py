import requests
import json
import random
from Core import Log as log
from Core.SmsServices.Classes import Phone
from Core.SmsServices.SmsService import SmsService

class FiveSimService(SmsService):
    name="5sim"
        
    def load(self,config):
##        self.api_key = config.getstring("api key")
        self.headers = {
            'Authorization': 'Bearer ' + config.getstring("api key"),
            'Accept': 'application/json',
        }
##        self.host = config.getstring("host")
##        self.url = f"{self.host}/stubs/handler_api.php?"
        self.service = config.getstring("service")
        operators = config.getstring("operators")
        if operators == "-":
            self.operators=["any"]
##            raise ValueError(f"сервис {self.name} должен иметь хотя бы один оператор, если опреатор не принципиален, то требуется использовать any")
        else:
            self.operators=[]
            for operator in operators.split(","):
                operator = operator.strip()
                if operator:
                    log.i(f"загружен оператор {operator}")
                    self.operators.append(operator)

        self.VoiceHandle = "1" if config.getbool("voice handle") else ""
        
    def GetCountries(self): ##Запрос количества доступных номеров
        raise ValueError(f"{self.name} сервис не поддерживает проверку стран")
        try:
            return self.request("/v1/guest/prices").json()
        except json.JSONDecodeError:
            raise ValueError("ответ сервиса не распознан как json")
        
    def GetPhone(self,country): ##Заказ номера
        response = self.request(
            f"/v1/user/buy/activation/{country.code}/{random.choice(self.operators)}/{self.service}",
            {
                "maxPrice":self.MaxPrice,
                "voice":self.VoiceHandle
            }
        )
##        log.d(response.request.url)
##        log.d(response.text)
        if response.ok:
            if response.text!="no free phones":
                data=response.json()
##                log.d(data["id"], data["phone"])
                return Phone(data["id"], data["phone"])
        else:
            raise RuntimeError(f"сервер вернул: {response.status_code} {response.text}")
            
    def GetSms(self,phone): ##Получить состояние активации
        response = self.request(f"/v1/user/check/{phone.id}")
##        log.d(response.request.url)
##        log.d(response.text)
        data=response.json()
        sms=data.get("sms")
        if sms:
            code=sms.get("code")
            if code:
                return code
            
    def SetFinish(self,phone): ##Изменение статуса активации
        self.request(f"/v1/user/finish/{phone.id}")

    def SetBan(self,phone): ##Изменение статуса активации
        self.request(f"/v1/user/ban/{phone.id}")

    def request(self,path,params={},proxy=None):
        if self.proxies:
##            log.d(self.host+path,proxy)
            proxy=proxy if proxy else random.choice(self.proxies)
            return requests.get(
                self.host+path,
                params=params,
                headers=self.headers,
                proxies=proxy,
                timeout=self.RequestTimeout
            )
        else:
            log.d(self.host+path)
            return requests.get(
                self.host+path,
                headers=self.headers,
                params=params,
                timeout=self.RequestTimeout
            )
