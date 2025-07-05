import requests
import random
from Core.EmailService.Live.Classes import EmailLive as Email
from Core.EmailService.Live.EmailLiveService import EmailLiveService
from Core.EmailService.Live.Classes import EmailStorageEmpty
from Core import Log as log

class EmailLocalService(EmailLiveService):
    name = "local"

    def load(self, config):
        EmailLiveService.load(self, config)
        self.path = "/api"
        try:
            code=self.request(self.path,{
                "action":"checkService"
            }).text
        except Exception as e:
            raise ValueError(f"почтовый сервис не доступен по причине: {type(e).__name__}({e})")
        else:
            if code=="OK":
                log.i("установелно соединение по http")
            else:
                raise ValueError("почтовый сервис дал не валидный ответ")
            
    def LoadStorage(self,config):
        self.EmailStorage=EmailStorageEmpty(self.name,self.host)
    
    def GetEmail(self):
        response = self.request(self.path,{
            "action":"getEmail"
        })
        data = response.text.split("|")
        if data[0]=="OK":
            return Email(data[1], data[2])

    def GetSms(self, email):
        response = self.request(self.path,{
            "action":"getCode",
            "id":email.id
        })
        data = response.text.split("|")
        if data[0]=="OK":
            return data[1]

    def SetStatus(self, email, status):
        self.request(self.path,{
            "action":"setStatus",
            "id":email.id,
            "status":status
        })

    def SetFinish(self,email):
        if not email.dislike:
            self.SetStatus(email,"success")

    def SetBan(self,email):
        if not email.dislike:
            self.SetStatus(email,"fail")

    def SetWrongCode(self,email):
        self.SetStatus(email,"wrongcode")

    def SetNoCode(self,email):
        self.SetStatus(email,"nocode")

    def DislikeEmail(self,email):
        self.SetStatus(email,"dislike")
        email.dislike=True


