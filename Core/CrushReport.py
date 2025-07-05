import traceback
import os
import threading as th
from Core import Log as log
from datetime import datetime
##CRUSH_DIR="crush"
def init():
    pass
##    if not os.path.exists(CRUSH_DIR):
##        os.mkdir(CRUSH_DIR)
class CrushReport:
    def __init__(self,name):
        self.name=name
        self.error=None
    def __enter__(self):
        return self
    def __exit__(self,cls,err,tb):
        if cls:
            stack=traceback.format_tb(tb)
            thread=th.current_thread().getName()
            error=f"Fatal exception in {thread}\n"
            for line in stack:
                error+=f"{line}"
            error+=f"{cls.__name__}: ({err})"
            log.e(error)
##            error=f"{cls.__name__}: ({err})"
##            name=datetime.now().strftime(f"{cls.__name__} {log.TIME_SCHEME}")
##            thread=th.current_thread().getName()
##            with open(f"{CRUSH_DIR}/{name}.txt","w",encoding="utf-8") as file:
##                file.write(f"Fatal exception in {thread}\n")
##                for line in stack:
##                    file.write(line)
##                file.write(error)
##            log.e(f"{self.name} {name}: ({err})")
            self.error=True
            return True
