

if __name__ == "__main__":
    print("Loading...")
    from LibPeer2.Repeater.FrameRepeater import FrameRepeater
    from LibPeer2.Networks.IPv4 import IPv4
    print("Initialising Network...")
    network = IPv4("0.0.0.0", 7777)
    network.bring_up()
    print("Initialising Frame Repeater...")
    repeater = FrameRepeater()
    print("Attaching Network...")
    repeater.register_network(network)
    print("Frame Repeater is Ready.")