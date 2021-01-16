from LibPeer2 import InstanceManager


class AppExample:

    def __init__(self, networks = []):
        self.manager = InstanceManager("AppExample", True, networks)
        self.manager.new_peer.subscribe(self.on_new_peer)
        self.manager.new_stream.subscribe(self.on_incoming_stream)
        self.manager.resources.add(b"HI"*16)

        self.message = b"Hello World!"



    def on_new_peer(self, peer):
        print("I just found a new peer!")
        self.manager.establish_stream(peer).subscribe(self.on_outgoing_stream)


    def on_outgoing_stream(self, stream):
        stream.write(self.message)
        stream.close()
        print("I just sent a hello world!")

        self.manager.find_resource_peers(b"HI"*16).subscribe(lambda x: print("I also found special resouce peer {}!".format(x)))


    def on_incoming_stream(self, stream):
        message = stream.read(len(self.message))
        stream.close()

        if(message != self.message):
            print("I didn't receive Hello World!")
            return

        print("I got a hello world from {}!".format(stream.origin))
        

if __name__ == "__main__":
    AppExample()