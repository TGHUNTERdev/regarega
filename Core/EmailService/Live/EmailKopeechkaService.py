import requests
import random
from Core.EmailService.Classes import Email
from Core.EmailService.Live.EmailLiveService import EmailLiveService
from Core import Log as log

class EmailKopeechkaService(EmailLiveService):
    name = "kopeechka"

    def load(self, config):
        EmailLiveService.load(self, config)
        
        # mailtype: ALL-случайные почты доменов копеечки
        # REAL: почты популярных доменов (gmail outlook, mail и т.д.)
        # либо группы почт (YANDEX, OUTLOOK, MAILCOM, MAILRU)
        self.mailDomains=[]
        for domain in config.getstring("mail domains").split(","):
            domain=domain.strip()
            if domain:
                self.mailDomains.append(domain)
                log.i(f"загружен домен {domain}")
        
    def GetEmail(self):
        path = '/mailbox-get-email?'
        params = {
            "token": self.api_key,
            "site": self.service,
            "mail_type": random.choice(self.mailDomains)
        }

        response = self.request(path, params=params)
        data = response.json()

        if data.get("status") == "OK":
            email_address = data["  mail"]
            activation_id = data["id"]
            log.m(f"Получен email: {email_address}, ID: {activation_id}")
            
            return Email(activation_id, email_address)
        else:
            log.e(f"Ошибка получения email: {data}")
        

    def GetSms(self, email):
        path = '/mailbox-get-message?'
        params = {
            "token": self.api_key,
            "id": email.id
        }

        response = self.request(path, params=params)
        data = response.json()

        if data.get("status") == "OK":
            code = data["value"]
            log.m(f"Получен код для {email.address}: {code}")
            return code
        else:
            log.e(f"Ошибка получения кода: {data}")
