import time
import requests
from Core import Log as log
from Core.EmailService.Classes import Email
from Core.TokenServices.Utils import antisafety
from Core.EmailService.EmailService import EmailService
class SelfMailService(EmailService):
    name="selfmail"
    def load(self,config):
        self.host=config.gethost("host")
        log.m(f"используется сервис {self.name} [{self.host}]")
        self.MailDefaultDelay=config.getdelay("mail default delay")
        self.MailErrorDelay=config.getdelay("mail error delay")
        self.CodeDefaultDelay=config.getdelay("code default delay")
        self.CodeErrorDelay=config.getdelay("code error delay")
        self.CodeWaitTime=config.getdelay("code wait time")
    def WaitEmail(self):
        while True:
            try:
                response=self.request({
                    "action":"newMail",
                    "checktime":self.CodeDefaultDelay,
                    "waittime":self.CodeWaitTime
                })
            except Exception as e:
                log.e(f"ошибка при получении почты: {e}",level=log.level.debug)
                time.sleep(self.MailErrorDelay)
            else:
                data=response.text
                if data.startswith("ID"):
                    sid=data.split(":")[1]
                    log.d(f"получен индентификатор {sid}",level=log.level.debug)
                    address=self.WaitAddress(sid)
                    if address:
                        log.w(f"получена почта {address}")
                        return Email(sid,address)
                    else:
                        log.d(f"почта не активирована",level=log.level.debug)
                time.sleep(self.MailDefaultDelay)
    def WaitAddress(self,sid):
        while True:
            try:
                response=self.request({
                    "action":"getMail",
                    "id":sid
                })
            except Exception as e:
                log.e(f"ошибка при получении адреса: {e}",level=log.level.debug)
                time.sleep(self.MailErrorDelay)
            else:
                data=response.text
                if data=="NO SESSION":
                    return
                elif data.startswith("MAIL"):
                    return data.split(":")[1]
                time.sleep(self.MailDefaultDelay)
    def WaitCode(self,email):
        first=time.time()
        limit=first+self.CodeWaitTime
        while True:
            try:
                reqtime=time.time()
                response=self.request({
                    "action":"getStatus",
                    "id":email.id
                })
            except Exception as e:
                log.e(f"{email}: ошибка получения кода: {e}")
                time.sleep(self.CodeErrorDelay)
            else:
                data=response.text
                if data.startswith("CODE"):
                    code=data.split(":")[1]
                    log.i(f"{email} получен код {code}")
                    return code
                elif reqtime>limit:
                    log.w(f"{email} код не пришёл в течении {int(reqtime-first)}s")
                    return
                time.sleep(self.CodeDefaultDelay)
    def SetFinish(self,email):
        return self.request({
            "action":"setStatus",
            "id":email.id,
            "status":"success"
        })
    def SetBan(self,email):
        return self.request({
            "action":"setStatus",
            "id":email.id,
            "status":"fail"
        })
    def DislikeEmail(self,email):
        self.SetBan(email)
    def request(self,params):
        return requests.get(
            self.host+"/api",
            params=params
        )
