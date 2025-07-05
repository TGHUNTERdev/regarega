import threading as th
import time
import requests
import random
import json
from Core import Log as log
from Core.EmailService.Live.Classes import Email
from Core.EmailService.Live.Classes import EmailStorage,EmailStorageEmpty,EmailStorageRemote
from Core.EmailService.EmailService import EmailService
class EmailLiveService(EmailService):
    name="smslive"
    def __init__(self,core):
        self.core=core
        self.service=None
        self.countries=[]
    def load(self,config):
        self.host=config.gethost("host")
        log.m(f"используется сервис {self.name} [{self.host}]")
        self.MailDefaultDelay=config.getdelay("mail default delay")
        self.MailErrorDelay=config.getdelay("mail error delay")
        self.MailWaitTime=config.getdelay("mail wait time")
        self.CodeDefaultDelay=config.getdelay("code default delay")
        self.CodeErrorDelay=config.getdelay("code error delay")
        self.CodeWaitTime=config.getdelay("code wait time")
        self.LoadStorage(config)
        self.api_key = config.getstring("api key")
        self.service = config.getstring("service")
        self.CodeWaitTimeout=config.getdelay("code timeout")
        if self.CodeWaitTime*2>self.CodeWaitTimeout:
            raise ValueError(f"таймаут ожидания кода должен быть больше времени ожидания кода хотя бы в 2 раза")
        self.RequestTimeout=config.getdelay("request timeout")
    def LoadStorage(self,config):
        self.EmailStorage=config.select("storage type",{
            "none":EmailStorageEmpty,
            "default":EmailStorage,
            "remote":EmailStorageRemote
        })(self.name,self.host)
        self.EmailStorage.load(config)
    def WaitEmail(self):
        email=self.EmailStorage.get()
        if email:
            log.w(f"получена почта из хранилища {email}")
            email.AccessTime=time.time()
            return email
        first=time.time()
        limit=first+self.MailWaitTime
        while True:
            try:
                reqtime=time.time()
                email=self.GetEmail()
            except json.JSONDecodeError:
                log.e("невозможно распознать ответ сервиса как json")
                time.sleep(self.MailErrorDelay)
            except RuntimeError as e:
                log.e(f"ошибка получения почты: {e}")
                time.sleep(self.MailErrorDelay)
            except Exception as e:
                log.e(f"ошибка при получении почты: {type(e)}({e})",level=log.level.debug)
                time.sleep(self.MailErrorDelay)
            else:
                if email:
                    log.w(f"получена почта из сервиса {email}")
                    email=self.EmailStorage.push(email)
                    email.AccessTime=time.time()
                    return email
                elif reqtime>limit:
                    log.w(f"почта не пришла в течении {int(reqtime-first)}s")
                    return
                else:
                    time.sleep(self.MailDefaultDelay)
    def GetEmail(self):
        url = f"/stubs/handler_api.php?action=buyMailActivation&api_key={self.api_key}\
&service={self.service}"
        response = self.request(url).json()
        sid=response.get("activation_id")
        address=response.get("email")
        if sid and address:
            return Email(sid,address)
    def WaitCode(self,email):
        first=time.time()
        limit=first+self.CodeWaitTime
        conrtol=first+self.CodeWaitTimeout
        while True:
            try:
                reqtime=time.time()
                code=self.GetSms(email)
            except json.JSONDecodeError:
                log.e("невозможно распознать ответ сервиса как json")
                if reqtime>conrtol:
                    raise RuntimeError("превышено время ожидания кода")
                time.sleep(self.CodeErrorDelay)
            except Exception as e:
                log.e(f"{email}: ошибка получения смс: {e}")
                if reqtime>conrtol:
                    raise RuntimeError("превышено время ожидания кода")
                time.sleep(self.CodeErrorDelay)
            else:
                if code and (str(code)!=str(email.lastcode)):
                    log.i(f"{email} получен новый код {code}")
                    email.lastcode=code
                    self.EmailStorage.setcode(email)
                    return code
                elif reqtime>limit:
                    log.w(f"{email} код не пришёл в течении {int(reqtime-first)}s")
                    return
                else:
##                    log.a(f"{email} ожидание кода")
                    time.sleep(self.CodeDefaultDelay)
    def GetSms(self,email,timelimit):
        url = f"/stubs/handler_api.php?action=checkMailActivation&api_key={self.api_key}\
&id={email.id}"
        response = self.request(url).json()
        return response.get("code")
    def request(self,path,params={}):
##        log.d(self.host+path,params)
        return requests.get(
            self.host+path,
            params=params,
            timeout=self.RequestTimeout
        )
    def SetFinish(self,email):
        if not email.dislike:
            log.d(f"{email} успешно верифицирована",level=log.level.debug)
            self.EmailStorage.success(email)
    def SetBan(self,email):
        if not email.dislike:
            log.d(f"{email} не верифицирована",level=log.level.debug)
            self.EmailStorage.fail(email)
    def SetWrongCode(self,email):
        log.d(f"{email} с невалидным кодом",level=log.level.debug)
        self.EmailStorage.wrongcode(email)
    def SetNoCode(self,email):
        log.d(f"{email} без кода",level=log.level.debug)
        self.EmailStorage.nocode(email)
    def DislikeEmail(self,email):
        log.d(f"{email} удалена",level=log.level.debug)
        self.EmailStorage.dislike(email)
        email.dislike=True
