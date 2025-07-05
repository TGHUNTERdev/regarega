import requests
import random
from Core.EmailService.Live.Classes import EmailLive as Email
from Core.EmailService.Live.EmailLiveService import EmailLiveService
from Core import Log as log

class EmailActivateService(EmailLiveService):
    name = "emailactivate"

    def load(self, config):
        EmailLiveService.load(self, config)
        self.path = "/stubs/handler_api.php"
        self.mailType = config.getstring("mail type")
        self.mailDomains=[]
        for domain in config.getstring("mail domains").split(","):
            domain=domain.strip()
            if domain:
                self.mailDomains.append(domain)
                log.i(f"загружен домен {domain}")
##        self.mailDomain = config.getstring("mail domain")
        
    def GetEmail(self):
        params = {
            "api_key": self.api_key,
            "action": "buyMailActivation",
            "site": self.service,
            "mail_type": self.mailType,
            "mail_domain": random.choice(self.mailDomains)
        }

        response = self.request(self.path, params=params)
        data = response.json()

        if data.get("status") == "OK":
            email_data = data.get("response")
            if email_data:
                email_address = email_data["email"]
                activation_id = email_data["id"]
##                log.m(f"Получен email: {email_address}, ID: {activation_id}")
                
                return Email(activation_id, email_address)
##        else:
##            log.e(f"Ошибка получения email: {data}")
        

    def GetSms(self, email):
        params = {
            "api_key": self.api_key,
            "action": "checkMailActivation",
            "id": email.id
        }

        response = self.request(self.path, params=params)
        data = response.json()

        if data.get("status") == "OK":
            code_data = data.get("response")
            if code_data:
                code = code_data.get("value")
                if code:
##                    log.m(f"Получен код для {email.address}: {code}")
                    return code
        else:
            log.e(f"Ошибка получения кода: {data}")
