import threading
import time
from typing import Callable

class Repeater:

    def __init__(self, interval: float, times: int, action: Callable, name="STP Action Repeater"):
        self.__interval = interval
        self.__times = times
        self.__cancelled = False
        self.__action = action

        threading.Thread(name=name, target=self.__run).start()



    def cancel(self):
        self.__cancelled = True


    def __run(self):
        for i in range(self.__times):
            self.__action()
            time.sleep(self.__interval)
            if(self.__cancelled):
                break

