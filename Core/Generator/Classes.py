import random
import string
from Core import Log as log
from Core.TelegramClient.Classes import Proxy
from Core.TelegramClient.Classes import TimeZone
class ClientData:
    def __init__(self,filename,jsonkey):
        self.variants=[]
        self.pars(filename)
        self.jsonkey=jsonkey
        log.i(f"загружено {len(self.variants)} из {filename}")
    def pars(self,filename):
        raise NotImplementedError
    def get(self):
        return random.choice(self.variants)
    def save(self,target,value):
        target[self.jsonkey]=value
class ClientDataString(ClientData):
    def pars(self,filename):
        with open(filename,encoding="utf-8") as file:
            for line in file:
                line=line.strip()
                if line:
                    self.variants.append(line)
class ClientDataInt(ClientData):
    def pars(self,filename):
        with open(filename,encoding="utf-8") as file:
            for index,line in enumerate(file,1):
                line=line.strip()
                if line:
                    if line.isdigit():
                        self.variants.append(int(line))
                    else:
                        raise ValueError(f"значение perfcat {line} не является числом (файл {filename}, строка {index})")
class ClientPair(ClientData):
    def __init__(self,*args,jsonkeyalt):
        ClientData.__init__(self,*args)
        self.jsonkeyalt=jsonkeyalt
    def pars(self,filename):
        with open(filename,encoding="utf-8") as file:
            for index,line in enumerate(file,1):
                line=line.strip()
                if line:
                    pair=line.split(":")
                    if len(pair)==2:
                        if pair[0].isdigit():
                            self.variants.append((int(pair[0]),pair[1]))
                        else:
                            raise ValueError(f"id {pair[0]} в паре id-hash {line} не является числом (файл {filename}, строка {index})")
                    elif len(pair)>2:
                        raise ValueError(f"пара id-hash {line} имеет больше двух элементов (файл {filename}, строка {index})")
                    else:
                        raise ValueError(f"пара id-hash {line} имеет меньше двух элементов (файл {filename}, строка {index})")
    def save(self,target,value):
        target[self.jsonkey]=value[0]
        target[self.jsonkeyalt]=value[1]
class ClientProxy(ClientData):
    def __init__(self,*args,protocol=None):
        self.protocol=protocol
        ClientData.__init__(self,*args)
    def pars(self,filename):
        with open(filename,encoding="utf-8") as file:
            for index,line in enumerate(file,1):
                line=line.strip()
                if line:
                    try:
                        self.variants.append(Proxy.fromstring(self.protocol,line))
                    except ValueError as e:
                        raise ValueError(f"ошибка парсинга прокси {line}: {e}, (строка {index})")
    def save(self,target,value):
        target[self.jsonkey]=value.tolist()
class ClientTimeZone(ClientData):
    def pars(self,filename):
        with open(filename,encoding="utf-8") as file:
            for line in file:
                line=line.strip()
                if line:
                    self.variants.append(TimeZone(line))
    def save(self,target,value):
        target[self.jsonkey]=value.name
symbols=string.ascii_letters+string.digits
class ClientPassword(ClientData):
    def __init__(self,count,jsonkey):
        self.count=count
        self.jsonkey=jsonkey
        log.i(f"загружено генератор 2fa паролей")
    def get(self):
        result=""
        for i in range(self.count):
            result+=random.choice(symbols)
        return result
