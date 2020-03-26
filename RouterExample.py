from LibPeer2.Router.Configuration import RouterConfiguration
from LibPeer2.Router import BasicRouter

from LibPeer2.Networks.Simulation import Conduit

import AipExample

if __name__ == "__main__":
    conduit1 = Conduit(False)
    conduit2 = Conduit(False)

    config = RouterConfiguration(
        [
            conduit1.get_interface(),
            conduit2.get_interface()
        ]
    )

    router = BasicRouter(config)

    net1 = conduit1.get_interface(False, 0, 0)
    net1.bring_up()
    app1 = AipExample.AipExample(net1)

    net2 = conduit2.get_interface(False, 0, 0)
    net2.bring_up()
    app2 = AipExample.AipExample(net2)

    
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