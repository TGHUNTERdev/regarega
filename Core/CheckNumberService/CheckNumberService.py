import threading as th
import time
import requests
import random
import json
from Core import Log as log
class Task:
    def __init__(self,tid,phone):
        self.id=tid
        self.phone=phone
    def __str__(self):
        return self.phone
class CheckNumberService:
    name=""
    def __init__(self,core):
        self.core=core
    def load(self,config):
        self.host=config.gethost("host")
        log.m(f"используется сервис {self.name} [{self.host}]")
        self.TaskDefaultDelay=config.getdelay("task default delay")
        self.TaskErrorDelay=config.getdelay("task error delay")
        self.TaskWaitTime=config.getdelay("task wait time")
        self.CodeDefaultDelay=config.getdelay("result default delay")
        self.CodeErrorDelay=config.getdelay("result error delay")
        self.CodeWaitTime=config.getdelay("result wait time")
        self.CodeWaitTimeout=config.getdelay("result timeout")
        self.CodeFilter={
            "NOTOCCUPIED":config.getbool("use not occupied"),
            "HASUSER":config.getbool("use has user"),
            "NOUSER":config.getbool("use not user")
        }
        for key,value in self.CodeFilter.items():
            if value:
                log.i("код",key,"продолжает работу с номером")
            else:
                log.w("код",key,"исключает работу с номером")
        self.CodeFilterDefault=config.getbool("use if no result")
        if self.CodeFilterDefault:
            log.i("при отсутствии результата продолжает работу с номером")
        else:
            log.w("при отстутсвии результата исключает работу с номером")
        if self.CodeWaitTime*2>self.CodeWaitTimeout:
            raise ValueError(f"таймаут ожидания результата должен быть больше времени ожидания кода хотя бы в 2 раза")
        self.path = "/api"
        try:
            code=self.request(self.path,{
                "action":"checkService"
            }).text
        except Exception as e:
            raise ValueError(f"сервис проверки номеров не доступен по причине: {type(e).__name__}({e})")
        else:
            if code=="OK":
                log.i("установелно соединение по http")
            else:
                raise ValueError("сервис проверки номеров дал не валидный ответ")
    def CheckNumber(self,phone):
        task=self.WaitTask(phone)
        if task:
            time.sleep(self.CodeDefaultDelay)
            return self.WaitResult(task)
        else:
            return self.CodeFilterDefault
    def WaitTask(self,phone):
        first=time.time()
        limit=first+self.TaskWaitTime
        while True:
            try:
                reqtime=time.time()
                task=self.GetTask(phone)
            except json.JSONDecodeError:
                log.e("невозможно распознать ответ сервиса как json")
                time.sleep(self.TaskErrorDelay)
            except RuntimeError as e:
                log.e(f"ошибка получения задачи: {e}")
                time.sleep(self.TaskErrorDelay)
            except Exception as e:
                log.e(f"ошибка при получении задачи: {type(e)}({e})",level=log.level.debug)
                time.sleep(self.TaskErrorDelay)
            else:
                if task:
                    log.w(f"получена задача из сервиса {task}",level=log.level.debug)
                    return task
                elif reqtime>limit:
                    log.w("задача не пришла в течении {int(reqtime-first)}s")
                    return
                else:
                    time.sleep(self.TaskDefaultDelay)
    def GetTask(self,phone):
        response = self.request(self.path,{
            "action":"addPhone",
            "phone":phone
        })
        data = response.text.split("|")
        if data[0]=="OK":
            return Task(data[1], phone)
    def WaitResult(self,task):
        first=time.time()
        limit=first+self.CodeWaitTime
        conrtol=first+self.CodeWaitTimeout
        while True:
            try:
                reqtime=time.time()
                code=self.GetResult(task)
            except json.JSONDecodeError:
                log.e("невозможно распознать ответ сервиса как json")
                if reqtime>conrtol:
                    raise RuntimeError("превышено время ожидания кода")
                time.sleep(self.CodeErrorDelay)
            except Exception as e:
                log.e(f"{task}: ошибка получения смс: {e}")
                if reqtime>conrtol:
                    raise RuntimeError("превышено время ожидания кода")
                time.sleep(self.CodeErrorDelay)
            else:
                if code:
                    log.d(f"{task} получен результат {code}")
                    return self.CodeFilter.get(code)
                elif reqtime>limit:
                    log.w(f"{task} результат не пришёл в течении {int(reqtime-first)}s")
                    return self.CodeFilterDefault
                else:
                    time.sleep(self.CodeDefaultDelay)
    def GetResult(self,task):
        response = self.request(self.path,{
            "action":"getResult",
            "id":task.id
        })
        data = response.text.split("|")
        if data[0]=="OK":
            return data[1]
    def request(self,path,params={}):
##        log.d(self.host+path,params)
        return requests.get(
            self.host+path,
            params=params,
        )
