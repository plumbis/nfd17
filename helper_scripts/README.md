# Helper Scripts
These scripts are useful additions to Topology Converter. Only the "apply_udev.py" script is required.

**Note that topology converter requires that python be installed on whatever system is to be simulated so that interface remapping can be performed.** This is especially important for devices running Fedora which does not ship with python installed by default. 

The [extra_server_config.sh] and [extra_switch_config.sh] scripts are used to pre-configure certain devices with configuration before first-login by a user. To use one of these scripts (or any other custom script) specify the config="[location of script]" option. in the node definition of the topology file (many of the included examples make use of these pre-configuration scripts.

See the [Documentation](../documentation/) glossary for more information on Interface Remapping.
