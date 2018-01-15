# Topology Converter
=====================


## See the [Documentation Section](./documentation) for way more information!



```
                                                                       +---------+
                                                                  +--> | LibVirt |
                    +----------------------+                      |    +---------+
+--------------+    |                      |    +--------------+  |
| Topology.dot +--> |  Topology-Converter  +--> | Vagrantfile  +--+
+--------------+    |                      |    +--------------+  |
                    +----------------------+                      |    +------------+
                                                                  +--> | VirtualBox |
                                                                       +------------+
```

## What is it?
Topology Converter can help you to simulate a custom network topology directly on your laptop or on a dedicated server. This topology can be extremely complete allowing for the capability to simulate hosts as well as network equipment. Cumulus Vx (which is the VM of Cumulus Linux) can be leveraged as real routers and switches would be to interconnect hosts. As long as the device is using Linux and has a vagrant box image available, it should be possible to simulate it here as part of a larger topology.
Topology Converter uses a graphviz topology file to represent the entire topology. Topology Converter will convert this topology file into a Vagrantfile which fully represents the topology. Vagrantfiles are used with the popular simulation tool Vagrant to interconnect VMs. The topology can then be simulated in either Virtualbox or Libvirt (/w KVM) using Vagrant.


## How to Contribute
PRs are actively welcomed.

1. Fork the Project

2. Make your Changes

3. Submit a PR on the **Development Branch**


## New Features in v4.6.5
* Support for Vagrant versions 1.8.6+
* Added enhancements to Helper Scripts to improve DHCP Request Timing
* Added Automatic MGMT_IP Assignment for devices using the -c Workflow
* Added Limited support for booting older 2.5.x versions of Vx.

### Bugfixes:
* N/A

## Changelog:
* v4\.6\.5 2017\_09\_13: Support for Vagrant versions 1.8.6+. Added enhancements to Helper Scripts to improve DHCP Request timing. Added Automatic Management IP Address assignment for all devices when using the "-c" workflow. Added Limited support for booting older 2.5.x versions of Vx.
* v4\.6\.4 2017\_08\_28: Removed Errant reference_topology.dot file. Fixing PXEboot semantics and fetch_udev_file.yml playbook. Fixed DHCP Range issue with the "-c" workflow. Added support for vagrant= on the oob-mgmt-server in oob-mgmt-server /w "-c" workflow. Added support for simid in virtualbox. Fix for Issue #65.
* v4\.6\.3 2017\_06\_28: Added support for new prefixes other than /24 for the "-c" workflow. Fixed Issue #62 and a regression in automatic NCLU support for the vagrant user.
* v4\.6\.2 2017\_06\_22: Added support for Python3. Added support for vagrant_user node attribute. Convert '/' characters to '-' now (for Cisco interface names) FR#51. Fixed AC97 Audio Driver issue (Virtualbox). Fixed the OOB-MGMT switch out of order config (issue #54). Removed reference to debian82 image (issue #52).
* v4\.6\.1 2017\_04\_20: Fixed reboot failures in some configurations, fixed LLDP on ubuntu hosts, Added Docs for CMD CCO, Added MOTD and better defaults for OOB-MGMT-Server, Added host config file check for -c workflows so options are not overwritten, Added versioning for templates.
* v4\.6\.0 2017\_02\_03: Added NCLU Support for Vagrant user, Added a version argument, all references to host, oob-server and oob-mgmt-server have been moved to the yk0/ubuntu-xenial image, two new options for the -c workflow were added (-cco and -cmd) added significant linting and sanity checking for the topology.dot file and device names, fixed a MAC address conversion issue on windows python installs.
* v4\.5\.2 2016\_12\_08: Fixed many aspects of the Auto Mgmt Workflow (-c), Added Selective install of Puppet/Ansible to OOB-MGMT-SERVER Script, Added More Compact DHCP Hosts format, Fixed Errors during software install at turnup, Added Passwordless Sudo and SSH key generation. Added more robust Reboot support for all devices. Added Arg_string printout to Vagrantfile so you can see how topology converter was called. Added the ability to specify custom ansible groups based on device function. Added ONIE DHCP fix for vagrant. Upped Max NIC count in Libvirt to 130
* v4\.5\.1 2016\_10\_14: Added Colored output for easy reading. Removed 2.5.x simulation measures. Updated for Vagrant v1.8.6 and boxes that can specify their own username/password. Added knob to avoid the Udev Remapping Operations for other boxes. Removed dependency on Apply_udev.py; did this to better support COREos and Fedora, cleaner overall solution.
* v4\.5\.0 2016\_09\_10: Added [Create Management Network](documentation/auto_mgmt_network) option, this can automatically add a management network connected to eth0 port of all devices. Also builds a mgmt switch and ubuntu 1604 mgmt server. Added a TOR and SuperSpine function group. Added Group support for Ansible based on functions. Fixed interface driver configuration in host images to use E1000 driver to allow getting link speed to setup bonds. Corrected and enhanced documentation for new features and the "config" attribute.
* v4\.3\.1 2016\_08\_07: Bugfix to fix regression in handling libvirt topologies. 
* v4\.3\.0 2016\_07\_29: Added Initial PXEboot for Libvirt Support. Deprecated ubuntu=true node attribute, it is handled automatically now for images with ubuntu in the name. Modified Functional Defaults to use Ubuntu 14.04 as the host default instead of ubuntu1604 for wider compatability. Fixed Broken Synced Folders flag. Fixed /root/.profile error message output on unsupported platforms. Added Error handling for use of incompatible Ubuntu 1604 images with Libvirt. Updated Example topologies for v4.3.0 supported attributes. Removed Reference Topology. Updated Documentation for Libvirt provider options.
* v4\.2\.0 2016\_06\_29: Improved support for VX 3.0, Improvements to the Apply_udev.py script to support more vagrant boxes used in host settings, Various Bug fixes for issues #7, #9, and other minor issues. Version node attribute support.
* v4\.1\.0 2016\_05\_25: Added Support for VX 3.0, Added support for Version as a node Attribute, added support for pxebooting in virtualbox, added determinisic interface ordering in Vagrantfiles. Added Support for prepending "left_" and "right_" to any passthrough link attribute to specify which side of the link the attribute applies to. Added more realistic licensing support and switchd behavior in 2.5.x branches.
* v4\.0\.5 2016\_05\_05: Fixed UDEV Remap to tie rules to interfaces on the PCI Bus. Fixed Fake Device support. Added check to confirm that future Vagrant interfaces are tied to the PCI bus.
* v4\.0\.4 2016\_05\_01: Added functional defaults and check for node/device existance when parsing edges/links.
* v4\.0\.3 2016\_04\_25: Added link-based passthrough attribute support, disabled zipfile generation-- needs more work, removed use_vagrant_interface_option
* v4\.0\.2 2016\_04\_14: Added UDEV Based Remapping
* v4\.0\.1 2016\_04\_14: Added Extensible Template Handling, Print Arg Support, node-based passthrough attributes
* v4\.0\.0 2016\_04\_11: MAJOR UPDATES... moved to jinja2 templates, pygraphviz library and removal of the definitions file, added multi-device tunnel support via libvirt.
* v3\.4\.4 2016\_03\_31: Added support for MAC handout on any interface, not just a specified MGMT interface.
* v3\.4\.3 2016\_03\_22: Added libvirt interface name support.
* v3\.4\.2 2016\_03\_21: Adding Exception catching for lack of cumulus-vagrant plugin
* v3\.4\.1 2016\_03\_16: Use Seconds from EPOCH as an extenstion to the device name in Vbox.
* v3\.4 2016\_03\_15 Use Seconds from EPOCH as an extenstion to the unique net number to add some limited network isolation for the vbox use case. Also fixed zipfile generation to include all needed files.
* v3\.3 2016\_03\_09 All Hosts are now remapped by default. Removed Debian_Host_Remaps as a required setting. Added simple true/false check for if the host is Ubuntu. moved "use_vagrant_interface" option into the definitions file; this option creates and uses Vagrant interface instead of the Default 1st interface (usually eth0)
* v3\.2 2016\_03\_08 Significant changes to surrounding packages i.e. rename_eth_swp script. Minor changes to topology converter in the way remap files are generated and hosts run the remap at reboot via rc.local.
* v3\.1 2016\_03\_03 Added Hidden "use_vagrant_interface" option to allow making use of the Vagrant interface optional. Added CLI for Debugging mode.
* v3\.0 2016\_02\_23 Added support for Interface Remapping without reboots on Vx and Hosts (to save time). Moved any remaining topology-specific settings into the definitions files. So topology_converter is truly agnostic and should not need to be modified. Also created an option to disable the vagrant synced folder to further speed boot. Hardened Interface remapping on hosts to work on reboots; and not to pause and wait for networking at reboot. Created remap_eth_swp script that is both hardened and works for both Vx nodes and generic hosts.
* v2\.8 2016\_02\_05 Added support for .def files along with definitions.py so seperate files can be stored in the same directory. Also added support for adding topology files to shareable zipfile.
* v2\.7 2016\_01\_27 Setup cleanup of remap_files added zip file for generated files
* v2\.6 2016\_01\_26 Moved provider and switch/server mem settings from topology_converter to definitions.py
* v2\.5 2016\_01\_25 Added libvirt support :) and added support for fake devices!
* v2\.2 2016\_01\_19 Added Support for optional switch interface configuration
* v2\.1 2016\_01\_15 Added Support Boot Ordering -- 1st device --> 2nd device --> servers --> switches
* v2\.0 2016\_01\_07 Added Support for MAC handout, empty ansible playbook (used to generate ansible inventory), [EMPTY] connections for more accurate automation simulation, 
"vagrant" interface remapping for hosts and switches, warnings for interface reuse, added optional support for OOB switch.
* v1\.0 2015\_10\_19 Initial version constructed

## To Do List
* Enhanced PXEBOOT Libvirt Support -- Blank OS value should be allowed
* Null Audio Driver
* os.path.abspath("./helper_scripts")
* Investigate Ruby Vagrantfile Segmentation (based on yaml)
