#!/usr/bin/env python
import pprint
import yaml

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

leaf_count = 128
chassis_list = ["chassis01", "chassis02", "chassis03", "chassis04"]
linecard_list = ["lc1-1", "lc1-2", "lc2-1", "lc2-2", "lc3-1", "lc3-2", "lc4-1", "lc4-2"]
fabriccard_list = ["fc1-1", "fc2-1", "fc3-1", "fc4-1"]

inventory = {}
subnet = "10.0.0."
asn = 64512

current_leaf = 1

while current_leaf <= leaf_count:
    v4_addr = subnet + str(current_leaf) + "/32"

    inventory["leaf" + str("%02d" % current_leaf)] = {"interfaces": {"lo": v4_addr},
                                                      "bgp" : {"asn": str(asn), "peers": ["swp1", "swp2", "swp3", "swp4"]}
                                                     }

    current_leaf += 1
    asn += 1

ip = current_leaf


for chassis in chassis_list:

    for linecard in linecard_list:
        hostname = chassis + "-" + linecard
        v4_addr = subnet + str(ip) + "/32"
        peers = []
        for swp in range(1,17):
            peers.append("swp" + str(swp))
            peers.append("fp" + str(swp - 1))

            inventory[hostname] = {"interfaces": {"lo": v4_addr},
                                                      "bgp" : {"asn": str(asn), "peers": peers}
                                                     }

        ip += 1
        asn += 1

    for fabriccard in fabriccard_list:
        hostname = chassis + "-" + fabriccard
        v4_addr = subnet + str(current_leaf) + "/32"
        peers = []
        for fp in range(0,32):
            peers.append("fp" + str(fp))

        inventory[hostname] = {"interfaces": {"lo": v4_addr},
                                                      "bgp" : {"asn": str(asn), "peers": peers}
                                                     }

        ip += 1

    asn += 1

print yaml.dump(inventory, default_flow_style=False)
