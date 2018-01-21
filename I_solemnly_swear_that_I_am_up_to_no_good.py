#!/usr/bin/env python

import subprocess
import argparse
import json

def run_command(host, command):
    process = subprocess.Popen("ssh " + host + " " + command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()

    if stderr:
        print "Error running command " + command + " on host " + host + ". Error: " + stderr

    else:
        return stdout

def cli_commands():
    parser = argparse.ArgumentParser(description="A simple chaos-monkey like application using Cumulus NetQ")

    parser.add_argument("-b", "--break", choices=["mtu", "evpn", "bgp", "interface", "routerid"],
                        help="What to break?")

    parser.add_argument("-v", "--victims", help="How many hosts to break?", action="strue_true")

    return parser


def get_all_agents():
    agent_json = json.loads(run_command("leaf01", "netq check agents json"))["agents"]

    hosts = []
    for agent in agent_json:
        hosts.append(agent["hostname"])

    return hosts


def break_mtu(num_victims):
    print get_all_agents()

def main():
    cli = cli_commands()
    cli_args = cli.parse_args()

    if cli_args.mtu:
        break_mtu(cli_args.victims)

if __name__ == "__main__":
    main()
