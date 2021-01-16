

class Repeater:

    def __init__(self):
        from LibPeer2.Debug import Log
        Log.msg("Loading frame repeater...")
        from LibPeer2.Repeater.FrameRepeater import FrameRepeater
        from LibPeer2.Networks.IPv4 import IPv4
        Log.msg("Initialising Network...")
        network = IPv4("0.0.0.0", 7777)
        network.bring_up()
        Log.msg("Initialising Frame Repeater...")
        repeater = FrameRepeater()
        Log.msg("Attaching Network...")
        repeater.register_network(network)
        Log.info("Frame Repeater is Ready.")


if __name__ == "__main__":
    Repeater()