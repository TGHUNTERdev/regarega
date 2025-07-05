import requests
import random
import os
import yarl
import time
TIME_SHEME="%Y-%m-%dT%H:%M:%S.%f%z"
##import datetime
from datetime import datetime
from Core.EmailService.Classes import Email
from Core.EmailService.Live.Classes import EmailStorage
from Core.EmailService.Live.EmailLiveService import EmailLiveService
from Core import Log as log
class EmailRentgmailService(EmailLiveService):
    name = "rentgmail"

    def load(self, config):
        EmailLiveService.load(self, config)
        self.mailDomains=[]
        for domain in config.getstring("mail domains").split(","):
            domain=domain.strip()
            if domain:
                self.mailDomains.append(domain)
                log.i(f"загружен домен {domain}")
        if isinstance(self.EmailStorage, EmailStorage):
            filename = config.getstring("email extend file")
            if os.path.isfile(filename):
                with open(filename, encoding='utf-8') as file:
                    count = 0
                    for line in file:
                        line = line.strip()
                        if line:
                            fullList = line.split('----')
                            address = fullList[0]
                            url = yarl.URL(fullList[1])
                            email_id = url.query["orderId"]
                            email = Email(email_id, address)
                            self.EmailStorage.emails.append(self.EmailStorage.push(email))
                            count += 1

                log.i(f"Загружено почт в хранилище: {count}")
                os.remove(filename)


        
    def GetEmail(self):
        path = '/prod/mail/order/rentMail?'
        params = {
            "token": self.api_key,
            "platform": self.service,
            "mailTypeCode": random.choice(self.mailDomains)
        }

        response = self.request(path, params=params)
##        log.d(response.request.url)
##        log.d(response.text)
        data = response.json()

        if data.get("code") == 200:
            email_data = data.get("data")
            if email_data:
                email_address = email_data["email"]
                activation_id = email_data["orderId"]
##                log.m(f"Получен email: {email_address}, ID: {activation_id}")
                
                return Email(activation_id, email_address)
##        else:
##            log.e(f"Ошибка получения email: {data}")
        

    def GetSms(self, email):
        path = '/prod/mail/order/mailOtp?'
        params = {
            "token": self.api_key,
            "orderId": email.id,
            "keepSecond":int(self.CodeWaitTime)
        }

        response = self.request(path, params=params) 
        data = response.json()

        if data.get("code") == 200:
            code_data = data.get("data")
            if code_data:
                src_update_time = code_data["updateTime"]
                get_update_time = datetime.strptime(src_update_time,TIME_SHEME)
                loc_update_time = get_update_time.timestamp()
##                utc_update_time = get_update_time.timestamp() - get_update_time.utcoffset().total_seconds()
##                utc_access_time = email.AccessTime + time.timezone
##                update_time = update_time + (-time.timezone)
##                log.d(f"{src_update_time} -> {get_update_time} -> {datetime.fromtimestamp(loc_update_time)} vs {datetime.fromtimestamp(email.AccessTime)}")
                if loc_update_time>email.AccessTime:
                    code = code_data["otp"]
                    log.d(
                        f"ПОЧТА - {email.address}",
                        "получен код - "+code,
                        "время получения - "+datetime.fromtimestamp(loc_update_time).strftime("%d.%m.%y %H:%M:%S"),
                        "время доступа - "+datetime.fromtimestamp(email.AccessTime).strftime("%d.%m.%y %H:%M:%S"),
                        "разница - "+str(round(loc_update_time-email.AccessTime))
                    )
##                log.m(f"Получен код для {email.address}: {code}")
                    return code
##        elif data.get("code") == "500":
##            return None
##        else:
##            log.e(f"Ошибка получения кода: {data}")
