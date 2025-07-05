import threading as th
import time
import requests
import random
from Core.SmsServices.Classes import Country
from Core.TelegramClient.Classes import Proxy
from Core import Log as log
class SmsService:
    name=None
    def __init__(self,core):
        self.core=core
        self.begin=True
        self.service=None
        self.countries=[]
    def load(self,config):
        raise NotImplementedError
    def LoadBase(self,config):
        self.host=config.gethost("host")
        log.m(f"используется сервис {self.name} [{self.host}]")
        self.semaphore=th.Semaphore(config.getint("phone request limit"))
        self.PhoneDefaultDelay=config.getdelay("phone default delay")
        self.PhoneErrorDelay=config.getdelay("phone error delay")
        self.SmsDefaultDelay=config.getdelay("sms default delay")
        self.SmsErrorDelay=config.getdelay("sms error delay")
        self.SmsWaitTime=config.getdelay("sms wait time")
        self.MaxPrice=config.getint("country price max")
        self.SmsWaitTimeout=config.getdelay("sms timeout")
        if self.SmsWaitTime*2>self.SmsWaitTimeout:
            raise ValueError(f"таймаут ожидания смс должен быть больше времени ожидания смс хотя бы в 2 раза")
        self.RequestTimeout=config.getdelay("request timeout")
        self.proxies=[]
        if config.getbool("enable proxies"):
            with open(config.getfile("proxy file"),encoding="utf-8") as file:
                for index,line in enumerate(file,1):
                    line=line.strip()
                    if line:
                        try:
                            proxy=Proxy.fromstring(None,line)
                            proxy=f"{proxy.user}:{proxy.password}@{proxy.host}:{proxy.port}"
                            self.proxies.append(
                                {
                                    "http":"http://"+proxy,
                                    "https":"https://"+proxy
                                }
                            )
                        except ValueError as e:
                            raise ValueError(f"ошибка парсинга прокси {line}: {e}, (строка {index})")
            if self.proxies:
                log.i(f"загружено {len(self.proxies)} проксей")
            else:
                raise ValueError(f"прокси не были загружены в смс сервис")
    def LoadCountries(self,config):
        check=config.getbool("country price check")
        reverse=config.getbool("countries reverse")
        filename=config.getfile("countries file")
        if check:
            CountriesData=self.GetCountries()
            MinPrice=config.getint("country price min")
        with open(filename,encoding="utf-8") as file:
            for line in file:
                line=line.strip()
                if line:
                    line=line.expandtabs(1)
                    line,_,proxy=line.partition("/")
                    proxy=proxy.lstrip()
                    if proxy:
                        proxy=Proxy.fromstring(proxy)
                    else:
                        proxy=None
                    if reverse:
                        name,_,code=line.rpartition(" ")
                    else:
                        code,_,name=line.partition(" ")
                    name=name.strip()
                    code=code.strip()
                    if check:
                        CountryData=CountriesData.get(code)
                        if CountryData:
                            CountryData=CountryData.get(self.service)
                            if CountryData:
                                cost=float(CountryData["cost"])
                                count=int(CountryData["count"])
                                if MinPrice<=cost<=self.MaxPrice:
                                    country=Country(code,name,proxy)
                                    self.countries.append(country)
                                    log.i(f"загружена страна {country} (цена - {cost}, номеров - {count})")
                                else:
                                    log.w(f"отклонена страна {name} (цена - {cost}, номеров - {count})")
                            else:
                                log.w(f"не найден сервис {self.service} по стране {name}")
                        else:
                            log.w(f"не найдена страна {name}")
                    else:
                        country=Country(code,name,proxy)
                        self.countries.append(country)
                        log.i(f"загружена страна {country}")
    def WaitPhone(self,country):
        while self.begin:
            try:
                with self.semaphore:
                    phone=self.GetPhone(country)
            except RuntimeError as e:
                log.e(f"{country}: ошибка получения номера: {e}")
                time.sleep(self.PhoneErrorDelay)
            except Exception as e:
                log.e(f"{country}: ошибка при получении номера: {e}",level=log.level.debug)
                time.sleep(self.PhoneErrorDelay)
            else:
                if phone:
                    log.m(f"{country} получен номер {phone}")
                    return phone
                else:
##                    log.w(f"{country} не получен номер")
                    time.sleep(self.PhoneDefaultDelay)
    def WaitCode(self,phone):
        first=time.time()
        limit=first+self.SmsWaitTime
        conrtol=first+self.SmsWaitTimeout
        while True:
            try:
                reqtime=time.time()
                code=self.GetSms(phone)
            except Exception as e:
                log.e(f"{phone}: ошибка получения смс: {e}")
                if reqtime>conrtol:
                    raise RuntimeError("превышено время ожидания кода")
                time.sleep(self.SmsErrorDelay)
            else:
                if code:
                    log.s(f"{phone} получен код {code}")
                    return code
                elif reqtime>limit:
                    log.e(f"{phone} код не пришёл в течении {int(reqtime-first)}s")
                    return
                else:
                    log.a(f"{phone} ожидание кода")
                    time.sleep(self.SmsDefaultDelay)
    def request(self,path,params={},proxy=None):
        if self.proxies:
##            log.d(self.host+path,proxy)
            return requests.get(
                self.host+path,
                params=params,
                proxies=proxy if proxy else random.choice(self.proxies),
                timeout=self.RequestTimeout
            )
        else:
##            log.d(self.host+path)
            return requests.get(
                self.host+path,
                params=params,
                timeout=self.RequestTimeout
            )
    def GetCountries(self):
        raise NotImplementedError
    def GetPhone(self,country):
        raise NotImplementedError
    def GetSms(self,phone):
        raise NotImplementedError
    def SetFinish(self,phone):
        raise NotImplementedError
    def SetBan(self,phone):
        raise NotImplementedError
