#!/usr/bin/env python
# pylint: disable=C0103
"""A Cumulus Linux Chaos Monkey built using NetQ
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

    parser.add_argument("-b", "--break", choices=["mtu", "evpn", "bgp", "interface", "routerid"],
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
    Excludes special interfaces: ["eth0", "lo", "vagrant", "bridge", "mgmt"]
    """
    interface_json = json.loads(run_command(
        victim, "netq " + victim + " show interfaces json"))["link"]

    exclude_list = ["eth0", "lo", "vagrant", "bridge", "mgmt"]
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

    return True


def break_evpn(num_victims):
    """Break EVPN on some number of devices. EVPN is disabled by either
    disabling the "advertise-all-vni" setting or by
    shutting down a peer in the l2vpn address fmaily. This choice is random

    Keyword Arguments:
    num_victims - The number of devices to change
    """
    victim_list = random.sample(get_agents("evpn"), num_victims)

    for victim in victim_list:
        evpn_peers = json.loads(run_command(
            str(victim), "net show bgp evpn summary json"))["peers"].keys()

        neighbor = random.sample(evpn_peers, 1)[0]
        misconfig_options = ["net del bgp evpn advertise-all-vni",
                             "net del bgp evpn neighbor " + neighbor + " activate "]

        misconfig_line = random.sample(misconfig_options, 1)[0]
        run_command(str(victim), misconfig_line)
        run_command(str(victim), "net commit")

        print "victim: " + str(victim) + " configured: " + misconfig_line

    return True

def break_bgp(num_victims):
    """Break BGP on a number of victims. This is done by randomly picking one of:
    - Flip BGP internal/external
    - Shutdown peer

    Keyword Arguments:
    num_victims - The number of devices to change
    """
    victim_list = random.sample(get_agents("bgp"), num_victims)

    for victim in victim_list:
        bgp_peers = json.loads(run_command(
            str(victim), "net show bgp ipv4 unicast summary json"))["peers"].keys()

        choosen_neighbor = random.sample(bgp_peers, 1)[0]
        misconfig_options = ["net add bgp neighbor " + choosen_neighbor + " shutdown",
                             "net add bgp neighbor " + choosen_neighbor + " remote-as internal "]

        misconfig_line = random.sample(misconfig_options, 1)[0]
        run_command(str(victim), misconfig_line)
        run_command(str(victim), "net commit")

        print "victim: " + str(victim) + " configured: " + misconfig_line

    return True

def main():
    """Make it so
    """
    cli = cli_commands()
    cli_args = cli.parse_args()

    if cli_args.breaking == "mtu":
        break_mtu(cli_args.num_victims)

    if cli_args.breaking == "evpn":
        break_evpn(cli_args.num_victims)

    if cli_args.breaking == "bgp":
        break_bgp(cli_args.num_victims)

    exit(0)

if __name__ == "__main__":
    main()
