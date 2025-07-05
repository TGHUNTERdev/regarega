import time
from Core import Log as log
from Core.EmailService.Classes import Email
from Core.TokenServices.Utils import antisafety
class EmailService:
    def __init__(self,core):
        self.core=core
    def load(self,config):
        raise NotImplementedError
    def WaitEmail(self):
        raise NotImplementedError
    def WaitCode(self,email):
        raise NotImplementedError
    def SetFinish(self,email):
        raise NotImplementedError
    def SetBan(self,email):
        raise NotImplementedError
    def SetWrongCode(self,email):
        pass
    def SetNoCode(self,email):
        pass
    def DislikeEmail(self,email):
        raise NotImplementedError
