import os
import time
import threading as th
from Core import Log as log
from Core.TokenServices.Classes import PushToken
from Core.TokenServices.TokenService import TokenService
from Core.TokenServices.Classes import PushTokenStorage
from Core.TokenServices.Utils import antisafety
class AntisafetyService(TokenService):
    def load(self,config):
        self.PushTokenStorage=PushTokenStorage(
            config.getfile("token file"),
            config.getfile("token drop file")
        )
        self.ErrorTokenFile=config.newfile("error file")
        self.ErrorTokenLock=th.Lock()
    def WaitPushToken(self):
        pushtoken=self.PushTokenStorage.get()
        if pushtoken:
            log.d(f"получен пуш-токен с файла {pushtoken}")
            return pushtoken
        token=None
        while not token:
            token=self.GetPushToken()
        secret = os.urandom(256)
        token_type = self.PushTokenType
        pushtoken=PushToken(token, token_type, secret)
        self.PushTokenStorage.push(pushtoken)
        log.d(f"получен новый пуш-токен {pushtoken}")
        return pushtoken
    def GetPushToken(self):
##        log.d(f"получение ид задачи")
        reg_id, token, token_secret = None, None, None
        sleep_tm = 5
        while not reg_id:
            reg_id = antisafety.create_push(self.key)
            if not reg_id:
                time.sleep(min(sleep_tm, 60))
                sleep_tm += 1
        sleep_tm = 1
##        log.d(f"получение пуш-токена")
        while not token:
            token, _ = antisafety.get_push(self.key, reg_id)
##            token="none"
            if not token:
                time.sleep(min(sleep_tm, 30))
                sleep_tm += 1
            elif token.lower()=="none":
                with self.ErrorTokenLock:
                    with open(self.ErrorTokenFile,"a") as file:
                        file.write(reg_id+"\n")
                log.e(f"получен пустой пуш-токен {reg_id}")
                time.sleep(60)
                return
        return token
    def ReleasePushToken(self,token):
        log.d(f"{token} освобождён",level=log.level.debug)
        self.PushTokenStorage.release(token)
    def DeletePushToken(self,token):
        log.d(f"{token} удалён")
        self.PushTokenStorage.delete(token)
    def DropToken(self,token):
        log.d(f"{token} исключён")
        self.PushTokenStorage.drop(token)
        
