import threading as th
class Phone:
    def __init__(self, phone_id, number):
        self.id = phone_id
        self.number = number
    def __str__(self):
        return self.number
class Country:
    def __init__(self, code, name, proxy):
        self.code = code
        self.name = name
        self.proxy = proxy
    def __str__(self):
        return f"{self.name}[{self.code}]"
