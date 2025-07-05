import json
class Account:
    phone=None
    client=None
    email=None
    smscode=None
    sentcode=None
    path=None
    status=None
    statefile=None
    error=None
    def __init__(self,country):
        self.country=country
        self.begin=True
        self.data={}
        self.SentCodeSequence=[]
        self.ActionSequence=[]
        self.restarts=0
    def __str__(self):
        return str(self.phone)
    def setsentcode(self,sentcode):
        self.SentCodeSequence.append(type(sentcode.type).__name__)
        self.sentcode=sentcode
    def getstate(self):
        return {
            "phone":self.phone.number,
            "captcha":self.client.CaptchaAction if self.client else None,
            "status":self.status,
            "error":self.error,
            "country":{
                "code":self.country.code,
                "name":self.country.name,
                "proxy":self.country.proxy
            },
            "data":self.data,
            "email":self.email.address if self.email else None,
            "smscode":self.smscode,
            "actions":self.ActionSequence,
            "codes":self.SentCodeSequence
        }
    def savestate(self):
        data=self.getstate()
        with open(self.statefile,"w",encoding="utf-8") as file:
            json.dump(data,file,indent=3)
