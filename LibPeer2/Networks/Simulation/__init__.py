from LibPeer2.Networks.Simulation.NetSim import NetSim
from LibPeer2.Networks.Simulation.InterfaceStats import InterfaceStats
from LibPeer2.Networks.Simulation.PairStats import PairStats
from io import BytesIO

import uuid
import time
import threading

class Conduit:

    def __init__(self, auto_print_pair_stats = True):
        self.interfaces = {}
        self.stats = {}
        self.pairs = {}
        self.count = 0

        if(auto_print_pair_stats):
            threading.Thread(name="Stat Timer", target=self.auto_print).start()
        

    def get_interface(self, print_stats = False, latency = 0.1, loss_probability = 0.0):
        self.count += 1
        identifier = uuid.uuid4().bytes
        interface = NetSim(self, identifier, self.count, latency, loss_probability)
        self.interfaces[identifier] = interface
        self.stats[identifier] = InterfaceStats(identifier, self.count, print_stats)

        return interface

    def send_packet(self, origin, destination, buffer):
        data = buffer.read()
        size = len(data)
        new_buffer = BytesIO(data)

        self.stats[origin].send(size)
        if(destination in self.interfaces):
            # Do we have a pair?
            pair = (origin, destination)
            if(pair not in self.pairs):
                # Create it
                self.pairs[pair] = PairStats(self.interfaces[origin].count, self.interfaces[destination].count)

            pstat = self.pairs[pair]
            pstat.send(size)

            self.stats[destination].receive(size)
            self.interfaces[destination]._receive_packet(origin, new_buffer)

    
    def auto_print(self):
        while True:
            try:
                self.print_pair_stats()
            except:
                pass
            time.sleep(5)



    def print_pair_stats(self):
        stats = list(self.pairs.values())
        most_packets = max(s.count for s in stats)
        most_packets_between = max(stats, key=lambda s: s.count).between
        least_packets = min(s.count for s in stats)
        least_packets_between = min(stats, key=lambda s: s.count).between
        avg_packets = sum(s.count for s in stats) / len(stats)

        most_data = max(s.size for s in stats)
        most_data_between = min(stats, key=lambda s: s.size).between
        least_data = min(s.size for s in stats)
        least_data_between = min(stats, key=lambda s: s.size).between
        avg_data = sum(s.size for s in stats) / len(stats)

        total_packets = sum(s.count for s in stats)
        total_data = sum(s.size  for s in stats)

        print()
        print("Packets:\tMAX: {} ({})\tMIN: {} ({})\t AVG: {}".format(most_packets, most_packets_between, least_packets, least_packets_between, avg_packets))
        print("Data:\t\tMAX: {} ({})\tMIN: {} ({})\t AVG: {}".format(most_data, most_data_between, least_data, least_data_between, avg_data))
        print("Total:\t\tPKTS: {}  \tBYTES: {}".format(total_packets, total_data))



    def advertise(self, origin, advertisment):
        for interface in self.interfaces.values():
            if(interface.identifier != origin):
                interface.incoming_advertisment.on_next(advertisment)
