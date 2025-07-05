import os
import time
from Core import Log as log
from Core.TokenServices.Classes import PushToken
from Core.TokenServices.TokenService import TokenService
class AutoPushService(TokenService):
    def WaitPushToken(self):
        token=PushToken(
            f"__FIREBASE_GENERATING_SINCE_{int(time.time())}__",
            self.PushTokenType,
            os.urandom(256)
        )
        log.d("пуш-токен сгенерирован")
        return token
