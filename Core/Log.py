import colorama
import os
import sys
import warnings
import logging
import queue
import threading as th
from datetime import datetime
from Core.Version import version
from Core.Version import appname
class level:
    debug = 0
    default = 100
warnings.filterwarnings("ignore")
logging.disable()
LOGLEVEL = level.default
##logging.basicConfig(level=logging.NOTSET)
##LOGLEVEL = level.debug
LINES=0
MAX=50000
IO=None
PATH="log"
CODES=[
    (">",colorama.Fore.WHITE),          #0
    ("+",colorama.Fore.GREEN),          #1
    ("-",colorama.Fore.YELLOW),         #2
    ("!",colorama.Fore.RED),            #3
    ("*",colorama.Fore.CYAN),           #4
    ("<",colorama.Fore.MAGENTA),        #5
    ("+",colorama.Fore.LIGHTGREEN_EX)   #6
]
TIME_SCHEME="%Y.%m.%d [%H %M %S]"
LOCK=th.Lock()
LOGS=queue.Queue()
MAX_LOGS=10
def init():
    global IO
    global LINES
    thread=th.current_thread().name="Главный поток"
    colorama.init(autoreset=True)
    if os.path.exists(PATH):
        file=getio()
        if file is None:
            newio()
        else:
            file=PATH+"/"+file
            with open(file,encoding="utf-8") as stream:
                LINES=stream.read().count("\n")
            IO=open(file,"a",encoding="utf-8")
    else:
        os.mkdir(PATH)
        newio()
    d(appname,version)
##def getio():
##    limit=0
##    result=None
##    for file in os.listdir(PATH):
##        if os.path.isfile(PATH+"/"+file):
##            name=os.path.splitext(file)[0]
##            try:
##                value=datetime.strptime(name,TIME_SCHEME).timestamp()
##            except ValueError:
##                pass
##            else:
##                if value>limit:
##                    limit=value
##                    result=file
##    return result
def getio():
    logs=[]
    for file in os.listdir(PATH):
        if os.path.isfile(PATH+"/"+file):
            name=os.path.splitext(file)[0]
            try:
                value=datetime.strptime(name,TIME_SCHEME).timestamp()
            except ValueError:
                pass
            else:
                logs.append((value,file))
    logs.sort(key=lambda x:x[0])
    if logs:
        for log in logs:
            LOGS.put(log[1])
        clean()
        return logs[0][1]
##                if value>limit:
##                    limit=value
##                    result=file
def newio():
    global IO
    name=datetime.now().strftime(f"{TIME_SCHEME}.txt")
    LOGS.put(name)
    IO=open(PATH+"/"+name,"w",encoding="utf-8")
    clean()
def clean():
    while LOGS.qsize()>MAX_LOGS:
        os.remove(PATH+"/"+LOGS.get())
def push(code,message,level):
    global LINES
    time=datetime.now().strftime("%H:%M:%S")
    thread=th.current_thread().getName()
    message=" ".join(map(str,message))
    symbol,color=CODES[code]
    with LOCK:
        if level>=LOGLEVEL:
            print(f"[{time}]{color}[{symbol}] {thread}: {message}")
        IO.write(f"[{time}][{symbol}] {thread}: {message}\n")
        IO.flush()
    LINES+=1
    if LINES>MAX:
        LINES=0
        IO.close()
        newio()
def d(*m,level=level.default):
    push(0,m,level)
def i(*m,level=level.default):
    push(1,m,level)
def w(*m,level=level.default):
    push(2,m,level)
def e(*m,level=level.default):
    push(3,m,level)
def a(*m,level=level.default):
    push(4,m,level)
def m(*m,level=level.default):
    push(5,m,level)
def s(*m,level=level.default):
    push(6,m,level)
