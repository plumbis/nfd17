# Network Field Day 17 Demo
=====================

This is a large scale Cumulus Vx topology, consisting of 8 servers, 128 leafs and 4 128-port chassis spines.

Each chassis is modeled after the Facebook Backpack. Each line card is actually two independent 32-port switches.
Each fabric card is 4 independent 32-port switches.
![Chasis Overview](https://github.com/plumbis/nfd17/blob/master/readme_images/Chassis.png "Chassis Overview")

Each line card switch has 4 individual ethernet connections to each fabric card switch.
![Linecard Close Up](https://github.com/plumbis/nfd17/blob/master/readme_images/Linecard.png "Linecard Close Up")

This creates a total of 12 "switches" per chassis, or 48 total "switches".
The entire inside of the chassis is running eBGP unnumbered.

Each of the 128 leafs is connected to each of the four chassis.
![Clos Topology](https://github.com/plumbis/nfd17/blob/master/readme_images/Clos.png "Clos Topology")

Each leaf uses eBGP unnumbered to all four chassis spine connections.

8 servers have also been deployed, attached to 8 individual VxLAN Tunnel Endpoints (VTEPs).
The VTEPs have been selected so that there one VTEP on each individual linecard "switch".
![VTEP Deployment](https://github.com/plumbis/nfd17/blob/master/readme_images/VTEPs.png "VTEP Deployment")

Cumulus NetQ has been deployed on all 176 switches in the environment, including chassis linecards and chassis fabric modules.
The NetQ Telemetry Server is running on an indpendent server in the out of band management networked. It is named `netq-ts`
