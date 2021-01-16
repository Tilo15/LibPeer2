from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from LibPeer2.Debug import Log

from rx.subject import Subject
from threading import Timer


import uuid
import time

class Inquiry:

    def __init__(self, target: InstanceReference, timeout = 10):
        self.id = uuid.uuid4().bytes
        self.target = target
        self.time = time.time()
        self.complete = Subject()

        self.timer = Timer(timeout, self.__timeout)
        self.timer.start()

    def response_received(self) -> float:
        self.timer.cancel()
        delay = time.time() - self.time

        self.complete.on_next(delay)
        self.complete.on_completed()

        return delay

    def __timeout(self):
        Log.warn("Inquiry timed out")
        self.complete.on_error(TimeoutError("The inquiry timed out."))
