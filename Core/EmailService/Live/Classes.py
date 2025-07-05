import json
import time
import yarl
import requests
import threading as th
from Core import Log as log
from Core.EmailService.Classes import Email
##class Email:
##    def __init__(self,email_id,address,token=None):
##        self.id=email_id
##        self.address=address
##        self.token=token
##    def __str__(self):
##        return f"{self.address}"
class EmailLive(Email):
    dislike=False
    @classmethod
    def fromdata(cls,data):
        email=cls(data["id"],data["address"])
        email.create=data["create"]
        email.success=data["success"]
        email.fail=data["fail"]
        return email
    @classmethod
    def fromemail(cls,email):
        newmail=cls(email.id,email.address)
        newmail.create=time.time()
        newmail.success=0
        newmail.fail=0
        return newmail
    def todata(self):
        return {
            "id":self.id,
            "address":self.address,
            "create":self.create,
            "success":self.success,
            "fail":self.fail
        }
class EmaiLiveRemote(Email):
    dislike=False
    RemoteId=None
class LoadErrors:
    def __init__(self):
        self.data=""
        self.count=0
    def add(self,error,data):
        self.data=self.data+f"{type(error).__name__}({error}) - {data}\n"
        self.count+=1
class EmailStorageEmpty:
    def __init__(self,name,host):
        pass
    def load(self,config):
        log.m("почтовое хранилище не используется")
    def push(self,email):
        email.dislike=False
        return email
    def get(self):
        return None
    def success(self,email):
        pass
    def fail(self,email):
        pass
    def wrongcode(self,email):
        pass
    def nocode(self,email):
        pass
    def dislike(self,email):
        pass
    def setcode(self,email):
        pass
class EmailStorageRemote:
    def __init__(self,name,host):
        self.type=name+" % "+yarl.URL(host).host
    def load(self,config):
        log.m("используется сетевое почтовое хранилище")
        self.host=config.gethost("storage host")
        try:
            code=requests.get(self.host+"/ok").text
        except Exception as e:
            raise ValueError(f"сетевое хранилище почт не доступно по причине: {type(e).__name__}({e})")
        else:
            if code=="OK":
                log.i("установелно соединение по http")
            else:
                raise ValueError("сетевое хранилище дало не валидный ответ")
    def push(self,email):
        email=EmaiLiveRemote(email.id,email.address)
        email.RemoteId=self.request("/push",{
            "name":self.type,
            "eid":email.id,
            "address":email.address
        }).text
        return email
    def get(self):
        result=self.request("/get",{
            "name":self.type
        }).text.split(":")
        if result[0]=="OK":
            email=EmaiLiveRemote(result[2],result[3])
            email.RemoteId=result[1]
            email.lastcode=result[4]
            return email
    def success(self,email):
        self.request("/success",{
            "eid":email.RemoteId
        })
    def fail(self,email):
        self.request("/fail",{
            "eid":email.RemoteId
        })
    def wrongcode(self,email):
        self.request("/wrongcode",{
            "eid":email.RemoteId
        })
    def nocode(self,email):
        self.request("/nocode",{
            "eid":email.RemoteId
        })
    def dislike(self,email):
##        self.fail(email)
        self.request("/dislike",{
            "eid":email.RemoteId
        })
    def setcode(self,email):
        self.request("/setcode",{
            "eid":email.RemoteId,
            "code":email.lastcode
        })
    def request(self,path,params):
        for i in range(10):
            for i in range(5):
                try:
                    return requests.get(self.host+path,params=params)
                except Exception as e:
                    time.sleep(10)
            log.e(f"невозможно добраться до сетевого хранлилища {self.host}")
            time.sleep(120)
        raise RuntimeError("сетевое почтовое хранилище не отвечает")
class EmailStorage:
    def __init__(self,name,host):
        self.lock=th.Lock()
        self.type=name+" % "+yarl.URL(host).host
        self.storage=[]
        self.emails=[]
        self.otherdata=""
    def load(self,config):
        log.m("используется стандартное почтовое хранилище")
        self.SuccessLimit=config.getint("email success limit")
        self.FailLimit=config.getint("email fail limit")
        self.LifeTime=config.getdelay("email life time")
        self.path=config.getfile("email file")
        errpath=config.newfile("email error file")
        self.LoadEmails(errpath)
    def LoadEmails(self,errpath):
        errors=LoadErrors()
        others=0
        with open(self.path,encoding="utf-8") as file:
            for line in file:
                line=line.strip()
                if line:
                    try:
                        data=json.loads(line)
                    except json.JSONDecodeError as e:
                        errors.add(e,line)
                    else:
                        try:
                            if data["type"]==self.type:
                                self.storage.append(EmailLive.fromdata(data["data"]))
                            else:
                                self.otherdata=self.otherdata+"\n"+line
                                others+=1
                        except KeyError as e:
                            errors.add(e,line)
        if errors.count>0:
            with open(errpath,"w",encoding="utf-8") as file:
                file.write(errors.data)
            log.w(f"обнаруженно {errors.count} сломанных почт")
        if others>0:
            log.w(f"обнаружено {others} почт, которые не могут использоваться в данном типе сервиса")
        for email in self.storage:
            self.add(email)
        if self.emails:
            log.i(f"загружено {len(self.emails)} почт")
        else:
            log.w("почты не были загружены")
        self.save()
    def save(self):
        with open(self.path,"w",encoding="utf-8") as file:
            for email in self.storage:
                file.write(json.dumps({
                    "type":self.type,
                    "data":email.todata()
                })+"\n")
            file.write(self.otherdata)
    def push(self,email):
        email=EmailLive.fromemail(email)
        with self.lock:
            self.storage.append(email)
            self.save()
        return email
    def get(self):
        with self.lock:
            drops=0
            while self.emails:
                email=self.emails.pop(0)
                if time.time()-email.create<self.LifeTime:
                    if drops>0:
                        self.save()
                    return email
                else:
                    drops+=1
                    self.storage.remove(email)
            if drops>0:
                self.save()
    def add(self,email):
        if time.time()-email.create<self.LifeTime:
            self.emails.append(email)
        else:
            self.drop(email)
    def success(self,email):
        with self.lock:
            email.success+=1
            if email.success<self.SuccessLimit:
                self.save()
                self.add(email)
            else:
                self.drop(email)
    def fail(self,email):
        with self.lock:
            email.fail+=1
            if email.fail<self.FailLimit:
                self.save()
                self.add(email)
            else:
                self.drop(email)
    def wrongcode(self,email):
        pass
    def nocode(self,email):
        pass
    def dislike(self,email):
        with self.lock:
            self.drop(email)
    def setcode(self,email):
        pass
    def drop(self,email):
        self.storage.remove(email)
        self.save()
