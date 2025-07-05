import requests
import random
from Core.CheckNumberService.CheckNumberService import CheckNumberService
from Core import Log as log

class CheckNumberEmptyService(CheckNumberService):
    name = "empty"

    def load(self, config):
        log.w("проверка номеров не используется")

    def CheckNumber(self,phone):
        return True


