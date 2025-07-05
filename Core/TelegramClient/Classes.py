import socks
import pytz
import datetime
class Proxy:
    @classmethod
    def fromstring(cls,protocol,source):
        data=source.split(":")
        if len(data)==4:
            if data[1].isdigit():
                return cls(
                    protocol,
                    data[0],
                    int(data[1]),
                    True,
                    data[2],
                    data[3]
                )
            else:
                raise ValueError("порт не является числом")
        else:
            raise ValueError("неверный формат прокси")
    def __init__(self,protocol,host,port,auth,user,password):
        self.protocol=protocol
        self.host=host
        self.port=port
        self.auth=auth
        self.user=user
        self.password=password
    def __str__(self):
        return f"{socks.PRINTABLE_PROXY_TYPES[self.protocol].lower()}://{self.host}:{self.port}:{self.user}:{self.password}"
    def tostring(self):
        return f"{socks.PRINTABLE_PROXY_TYPES[self.protocol].lower()}://{self.user}:{self.password}@{self.host}:{self.port}"
    def tolist(self):
        return [
            self.protocol,
            self.host,
            self.port,
            self.auth,
            self.user,
            self.password
        ]
class TimeZone:
    def __init__(self,name):
        self.name=name
        try:
            self.offset=int(datetime.datetime.now(pytz.timezone(name)).utcoffset().total_seconds())
        except:
            raise ValueError(f"не известная тайм-зона: {name}")
    def __str__(self):
        return f"{self.name} ({self.offset})"
    def __repr__(self):
        return str(self)
        
