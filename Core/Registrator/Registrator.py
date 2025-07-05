import telethon
import time
import random
import json
import os
from telethon.tl.types import auth
from Core.TelegramClient import TelegramClient
from Core import Log as log
from Core.CrushReport import CrushReport
from Core.Registrator.Classes import Account
##class EmailCheckerLoader:
##    def __init__(self,config,handlers,function):
##        self.config=config
##        self.handlers=handlers
##        self.function=function
##    def load(self,keytype,action):
##        key="if not email with "+keytype
##        value=self.config.getstring(key)
##        if value=="ignore":
##            log.w(f"проверка почты для {keytype} отключена")
##            return action
##        else:
##            noaction=self.handlers.get(value)
##            if noaction:
##                log.i(f"при отсутсвии почты для {keytype} выбрано действие {value}")
##                return lambda account: self.function(account,action,noaction)
##            else:
##                raise ValueError(f"параметр {key} может принимать только значения "+", ".join(self.handlers.keys())+" или ignore")
class Registrator:
    name="synchronous"
    def __init__(self,core):
        self.core=core
    def load(self,config):
##        log.m(f"используется регер {self.name}")
        self.DefaultResendTimeout=config.getdelay("default resend timeout")
        self.RsendTimeoutLimit=config.getdelay("resend timeout limit")
##        checker=EmailCheckerLoader(config,{
##            "skip":self.ActionSkipCode,
##            "restart":self.ActionRestartClient,
##            "droptoken":lambda a:self.ActionRestartClient(a,drop=True)
##        },self.ActionCheckEmail)
        CheckerHandlers={
            "skip":self.ActionSkipCode,
            "restart":self.ActionRestartClient,
            "droptoken":lambda a:self.ActionRestartClient(a,drop=True)
        }
        DefaultHandlers={
            "skip":self.ActionSkipCode,
            "resend":self.ActionResendCode,
            "restart":self.ActionRestartClient,
            "droptoken":lambda a:self.ActionRestartClient(a,drop=True)
        }
        CallHandlers={
            "skip":self.ActionSkipCode,
            "resend":self.ActionResendCode,
            "restart":self.ActionRestartClient,
            "droptoken":lambda a:self.ActionRestartClient(a,drop=True),
            "waitcode":self.ActionWaitSms
##            "waitcode":checker.load("call",self.ActionWaitSms)
        }
        EmailHandlers={
            "skip":self.ActionSkipCode,
            "resend":self.ActionResendCode,
            "restart":self.ActionRestartClient,
            "droptoken":lambda a:self.ActionRestartClient(a,drop=True),
            "verify":self.ActionVerifyEmail
        }
        FirebaseHandlers={
            "skip":self.ActionSkipCode,
            "resend":self.ActionResendCode,
            "restart":self.ActionRestartClient,
            "droptoken":lambda a:self.ActionRestartClient(a,drop=True),
            "verify":self.ActionVerifyFirebase,
            "waitsms":self.ActionWaitFirebaseSms
##            "verify":checker.load("fb verify",self.ActionVerifyFirebase),
##            "waitsms":checker.load("fb waitsms",self.ActionWaitFirebaseSms)
        }
        SmsHadlers={
            "skip":self.ActionSkipCode,
            "resend":self.ActionResendCode,
            "restart":self.ActionRestartClient,
            "droptoken":lambda a:self.ActionRestartClient(a,drop=True),
            "waitsms":self.ActionWaitSms
##            "waitsms":checker.load("sms",self.ActionWaitSms)
        }
        self.LoadHandlers(
            config,
            [
                (auth.SentCodeTypeApp,"app",DefaultHandlers),
                (auth.SentCodeTypeCall,"call",CallHandlers),
                (auth.SentCodeTypeFlashCall,"flash call",CallHandlers),
                (auth.SentCodeTypeMissedCall,"missed call",CallHandlers),
                (auth.SentCodeTypeSetUpEmailRequired,"setup email",EmailHandlers),
                (auth.SentCodeTypeFragmentSms,"fragment sms",DefaultHandlers),
                (auth.SentCodeTypeFirebaseSms,"firebase sms",FirebaseHandlers),
                (auth.SentCodeTypeEmailCode,"email code",DefaultHandlers),
                (auth.SentCodeTypeSms,"sms",SmsHadlers)
            ]
        )
        self.LoadCheckers(
            config,
            [
                (auth.SentCodeTypeApp,"app",CheckerHandlers),
                (auth.SentCodeTypeCall,"call",CheckerHandlers),
                (auth.SentCodeTypeFlashCall,"flash call",CheckerHandlers),
                (auth.SentCodeTypeMissedCall,"missed call",CheckerHandlers),
##                (auth.SentCodeTypeSetUpEmailRequired,"setup email",CheckerHandlers),
                (auth.SentCodeTypeFragmentSms,"fragment sms",CheckerHandlers),
                (auth.SentCodeTypeFirebaseSms,"firebase sms",CheckerHandlers),
##                (auth.SentCodeTypeEmailCode,"email code",CheckerHandlers),
                (auth.SentCodeTypeSms,"sms",CheckerHandlers)
            ]
        )
##        self.handlers[auth.SentCodeTypeSms]=self.ActionWaitSms
##        self.PhoneInvalidAction=config.select("if phone invalid",{
##            "skip":self.ActionSkipCode,
##            "restart":self.ActionRestartClient,
##            "droptoken":lambda a:self.ActionRestartClient(a,drop=True)
##        })
        self.EmailSetupAttempts=config.getint("email setup attempts")
        self.TempAccountDir=config.getdir("temp account dir")
        for file in os.listdir(self.TempAccountDir):
            os.remove(self.TempAccountDir+"/"+file)
            log.w(f"уничтожен {file}")
        self.RegisteredAccountDir=config.getdir("registered account dir")
        self.AuthorizedAccountDir=config.getdir("authorized account dir")
        self.ActionPassword=self.ActionSetPassword if config.getbool("setup 2fa") else self.ActionSaveAccount
##        self.FirebaseRestartNoEmail=config.getbool("firebase restart no email")
        self.RestartLimit=config.getint("restart limit")
        self.RestartWait=config.getdelay("restart wait")
        self.EnableIntegrityVerification=config.getbool("enable integrity verification")
        if self.EnableIntegrityVerification:
            log.i("включена верификация integrity токена при проверке firebase")
        self.CaptchaSolve=config.getbool("enable captcha solve")
        if self.CaptchaSolve:
            log.i("включена проверка капч")
        self.TelegramErrors=TelegramClient.GetErrors()
    def LoadHandlers(self,config,data):
        self.handlers={}
        for codetype,key,variants in data:
            variant=config.getenum("if code type "+key,tuple(variants.keys()))
            self.handlers[codetype]=variants[variant]
            log.i(f"обработчик code type {key} задан как {variant}")
    def LoadCheckers(self,config,data):
        self.checkers={}
        filters=[
            ("email","почты"),
            ("captcha","капчи")
        ]
        for codetype,keytype,variants in data:
            checkers=[None]*2
            self.checkers[codetype]=checkers
            for index,(check,name) in enumerate(filters):
                key=f"if not {check} with "+keytype
                value=config.getstring(key)
                if value=="ignore":
                    log.w(f"проверка {name} для {keytype} отключена")
                else:
                    action=variants.get(value)
                    if action:
                        log.i(f"при отсутсвии {name} для {keytype} выбрано действие {value}")
                        checkers[index]=action
##                        self.checkers[codetype]=action
                    else:
                        raise ValueError(f"параметр {key} может принимать только значения "+", ".join(variants.keys())+" или ignore")
    def registrate(self,country):
        log.d(f"{country} регистрация",level=log.level.debug)
        account=Account(country)
        action=self.ActionGetPhone
        with CrushReport("ошибка регистрации"):
            try:
                while action:
                    account.ActionSequence.append(action.__name__)
##                    if account.statefile:
##                        account.savestate()
                    action=action(account)
            except self.TelegramErrors as e:
                account.status="error"
                account.error=str(e)
                log.e(f"{account} произошла внутрения ошибка телеграм: {e}")
        if account.statefile:
##            account.savestate()
            self.core.stat.push(account.getstate())
##            os.remove(account.statefile)
        if account.client:
            if account.begin:
                log.d(f"{account} отключение",level=log.level.debug)
                self.core.TokenService.ReleasePushToken(account.client.pushtoken)
                account.client.terminate()
                os.remove(account.client.path+".session")
                if account.email:
                    self.core.EmailService.SetBan(account.email)
            elif account.email:
                self.core.EmailService.SetFinish(account.email)
    def ActionGetPhone(self,account):
        log.d(f"{account.country} получение номера",level=log.level.debug)
        phone=self.core.SmsService.WaitPhone(account.country)
        if phone:
            account.phone=phone
            account.statefile=self.TempAccountDir+"/"+account.phone.number+".state"
            return self.ActionCreateClient
    def ActionCreateClient(self,account):
        log.d(f"{account} создание клиента",level=log.level.debug)
        token=self.core.TokenService.WaitPushToken()
        proxy=account.country.proxy if account.country.proxy else self.core.generator.ProxyData.get()
        account.client=TelegramClient.TelegramClient(
            self.core,
            self.TempAccountDir+"/"+account.phone.number,
            token,
            self.core.generator.GenerateBaseClientData(proxy),
            proxy
##            self.core.generator.GenerateClientData(
##                self.core.generator.ClientData
##            ),
##            account.country.proxy if account.country.proxy else self.core.generator.ProxyData.get()
        )
        account.client.CaptchaSolve=self.CaptchaSolve
        try:
            account.client.ConnectToTelegram()
        except Exception as e:
            log.w(f"{account} ошибка подключения через {account.client.proxy}: {e}")
            self.core.TokenService.ReleasePushToken(account.client.pushtoken)
            account.client.terminate()
            return self.ActionCreateClient
        else:
            log.d(f"{account} подключился через {account.client.proxy}")
            if account.client.is_user_authorized():
                log.w(f"{account} уже авторизован")
            else:
                self.core.generator.SaveClientData(
                    account.data,
                    self.core.generator.ClientData,
                    account.client.data
                )
                self.core.generator.ProxyData.save(
                    account.data,
                    account.client.proxy
                )
                return self.ActionSendCode
##                account.path=self.RegisteredAccountDir
##                return self.ActionSaveAccount
    def ActionRestartClient(self,account,drop=False):
        if account.restarts<self.RestartLimit:
            account.restarts+=1
            log.w(f"{account} перезапуск {account.restarts} / {self.RestartLimit}")
            if drop:
                self.core.TokenService.DropToken(account.client.pushtoken)
            else:
                self.core.TokenService.ReleasePushToken(account.client.pushtoken)
            account.client.terminate()
            os.remove(account.client.path+".session")
            time.sleep(self.RestartWait)
            return self.ActionCreateClient
        else:
            log.e(f"{account} исчерпан лимит перезапусков")
    def ActionSendCode(self,account):
        log.d(f"{account} отправка кода",level=log.level.debug)
        try:
            account.setsentcode(account.client.SendCode(account.phone.number))
        except telethon.errors.PhoneNumberBannedError:
            log.e(f"{account} номер забанен")
            account.status="phone banned"
            self.core.SmsService.SetBan(account.phone)
        except telethon.errors.PhoneNumberFloodError:
            log.e(f"{account} номер во флуде")
            account.status="phone flood"
        else:
            return self.ActionHandleCode
    def ActionHandleCode(self,account):
        log.d(f"{account} обработка кода {type(account.sentcode.type).__name__}")
        if account.sentcode:
            checker=self.checkers.get(type(account.sentcode.type))
            if checker:
                if not account.email and checker[0]:
                    log.e(f"{account} почта не установлена")
                    return checker[0]
                if not account.client.CaptchaAction and checker[1]:
                    log.e(f"{account} капча не установлена")
                    return checker[1]
            action=self.handlers.get(type(account.sentcode.type))
            if action:
                return action
            else:
                log.w(f"{account} {account.sentcode.type} неизвестен")
                account.status="sentcode undefined"
                return
    def ActionResendCode(self,account):
        log.d(f"{account} переотправка кода",level=log.level.debug)
        if account.sentcode.next_type:
            if account.sentcode.timeout:
                if account.sentcode.timeout<self.RsendTimeoutLimit:
                    timeout=account.sentcode.timeout
                else:
                    log.w(f"{account} превышен таймаут переотправки кода {account.sentcode.timeout}s")
                    account.status="resend timeout uplimit"
                    return
            else:
                timeout=self.DefaultResendTimeout
            log.d(f"{account} ожидание {timeout}s")
            time.sleep(timeout)
            account.setsentcode(account.client.ResendCode())
            return self.ActionHandleCode
        else:
            log.w(f"{account} невозможно выполнить переотправку кода")
            account.status="not resend"
            return
    def ActionSkipCode(self,account):
        log.w(f"{account} {type(account.sentcode.type).__name__} пропущен")
    def ActionVerifyEmail(self,account):
        if account.email:
            log.w(f"{account} почта уже была настроена")
            account.status="email setup"
            return
        for i in range(self.EmailSetupAttempts):
            log.d(f"{account} получение почты (попытка {i+1}/{self.EmailSetupAttempts})")
            account.email=self.core.EmailService.WaitEmail()
            if not account.email:
                continue
            time.sleep(random.randint(7,15))
            if account.email.token:
                emailcode=telethon.types.EmailVerificationGoogle(
                    account.email.token
                )
            else:
                log.d(f"{account} отправка почты",level=log.level.debug)
                account.client.SendEmail(account.email.address)
                log.d(f"{account} ожидание кода",level=log.level.debug)
                emailcode=self.core.EmailService.WaitCode(account.email)
                if emailcode:
                    emailcode=telethon.types.EmailVerificationCode(
                        emailcode
                    )
                else:
                    account.status="email not code"
##                    self.core.EmailService.SetBan(account.email)
                    self.core.EmailService.SetNoCode(account.email)
                    account.email=None
                    continue
##            log.d(f"{account} отправка почты",level=log.level.debug)
##            account.client.SendEmail(account.email.address)
##            log.d(f"{account} ожидание кода",level=log.level.debug)
##            emailcode=self.core.EmailService.WaitCode(account.email)
##            if emailcode:
            try:
                log.d(f"{account} верификация почты",level=log.level.debug)
##                    verify=account.client.VerifyEmail(emailcode)
                verify=account.client.VerifyEmail(
                    emailcode
                )
            except telethon.errors.CodeInvalidError:
                log.w(f"{account} неверный код")
                account.status="wrong email code"
                self.core.EmailService.SetWrongCode(account.email)
                account.email=None
                continue
            except telethon.errors.BadRequestError as e:
                log.w(f"{account} не валидная почта: {e}")
                self.core.EmailService.DislikeEmail(account.email)
            else:
                if isinstance(verify,telethon.tl.types.account.EmailVerifiedLogin):
                    log.d(f"{account} почта успешно верифицирована")
                    account.setsentcode(verify.sent_code)
                    return self.ActionHandleCode
                else:
                    log.e(f"{account} почта не верифицирована")
                    account.status="email not verifed"
                    self.core.EmailService.SetBan(account.email)
                    account.email=None
                    continue
        account.status="email not setup"
        log.w(f"{account} почта не настроена")
##    def ActionCheckEmail(self,account,action,noaction):
##        if account.email:
##            return action
##        else:
##            log.e(f"{account} почта не установлена")
##            return noaction
##    def ActionVerifyEmailGoogle(self,account):
##        if account.email:
##            log.w(f"{account} почта уже была настроена")
##            account.status="email setup"
##            return
##        for i in range(self.EmailSetupAttempts):
##            log.d(f"{account} получение почты с гугл идентификатором (попытка {i+1}/{self.EmailSetupAttempts})")
##            account.email=self.EmailService.WaitEmailGoogle()
##            time.sleep(random.randint(7,15))
##            try:
##                log.d(f"{account} верификация почты через гугл идентификатор",level=log.level.debug)
##                verify=account.client.VerifyEmail(
##                    telethon.types.EmailVerificationGoogle(
##                        email.token
##                    )
##                )
##            except telethon.errors.CodeInvalidError:
##                log.w(f"{account} неверный токен")
##                account.status="wrong email code"
##                return
##            except telethon.errors.BadRequestError as e:
##                log.w(f"{account} не валидная почта: {e}")
##                self.core.EmailService.DislikeEmailGoogle(account.email)
##            else:
##                if isinstance(verify,telethon.tl.types.account.EmailVerifiedLogin):
##                    log.d(f"{account} почта успешно верифицирована")
##                    account.setsentcode(verify.sent_code)
##                    return self.ActionHandleCode
##                else:
##                    log.e(f"{account} почта не верифицирована")
##                    account.status="email not verifed"
##                    return
    def ActionVerifyFirebase(self,account):
##        if self.FirebaseRestartNoEmail and (not account.email):
##            log.d(f"{account} почта не установлена, перезапуск")
##            return self.ActionRestartClient
        log.d(f"{account} верификация firebase",level=log.level.debug)
        if self.EnableIntegrityVerification and account.sentcode.type.play_integrity_nonce:
            token=self.core.TokenService.VerifyIntegrity(account.sentcode.type.play_integrity_nonce)
            if account.client.VerifyIntegrity(token):
                log.d(f"{account} верификация integrity прошла успешно")
                return self.ActionWaitSms
            else:
                log.w(f"{account} верификация integrity прошла неуспешно")
        else:
            token=self.core.TokenService.VerifySafetynet(account.sentcode.type.nonce)
            if account.client.VerifyFirebase(token):
                log.d(f"{account} верификация safetynet прошла успешно")
                return self.ActionWaitSms
            else:
                log.w(f"{account} верификация safetynet прошла неуспешно")
    def ActionWaitFirebaseSms(self,account):
##        if self.FirebaseRestartNoEmail and (not account.email):
##            log.d(f"{account} почта не установлена, перезапуск")
##            return self.ActionRestartClient
        log.d(f"{account} имитация верификации firebase",level=log.level.debug)
        if account.client.VerifyFirebase(account.sentcode.type.nonce):
            log.d(f"{account} верификация firebase прошла успешно")
            return self.ActionWaitSms
        else:
            log.w(f"{account} верификация firebase прошла неуспешно")
            account.status="firebase not verifed"
            return
    def ActionWaitSms(self,account):
        log.a(f"{account} ожидание смс")
##        log.d(f"{account} длинна кода {account.sentcode.type.length}")
        account.smscode=self.core.SmsService.WaitCode(account.phone)
        if account.smscode:
            return self.ActionRegistrate
        else:
            account.status="not sms"
            return
    def ActionRegistrate(self,account):
        log.d(f"{account} авторизация",level=log.level.debug)
        try:
            auth=account.client.signin(account.smscode)
        except telethon.errors.SessionPasswordNeededError:
            log.e(f"{account} требуется пароль")
            account.status="2fa"
            return
        else:
            if isinstance(auth,telethon.types.auth.AuthorizationSignUpRequired):
                log.d(f"{account} содание учётной записи",level=log.level.debug)
                account.client.signup(
                    self.core.generator.GenerateClientData(
                        self.core.generator.AddationData
                    ),
                    auth.terms_of_service
                )
                account.path=self.RegisteredAccountDir
                self.core.generator.SaveClientData(
                    account.data,
                    self.core.generator.AddationData,
                    account.client.regdata
                )
                account.status="registered"
                log.i(f"{account} учётная запись успешно создана")
            else:
                account.path=self.AuthorizedAccountDir
                account.status="authorized"
                log.i(f"{account} уже существует")
            log.d(f"{account} регистрация устройства",level=log.level.debug)
            account.client.RegisterDevice()
            self.core.TokenService.DeletePushToken(account.client.pushtoken)
            return self.ActionPassword
    def ActionSetPassword(self,account):
        log.d(f"{account} установка двухфакторки")
        account.client.setpassword(self.core.generator.PasswordData.get())
        self.core.generator.PasswordData.save(
            account.data,
            account.client.password
        )
        return self.ActionSaveAccount
    def ActionSaveAccount(self,account):
        log.d(f"{account} отключение",level=log.level.debug)
        account.client.terminate()
        account.begin=False
        log.d(f"{account} сохранение данных",level=log.level.debug)
        if account.phone.number[0]=="+":
            savepath=account.path+"/"+account.phone.number[1:]
        else:
            savepath=account.path+"/"+account.phone.number
        os.rename(account.client.path+".session",savepath+".session")
        data={
            "session_file":account.phone.number+".session",
            "phone":account.phone.number,
            "device_token":account.client.pushtoken.device,
            "register_time":time.time(),
            "last_check_time":time.time(),
            "avatar":None,
            "sex":0,
            "ipv6":False
        }
        data.update(account.data)
        with open(savepath+".json","w",encoding="utf-8") as file:
            json.dump(data,file)
        log.a(f"{account} создан",level=log.level.debug)
