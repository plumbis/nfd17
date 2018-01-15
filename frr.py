#!/usr/bin/env python

fabric_interface_list = ["swp1", "swp2"]
asn = "65011"
router_id = "10.0.0.11"
bgp_networks = ["10.0.0.11/32", "10.0.0.112/32"]
bgp_peer_ips = []

host = 0
subnet = 0
block = "10.0"

while host < 255:
    if host % 2:
        bgp_peer_ips.append(block + "." + str(subnet) + "." + str(host))
    host += 1


output = []
output.append("frr version 3.1+cl3u1")
output.append("frr defaults datacenter")
output.append("username cumulus nopassword")
output.append("!")
output.append("service integrated-vtysh-config")
output.append("!")
output.append("log syslog informational")
output.append("!")

for interface in fabric_interface_list:
    output.append("interface " + interface)
    output.append(" ipv6 nd ra-interval 10")
    output.append(" no ipv6 nd suppress-ra")
    output.append("!")

output.append("router bgp " + asn)
output.append(" bgp router-id" + router_id)
output.append(" bgp bestpath as-path multipath-relax")

for interface in fabric_interface_list:
    output.append(" neighbor " + interface + " interface remote-as external")

output.append(" !")
output.append(" address-family ipv4 unicast")

for network in bgp_networks:
    output.append("  network " + network)

output.append(" exit-address-family")
output.append(" !")
output.append(" address-family l2vpn evpn")
for interface in fabric_interface_list:
    output.append("  neighbor " + interface + " activate")

output.append("  advertise-all-vni")
output.append(" exit-address-family")
output.append("!")
output.append("line vty")
output.append("!")

print "\n".join(output)

