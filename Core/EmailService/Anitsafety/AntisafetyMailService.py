import time
from Core import Log as log
from Core.EmailService.Classes import Email
from Core.TokenServices.Utils import antisafety
from Core.EmailService.EmailService import EmailService
class AntisafetyMailService(EmailService):
    name="antisafety"
    def __init__(self,core):
        self.core=core
    def load(self,config):
        self.key=self.core.TokenService.key
        log.m(f"используется сервис {self.name} [{antisafety.ANTISAFETY}]")
        log.i("используется ключ из токен-сервиса")
        self.premium=config.getbool("premium")
        self.login=config.getbool("login")
    def WaitEmail(self):
##        reg_id, email = None, None
##        sleep_tm = 5
##        while not reg_id:
##            reg_id, email = antisafety.create_email(self.key, self.premium, self.login)
##            if not reg_id or not email:
##                time.sleep(min(sleep_tm, 60))
##                sleep_tm += 1
        data = None
        sleep_tm = 5
        while not data:
            data = antisafety.create_email(self.key, self.premium, self.login)
            if not data:
                time.sleep(min(sleep_tm, 60))
                sleep_tm += 1
        email=Email(
            data["id"],
            data["email"],
            None
        )
        if self.login:
            email.token=data.get("token")
            if email.token:
                log.w(f"получена почта с гугл идентификатором {email}")
                return email
        log.w(f"получена почта {email}")
        return email
    def WaitCode(self,email):
        code=antisafety.get_email(self.key, email.id, self.premium)
        if code:
            log.i(f"{email} получен код {code}")
            return code
        else:
            log.w(f"{email} неполучен код")
    def SetFinish(self,email):
        pass
    def SetBan(self,email):
        pass
    def DislikeEmail(self,email):
        if email.token:
            antisafety.dislike_email_google(self.key, email.id)
        else:
            antisafety.dislike_email(self.key, email.id)
