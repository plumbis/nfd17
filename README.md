# Network Field Day 17 Demo

This is a large scale Cumulus Vx topology, consisting of 6 servers, 32 leafs and 4 spines configured in a Clos topology.

![Clos Topology](https://github.com/plumbis/nfd17/blob/master/readme_images/Clos.png "Clos Topology")

Each leaf uses eBGP unnumbered to all four spine connections.

6 servers have also been deployed, attached to 6 individual Leafs.

host01 and host02 are configured to be L2 adjacent via VxLAN.

host03, host04, host05 and host06 are all configured to be members of a Docker Swarm cluster.

Cumulus NetQ has been deployed on all 36 switches in the environment and all 6 hosts.
The NetQ Telemetry Server is running on an indpendent server in the out of band management networked. It is named `netq-ts`
