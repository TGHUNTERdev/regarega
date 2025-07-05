# url = "http://api.activatecode.org/backend/out_interface.php?"
from Core import Log as log
from Core.SmsServices.Classes import Phone
from Core.SmsServices.SmsService import SmsService


class ActivatecodeService(SmsService):
    name = "activatecode"

    def load(self, config):
        self.api_key = config.getstring("api key")
        self.service = config.getstring("service")

    def GetCountries(self):
        raise ValueError("smsacktiwator сервис пока не поддерживает проверку стран")


    def GetPhone(self, country):
        url = f"/backend/out_interface.php?api_key={self.api_key}&action=getnumber&appcode={self.service}&country={country.code}"

        response = self.request(url)

##        log.d(url)
##        log.d(response.request.url)
##        log.d(response.text)

        if response.status_code != 200:
            raise RuntimeError(f"Ошибка запроса: {response.status_code}")

        data = response.json()

        code=data.get("ResponseCode")
        
        if code == 2:
            return
        elif code != 0:
            raise RuntimeError(f"Ошибка API: {data['Msg']}")

        result = data.get("Result")
        if not result:
            return None

        phone_id = result["id"]
        number = str(result["Number"])
        return Phone(phone_id, number)


    def GetSms(self, phone):
        url = f"/backend/out_interface.php?api_key={self.api_key}&action=getcode&id={phone.id}"

        response = self.request(url)

##        log.d(response.request.url)
##        log.d(response.text)

        if response.status_code != 200:
            raise RuntimeError(f"Ошибка запроса: {response.status_code}")

        data = response.json()

        code=data.get("ResponseCode")

        if code == 1:
            return
        elif code != 0:
            raise RuntimeError(f"Ошибка API: {data['Msg']}")

        result = data.get("Result")
        if not result:
            return None

        return str(result["Code"])


    def SetFinish(self,phone):
        pass

    def SetBan(self,phone):
        pass
