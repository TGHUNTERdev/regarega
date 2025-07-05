import requests
from Core import Log as log
import threading as th
from Core.SmsServices.Classes import Phone
from Core.SmsServices.SmsService import SmsService

class DurainPhone(Phone):
    def __init__(self, number, key):
        Phone.__init__(self, number, number)
        self.key = key

class DurainKey:
    def __init__(self,username,key,proxy):
        self.username=username
        self.key=key
        self.proxy=proxy
        
class KeyRotorParallel:
    mode = "параллельный"
    def __init__(self, filename, service):
        self.service=service
        ProxyIndex=0
        self.keys = []
        self.store = []
        with open(filename, encoding = "utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    username,key = line.split(":")
                    if self.service.proxies:
                        proxy=self.service.proxies[ProxyIndex%len(self.service.proxies)]
                        self.keys.append(
                            DurainKey(
                                username,
                                key,
                                proxy
                            )
                        )
                        ProxyIndex+=1
                    else:
                        self.keys.append(DurainKey(username,key,None))
        self.lock = th.Lock()
        self.shift = 0
        log.i(f"загружено {len(self.keys)} ключей (режим {self.mode})")
        
    def get(self):
        with self.lock:
            if self.keys:
                return self.getkey()
            else:
                log.i(f"ключи исперчпались, переконфигурация")
                self.keys = self.store
                self.store = []

    def getkey(self):
        key = self.keys[self.shift]
        self.shift += 1
        if self.shift >= len(self.keys):
            self.shift = 0
        return key

    def delete(self, key):
        with self.lock:
            if key in self.keys:
                self.keys.remove(key)
                self.store.append(key)
                log.e(f"Ключ исчерпал дневной лимит. Ключей осталось: {len(self.keys)}")
                
class KeyRotorSequence(KeyRotorParallel):
    mode = "последовательный"
    def getkey(self):
        return self.keys[0]

class DurainCloudService(SmsService):
    name="duraincloud"

    def load(self,config):
##        self.api_key = config.getstring("key")
##        self.url = config.getstring("host")+"/out/ext_api/"
        self.pid = config.getstring("pid")
        self.keyrotor = config.select(
            "key mode",
            {
                "sequence":KeyRotorSequence,
                "parallel":KeyRotorParallel
            }
        )(config.getfile("keys"),self)
##        self.keyrotor = KeyRotor(config.getfile("keys"))
##        url = "https://api.duraincloud.com/out/ext_api/"

    def GetCountries(self):
        raise ValueError("duraincloud сервис не поддерживает проверку стран")
    
    def GetPhone(self, country):
        key = self.keyrotor.get()
        url = f"/out/ext_api/getMobile?name={key.username}&ApiKey={key.key}\
&cuy={country.code}&pid={self.pid}&num=1&noblack=1&serial=2&secret_key=null&vip=null"
        
        response = self.request(url,proxy=key.proxy)
        response = response.json()
        
        code = response["code"]
    
        if code == 200:
            data = response["data"]
##            log.i("Номер успешно арендован")
            return DurainPhone(data, key)
        elif code == 906:
##            log.w("Нет номеров")
            return None
        elif code == 406:
            self.keyrotor.delete(key)
        else:
##            log.e("Непредвиденная ошибка")
            raise RuntimeError(response["msg"])
        
    def GetSms(self, phone):
        url = f"/out/ext_api/getMsg?name={phone.key.username}&ApiKey={phone.key.key}\
&pn={phone.id}&pid={self.pid}&serial=2"

        response = self.request(url,proxy=phone.key.proxy)
##        log.d(response.request.url)
        response = response.json()

##        log.d(response)
        code = response["code"]

        if code == 200:
            data = response["data"]
##            log.i("Смс успешно получено")
            return data
        elif code in [908, 405, 407]:
##            log.w("Смс не получено")
            return None
        else:
##            log.e("Непредвиденная ошибка")
            raise RuntimeError(response["msg"])
        
    def SetBan(self, phone):
        url = f"/out/ext_api/addBlack?name={phone.key.username}&ApiKey={phone.key.key}\
&pn={phone.id}&pid={self.pid}"

        response = self.request(url,proxy=phone.key.proxy)
        
