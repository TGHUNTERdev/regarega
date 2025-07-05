import asyncio
import inspect
import time
import telethon.sync as telethon
from telethon.sync import syncify
from telethon.tl.types import JsonObject, JsonObjectValue, JsonString, JsonNumber
from Core import Log as log

# Константы (будут переопределены в init())
CONNECT_TIMEOUT = 10
CONNECT_ATTEMPTS = 3
CONNECT_DELAY = 1
SEND_TIMEOUT = 10
SEND_ATTEMPTS = 3
SEND_DELAY = 1

class AntilonamiAsyncioIgnore:
    @staticmethod
    def handle_exception(loop, context):
        pass

class TelegramClient(telethon.TelegramClient):
    CaptchaAction = None
    CaptchaSolve = False
    
    def __init__(self, core, path, pushtoken, data, proxy):
        self.core = core
        self.path = path
        self.data = data
        self.proxy = proxy
        self.pushtoken = pushtoken
        self.regdata = None
        self.password = None
        self.phone = None
        self.PhoneCodeHash = None
        
        # Инициализация event loop
        self._loop = asyncio.new_event_loop()
        self._loop.set_exception_handler(AntilonamiAsyncioIgnore.handle_exception)
        asyncio.set_event_loop(self._loop)
        
        # Инициализация базового клиента
        super().__init__(
            session=self.path + ".session",
            api_id=data[0][0],
            api_hash=data[0][1],
            device_model=data[1],
            system_version=data[2],
            app_version=data[3],
            lang_code=data[4],
            system_lang_code=data[5],
            proxy=self.proxy.tolist() if hasattr(proxy, 'tolist') else proxy,
            loop=self._loop,
            timeout=CONNECT_TIMEOUT,
            connection_retries=CONNECT_ATTEMPTS,
            retry_delay=CONNECT_DELAY,
            auto_reconnect=True
        )
        
        # Настройка параметров инициализации
        self._init_request.lang_pack = self.data[9]
        self._init_request.params = JsonObject([
            JsonObjectValue("device_token", JsonString(self.pushtoken.device)),
            JsonObjectValue("data", JsonString("")),
            JsonObjectValue("installer", JsonString("com.google.android.packageinstaller")),
            JsonObjectValue("package_id", JsonString(self.data[8])),
            JsonObjectValue("tz_offset", JsonNumber(self.data[6].offset)),
            JsonObjectValue("perf_cat", JsonNumber(self.data[7])),
        ])

    async def TryCall(self, request):
        last_exception = None
        for i in range(SEND_ATTEMPTS):
            try:
                result = await asyncio.wait_for(
                    super().__call__(request),
                    SEND_TIMEOUT
                )
                return result
            except (asyncio.IncompleteReadError, asyncio.TimeoutError) as e:
                log.e(f"Ошибка запроса {type(request).__name__} через прокси {self.proxy}: {str(e)}")
                last_exception = e
                await asyncio.sleep(SEND_DELAY)
            except Exception as e:
                log.e(f"Неожиданная ошибка при запросе {type(request).__name__}: {str(e)}")
                last_exception = e
                await asyncio.sleep(SEND_DELAY)
        
        raise RuntimeError(f"Не удалось выполнить запрос {type(request).__name__} после {SEND_ATTEMPTS} попыток") from last_exception

    async def __call__(self, request):
        try:
            return await self.TryCall(request)
        except telethon.errors.RPCError as error:
            if error.code == 403 and error.message.startswith("RECAPTCHA_CHECK_") and self.CaptchaSolve:
                prefix = "RECAPTCHA_CHECK_"
                action, _, key = error.message[len(prefix):].partition("__")
                log.w(f"Требуется решение капчи: {action} {key}")
                
                try:
                    token = await self.core.CaptchaService.WaitCaptchaToken(action)
                    self.CaptchaAction = action
                    return await self.TryCall(
                        telethon.functions.InvokeWithReCaptchaRequest(
                            token.token,
                            request
                        )
                    )
                except Exception as captcha_error:
                    log.e(f"Ошибка при обработке капчи: {str(captcha_error)}")
                    raise error from captcha_error
            raise

    async def connect(self):
        last_exception = None
        for i in range(CONNECT_ATTEMPTS):
            try:
                result = await asyncio.wait_for(
                    super().connect(),
                    CONNECT_TIMEOUT
                )
                return result
            except (asyncio.IncompleteReadError, asyncio.TimeoutError) as e:
                log.e(f"Ошибка подключения через прокси {self.proxy}: {str(e)}")
                last_exception = e
                await asyncio.sleep(CONNECT_DELAY)
            except Exception as e:
                log.e(f"Неожиданная ошибка подключения: {str(e)}")
                last_exception = e
                await asyncio.sleep(CONNECT_DELAY)
        
        raise RuntimeError(f"Не удалось подключиться через прокси {self.proxy}") from last_exception

    def ConnectToTelegram(self):
        self._loop.run_until_complete(self.connect())
        self._loop.run_until_complete(self(telethon.functions.help.GetNearestDcRequest()))
        self._loop.run_until_complete(self(telethon.functions.langpack.GetLangPackRequest("android", "en")))

    def SendCode(self, phone):
        self.phone = phone
        sentcode = self._loop.run_until_complete(self(telethon.functions.auth.SendCodeRequest(
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
        )))
        
        if isinstance(sentcode, telethon.types.auth.SentCode):
            self.PhoneCodeHash = sentcode.phone_code_hash
            return sentcode
        return None

    def ResendCode(self):
        if not hasattr(self, 'PhoneCodeHash'):
            raise ValueError("PhoneCodeHash не установлен")
            
        sentcode = self._loop.run_until_complete(self(telethon.functions.auth.ResendCodeRequest(
            self.phone,
            self.PhoneCodeHash
        )))
        
        if isinstance(sentcode, telethon.types.auth.SentCode):
            self.PhoneCodeHash = sentcode.phone_code_hash
            return sentcode
        return None

    def SendEmail(self, email):
        return self._loop.run_until_complete(self(telethon.functions.account.SendVerifyEmailCodeRequest(
            telethon.types.EmailVerifyPurposeLoginSetup(
                self.phone,
                self.PhoneCodeHash
            ),
            email
        )))

    def VerifyEmail(self, verify):
        return self._loop.run_until_complete(self(telethon.functions.account.VerifyEmailRequest(
            telethon.types.EmailVerifyPurposeLoginSetup(
                self.phone,
                self.PhoneCodeHash
            ),
            verify
        )))

    def VerifyFirebase(self, token):
        return self._loop.run_until_complete(self(telethon.functions.auth.RequestFirebaseSmsRequest(
            self.phone,
            self.PhoneCodeHash,
            token
        )))

    def VerifyIntegrity(self, token):
        return self._loop.run_until_complete(self(telethon.functions.auth.RequestFirebaseSmsRequest(
            self.phone,
            self.PhoneCodeHash,
            play_integrity_token=token
        )))

    def signin(self, code):
        return self._loop.run_until_complete(self(telethon.functions.auth.SignInRequest(
            self.phone,
            self.PhoneCodeHash,
            code
        )))

    def signup(self, data, tos):
        self.regdata = data
        result = self._loop.run_until_complete(self(telethon.functions.auth.SignUpRequest(
            self.phone,
            self.PhoneCodeHash,
            self.regdata[0],
            self.regdata[1]
        )))
        
        if tos:
            self._loop.run_until_complete(self(telethon.functions.help.AcceptTermsOfServiceRequest(tos.id)))
        return result

    def RegisterDevice(self):
        return self._loop.run_until_complete(self(telethon.functions.account.RegisterDeviceRequest(
            self.pushtoken.type,
            self.pushtoken.device,
            False,
            self.pushtoken.secret,
            []
        )))

    def setpassword(self, password):
        try:
            result = self._loop.run_until_complete(self.edit_2fa(password))
            self.password = password if result else None
            return result
        except Exception as e:
            log.e(f"Ошибка установки пароля: {str(e)}")
            self.password = None
            return False

    def terminate(self):
        try:
            self._loop.run_until_complete(self.disconnect())
        except Exception as e:
            log.e(f"Ошибка при завершении работы: {str(e)}")
        finally:
            if hasattr(self, '_loop'):
                self._loop.close()

def GetErrors():
    return tuple(
        value for name, value in vars(telethon.errors).items()
        if inspect.isclass(value) and issubclass(value, telethon.errors.rpcbaseerrors.RPCError)
    )

def init(config):
    global CONNECT_TIMEOUT, CONNECT_ATTEMPTS, CONNECT_DELAY
    global SEND_TIMEOUT, SEND_ATTEMPTS, SEND_DELAY
    
    CONNECT_TIMEOUT = config.getdelay("connect timeout")
    CONNECT_ATTEMPTS = config.getint("connect attempts")
    if CONNECT_ATTEMPTS <= 0:
        raise ValueError("Количество попыток подключения должно быть больше нуля")
    CONNECT_DELAY = config.getdelay("connect delay")
    
    SEND_TIMEOUT = config.getdelay("send timeout")
    SEND_ATTEMPTS = config.getint("send attempts")
    SEND_DELAY = config.getdelay("send delay")
    
    layer = config.getint("layer")
    if layer > 0 and telethon.tl.alltlobjects.LAYER != layer:
        log.w(f"Используется слой {layer}, не связанный с текущей версией Telethon ({telethon.tl.alltlobjects.LAYER})")
        telethon.tl.alltlobjects.LAYER = layer
        telethon.client.telegrambaseclient.LAYER = layer
    
    log.m(f"Используется Telethon {telethon.__version__}, слой {telethon.tl.alltlobjects.LAYER}")
    syncify(TelegramClient)