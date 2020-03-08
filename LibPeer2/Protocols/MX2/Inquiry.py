from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference

from rx.subjects import Subject
from threading import Timer

import uuid
import time

class Inquiry:

    def __init__(self, target: InstanceReference, timeout = 120):
        self.id = uuid.uuid4().bytes
        self.target = target
        self.time = time.time()
        self.complete = Subject()

        self.timer = Timer(timeout, self.complete.on_error, (TimeoutError("The inquiry timed out.",)))

    def response_received(self) -> float:
        self.timer.cancel()
        time = time.time() - self.time

        self.complete.on_next(self.time)
        self.complete.on_completed()

        return time

    
