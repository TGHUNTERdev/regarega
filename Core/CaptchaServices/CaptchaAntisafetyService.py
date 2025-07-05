import os
import time
import threading as th
from Core import Log as log
from Core.TokenServices.Utils import antisafety
from Core.CaptchaServices.CaptchaService import CaptchaService
from Core.CaptchaServices.Classes import CaptchaToken
class CaptchaAntisafetyService(CaptchaService):
    name="antisafety"
    def load(self,config):
        self.key=self.core.TokenService.key
        log.m(f"используется сервис {self.name} [{antisafety.ANTISAFETY}]")
        log.i("используется ключ из токен-сервиса")
    def WaitCaptchaToken(self, action):
        reg_id, token = None, None
        sleep_tm = 5
        while not reg_id:
            reg_id = antisafety.create_recaptcha(self.key, action)
            if not reg_id:
                time.sleep(min(sleep_tm, 60))
                sleep_tm += 1
        sleep_tm = 1
        while not token:
            token = antisafety.get_recaptcha(self.key, reg_id)
            if not token:
                time.sleep(min(sleep_tm, 30))
                sleep_tm += 1
        return CaptchaToken(reg_id, token)

