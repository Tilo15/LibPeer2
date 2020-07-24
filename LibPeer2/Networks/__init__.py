import rx

class Network:

    NETWORK_IDENTIFIER = b""

    def __init__(self):
        self.incoming_advertisment = rx.subject.Subject()
        self.incoming_receiption = rx.subject.Subject()

    def bring_up(self):
        raise NotImplementedError

    def bring_down(self):
        raise NotImplementedError

    def advertise(self, instance_reference):
        raise NotImplementedError

    def send(self, buffer, peer_info):
        raise NotImplementedError
