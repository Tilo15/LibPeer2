from LibPeer2.Protocols.MX2.Frame import Frame

class Packet:

    def __init__(self, frame: Frame):
        self.origin = frame.origin
        self.destination = frame.destination
        self.stream = frame.payload
