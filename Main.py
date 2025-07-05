from Core import Log as log
from Core.Core import Core
from Core.CrushReport import CrushReport
def main():
    with CrushReport("ошибка запуска") as report:
        core=Core()
        if not core.start():
            return
    if report.error:
        return
    with CrushReport("ошибка конфигурирования") as report:
        try:
            core.LoadConfig()
        except ValueError as e:
            log.w("Ошибка загрузки конфигурации:",e)
            return
    if report.error:
        return
    with CrushReport("ошибка выполнения"):
        core.run()
main()
input(">> ")
