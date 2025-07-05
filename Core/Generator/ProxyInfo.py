import requests
import time
from Core import Log as log
class ProxyInfo:
    delay=5
    host=None
    def getip(self,proxy):
        while True:
            try:
                return requests.get(
                    self.host+"/api/getip",
                    proxies={"http":proxy}
                ).text
            except Exception as e:
                log.e(f"прокси: {e}",level=log.level.debug)
                time.sleep(self.delay)
    def getinfo(self,ip):
        while True:
            try:
                return requests.get(
                    self.host+"/api/getinfo",
                    params={"ip":ip}
                ).json()
            except Exception as e:
                log.e(f"прокси: {e}",level=log.level.debug)
                time.sleep(self.delay)
    def getdata(self,proxy):
        ip=self.getip(proxy)
##        print("ip",ip)
        log.d(f"прокси: {ip}",level=log.level.debug)
        return self.getinfo(ip)
##pi=ProxyInfo()
##pi.host="http://194.15.46.98:80"
##pi.getdata("http://zpyvful57q-res-country-US-hold-session-session-664725bdcbcd1:zvlt66jyD4Uod94y@190.2.143.237:9999")
