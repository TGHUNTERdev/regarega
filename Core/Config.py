import os
import yarl
DELAY_MULTIPLERS={
    "d":3600*24,
    "h":3600,
    "m":60,
    "s":1
}
class Position:
    def __init__(self,key,value,index):
        self.key=key
        self.value=value
        self.visited=False
        self.index=index
    def __str__(self):
        return f"{self.key} = {self.value} (строка {self.index})"
class Category:
    def __init__(self,name):
        self.name=name
        self.data={}
        self.visited=False
    def getpos(self,key):
        position=self.data.get(key)
        if position:
            if position.visited:
                raise RuntimeError(f"повторное использование позиции {self.name}: {position}")
            else:
                position.visited=True
                return position
        else:
            raise ValueError(f"позиция {key} не найдена в категории {self.name}")
    def getstring(self,key):
        return self.getpos(key).value
    def getint(self,key):
        position=self.getpos(key)
        try:
            return int(position.value)
        except ValueError:
            raise ValueError(f"не распознано как число {self.name}: {position}")
    def getfloat(self,key):
        position=self.getpos(key)
        try:
            return float(position.value)
        except ValueError:
            raise ValueError(f"не распознано как число {self.name}: {position}")
    def getbool(self,key):
        position=self.getpos(key)
        value=position.value.lower()
        if value=="true":
            return True
        elif value=="false":
            return False
        else:
            raise ValueError(f"{value} не распознано как true или false в {self.name}: {position}")
    def getenum(self,key,enum):
        position=self.getpos(key)
        value=position.value.lower()
        if value in enum:
            return value
        else:
            variants=", ".join(enum)
            raise ValueError(f"{self.name}: {position} может принимать только значения {variants}")
    def select(self,key,data):
        position=self.getpos(key)
        value=position.value.lower()
        item=data.get(value)
        if item:
            return item
        else:
            variants=", ".join(data.keys())
            raise ValueError(f"{self.name}: {position} может принимать только значения {variants}")
    def getdelay(self,key):
        position=self.getpos(key)
        value=position.value.lower()
        buffer=""
        hasdot=False
        result=0
        for char in value:
            if char!=" ":
                if char.isdigit():
                    buffer+=char
                elif char==".":
                    if hasdot:
                        raise ValueError(f"неверный формат числа {buffer}. в {self.name}: {position}")
                    else:
                        buffer+="."
                        hasdot=True
                else:
                    multipler=DELAY_MULTIPLERS.get(char)
                    if multipler:
                        result+=multipler*float(buffer)
                        buffer=""
                        hasdot=False
                    else:
                        raise ValueError(f"не известный формат времени {char} в {self.name}: {position}")
        if buffer:
            raise ValueError(f"не известное число без указателя на формат времени {buffer} в {self.name}: {position}")
        return result
    def getfile(self,key):
        position=self.getpos(key)
        if os.path.isfile(position.value):
            return position.value
        else:
            raise ValueError(f"файл не определён {position.value} в {self.name}: {position}")
    def newfile(self,key,default=""):
        position=self.getpos(key)
        if not os.path.isfile(position.value):
            with open(position.value,"w",encoding="utf-8") as file:
                file.write(default)
        return position.value
    def getdir(self,key):
        position=self.getpos(key)
        if os.path.isdir(position.value):
            return position.value
        else:
            raise ValueError(f"директория не определёна {position.value} в {self.name}: {position}")
    def gethost(self,key):
        position=self.getpos(key)
        url=yarl.URL(position.value)
        if not url.scheme:
            raise ValueError(f"протокол (http/https) не определён {position.value} в {self.name}: {position}")
        if not url.host:
            raise ValueError(f"хост не определён {position.value} в {self.name}: {position}")
        return url.scheme+"://"+url.host+(":"+str(url.port)) if url.port else ""
class Config:
    def __init__(self,path):
        self.path=path
        self.data={}
        self.load()
    def load(self):
        if os.path.isfile(self.path):
            with open(self.path) as file:
                for index,line in enumerate(file,1):
                    line=line.strip()
                    if line:
                        if line[-1]==":":
                            category=line[:-1].rstrip()
                            if category in self.data:
                                raise RuntimeError(f"дублирование категории {line} в строке {index}")
                            else:
                                config=Category(category)
                                self.data[category]=config
                        else:
                            key,_,val=line.partition("=")
                            key=key.rstrip()
                            val=val.lstrip()
                            if not key:
                                raise RuntimeError(f"пустой ключ {line} в строке {index}")
                            if key in config.data:
                                raise RuntimeError(f"дублирование позиции {line} в строке {index}")
                            else:
                                config.data[key]=Position(key,val,index)
        else:
            raise ValueError(f"файл конфигурации {self.path} не найден")
    def get(self,key):
        category=self.data.get(key)
        if category:
            if category.visited:
                raise RuntimeError(f"повторное использование категории {key}")
            else:
                category.visited=True
                return category
        else:
            raise ValueError(f"категория {key} не найдена")
