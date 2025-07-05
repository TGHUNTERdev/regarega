from Core import Log as log
from Core.Generator.Generator import Generator
from Core.Generator.ProxyInfo import ProxyInfo
from Core.TelegramClient.Classes import TimeZone
class LocateGenerator(Generator):
    name="locate"
    def load(self,config):
        Generator.load(self,config)
        self.ProxyInfo=ProxyInfo()
        self.ProxyInfo.host=config.gethost("proxy info host")
        self.ProxyInfo.delay=config.getdelay("proxy info error delay")
        log.i(f"загружен прокси-чекер {self.ProxyInfo.host}")
    def GenerateBaseClientData(self,proxy):
        data=self.ProxyInfo.getdata(proxy.tostring())
        timezone=data.get("timezone")
        if timezone:
            try:
                timezone=TimeZone(timezone)
            except ValueError:
                timezone=self.ClientData[6].get()
##            else:
##                log.d(f"тайм-зона прокси {timezone}")
        else:
            timezone=self.ClientData[6].get()
        langpack=data.get("countryCode")
        if langpack:
            langpack=langpack.lower()
##            log.d(f"ланг-пак прокси {langpack}")
        else:
            langpack=self.ClientData[4].get()
        return [
            self.ClientData[0].get(),
            self.ClientData[1].get(),
            self.ClientData[2].get(),
            self.ClientData[3].get(),
            langpack,
            self.ClientData[5].get(),
            timezone,
            self.ClientData[7].get()
        ]
