#!/usr/bin/env python
import pprint
import yaml
import copy
# node:
#     leaf01:
#         interfaces:
#             lo:
#                 ipv4: "10.0.0.1/32"
#         bgp:
#             asn: 65011
#             server_ports: ["swp1", "swp2"]

#     chassis01-lc2-2:
#             interfaces:
#                 lo:
#                     ipv4: "10.1.2.2/32"
#             bgp:
#                 asn: 4200000122
#                 leafs: ["swp4"]

#     chassis01-fc2-1:
#             interfaces:
#                 lo:
#                     ipv4: "10.1.255.2/32"
#             bgp:
#                 asn: 4200000100

leaf_count = 32
spine_count = 4
host_count = 6

inventory = {}
subnet = "10.0.0."
asn = 64512
peer_output = []

for leaf in range(1, leaf_count + 1):
    v4_addr = subnet + str(leaf) + "/32"

    inventory["leaf" + str("%02d" % leaf)] = {"interfaces": {"lo": v4_addr},
                                                      "bgp" : {"asn": str(asn), "peers": ["swp1", "swp2", "swp3", "swp4"]}
                                                     }
    peer_output.append("swp" + str(leaf))
    asn += 1

subnet = "10.255.255."


for spine in range(1, spine_count + 1):
    v4_addr = subnet + str(spine) + "/32"
    inventory["spine" + str("%02d" % spine)] = {"interfaces": {"lo": v4_addr},
                                                      "bgp" : {"asn": str(asn), "peers": copy.deepcopy(peer_output)}
                                                     }

    asn += 1

output = {"node": inventory}
print yaml.dump(output, default_flow_style=False)
