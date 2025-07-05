import socks
from Core import Log as log
from Core.Generator.Classes import ClientDataString
from Core.Generator.Classes import ClientDataInt
from Core.Generator.Classes import ClientPair
from Core.Generator.Classes import ClientProxy
from Core.Generator.Classes import ClientTimeZone
from Core.Generator.Classes import ClientPassword
class Generator:
    name="standart"
    def __init__(self,core):
        self.core=core
    def load(self,config):
        log.m(f"используется генератор {self.name}")
        protocol=socks.PROXY_TYPES[config.getenum("proxy type",map(lambda x:x.lower(),socks.PROXY_TYPES.keys())).upper()]
        self.ClientData=[
            ClientPair(config.getfile("pairs file"),"app_id",jsonkeyalt="app_hash"),          #0
            ClientDataString(config.getfile("devices file"),"device"),                        #1
            ClientDataString(config.getfile("sdk file"),"sdk"),                               #2
            ClientDataString(config.getfile("app version file"),"app_version"),               #3
            ClientDataString(config.getfile("lang code file"),"lang_code"),                   #4
            ClientDataString(config.getfile("system lang code file"),"system_lang_pack"),     #5
            ClientTimeZone(config.getfile("timezone file"),"tz"),                             #6
            ClientDataInt(config.getfile("perfcat file"),"perfcat"),                          #7
            ClientDataString(config.getfile("package ids file"),"package_id"),                #8
            ClientDataString(config.getfile("lang pack file"),"lang_pack")                    #9
        ]
        self.ProxyData=ClientProxy(config.getfile("proxies file"),"proxy",protocol=protocol)
        self.AddationData=[
            ClientDataString(config.getfile("first names file"),"first_name"),                #0
            ClientDataString(config.getfile("last names file"),"last_name"),                  #1
        ]
        self.PasswordData=ClientPassword(config.getint("password length"),"twoFA")
##        log.d(self.GenerateBaseClientData(self.ProxyData.get()))
    def GenerateBaseClientData(self,proxy):
        return self.GenerateClientData(self.ClientData)
    def GenerateAddationClientData(self):
        return self.GenerateClientData(self.AddationData)
    def GenerateClientData(self,sources):
        return [source.get() for source in sources]
    def SaveClientData(self,target,sources,values):
        for source,value in zip(sources,values):
            source.save(target,value)
