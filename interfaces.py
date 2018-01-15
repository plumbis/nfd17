#!/usr/bin/env python

loopback = "9.9.9.1/32"

interfaces = {
  "swp25": "",
  "swp49": "172.168.12.1/30",
}

vrf = False
subnet = 16
host_bits = 1

x = 100
while x < 105:
    interfaces["vni" + str(x)] = ""
    x += 1

bridge_ports = []
for interface, ip in interfaces.iteritems():
  if ip == "":
    bridge_ports.append(interface)
bridge_vids = []
output = []
output.append("# Management interface")
output.append("auto eth0")
output.append("iface eth0")
output.append("  alias management interface")
output.append("  address 10.219.130.92/23")
output.append("  gateway 10.219.130.1")
output.append("")
output.append("# Loopback interface")
output.append("auto lo")
output.append("iface lo inet loopback")
output.append("  alias loopback interface")
output.append("  address " + loopback)
output.append("")
output.append("auto blue")
output.append("iface blue")
output.append("   vrf-table auto")
output.append("")
for interface, ip in interfaces.iteritems():
    output.append("auto " + interface)
    output.append("iface " + interface)

    if interface == "swp25":
        output.append(" link-speed 10000")
        output.append(" mtu 9000")

    if interface == "swp49":
        output.append("  mtu 9216")

    if ip != "":
        output.append(" address " + ip)

    if interface.find("vni") >= 0:
        id = interface[interface.find("vni") + 3:]
        output.append("  vxlan-id " + id)
        output.append("  bridge-access " + id)
        output.append("  bridge-learning off")
        output.append("  mstpctl-bpduguard yes")
        output.append("  mstpctl-portbpdufilter yes")
        output.append("  bridge-arp-nd-suppress on")
        output.append("  vxlan-local-tunnelip " + loopback[:loopback.find("/")])
        output.append("  mtu 9000")
        output.append("")
        output.append("auto vlan" + id)
        output.append("iface vlan" + id)
        if int(id) < 255:
            output.append(" address 172.1." + id + ".1/24")

        if id > int(255) and id < int(510) :
            output.append(" address 172.2." + str(int(id - 255)) + ".1/24")

        if id > int(510) and id < int(765) :
            output.append(" address 172.3." + str(int(id - 510)) + ".1/24")

        if id > int(765) and id < int(1020) :
            output.append(" address 172.3." + str(int(id - 1020)) + ".1/24")

        if id > int(1020) and id < int(1275) :
            output.append(" address 172.4." + str(int(id - 1020)) + ".1/24")

        if int(id) > 1275:
            print "id is too high"
            exit(1)

        output.append("  vlan-id " + id)
        if vrf:
            output.append("vrf blue")
        output.append("  vlan-raw-device bridge")
        bridge_vids.append(id)
    output.append("")

output.append("auto bridge")
output.append("iface bridge")
output.append("  bridge-vlan-aware yes")
output.append("  bridge-ports " + " ".join(bridge_ports))
output.append("  bridge-vids " + " ".join(bridge_vids))
output.append("")

output.append("# auto vni2000")
output.append("# iface vni2000")
output.append("#    vxlan-id 2000")
output.append("#    vxlan-local-tunnelip 9.9.9.1")
output.append("#    bridge-learning off")
output.append("#    bridge-access 120")
output.append("")
output.append("# auto vlan120")
output.append("# iface vlan2000")
output.append("#    vlan-id 2000")
output.append("#    vlan-raw-device bridge")
output.append("#    vrf blue")
output.append("#### Add vni to bridge as well! ")

print "\n".join(output)
