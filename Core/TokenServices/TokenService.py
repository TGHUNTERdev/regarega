import os
import time
import base64
from Core import Log as log
from Core.TokenServices.Utils import antisafety
class TokenService:
    def __init__(self,core):
        self.core=core
    def LoadBase(self,config):
        self.key=config.getstring("key")
        antisafety.ANTISAFETY=config.getstring("host")
        self.PushTokenType=config.getint("token type")
    def load(self,config):
        pass
    def WaitPushToken(self):
        pass
    def ReleasePushToken(self,token):
        pass
    def DeletePushToken(self,token):
        pass
    def DropToken(self,token):
        pass
    def VerifySafetynet(self,nonce):
        reg_id, token = None, None
        sleep_tm = 5
        while not reg_id:
            reg_id = antisafety.create_safetynet(self.key, base64.b64encode(nonce).decode())
            if not reg_id:
                time.sleep(min(sleep_tm, 60))
                sleep_tm += 1
        sleep_tm = 1
        while not token:
            token = antisafety.get_safetynet(self.key, reg_id)
            if not token:
                time.sleep(min(sleep_tm, 30))
                sleep_tm += 1
        log.d(f"получен safetynet токен")
        return token
    def VerifyIntegrity(self,nonce):
        reg_id, token = None, None
        sleep_tm = 5
        while not reg_id:
            reg_id = antisafety.create_integrity(self.key, base64.b64encode(nonce).decode())
            if not reg_id:
                time.sleep(min(sleep_tm, 60))
                sleep_tm += 1
        sleep_tm = 1
        while not token:
            token = antisafety.get_integrity(self.key, reg_id)
            if not token:
                time.sleep(min(sleep_tm, 30))
                sleep_tm += 1
        log.d(f"получен integrity токен")
        return token

