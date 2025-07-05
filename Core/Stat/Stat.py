import json
import gzip
import base64
import threading as th
from Core import Log as log
COUNTER_BASE = 0
COUNTER_SMSCODE = 1
COUNTER_2FA = 2
COUNTER_CAPTCHA = 3
TOTAL_COUNTERS = 4
class Counter:
    def __init__(self,filename,size):
        self.filename=filename
        self.size=size
        self.data={}
        self.load()
    def load(self):
        with open(self.filename,"r",encoding="utf-8") as file:
            for line in file:
                line=line.strip()
                if line:
                    line,_,data=line.rpartition(" ")
                    name,_,code=line.rstrip().rpartition(" ")
                    name=name.rstrip()
                    values=self.fill(list(map(int,data.split("/"))))
                    self.data[(name,code)]=values
##        log.d(self.data)
        if self.data:
            log.m("country".ljust(24)+"all".center(8)+"sms".center(8)+"2fa".center(8)+"captcha".center(8))
            for ((name,code),val) in self.data.items():
                line=(name+"["+code+"]").ljust(24)
                for cell in val:
                    line+=str(cell).center(8)
                log.i(line)
    def fill(self,values):
##        log.d(self.size,len(values))
        if len(values)>self.size:
            return values[:self.size]
        elif len(values)<self.size:
            return values+[0]*(self.size-len(values))
        else:
            return values
    def save(self):
        with open(self.filename,"w",encoding="utf-8") as file:
            for country,data in self.data.items():
                file.write((country[0]+" "+country[1]).ljust(48)+"/".join(map(str,data))+"\n")
    def inc(self,country,counter):
        data=self.data.get(country)
        if not data:
            data=[0]*self.size
            self.data[country]=data
        data[counter]+=1
##class Stat:
##    def __init__(self,core):
##        self.core=core
##        self.lock=th.Lock()
##    def load(self,config):
##        self.filename=config.newfile("full stat file","[]")
##        with open(self.filename,encoding="utf-8") as file:
##            self.data=json.load(file)
##        self.counter=Counter(config.newfile("count stat file",""),3)
##    def push(self,data):
##        with self.lock:
##            self.data.append(data)
##            self.calculate(data)
##            self.counter.save()
##            self.save()
##    def save(self):
##        with open(self.filename,"w",encoding="utf-8") as file:
##            json.dump(self.data,file,indent=3)
##    def calculate(self,data):
##        country=data["country"]
##        country=(country["name"],country["code"])
##        self.counter.inc(country,COUNTER_BASE)
##        if data.get("smscode"):
##            self.counter.inc(country,COUNTER_SMSCODE)
##        if data.get("status")=="2fa":
##            self.counter.inc(country,COUNTER_2FA)
class Stat:
    def __init__(self,core):
        self.core=core
        self.lock=th.Lock()
    def load(self,config):
        self.savestat=config.getbool("savestat")
        self.FileLog2FA=config.newfile("log 2fa file")
        self.FileLogCaptcha=config.newfile("log captcha file")
        self.FileLogPhoneBanned=config.newfile("log banned file")
        self.FileLogNotSms=config.newfile("log not sms file")
        self.FileLogNotSmsHasEmail=config.newfile("log not sms has email file")
        self.FileLogError=config.newfile("log error file")
        self.FileLogRegistered=config.newfile("log registered file")
        self.FileLogAuthorized=config.newfile("log authorized file")
        self.filename=config.newfile("history file")
        self.counter=Counter(config.newfile("count stat file",""),TOTAL_COUNTERS)
    def push(self,data):
        with self.lock:
            if self.savestat:
                with open(self.filename,"a") as file:
                    file.write(
##                        json.dumps(data,indent=3)+"\n"
                        base64.b85encode(
                            gzip.compress(
                                json.dumps(data,separators=(",",":")).encode()
                            )
                        ).decode()+"\n"
                    )
            self.calculate(data)
            self.counter.save()
    def calculate(self,data):
        country=data["country"]
        country=(country["name"],country["code"])
        status=data.get("status")
        phone=data["phone"]
        self.counter.inc(country,COUNTER_BASE)
        log.d("status",status,"email",data.get("email"))
        if data.get("smscode"):
            self.counter.inc(country,COUNTER_SMSCODE)
        if data.get("captcha"):
            self.counter.inc(country,COUNTER_CAPTCHA)
            with open(self.FileLogCaptcha,"a") as file:
                file.write(phone+"\n")
        if status=="2fa":
            self.counter.inc(country,COUNTER_2FA)
            with open(self.FileLog2FA,"a") as file:
                file.write(phone+"\n")
        elif status=="phone banned":
            with open(self.FileLogPhoneBanned,"a") as file:
                file.write(phone+"\n")
        elif status=="not code":
            if data.get("email"):
                log.d("push email")
                with open(self.FileLogNotSmsHasEmail,"a") as file:
                    file.write(phone+"\n")
            else:
                log.d("push nosms")
                with open(self.FileLogNotSms,"a") as file:
                    file.write(phone+"\n")
        elif status=="error":
            with open(self.FileLogError,"a") as file:
                file.write(phone+" "+data["error"]+"\n")
        elif status=="registered":
            with open(self.FileLogRegistered,"a") as file:
                file.write(phone+"\n")
        elif status=="authorized":
            with open(self.FileLogAuthorized,"a") as file:
                file.write(phone+"\n")
