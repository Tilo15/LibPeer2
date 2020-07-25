from LibPeer2.Networks.Simulation import Conduit
from LibPeer2.Repeater.FrameRepeater import FrameRepeater

import AppExample
import time

if __name__ == "__main__":
    conduit1 = Conduit(False)
    conduit2 = Conduit(False)
    conduit3 = Conduit(False)

    repeater1 = FrameRepeater()
    r1net1 = conduit1.get_interface(False, 0, 0.0)
    r1net1.bring_up()
    r1net2 = conduit2.get_interface(False, 0, 0.0)
    r1net2.bring_up()
    repeater1.register_network(r1net1)
    repeater1.register_network(r1net2)
    #router2 = BasicRouter(config2)

    print("Waiting 10 seconds before starting apps")
    time.sleep(10)

    net1 = conduit1.get_interface(False, 0, 0.0)
    net1.bring_up()
    app1 = AppExample.AppExample([net1])

    net2 = conduit2.get_interface(False, 0, 0.0)
    net2.bring_up()
    app2 = AppExample.AppExample([net2])

    # net3 = conduit2.get_interface(False, 0, 0)
    # net3.bring_up()
    # app3 = AppExample.AppExample([net3])