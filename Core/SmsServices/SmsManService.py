import requests
import json
from Core import Log as log
from Core.SmsServices.Classes import Phone
from Core.SmsServices.SmsService import SmsService

class SmsManService(SmsService):
    name="smsman"
        
    def load(self,config):
        self.api_key = config.getstring("api key")
##        self.host = config.getstring("host")
##        self.url = f"{self.host}/stubs/handler_api.php?"
        self.service = config.getstring("service")
        operators = config.getstring("operators")
        if operators == "-":
            log.w("операторы не используются")
            self.operators = None
        else:
            self.operators=""
            for operator in operators.split(","):
                operator = operator.strip()
                if operator:
                    log.i(f"загружен оператор {operator}")
                    self.operators += operator + ","
            self.operators = self.operators[:-1]
                
    def GetCountries(self): ##Запрос количества доступных номеров
        url = f"/stubs/handler_api.php?action=getPrices&api_key={self.api_key}\
&service={self.service}"
        response = self.request(url)

        if response.text == "BAD_KEY":
##            log.e("не верный API ключ")
            raise ValueError("не верный API ключ")
        else:
##            log.i("запрос выполнен успешно")
            try:
                return response.json()
            except json.JSONDecodeError:
                raise ValueError("ответ сервиса не распознан как json")
        
    
    def GetPhone(self,country): ##Заказ номера
##        return Phone(0,"89115859736")
        url = f"/stubs/handler_api.php?action=getNumber&api_key={self.api_key}\
&service={self.service}&country={country.code}&maxPrice={self.MaxPrice}"
        if self.operators:
            url += f"&operators={self.operators}"

        response = self.request(url)
##        log.d(response.request.url)
##        log.d(response.text)

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
            return None
##        else:
##            raise RuntimeError("сервер вернул "+str([text[:22]+"..."]))
            
    def GetSms(self,phone): ##Получить состояние активации
 
        url = f"/stubs/handler_api.php?action=getStatus&api_key={self.api_key}\
&id={phone.id}"
        response = self.request(url)
        text = response.text

        if text == "BAD_KEY":
##            log.e("Не верный API ключ")
            return None
        if text == "NO_ACTIVATION":
##            log.w("Активации не существует")
            return None
        if text.startswith("STATUS_OK"):
##            log.i("Код получен")
            text = text.split(":")
            return text[1]
        else:
##            log.w("Статус получен: ", text)
            return None
            
    def SetFinish(self,phone): ##Изменение статуса активации
        url = f"/stubs/handler_api.php?action=setStatus&api_key={self.api_key}\
&id={phone.id}&status=6"
        response = self.request(url)

    def SetBan(self,phone): ##Изменение статуса активации
        url = f"/stubs/handler_api.php?action=setStatus&api_key={self.api_key}\
&id={phone.id}&status=8"
        response = self.request(url)
