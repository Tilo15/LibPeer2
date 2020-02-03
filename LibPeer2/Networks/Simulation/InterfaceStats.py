import base64

class InterfaceStats:

    def __init__(self, identifier, number, print_stats):
        self.number = number
        self.identifier = identifier
        self.packets_sent = 0
        self.packets_received = 0
        self.data_sent = 0
        self.data_received = 0
        self.print_stats = print_stats
        self.print_info()

    def send(self, size):
        self.packets_sent += 1
        self.data_sent += size
        self.print_info()

    def receive(self, size):
        self.packets_received += 1
        self.data_received += size
        self.print_info()

    def print_info(self):
        if(self.print_stats):
            print("NetSim{}:\tRX: {} pkts  {} bytes\tTX: {} pkts  {} bytes".format(self.number, self.packets_received, self.data_received, self.packets_sent, self.data_sent))