from LibPeer2.Router.Configuration import RouterConfiguration
from LibPeer2.Router import BasicRouter

from LibPeer2.Networks.Simulation import Conduit

import AppExample

if __name__ == "__main__":
    conduit1 = Conduit(False)
    conduit2 = Conduit(False)

    config = RouterConfiguration(
        [
            conduit1.get_interface(False, 0, 0.0),
            conduit2.get_interface(False, 0, 0.0)
        ]
    )

    router = BasicRouter(config)

    net1 = conduit1.get_interface(False, 0, 0.0)
    net1.bring_up()
    app1 = AppExample.AppExample([net1])

    net2 = conduit2.get_interface(False, 0, 0.0)
    net2.bring_up()
    app2 = AppExample.AppExample([net2])

    # net3 = conduit2.get_interface(False, 0, 0)
    # net3.bring_up()
    # app3 = AipExample.AipExample(net3)

    
#
# Aight, what you need to do to get this going now
# - Add a new capability to AIP - a "Do you have" request to see if an AIP instance is also connected to a particular application instance (or can route to it)
# - Route queries need to also have the target application instance in the query
# - When a route query is received that is serviceable, the AIP instance must ask the target AIP instance if they have the target application instance (or can route to it)
# - If a reply is received, respond to the query and notify the router (via a subject) of an association between the AIP instance and the application instance
# - Router will add a route to the instance using the 
#
# The "Do you have" capability should specify how many hops it has to go through. You'll figure it out.
#