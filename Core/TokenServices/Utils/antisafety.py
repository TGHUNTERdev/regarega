##import asyncio
import time
from functools import wraps
from Core import Log as log

import requests
##import httpx


ANTISAFETY = "https://antisafety.net/"
# ANTISAFETY = "http://127.0.0.1:3000/"


def retry(coro):
    @wraps(coro)
    def wrapper(*args, **kwargs):
        total_offsets = 0
        while total_offsets < 10:
            try:
##                log.d(coro,args,kwargs)
                return coro(*args, **kwargs)
            except Exception as e:
##                log.d("WE")
                time.sleep(1)
                total_offsets += 1
        return coro(*args, **kwargs)
    return wrapper


@retry
def get_balance(key: str):
##    client = httpx.AsyncClient(timeout=30)
##    res = await client.get(f"{ANTISAFETY}api/tasks/balance?api_key={key}")
    res = requests.get(f"{ANTISAFETY}api/tasks/balance?api_key={key}")
    res = res.json()
    return str(res.get("balance", 0) / 1000000) + " " + res.get("currency", "XMR")


@retry
def create_safetynet(key: str, nonce):
##    client = httpx.AsyncClient(timeout=30)
##    res = await client.get(f"{ANTISAFETY}api/tasks/safetynet/create?api_key={key}&nonce={nonce}")
    res = requests.get(f"{ANTISAFETY}api/tasks/safetynet/create?api_key={key}&nonce={nonce}")
    res = res.json()
    if res["status"] != "ok":
        return None
    return res["id"]


@retry
def get_safetynet(key: str, id):
##    client = httpx.AsyncClient(timeout=30)
##    res = await client.get(f"{ANTISAFETY}api/tasks/safetynet/get?api_key={key}&id={id}")
    res = requests.get(f"{ANTISAFETY}api/tasks/safetynet/get?api_key={key}&id={id}")
    res = res.json()
    if res["status"] != "ok":
        return None
    return res["token"]

@retry
def create_integrity(key: str, nonce):
##    client = httpx.AsyncClient(timeout=30)
##    res = await client.get(f"{ANTISAFETY}api/tasks/safetynet/create?api_key={key}&nonce={nonce}")
    res = requests.get(f"{ANTISAFETY}api/tasks/play-integrity/create?api_key={key}&nonce={nonce}")
    res = res.json()
    if res["status"] != "ok":
        return None
    return res["id"]


@retry
def get_integrity(key: str, id):
##    client = httpx.AsyncClient(timeout=30)
##    res = await client.get(f"{ANTISAFETY}api/tasks/safetynet/get?api_key={key}&id={id}")
    res = requests.get(f"{ANTISAFETY}api/tasks/play-integrity/get?api_key={key}&id={id}")
    res = res.json()
    if res["status"] != "ok":
        return None
    return res["token"]


##@retry
##def create_integrity(key: str, nonce):
####    client = httpx.AsyncClient(timeout=30)
####    res = await client.get(f"{ANTISAFETY}api/tasks/safetynet/create?api_key={key}&nonce={nonce}")
##    res = requests.get(f"{ANTISAFETY}api/tasks/safetynet/create?api_key={key}&nonce={nonce}")
##    res = res.json()
##    if res["status"] != "ok":
##        return None
##    return res["id"]
##
##@retry
##def get_integrity(key: str, id):
####    client = httpx.AsyncClient(timeout=30)
####    res = await client.get(f"{ANTISAFETY}api/tasks/safetynet/get?api_key={key}&id={id}")
##    res = requests.get(f"{ANTISAFETY}api/tasks/safetynet/get?api_key={key}&id={id}")
##    res = res.json()
##    if res["status"] != "ok":
##        return None
##    return res["token"]


@retry
def create_push(key: str):
##    client = httpx.AsyncClient(timeout=30)
##    res = await client.get(f"{ANTISAFETY}api/tasks/android-push/create?api_key={key}")
    res = requests.get(f"{ANTISAFETY}api/tasks/android-push/create?api_key={key}")
    res = res.json()
    if res["status"] != "ok":
        return None
    return res["id"]


@retry
def get_push(key: str, id):
##    client = httpx.AsyncClient(timeout=30)
##    res = await client.get(f"{ANTISAFETY}api/tasks/android-push/get?api_key={key}&id={id}")
    res = requests.get(f"{ANTISAFETY}api/tasks/android-push/get?api_key={key}&id={id}")
    res = res.json()
    if res["status"] != "ok":
        return None, None
    return res["token"], res["token_secret"]

@retry
def create_email(key: str, premium: bool, login: bool):
##    client = httpx.AsyncClient(timeout=30)
##    res = await client.get(f"{ANTISAFETY}api/tasks/email/create?api_key={key}")
##    if premium:
##        log.d(f"{ANTISAFETY}api/tasks/email/create?api_key={key}&type=premium")
##        res = requests.get(f"{ANTISAFETY}api/tasks/email/create?api_key={key}&type=premium")
##    else:
##        res = requests.get(f"{ANTISAFETY}api/tasks/email/create?api_key={key}")
    url = f"{ANTISAFETY}api/tasks/"+("login" if login else "email")+f"/create?api_key={key}"+("&type=premium" if premium else "")
    res = requests.get(url)
##    log.d("NETWORK", url, res.text)
    try:
        res = res.json()
        if res["status"] != "ok":
            log.e(f"Antisafety: {res}")
            return None
        return res
    except:
        log.e(f"Antisafety invalid response, status={res.status_code}")
        return None

@retry
def get_email(key: str, id, premium: bool):
    attempts = 0
##    client = httpx.AsyncClient(timeout=30)
    while attempts < 15:
##        res = await client.get(f"{ANTISAFETY}api/tasks/email/get?api_key={key}&id={id}")
        if premium:
##            log.d(f"{ANTISAFETY}api/tasks/email/get?api_key={key}&id={id}&type=premium")
            res = requests.get(f"{ANTISAFETY}api/tasks/email/get?api_key={key}&id={id}&type=premium")
        else:
            res = requests.get(f"{ANTISAFETY}api/tasks/email/get?api_key={key}&id={id}")
##        log.d("NETWORK", res.text)
        try:
            res = res.json()
            if res["status"] != "ok":
##                log.w(f"Antisafety: {res}")
                return None
            if res["status"] == "ok" and not res.get("result"):
##                log.d(f"Antisafety: {res}")
                time.sleep(10)
                attempts += 1
                continue
            return res["result"]
        except:
##            log.e(f"Antisafety invalid response, status={res.status_code}")
            time.sleep(10)
            continue


@retry
def dislike_email(key: str, id):
    res = requests.get(f"{ANTISAFETY}api/tasks/email/dislike?api_key={key}&id={id}")
##    client = httpx.AsyncClient(timeout=30)
##    res = await client.get(f"{ANTISAFETY}api/tasks/email/dislike?api_key={key}&id={id}")
##    logger.log("NETWORK", res.text)

@retry
def dislike_email_google(key: str, id):
    res = requests.get(f"{ANTISAFETY}api/tasks/gauth/dislike?api_key={key}&id={id}")


@retry
def create_recaptcha(key: str, action: str):
    res = requests.get(f"{ANTISAFETY}api/tasks/recaptcha/create?api_key={key}&action={action}")
##    log.d("NETWORK", res.request.url, res.text)
    res = res.json()
    if res["status"] != "ok":
        return None
    return res["id"]

@retry
def get_recaptcha(key: str, id):
    res = requests.get(f"{ANTISAFETY}api/tasks/recaptcha/get?api_key={key}&id={id}")
##    log.d("NETWORK", res.request.url, res.text)
    res = res.json()
    if res["status"] != "ok":
        return None
    return res["token"]
