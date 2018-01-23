#!/usr/bin/env python
# pylint: disable=C0103
"""A Cumulus Linux Chaos Monkey built using NetQ.
The idea for this comes from the Netflix Chaos Monkey engine.
https://github.com/Netflix/chaosmonkey

However it's not nearly as powerful as their engine, so it's a tiny money.
A tamarin is a tiny monkey, weighing 200 to 900 grams (1.4 - 2 lbs)
https://en.wikipedia.org/wiki/Tamarin
"""

import subprocess
import argparse
import json
import random


def cli_commands():
    """Build the CLI arguments
    """
    parser = argparse.ArgumentParser(
        description="A simple chaos-monkey like application using Cumulus NetQ")

    parser.add_argument("-b", "--break", choices=["mtu", "evpn", "bgp", "interface"],
                        help="What to break?", required=True, dest="breaking")

    parser.add_argument("-v", "--victims", help="How many hosts to break?",
                        type=int, required=True, dest="num_victims")

    return parser


def run_command(host, command):
    """Run a given command on the given host.

    Keyword Arguments:
    host - the device on which the command will be run
    command - the command string to run
    """
    commands = ['ssh', '-t', host, command]
    command_output = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return command_output.stdout.read()


def get_agents(agent_type):
    """Get a list of hostnames that match a type

    Keyword Arguments:
    agent_type - The agent type we wish to collect. This is a NetQ key field
    """
    agent_json = json.loads(run_command("leaf01", "netq show " +  agent_type + " json"))[agent_type]

    agents = set()

    for agent in agent_json:
        agents.add(agent["hostname"])

    return agents


def get_interfaces(victim):
    """Get a list of a device's interfaces.
    Excludes special interfaces: ["eth0", "lo", "vagrant", "bridge", "mgmt", "swp5"]
    """
    interface_json = json.loads(run_command(
        victim, "netq " + victim + " show interfaces json"))["link"]

    # swp5 is a host facing interface
    exclude_list = ["eth0", "lo", "vagrant", "bridge", "mgmt", "swp5"]

    interface_list = []
    # Exclude loopback and eth0
    for interface in interface_json:
        if interface["interface"] not in exclude_list:
            interface_list.append(interface["interface"])

    return interface_list


def break_mtu(num_victims):
    """Change the MTU on some number of devices. Only a single MTU will be changed.
    The MTU of an interface will be set to 1300.

    Keyword Arguments:
    num_victims - the number of devices to change
    """
    possible_victims = get_agents("agents")
    victim_list = random.sample(possible_victims, num_victims)

    for victim in victim_list:
        interfaces = get_interfaces(victim)
        victim_interface = random.sample(interfaces, 1)[0]

        run_command(str(victim), "sudo ip link set dev " +
                    str(victim_interface).encode("ascii") + " mtu 1300")
        print "victim: " + str(victim) + " -- interface: " + str(victim_interface)

    return victim_list


def break_evpn(num_victims):
    """Break EVPN on some number of devices. EVPN is disabled by either
    disabling the "advertise-all-vni" setting or by
    shutting down a peer in the l2vpn address fmaily. This choice is random

    Keyword Arguments:
    num_victims - The number of devices to change
    """
    victim_list = random.sample(get_agents("evpn"), num_victims)

    for victim in victim_list:

        misconfig_options = ["net del bgp evpn advertise-all-vni",
                             "net del bgp evpn neighbor FABRIC activate "]

        misconfig_line = random.sample(misconfig_options, 1)[0]
        run_command(str(victim), misconfig_line)
        run_command(str(victim), "net commit")

        print "victim: " + str(victim) + " configured: " + misconfig_line

    return victim_list

def break_bgp(num_victims):
    """Break BGP on a number of victims. This is done by randomly picking one of:
    - Flip BGP internal/external
    - Shutdown peer

    Keyword Arguments:
    num_victims - The number of devices to change
    """
    victim_list = random.sample(get_agents("bgp"), num_victims)

    for victim in victim_list:
        try:
            bgp_peers = json.loads(run_command(
                str(victim), "net show bgp ipv4 unicast summary json"))["peers"].keys()
        except Exception as e:
            print "Hey, you found the break_bgp bug " + e
            print "Victim: " + str(victim)
            exit(1)

        choosen_neighbor = random.sample(bgp_peers, 1)[0]
        # "net add bgp neighbor " + choosen_neighbor + " remote-as internal "
        misconfig_options = ["net add bgp neighbor " + choosen_neighbor + " shutdown"]

        misconfig_line = random.sample(misconfig_options, 1)[0]
        run_command(str(victim), misconfig_line)
        run_command(str(victim), "net commit")

        print "victim: " + str(victim) + " configured: " + misconfig_line

    return victim_list


def break_interface(num_victims):
    """ Shut down a random interface on the target host

    Keyword Arguments:
    num_victims - The number of devices to change
    """

    victim_list = random.sample(get_agents("agents"), num_victims)

    for victim in victim_list:
        choosen_interface = random.sample(get_interfaces(victim), 1)[0].encode("ascii")

        run_command(victim, "sudo ifdown " + choosen_interface)

        print "victim: " + str(victim + " shutdown interface: " + str(choosen_interface))


    return victim_list


def main():
    """Make it so
    """
    cli = cli_commands()
    cli_args = cli.parse_args()

    if cli_args.breaking == "mtu":
        victims = break_mtu(cli_args.num_victims)

    if cli_args.breaking == "evpn":
        victims = break_evpn(cli_args.num_victims)

    if cli_args.breaking == "bgp":
        victims = break_bgp(cli_args.num_victims)

    if cli_args.breaking == "interface":
        victims = break_interface(cli_args.num_victims)

    print ""
    print ",".join(victims)
    exit(0)

if __name__ == "__main__":
    main()
