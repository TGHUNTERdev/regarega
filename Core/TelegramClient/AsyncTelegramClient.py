import asyncio
import inspect
import time
import telethon.sync as telethon
from telethon.sync import syncify
from telethon.tl.types import JsonObject
from telethon.tl.types import JsonObjectValue
from telethon.tl.types import JsonString
from telethon.tl.types import JsonNumber
from Core import Log as log
def AntilonamiAsyncioIgnore(*args):
    pass
class TelegramClient(telethon.TelegramClient):
    CaptchaAction=None
    CaptchaSolve=False
    def __init__(self,core,path,pushtoken,data,proxy):
        self.core=core
        self.path=path
        self.data=data
##        log.d("сгенерированы данные:",self.data)
        self.proxy=proxy
        self.pushtoken=pushtoken
        self.regdata=None
        self.password=None
##        loop=asyncio.new_event_loop()
##        loop.set_exception_handler(AntilonamiAsyncioIgnore)
##        asyncio.set_event_loop(loop)
        telethon.TelegramClient.__init__(
            self,
            session=self.path+".session",
            api_id=data[0][0],
            api_hash=data[0][1],
            device_model=data[1],
            system_version=data[2],
            app_version=data[3],
            lang_code=data[4],
            system_lang_code=data[5],
            proxy=self.proxy.tolist(),
##            loop=loop,
            timeout=CONNECT_TIMEOUT,
            connection_retries=CONNECT_ATTEMPTS,
            retry_delay=CONNECT_DELAY,
            auto_reconnect=True
        )
##        self._init_request.lang_pack = "android"
        self._init_request.lang_pack = self.data[9]
        self._init_request.params = JsonObject([
            JsonObjectValue("device_token", JsonString(self.pushtoken.device)),
            JsonObjectValue("data", JsonString("49C1522548EBACD46CE322B6FD47F6092BB745D0F88082145CAF35E14DCC38E1")),
            JsonObjectValue("installer", JsonString("com.google.android.packageinstaller")),
            JsonObjectValue("package_id", JsonString(self.data[8])),
            JsonObjectValue("tz_offset", JsonNumber(self.data[6].offset)),
            JsonObjectValue("perf_cat", JsonNumber(self.data[7])),
        ])
##        log.d(self._init_request)
    async def TryCall(self,request):
        for i in range(SEND_ATTEMPTS):
            try:
                result=await asyncio.wait_for(telethon.TelegramClient.__call__(self,request),SEND_TIMEOUT)
##                result=await asyncio.wait_for(asyncio.Future(),1)
            except asyncio.IncompleteReadError:
                log.e(f"принятие битого ответа по запросу {type(request).__name__} через прокси {self.proxy}")
                time.sleep(SEND_DELAY)
            except asyncio.TimeoutError:
                log.e(f"превышен таймаут по запросу {type(request).__name__} через прокси {self.proxy}")
                time.sleep(SEND_DELAY)
            else:
                return result
        raise RuntimeError(f"невозможно выполнить запрос {type(request).__name__}")
    async def __call__(self,request):
        try:
            return await self.TryCall(request)
        except telethon.errors.RPCError as error:
##            log.w("ошибка вызова",error)
            prefix="RECAPTCHA_CHECK_"
            if error.code==403 and error.message.startswith(prefix) and self.CaptchaSolve:
                action,_,key=error.message[len(prefix):].partition("__")
                log.w("решение капчи",action,key)
                token=self.core.CaptchaService.WaitCaptchaToken(action).token
##                log.d(token)
                self.CaptchaAction=action
                return await self.TryCall(
                    telethon.functions.InvokeWithReCaptchaRequest(
                        token,
                        request
                    )
                )
            else:
                raise error
    async def connect(self):
        for i in range(SEND_ATTEMPTS):
            try:
                result=await asyncio.wait_for(telethon.TelegramClient.connect(self),SEND_TIMEOUT)
            except asyncio.IncompleteReadError:
                log.e(f"принятие битого ответа при подключении через прокси {self.proxy}")
                time.sleep(SEND_DELAY)
            except asyncio.TimeoutError:
                log.e(f"превышен таймаут при подключении через прокси {self.proxy}")
                time.sleep(SEND_DELAY)
            else:
                return result
        raise RuntimeError(f"невозможно подключиться через прокси {self.proxy}")
    async def ConnectToTelegram(self):
        await self.connect()
        await self(telethon.functions.help.GetNearestDcRequest())
        await self(telethon.functions.langpack.GetLangPackRequest("android","en"))
    async def SendCode(self,phone):
        self.phone=phone
##        return telethon.types.auth.SentCode(
##            telethon.types.auth.SentCodeTypeFirebaseSms(
##                8,
##                "213435"
##            ),
##            "1287654"
##        )
        sentcode=await self(telethon.functions.auth.SendCodeRequest(
            self.phone,
            self.data[0][0],
            self.data[0][1],
            telethon.types.CodeSettings(
                allow_firebase=True,
                allow_flashcall=True,
                app_sandbox=False,
                allow_missed_call=True,
                allow_app_hash=True,
                current_number=True,
                token="",
                logout_tokens=[]
            )
        ))
        if isinstance(sentcode,telethon.types.auth.SentCode):
##            sentcode.type=telethon.types.auth.SentCodeTypeSms(6)
            self.PhoneCodeHash=sentcode.phone_code_hash
            return sentcode
    async def ResendCode(self):
        sentcode=await self(telethon.functions.auth.ResendCodeRequest(
            self.phone,
            self.PhoneCodeHash
        ))
        if isinstance(sentcode,telethon.types.auth.SentCode):
            self.PhoneCodeHash=sentcode.phone_code_hash
            return sentcode
    async def SendEmail(self,email):
        return await self(telethon.functions.account.SendVerifyEmailCodeRequest(
            telethon.types.EmailVerifyPurposeLoginSetup(
                self.phone,
                self.PhoneCodeHash
            ),
            email
        ))
##    def VerifyEmail(self,code):
##        return self(telethon.functions.account.VerifyEmailRequest(
##            telethon.types.EmailVerifyPurposeLoginSetup(
##                self.phone,
##                self.PhoneCodeHash
##            ),
##            telethon.types.EmailVerificationCode(
##                code
##            )
##        ))
    async def VerifyEmail(self,verify):
##        log.d(verify)
        return await self(telethon.functions.account.VerifyEmailRequest(
            telethon.types.EmailVerifyPurposeLoginSetup(
                self.phone,
                self.PhoneCodeHash
            ),
            verify
        ))
    async def VerifyFirebase(self,token):
        return await self(telethon.functions.auth.RequestFirebaseSmsRequest(
            self.phone,
            self.PhoneCodeHash,
            token
        ))
    async def VerifyIntegrity(self,token):
        return await self(telethon.functions.auth.RequestFirebaseSmsRequest(
            self.phone,
            self.PhoneCodeHash,
            play_integrity_token = token
        ))
    async def signin(self,code):
        return await self(telethon.functions.auth.SignInRequest(
            self.phone,
            self.PhoneCodeHash,
            code
        ))
    async def signup(self,data,tos):
        self.regdata=data
        await self(telethon.functions.auth.SignUpRequest(
            self.phone,
            self.PhoneCodeHash,
            self.regdata[0],
            self.regdata[1]
        ))
        if tos:
            await self(telethon.functions.help.AcceptTermsOfServiceRequest(tos.id))
    async def RegisterDevice(self):
        await self(telethon.functions.account.RegisterDeviceRequest(
            self.pushtoken.type,
            self.pushtoken.device,
            False,
            self.pushtoken.secret,
            []
        ))
    async def setpassword(self,password):
        try:
            result=await self.edit_2fa(password)
        except:
            self.password=None
        else:
            if result:
                self.password=password
            else:
                self.password=None
    async def terminate(self):
        try:
            await self.disconnect()
        except:
            self.session.close()
def GetErrors():
    result=[]
    for name in dir(telethon.errors):
        value=getattr(telethon.errors,name)
        if inspect.isclass(value) and issubclass(value,telethon.errors.rpcbaseerrors.RPCError):
            result.append(value)
    return tuple(result)
def init(config):
    global CONNECT_TIMEOUT,CONNECT_ATTEMPTS,CONNECT_DELAY,SEND_TIMEOUT,SEND_ATTEMPTS,SEND_DELAY
    CONNECT_TIMEOUT=config.getdelay("connect timeout")
    CONNECT_ATTEMPTS=config.getint("connect attempts")
    if CONNECT_ATTEMPTS<=0:
        raise ValueError("количество попыток подключения должно быть больше нуля")
    CONNECT_DELAY=config.getdelay("connect delay")
    SEND_TIMEOUT=config.getdelay("send timeout")
    SEND_ATTEMPTS=config.getint("send attempts")
    SEND_DELAY=config.getdelay("send delay")
    import telethon
    layer=config.getint("layer")
    if layer>0:
        if telethon.tl.alltlobjects.LAYER!=layer:
            log.w("используется лайер не связаный с текущей версией телетона,соединение с телеграм может работать некорректно")
            telethon.tl.alltlobjects.LAYER=layer
            telethon.client.telegrambaseclient.LAYER=layer
    log.m("используется телетон",telethon.__version__,"лайер",telethon.tl.alltlobjects.LAYER)
##    syncify(TelegramClient)
