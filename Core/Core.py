import sys
import threading as th
import os
import time

from Core import Log as log
from Core.Config import Config
from Core import CrushReport

from Core.Stat.Stat import Stat
from Core.Generator.Generator import Generator
from Core.Generator.LocateGenerator import LocateGenerator
##from Core.Registrator.Registrator import Registrator
##from Core.TelegramClient import TelegramClient
from Core.Registrator.RegistratorAsync import Registrator
from Core.TelegramClient import AsyncTelegramClient as TelegramClient

from Core.TokenServices.TokenService import TokenService
from Core.TokenServices.AutoPushService import AutoPushService
from Core.TokenServices.AntisafetyService import AntisafetyService

from Core.CaptchaServices.CaptchaAntisafetyService import CaptchaAntisafetyService

from Core.EmailService.Anitsafety.AntisafetyMailService import AntisafetyMailService
from Core.EmailService.Self.SelfMailService import SelfMailService
from Core.EmailService.Live.EmailLiveService import EmailLiveService
from Core.EmailService.Live.EmailActivateService import EmailActivateService
from Core.EmailService.Live.EmailKopeechkaService import EmailKopeechkaService
from Core.EmailService.Live.EmailRentgmailService import EmailRentgmailService
from Core.EmailService.Live.EmailLocalService import EmailLocalService

from Core.SmsServices.SmsManService import SmsManService
from Core.SmsServices.DurainCloudService import DurainCloudService
from Core.SmsServices.SmsAcktiwator import SmsAcktiwator
from Core.SmsServices.FirefoxFunService import FirefoxFunService
from Core.SmsServices.FiveSimService import FiveSimService
from Core.SmsServices.ActivatecodeService import ActivatecodeService

from Core.CheckNumberService.CheckNumberService import CheckNumberService
from Core.CheckNumberService.CheckNumberEmptyService import CheckNumberEmptyService

class Core:
    def __init__(self):
        self.SmsServices=self.registrate([
            SmsManService,
            DurainCloudService,
            SmsAcktiwator,
            FirefoxFunService,
            FiveSimService,
            ActivatecodeService
        ])
        self.EmailServices=self.registrate([
            AntisafetyMailService,
            SelfMailService,
            EmailLiveService,
            EmailActivateService,
            EmailKopeechkaService,
            EmailRentgmailService,
            EmailLocalService
        ])
        self.generators=self.registrate([
            Generator,
            LocateGenerator
        ])
        self.ThreadStartLock=th.Lock()
    def registrate(self,classes):
        return {cls.name:cls for cls in classes}
    def start(self):
        if len(sys.argv)>1:
            path=sys.argv[1]
        else:
            path=input("введите директорию выполнения: ")
        if os.path.isdir(path):
            os.chdir(path)
            log.init()
            CrushReport.init()
            log.i("система инициализирована в",path)
            return True
        else:
            print(f"директория {path} не найдена")
    def LoadConfig(self):
        self.config=Config("config.txt")
        log.d("загрузка ядра")
        config=self.config.get("global")
        self.threads=config.getint("threads")
        self.ThreadStartDelay=config.getdelay("thread start delay")
        self.SoftStateFile=config.getfile("soft state file")
        self.SoftStateCheckDelay=config.getdelay("soft state check delay")
        self.WaitAfterCreate=config.getdelay("wait after create")
        log.d("загрузка учёта статистики")
        config=self.config.get("stat")
        self.stat=Stat(self)
        self.stat.load(config)
        log.d("загрузка генератора данных клиента")
        config=self.config.get("generator")
        self.generator=config.select("type",self.generators)(self)
        self.generator.load(config)
        log.d("загрузка регистратора")
        config=self.config.get("registrator")
        self.registrator=Registrator(self)
        self.registrator.load(config)
        log.d("загрузка телеграм клиента")
        config=self.config.get("telegram client")
        TelegramClient.init(config)
        log.d("загрузка токен сервиса")
        config=self.config.get("token service")
        self.TokenService=(AntisafetyService if config.getbool("push token enable") else AutoPushService)(self)
        self.TokenService.LoadBase(config)
        self.TokenService.load(config)
        log.d("загрузка сервиса решения капч")
        self.CaptchaService=CaptchaAntisafetyService(self)
        self.CaptchaService.load(None)
        log.d("загрузка почтового сервиса")
        config=self.config.get("email service")
        self.EmailService=self.EmailServices[config.getenum("api type",tuple(self.EmailServices.keys()))](self)
        self.EmailService.load(config)
        log.d("загрузка сервиса проверки номеров")
        config=self.config.get("check number service")
        self.CheckNumberService=config.select("check service type",{
            "disable":CheckNumberEmptyService,
            "enable":CheckNumberService
        })(self)
        self.CheckNumberService.load(config)
        log.d("загрузка смс-сервиса")
        config=self.config.get("sms service")
        self.SmsService=self.SmsServices[config.getenum("api type",tuple(self.SmsServices.keys()))](self)
        self.SmsService.LoadBase(config)
        self.SmsService.load(config)
        self.SmsService.LoadCountries(config)
    def LoadThreads(self):
        threads=[]
        index=1
        for country in self.SmsService.countries:
            for i in range(self.threads):
                threads.append(
                    th.Thread(
                        target=self.RunThread,
                        name=f"Поток {index}",
                        args=(index,country)
                    )
                )
                index+=1
        return threads
    def run(self):
        log.d("запуск")
        threads=self.LoadThreads()
        log.i(f"создано {len(threads)} потоков")
        input(">> ")
        with open(self.SoftStateFile,"w") as file:
            file.write("on")
        self.begin=True
        self.ActiveThreads=len(threads)
        for thread in threads:
            thread.start()
        while self.begin:
            time.sleep(self.SoftStateCheckDelay)
            if os.path.isfile(self.SoftStateFile):
                with open(self.SoftStateFile) as file:
                    self.begin=(file.read().lower()=="on")
            else:
                self.begin=False
        self.SmsService.begin=False
        log.m(f"завершение работы")
        for thread in threads:
            thread.join()
    def RunThread(self,index,country):
        with self.ThreadStartLock:
            time.sleep(self.ThreadStartDelay)
        log.d("запущен")
        while self.begin:
            with CrushReport.CrushReport("ошибка выполнения потока"):
                self.registrator.registrate(country)
            time.sleep(self.WaitAfterCreate)
        with self.ThreadStartLock:
            self.ActiveThreads-=1
            if self.ActiveThreads>0:
                log.w(f"остановлен, в работе ещё {self.ActiveThreads}")
            else:
                log.w(f"остановлен")
