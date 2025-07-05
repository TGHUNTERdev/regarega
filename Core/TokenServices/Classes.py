import threading as th
from Core import Log as log
class PushToken:
    @classmethod
    def fromstring(cls,source):
        device,secret,token_type=source.split(" ")
        return cls(
            device,
            int(token_type),
            bytes.fromhex(secret)
        )
    def __init__(self,device,token_type,secret):
        self.device=device
        self.type=token_type
        self.secret=secret
    def __str__(self):
        return f"{self.device[:22]}[{self.type}]"
    def tostring(self):
        return self.device+" "+self.secret.hex()+" "+str(self.type)
class PushTokenStorage:
    def __init__(self,file,dropfile):
        self.file=file
        self.dropfile=dropfile
        self.saved=[]
        self.worked=[]
        self.lock=th.Lock()
        self.droplock=th.Lock()
        self.load()
    def load(self):
        with open(self.file) as file:
            for row,line in enumerate(file):
                line=line.strip()
                if line:
                    if not line.startswith("//"):
##                        print(row,line)
                        self.saved.append(PushToken.fromstring(line))
        log.i(f"загружено {len(self.saved)} пуш-токенов")
    def save(self):
        with open(self.file,"w") as file:
            file.write("//WORKS\n")
            for token in self.worked:
                file.write(token.tostring()+"\n")
            file.write("//SAVED\n")
            for token in self.saved:
                file.write(token.tostring()+"\n")
    def push(self,token):
        with self.lock:
            self.worked.append(token)
            self.save()
    def get(self):
        with self.lock:
            if self.saved:
                token=self.saved.pop(0)
                self.worked.append(token)
                self.save()
                return token
    def release(self,token):
        with self.lock:
            self.worked.remove(token)
            self.saved.append(token)
            self.save()
    def delete(self,token):
        with self.lock:
            self.worked.remove(token)
            self.save()
    def drop(self,token):
        self.delete(token)
        with self.droplock:
            with open(self.dropfile,"a") as file:
                file.write(token.tostring()+"\n")
