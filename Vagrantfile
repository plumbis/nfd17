# Created by Topology-Converter v4.6.5
#    Template Revision: v4.6.5
#    https://github.com/cumulusnetworks/topology_converter
#    using topology data from: topology.dot
#    built with the following args: topology_converter.py -p libvirt -s 8000 -g 2000 -cmd topology.dot
#
#    NOTE: in order to use this Vagrantfile you will need:
#       -Vagrant(v1.8.6+) installed: http://www.vagrantup.com/downloads
#       -the "helper_scripts" directory that comes packaged with topology-converter.py
#        -Libvirt Installed -- guide to come
#       -Vagrant-Libvirt Plugin installed: $ vagrant plugin install vagrant-libvirt
#       -Boxes which have been mutated to support Libvirt -- see guide below:
#            https://community.cumulusnetworks.com/cumulus/topics/converting-cumulus-vx-virtualbox-vagrant-box-gt-libvirt-vagrant-box
#       -Start with \"vagrant up --provider=libvirt --no-parallel\n")

#Set the default provider to libvirt in the case they forget --provider=libvirt or if someone destroys a machine it reverts to virtualbox
ENV['VAGRANT_DEFAULT_PROVIDER'] = 'libvirt'

Vagrant.require_version ">= 1.8.6"

# Check required plugins
REQUIRED_PLUGINS_LIBVIRT = %w(vagrant-libvirt)
exit unless REQUIRED_PLUGINS_LIBVIRT.all? do |plugin|
  Vagrant.has_plugin?(plugin) || (
    puts "The #{plugin} plugin is required. Please install it with:"
    puts "$ vagrant plugin install #{plugin}"
    false
  )
end


$script = <<-SCRIPT
if grep -q -i 'cumulus' /etc/lsb-release &> /dev/null; then
    echo "### RUNNING CUMULUS EXTRA CONFIG ###"
    source /etc/lsb-release
    if [[ $DISTRIB_RELEASE =~ ^2.* ]]; then
        echo "  INFO: Detected a 2.5.x Based Release"

        echo "  adding fake cl-acltool..."
        echo -e "#!/bin/bash\nexit 0" > /usr/bin/cl-acltool
        chmod 755 /usr/bin/cl-acltool

        echo "  adding fake cl-license..."
        echo -e "#!/bin/bash\nexit 0" > /usr/bin/cl-license
        chmod 755 /usr/bin/cl-license

        echo "  Disabling default remap on Cumulus VX..."
        mv -v /etc/init.d/rename_eth_swp /etc/init.d/rename_eth_swp.backup

        echo "### Rebooting to Apply Remap..."

    elif [[ $DISTRIB_RELEASE =~ ^3.* ]]; then
        echo "  INFO: Detected a 3.x Based Release"
        echo "### Disabling default remap on Cumulus VX..."
        mv -v /etc/hw_init.d/S10rename_eth_swp.sh /etc/S10rename_eth_swp.sh.backup &> /dev/null
        echo "### Disabling ZTP service..."
        systemctl stop ztp.service
        ztp -d 2>&1
        echo "### Resetting ZTP to work next boot..."
        ztp -R 2>&1
        echo "  INFO: Detected Cumulus Linux v$DISTRIB_RELEASE Release"
        if [[ $DISTRIB_RELEASE =~ ^3.[1-9].* ]]; then
            echo "### Fixing ONIE DHCP to avoid Vagrant Interface ###"
            echo "     Note: Installing from ONIE will undo these changes."
            mkdir /tmp/foo
            mount LABEL=ONIE-BOOT /tmp/foo
            sed -i 's/eth0/eth1/g' /tmp/foo/grub/grub.cfg
            sed -i 's/eth0/eth1/g' /tmp/foo/onie/grub/grub-extra.cfg
            umount /tmp/foo
        fi
        if [[ $DISTRIB_RELEASE =~ ^3.[2-9].* ]]; then
            if [[ $(grep "vagrant" /etc/netd.conf | wc -l ) == 0 ]]; then
                echo "### Giving Vagrant User Ability to Run NCLU Commands ###"
                sed -i 's/users_with_edit = root, cumulus/users_with_edit = root, cumulus, vagrant/g' /etc/netd.conf
                sed -i 's/users_with_show = root, cumulus/users_with_show = root, cumulus, vagrant/g' /etc/netd.conf
            fi
        fi

    fi
fi
echo "### DONE ###"
echo "### Rebooting Device to Apply Remap..."
nohup bash -c 'sleep 10; shutdown now -r "Rebooting to Remap Interfaces"' &
SCRIPT

Vagrant.configure("2") do |config|

  config.vm.provider :libvirt do |domain|
    # increase nic adapter count to be greater than 8 for all VMs.
    domain.management_network_address = "10.255.1.0/24"
    domain.management_network_name = "wbr1"
    domain.nic_adapter_count = 130
  end




  ##### DEFINE VM for oob-mgmt-server #####
  config.vm.define "oob-mgmt-server" do |device|

    device.vm.hostname = "oob-mgmt-server"

    device.vm.box = "yk0/ubuntu-xenial"

    device.vm.provider :libvirt do |v|
      v.memory = 1024
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth1 --> oob-mgmt-switch:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:75",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8059',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10059',
            :libvirt__iface_name => 'eth1',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    # Shorten Boot Process - Applies to Ubuntu Only - remove \"Wait for Network\"
    device.vm.provision :shell , inline: "sed -i 's/sleep [0-9]*/sleep 1/' /etc/init/failsafe.conf 2>/dev/null || true"

    #Copy over DHCP files and MGMT Network Files
    device.vm.provision "file", source: "./helper_scripts/auto_mgmt_network/dhcpd.conf", destination: "~/dhcpd.conf"
    device.vm.provision "file", source: "./helper_scripts/auto_mgmt_network/dhcpd.hosts", destination: "~/dhcpd.hosts"
    device.vm.provision "file", source: "./helper_scripts/auto_mgmt_network/hosts", destination: "~/hosts"
    device.vm.provision "file", source: "./helper_scripts/auto_mgmt_network/ansible_hostfile", destination: "~/ansible_hostfile"
    device.vm.provision "file", source: "./helper_scripts/auto_mgmt_network/ztp_oob.sh", destination: "~/ztp_oob.sh"

    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/auto_mgmt_network/OOB_Server_Config_auto_mgmt.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:75 --> eth1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:75", NAME="eth1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for oob-mgmt-switch #####
  config.vm.define "oob-mgmt-switch" do |device|

    device.vm.hostname = "oob-mgmt-switch"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.0"

    device.vm.provider :libvirt do |v|
      v.memory = 256
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for swp1 --> oob-mgmt-server:eth1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:76",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10059',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8059',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> leaf01:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:21",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8145',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10145',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> leaf02:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:33",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8154',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10154',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> leaf03:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:63",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8178',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10178',
            :libvirt__iface_name => 'swp4',
            auto_config: false
      # link for swp5 --> leaf04:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:f3",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8122',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10122',
            :libvirt__iface_name => 'swp5',
            auto_config: false
      # link for swp6 --> leaf05:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:83",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8066',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10066',
            :libvirt__iface_name => 'swp6',
            auto_config: false
      # link for swp7 --> leaf06:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:5f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8048',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10048',
            :libvirt__iface_name => 'swp7',
            auto_config: false
      # link for swp8 --> leaf07:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:2b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8150',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10150',
            :libvirt__iface_name => 'swp8',
            auto_config: false
      # link for swp9 --> leaf08:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:69",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8053',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10053',
            :libvirt__iface_name => 'swp9',
            auto_config: false
      # link for swp10 --> leaf09:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:fd",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8127',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10127',
            :libvirt__iface_name => 'swp10',
            auto_config: false
      # link for swp11 --> leaf10:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:c5",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8099',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10099',
            :libvirt__iface_name => 'swp11',
            auto_config: false
      # link for swp12 --> leaf11:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:51",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8169',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10169',
            :libvirt__iface_name => 'swp12',
            auto_config: false
      # link for swp13 --> leaf12:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:6f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8056',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10056',
            :libvirt__iface_name => 'swp13',
            auto_config: false
      # link for swp14 --> leaf13:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:f1",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8121',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10121',
            :libvirt__iface_name => 'swp14',
            auto_config: false
      # link for swp15 --> leaf14:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:e5",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8115',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10115',
            :libvirt__iface_name => 'swp15',
            auto_config: false
      # link for swp16 --> leaf15:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:41",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8161',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10161',
            :libvirt__iface_name => 'swp16',
            auto_config: false
      # link for swp17 --> leaf16:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:4f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8040',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10040',
            :libvirt__iface_name => 'swp17',
            auto_config: false
      # link for swp18 --> leaf17:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:a3",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8082',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10082',
            :libvirt__iface_name => 'swp18',
            auto_config: false
      # link for swp19 --> leaf18:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:a1",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8081',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10081',
            :libvirt__iface_name => 'swp19',
            auto_config: false
      # link for swp20 --> leaf19:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:f7",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8124',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10124',
            :libvirt__iface_name => 'swp20',
            auto_config: false
      # link for swp21 --> leaf20:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:17",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8140',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10140',
            :libvirt__iface_name => 'swp21',
            auto_config: false
      # link for swp22 --> leaf21:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:03",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8002',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10002',
            :libvirt__iface_name => 'swp22',
            auto_config: false
      # link for swp23 --> leaf22:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:27",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8020',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10020',
            :libvirt__iface_name => 'swp23',
            auto_config: false
      # link for swp24 --> leaf23:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:0f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8008',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10008',
            :libvirt__iface_name => 'swp24',
            auto_config: false
      # link for swp25 --> leaf24:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:ef",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8120',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10120',
            :libvirt__iface_name => 'swp25',
            auto_config: false
      # link for swp26 --> leaf25:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:23",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8146',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10146',
            :libvirt__iface_name => 'swp26',
            auto_config: false
      # link for swp27 --> leaf26:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:25",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8147',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10147',
            :libvirt__iface_name => 'swp27',
            auto_config: false
      # link for swp28 --> leaf27:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:ed",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8119',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10119',
            :libvirt__iface_name => 'swp28',
            auto_config: false
      # link for swp29 --> leaf28:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:61",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8177',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10177',
            :libvirt__iface_name => 'swp29',
            auto_config: false
      # link for swp30 --> leaf29:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:2b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8022',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10022',
            :libvirt__iface_name => 'swp30',
            auto_config: false
      # link for swp31 --> leaf30:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:89",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8069',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10069',
            :libvirt__iface_name => 'swp31',
            auto_config: false
      # link for swp32 --> leaf31:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:af",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8088',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10088',
            :libvirt__iface_name => 'swp32',
            auto_config: false
      # link for swp33 --> leaf32:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:9d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8079',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10079',
            :libvirt__iface_name => 'swp33',
            auto_config: false
      # link for swp34 --> host01:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:5d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8047',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10047',
            :libvirt__iface_name => 'swp34',
            auto_config: false
      # link for swp35 --> host02:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:0d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8007',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10007',
            :libvirt__iface_name => 'swp35',
            auto_config: false
      # link for swp36 --> host03:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:8b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8070',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10070',
            :libvirt__iface_name => 'swp36',
            auto_config: false
      # link for swp37 --> host04:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:99",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8077',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10077',
            :libvirt__iface_name => 'swp37',
            auto_config: false
      # link for swp38 --> host05:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:2d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8023',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10023',
            :libvirt__iface_name => 'swp38',
            auto_config: false
      # link for swp39 --> host06:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:09",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8005',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10005',
            :libvirt__iface_name => 'swp39',
            auto_config: false
      # link for swp40 --> spine01:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:55",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8043',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10043',
            :libvirt__iface_name => 'swp40',
            auto_config: false
      # link for swp41 --> spine02:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:4b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8038',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10038',
            :libvirt__iface_name => 'swp41',
            auto_config: false
      # link for swp42 --> spine03:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:f5",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8123',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10123',
            :libvirt__iface_name => 'swp42',
            auto_config: false
      # link for swp43 --> spine04:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:2f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8152',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10152',
            :libvirt__iface_name => 'swp43',
            auto_config: false
      # link for swp44 --> netq-ts:eth0
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:73",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8058',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10058',
            :libvirt__iface_name => 'swp44',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"

# Transfer Bridge File
      device.vm.provision "file", source: "./helper_scripts/auto_mgmt_network/bridge-untagged", destination: "~/bridge-untagged"

    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/config_oob_switch.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:76 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:76", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:21 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:21", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:33 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:33", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:63 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:63", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:f3 --> swp5"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:f3", NAME="swp5", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:83 --> swp6"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:83", NAME="swp6", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:5f --> swp7"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:5f", NAME="swp7", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:2b --> swp8"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:2b", NAME="swp8", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:69 --> swp9"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:69", NAME="swp9", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:fd --> swp10"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:fd", NAME="swp10", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:c5 --> swp11"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:c5", NAME="swp11", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:51 --> swp12"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:51", NAME="swp12", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:6f --> swp13"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:6f", NAME="swp13", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:f1 --> swp14"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:f1", NAME="swp14", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:e5 --> swp15"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:e5", NAME="swp15", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:41 --> swp16"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:41", NAME="swp16", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:4f --> swp17"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:4f", NAME="swp17", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:a3 --> swp18"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:a3", NAME="swp18", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:a1 --> swp19"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:a1", NAME="swp19", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:f7 --> swp20"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:f7", NAME="swp20", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:17 --> swp21"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:17", NAME="swp21", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:03 --> swp22"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:03", NAME="swp22", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:27 --> swp23"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:27", NAME="swp23", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:0f --> swp24"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:0f", NAME="swp24", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:ef --> swp25"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:ef", NAME="swp25", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:23 --> swp26"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:23", NAME="swp26", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:25 --> swp27"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:25", NAME="swp27", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:ed --> swp28"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:ed", NAME="swp28", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:61 --> swp29"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:61", NAME="swp29", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:2b --> swp30"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:2b", NAME="swp30", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:89 --> swp31"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:89", NAME="swp31", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:af --> swp32"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:af", NAME="swp32", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:9d --> swp33"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:9d", NAME="swp33", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:5d --> swp34"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:5d", NAME="swp34", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:0d --> swp35"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:0d", NAME="swp35", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:8b --> swp36"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:8b", NAME="swp36", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:99 --> swp37"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:99", NAME="swp37", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:2d --> swp38"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:2d", NAME="swp38", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:09 --> swp39"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:09", NAME="swp39", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:55 --> swp40"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:55", NAME="swp40", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:4b --> swp41"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:4b", NAME="swp41", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:f5 --> swp42"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:f5", NAME="swp42", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:2f --> swp43"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:2f", NAME="swp43", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:73 --> swp44"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:73", NAME="swp44", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for spine02 #####
  config.vm.define "spine02" do |device|

    device.vm.hostname = "spine02"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp41
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:4c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10038',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8038',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> leaf01:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:44",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10034',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8034',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> leaf02:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:b6",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10091',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8091',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> leaf03:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:4c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10166',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8166',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> leaf04:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:9c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10078',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8078',
            :libvirt__iface_name => 'swp4',
            auto_config: false
      # link for swp5 --> leaf05:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:2a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10021',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8021',
            :libvirt__iface_name => 'swp5',
            auto_config: false
      # link for swp6 --> leaf06:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:12",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10009',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8009',
            :libvirt__iface_name => 'swp6',
            auto_config: false
      # link for swp7 --> leaf07:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:1a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10141',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8141',
            :libvirt__iface_name => 'swp7',
            auto_config: false
      # link for swp8 --> leaf08:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:02",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10129',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8129',
            :libvirt__iface_name => 'swp8',
            auto_config: false
      # link for swp9 --> leaf09:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:3a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10157',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8157',
            :libvirt__iface_name => 'swp9',
            auto_config: false
      # link for swp10 --> leaf10:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:54",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10042',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8042',
            :libvirt__iface_name => 'swp10',
            auto_config: false
      # link for swp11 --> leaf11:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:0c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10006',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8006',
            :libvirt__iface_name => 'swp11',
            auto_config: false
      # link for swp12 --> leaf12:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:de",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10111',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8111',
            :libvirt__iface_name => 'swp12',
            auto_config: false
      # link for swp13 --> leaf13:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:14",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10138',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8138',
            :libvirt__iface_name => 'swp13',
            auto_config: false
      # link for swp14 --> leaf14:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:40",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10160',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8160',
            :libvirt__iface_name => 'swp14',
            auto_config: false
      # link for swp15 --> leaf15:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:1c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10014',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8014',
            :libvirt__iface_name => 'swp15',
            auto_config: false
      # link for swp16 --> leaf16:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:34",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10026',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8026',
            :libvirt__iface_name => 'swp16',
            auto_config: false
      # link for swp17 --> leaf17:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:ae",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10087',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8087',
            :libvirt__iface_name => 'swp17',
            auto_config: false
      # link for swp18 --> leaf18:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:58",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10172',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8172',
            :libvirt__iface_name => 'swp18',
            auto_config: false
      # link for swp19 --> leaf19:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:46",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10035',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8035',
            :libvirt__iface_name => 'swp19',
            auto_config: false
      # link for swp20 --> leaf20:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:20",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10144',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8144',
            :libvirt__iface_name => 'swp20',
            auto_config: false
      # link for swp21 --> leaf21:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:6e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10055',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8055',
            :libvirt__iface_name => 'swp21',
            auto_config: false
      # link for swp22 --> leaf22:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:64",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10050',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8050',
            :libvirt__iface_name => 'swp22',
            auto_config: false
      # link for swp23 --> leaf23:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:b8",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10092',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8092',
            :libvirt__iface_name => 'swp23',
            auto_config: false
      # link for swp24 --> leaf24:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:ce",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10103',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8103',
            :libvirt__iface_name => 'swp24',
            auto_config: false
      # link for swp25 --> leaf25:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:2e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10151',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8151',
            :libvirt__iface_name => 'swp25',
            auto_config: false
      # link for swp26 --> leaf26:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:5c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10174',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8174',
            :libvirt__iface_name => 'swp26',
            auto_config: false
      # link for swp27 --> leaf27:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:38",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10028',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8028',
            :libvirt__iface_name => 'swp27',
            auto_config: false
      # link for swp28 --> leaf28:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:7e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10063',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8063',
            :libvirt__iface_name => 'swp28',
            auto_config: false
      # link for swp29 --> leaf29:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:36",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10155',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8155',
            :libvirt__iface_name => 'swp29',
            auto_config: false
      # link for swp30 --> leaf30:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:78",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10060',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8060',
            :libvirt__iface_name => 'swp30',
            auto_config: false
      # link for swp31 --> leaf31:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:86",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10067',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8067',
            :libvirt__iface_name => 'swp31',
            auto_config: false
      # link for swp32 --> leaf32:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:fc",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10126',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8126',
            :libvirt__iface_name => 'swp32',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:4c --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:4c", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:44 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:44", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:b6 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:b6", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:4c --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:4c", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:9c --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:9c", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:2a --> swp5"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:2a", NAME="swp5", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:12 --> swp6"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:12", NAME="swp6", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:1a --> swp7"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:1a", NAME="swp7", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:02 --> swp8"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:02", NAME="swp8", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:3a --> swp9"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:3a", NAME="swp9", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:54 --> swp10"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:54", NAME="swp10", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:0c --> swp11"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:0c", NAME="swp11", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:de --> swp12"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:de", NAME="swp12", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:14 --> swp13"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:14", NAME="swp13", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:40 --> swp14"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:40", NAME="swp14", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:1c --> swp15"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:1c", NAME="swp15", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:34 --> swp16"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:34", NAME="swp16", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:ae --> swp17"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:ae", NAME="swp17", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:58 --> swp18"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:58", NAME="swp18", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:46 --> swp19"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:46", NAME="swp19", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:20 --> swp20"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:20", NAME="swp20", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:6e --> swp21"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:6e", NAME="swp21", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:64 --> swp22"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:64", NAME="swp22", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:b8 --> swp23"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:b8", NAME="swp23", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:ce --> swp24"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:ce", NAME="swp24", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:2e --> swp25"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:2e", NAME="swp25", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:5c --> swp26"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:5c", NAME="swp26", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:38 --> swp27"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:38", NAME="swp27", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:7e --> swp28"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:7e", NAME="swp28", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:36 --> swp29"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:36", NAME="swp29", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:78 --> swp30"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:78", NAME="swp30", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:86 --> swp31"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:86", NAME="swp31", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:fc --> swp32"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:fc", NAME="swp32", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for spine03 #####
  config.vm.define "spine03" do |device|

    device.vm.hostname = "spine03"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp42
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:f6",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10123',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8123',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> leaf01:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:3e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10031',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8031',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> leaf02:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:ac",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10086',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8086',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> leaf03:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:06",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10131',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8131',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> leaf04:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:6c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10054',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8054',
            :libvirt__iface_name => 'swp4',
            auto_config: false
      # link for swp5 --> leaf05:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:5a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10173',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8173',
            :libvirt__iface_name => 'swp5',
            auto_config: false
      # link for swp6 --> leaf06:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:0a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10133',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8133',
            :libvirt__iface_name => 'swp6',
            auto_config: false
      # link for swp7 --> leaf07:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:1a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10013',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8013',
            :libvirt__iface_name => 'swp7',
            auto_config: false
      # link for swp8 --> leaf08:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:88",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10068',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8068',
            :libvirt__iface_name => 'swp8',
            auto_config: false
      # link for swp9 --> leaf09:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:06",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10003',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8003',
            :libvirt__iface_name => 'swp9',
            auto_config: false
      # link for swp10 --> leaf10:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:a8",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10084',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8084',
            :libvirt__iface_name => 'swp10',
            auto_config: false
      # link for swp11 --> leaf11:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:ea",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10117',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8117',
            :libvirt__iface_name => 'swp11',
            auto_config: false
      # link for swp12 --> leaf12:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:fa",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10125',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8125',
            :libvirt__iface_name => 'swp12',
            auto_config: false
      # link for swp13 --> leaf13:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:3c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10030',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8030',
            :libvirt__iface_name => 'swp13',
            auto_config: false
      # link for swp14 --> leaf14:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:66",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10051',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8051',
            :libvirt__iface_name => 'swp14',
            auto_config: false
      # link for swp15 --> leaf15:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:14",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10010',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8010',
            :libvirt__iface_name => 'swp15',
            auto_config: false
      # link for swp16 --> leaf16:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:4a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10165',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8165',
            :libvirt__iface_name => 'swp16',
            auto_config: false
      # link for swp17 --> leaf17:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:1c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10142',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8142',
            :libvirt__iface_name => 'swp17',
            auto_config: false
      # link for swp18 --> leaf18:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:d0",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10104',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8104',
            :libvirt__iface_name => 'swp18',
            auto_config: false
      # link for swp19 --> leaf19:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:04",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10130',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8130',
            :libvirt__iface_name => 'swp19',
            auto_config: false
      # link for swp20 --> leaf20:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:2a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10149',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8149',
            :libvirt__iface_name => 'swp20',
            auto_config: false
      # link for swp21 --> leaf21:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:4e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10039',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8039',
            :libvirt__iface_name => 'swp21',
            auto_config: false
      # link for swp22 --> leaf22:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:62",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10049',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8049',
            :libvirt__iface_name => 'swp22',
            auto_config: false
      # link for swp23 --> leaf23:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:4e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10167',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8167',
            :libvirt__iface_name => 'swp23',
            auto_config: false
      # link for swp24 --> leaf24:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:50",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10168',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8168',
            :libvirt__iface_name => 'swp24',
            auto_config: false
      # link for swp25 --> leaf25:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:40",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10032',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8032',
            :libvirt__iface_name => 'swp25',
            auto_config: false
      # link for swp26 --> leaf26:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:22",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10017',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8017',
            :libvirt__iface_name => 'swp26',
            auto_config: false
      # link for swp27 --> leaf27:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:72",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10057',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8057',
            :libvirt__iface_name => 'swp27',
            auto_config: false
      # link for swp28 --> leaf28:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:be",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10095',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8095',
            :libvirt__iface_name => 'swp28',
            auto_config: false
      # link for swp29 --> leaf29:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:d6",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10107',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8107',
            :libvirt__iface_name => 'swp29',
            auto_config: false
      # link for swp30 --> leaf30:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:08",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10132',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8132',
            :libvirt__iface_name => 'swp30',
            auto_config: false
      # link for swp31 --> leaf31:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:8e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10071',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8071',
            :libvirt__iface_name => 'swp31',
            auto_config: false
      # link for swp32 --> leaf32:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:16",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10011',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8011',
            :libvirt__iface_name => 'swp32',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:f6 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:f6", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:3e --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:3e", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:ac --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:ac", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:06 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:06", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:6c --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:6c", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:5a --> swp5"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:5a", NAME="swp5", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:0a --> swp6"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:0a", NAME="swp6", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:1a --> swp7"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:1a", NAME="swp7", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:88 --> swp8"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:88", NAME="swp8", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:06 --> swp9"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:06", NAME="swp9", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:a8 --> swp10"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:a8", NAME="swp10", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:ea --> swp11"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:ea", NAME="swp11", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:fa --> swp12"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:fa", NAME="swp12", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:3c --> swp13"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:3c", NAME="swp13", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:66 --> swp14"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:66", NAME="swp14", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:14 --> swp15"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:14", NAME="swp15", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:4a --> swp16"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:4a", NAME="swp16", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:1c --> swp17"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:1c", NAME="swp17", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:d0 --> swp18"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:d0", NAME="swp18", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:04 --> swp19"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:04", NAME="swp19", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:2a --> swp20"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:2a", NAME="swp20", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:4e --> swp21"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:4e", NAME="swp21", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:62 --> swp22"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:62", NAME="swp22", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:4e --> swp23"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:4e", NAME="swp23", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:50 --> swp24"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:50", NAME="swp24", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:40 --> swp25"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:40", NAME="swp25", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:22 --> swp26"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:22", NAME="swp26", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:72 --> swp27"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:72", NAME="swp27", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:be --> swp28"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:be", NAME="swp28", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:d6 --> swp29"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:d6", NAME="swp29", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:08 --> swp30"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:08", NAME="swp30", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:8e --> swp31"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:8e", NAME="swp31", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:16 --> swp32"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:16", NAME="swp32", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for spine01 #####
  config.vm.define "spine01" do |device|

    device.vm.hostname = "spine01"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp40
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:56",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10043',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8043',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> leaf01:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:e0",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10112',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8112',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> leaf02:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:d4",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10106',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8106',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> leaf03:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:b2",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10089',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8089',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> leaf04:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:52",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10041',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8041',
            :libvirt__iface_name => 'swp4',
            auto_config: false
      # link for swp5 --> leaf05:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:5a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10045',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8045',
            :libvirt__iface_name => 'swp5',
            auto_config: false
      # link for swp6 --> leaf06:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:5e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10175',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8175',
            :libvirt__iface_name => 'swp6',
            auto_config: false
      # link for swp7 --> leaf07:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:a0",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10080',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8080',
            :libvirt__iface_name => 'swp7',
            auto_config: false
      # link for swp8 --> leaf08:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:48",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10164',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8164',
            :libvirt__iface_name => 'swp8',
            auto_config: false
      # link for swp9 --> leaf09:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:c2",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10097',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8097',
            :libvirt__iface_name => 'swp9',
            auto_config: false
      # link for swp10 --> leaf10:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:46",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10163',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8163',
            :libvirt__iface_name => 'swp10',
            auto_config: false
      # link for swp11 --> leaf11:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:92",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10073',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8073',
            :libvirt__iface_name => 'swp11',
            auto_config: false
      # link for swp12 --> leaf12:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:60",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10176',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8176',
            :libvirt__iface_name => 'swp12',
            auto_config: false
      # link for swp13 --> leaf13:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:c4",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10098',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8098',
            :libvirt__iface_name => 'swp13',
            auto_config: false
      # link for swp14 --> leaf14:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:68",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10052',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8052',
            :libvirt__iface_name => 'swp14',
            auto_config: false
      # link for swp15 --> leaf15:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:82",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10065',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8065',
            :libvirt__iface_name => 'swp15',
            auto_config: false
      # link for swp16 --> leaf16:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:e4",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10114',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8114',
            :libvirt__iface_name => 'swp16',
            auto_config: false
      # link for swp17 --> leaf17:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:ec",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10118',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8118',
            :libvirt__iface_name => 'swp17',
            auto_config: false
      # link for swp18 --> leaf18:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:7c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10062',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8062',
            :libvirt__iface_name => 'swp18',
            auto_config: false
      # link for swp19 --> leaf19:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:36",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10027',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8027',
            :libvirt__iface_name => 'swp19',
            auto_config: false
      # link for swp20 --> leaf20:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:5c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10046',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8046',
            :libvirt__iface_name => 'swp20',
            auto_config: false
      # link for swp21 --> leaf21:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:3e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10159',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8159',
            :libvirt__iface_name => 'swp21',
            auto_config: false
      # link for swp22 --> leaf22:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:00",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10128',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8128',
            :libvirt__iface_name => 'swp22',
            auto_config: false
      # link for swp23 --> leaf23:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:56",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10171',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8171',
            :libvirt__iface_name => 'swp23',
            auto_config: false
      # link for swp24 --> leaf24:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:1e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10015',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8015',
            :libvirt__iface_name => 'swp24',
            auto_config: false
      # link for swp25 --> leaf25:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:02",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10001',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8001',
            :libvirt__iface_name => 'swp25',
            auto_config: false
      # link for swp26 --> leaf26:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:bc",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10094',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8094',
            :libvirt__iface_name => 'swp26',
            auto_config: false
      # link for swp27 --> leaf27:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:d8",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10108',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8108',
            :libvirt__iface_name => 'swp27',
            auto_config: false
      # link for swp28 --> leaf28:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:1e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10143',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8143',
            :libvirt__iface_name => 'swp28',
            auto_config: false
      # link for swp29 --> leaf29:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:42",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10033',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8033',
            :libvirt__iface_name => 'swp29',
            auto_config: false
      # link for swp30 --> leaf30:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:a6",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10083',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8083',
            :libvirt__iface_name => 'swp30',
            auto_config: false
      # link for swp31 --> leaf31:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:c8",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10100',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8100',
            :libvirt__iface_name => 'swp31',
            auto_config: false
      # link for swp32 --> leaf32:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:16",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10139',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8139',
            :libvirt__iface_name => 'swp32',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:56 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:56", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:e0 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:e0", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:d4 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:d4", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:b2 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:b2", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:52 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:52", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:5a --> swp5"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:5a", NAME="swp5", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:5e --> swp6"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:5e", NAME="swp6", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:a0 --> swp7"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:a0", NAME="swp7", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:48 --> swp8"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:48", NAME="swp8", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:c2 --> swp9"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:c2", NAME="swp9", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:46 --> swp10"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:46", NAME="swp10", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:92 --> swp11"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:92", NAME="swp11", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:60 --> swp12"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:60", NAME="swp12", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:c4 --> swp13"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:c4", NAME="swp13", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:68 --> swp14"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:68", NAME="swp14", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:82 --> swp15"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:82", NAME="swp15", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:e4 --> swp16"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:e4", NAME="swp16", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:ec --> swp17"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:ec", NAME="swp17", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:7c --> swp18"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:7c", NAME="swp18", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:36 --> swp19"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:36", NAME="swp19", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:5c --> swp20"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:5c", NAME="swp20", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:3e --> swp21"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:3e", NAME="swp21", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:00 --> swp22"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:00", NAME="swp22", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:56 --> swp23"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:56", NAME="swp23", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:1e --> swp24"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:1e", NAME="swp24", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:02 --> swp25"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:02", NAME="swp25", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:bc --> swp26"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:bc", NAME="swp26", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:d8 --> swp27"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:d8", NAME="swp27", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:1e --> swp28"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:1e", NAME="swp28", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:42 --> swp29"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:42", NAME="swp29", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:a6 --> swp30"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:a6", NAME="swp30", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:c8 --> swp31"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:c8", NAME="swp31", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:16 --> swp32"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:16", NAME="swp32", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for spine04 #####
  config.vm.define "spine04" do |device|

    device.vm.hostname = "spine04"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp43
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:30",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10152',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8152',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> leaf01:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:48",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10036',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8036',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> leaf02:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:3c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10158',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8158',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> leaf03:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:da",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10109',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8109',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> leaf04:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:96",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10075',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8075',
            :libvirt__iface_name => 'swp4',
            auto_config: false
      # link for swp5 --> leaf05:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:26",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10019',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8019',
            :libvirt__iface_name => 'swp5',
            auto_config: false
      # link for swp6 --> leaf06:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:54",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10170',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8170',
            :libvirt__iface_name => 'swp6',
            auto_config: false
      # link for swp7 --> leaf07:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:ca",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10101',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8101',
            :libvirt__iface_name => 'swp7',
            auto_config: false
      # link for swp8 --> leaf08:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:32",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10025',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8025',
            :libvirt__iface_name => 'swp8',
            auto_config: false
      # link for swp9 --> leaf09:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:e2",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10113',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8113',
            :libvirt__iface_name => 'swp9',
            auto_config: false
      # link for swp10 --> leaf10:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:28",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10148',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8148',
            :libvirt__iface_name => 'swp10',
            auto_config: false
      # link for swp11 --> leaf11:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:20",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10016',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8016',
            :libvirt__iface_name => 'swp11',
            auto_config: false
      # link for swp12 --> leaf12:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:c0",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10096',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8096',
            :libvirt__iface_name => 'swp12',
            auto_config: false
      # link for swp13 --> leaf13:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:18",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10012',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8012',
            :libvirt__iface_name => 'swp13',
            auto_config: false
      # link for swp14 --> leaf14:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:12",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10137',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8137',
            :libvirt__iface_name => 'swp14',
            auto_config: false
      # link for swp15 --> leaf15:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:0e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10135',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8135',
            :libvirt__iface_name => 'swp15',
            auto_config: false
      # link for swp16 --> leaf16:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:ba",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10093',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8093',
            :libvirt__iface_name => 'swp16',
            auto_config: false
      # link for swp17 --> leaf17:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:cc",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10102',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8102',
            :libvirt__iface_name => 'swp17',
            auto_config: false
      # link for swp18 --> leaf18:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:38",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10156',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8156',
            :libvirt__iface_name => 'swp18',
            auto_config: false
      # link for swp19 --> leaf19:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:30",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10024',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8024',
            :libvirt__iface_name => 'swp19',
            auto_config: false
      # link for swp20 --> leaf20:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:4a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10037',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8037',
            :libvirt__iface_name => 'swp20',
            auto_config: false
      # link for swp21 --> leaf21:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:24",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10018',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8018',
            :libvirt__iface_name => 'swp21',
            auto_config: false
      # link for swp22 --> leaf22:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:7a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10061',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8061',
            :libvirt__iface_name => 'swp22',
            auto_config: false
      # link for swp23 --> leaf23:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:44",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10162',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8162',
            :libvirt__iface_name => 'swp23',
            auto_config: false
      # link for swp24 --> leaf24:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:90",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10072',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8072',
            :libvirt__iface_name => 'swp24',
            auto_config: false
      # link for swp25 --> leaf25:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:94",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10074',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8074',
            :libvirt__iface_name => 'swp25',
            auto_config: false
      # link for swp26 --> leaf26:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:80",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10064',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8064',
            :libvirt__iface_name => 'swp26',
            auto_config: false
      # link for swp27 --> leaf27:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:58",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10044',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8044',
            :libvirt__iface_name => 'swp27',
            auto_config: false
      # link for swp28 --> leaf28:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:32",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10153',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8153',
            :libvirt__iface_name => 'swp28',
            auto_config: false
      # link for swp29 --> leaf29:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:0c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10134',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8134',
            :libvirt__iface_name => 'swp29',
            auto_config: false
      # link for swp30 --> leaf30:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:dc",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10110',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8110',
            :libvirt__iface_name => 'swp30',
            auto_config: false
      # link for swp31 --> leaf31:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:aa",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10085',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8085',
            :libvirt__iface_name => 'swp31',
            auto_config: false
      # link for swp32 --> leaf32:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:e8",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10116',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8116',
            :libvirt__iface_name => 'swp32',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:30 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:30", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:48 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:48", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:3c --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:3c", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:da --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:da", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:96 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:96", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:26 --> swp5"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:26", NAME="swp5", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:54 --> swp6"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:54", NAME="swp6", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:ca --> swp7"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:ca", NAME="swp7", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:32 --> swp8"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:32", NAME="swp8", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:e2 --> swp9"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:e2", NAME="swp9", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:28 --> swp10"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:28", NAME="swp10", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:20 --> swp11"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:20", NAME="swp11", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:c0 --> swp12"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:c0", NAME="swp12", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:18 --> swp13"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:18", NAME="swp13", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:12 --> swp14"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:12", NAME="swp14", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:0e --> swp15"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:0e", NAME="swp15", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:ba --> swp16"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:ba", NAME="swp16", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:cc --> swp17"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:cc", NAME="swp17", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:38 --> swp18"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:38", NAME="swp18", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:30 --> swp19"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:30", NAME="swp19", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:4a --> swp20"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:4a", NAME="swp20", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:24 --> swp21"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:24", NAME="swp21", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:7a --> swp22"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:7a", NAME="swp22", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:44 --> swp23"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:44", NAME="swp23", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:90 --> swp24"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:90", NAME="swp24", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:94 --> swp25"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:94", NAME="swp25", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:80 --> swp26"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:80", NAME="swp26", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:58 --> swp27"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:58", NAME="swp27", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:32 --> swp28"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:32", NAME="swp28", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:0c --> swp29"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:0c", NAME="swp29", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:dc --> swp30"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:dc", NAME="swp30", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:aa --> swp31"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:aa", NAME="swp31", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:e8 --> swp32"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:e8", NAME="swp32", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf15 #####
  config.vm.define "leaf15" do |device|

    device.vm.hostname = "leaf15"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp16
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:42",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10161',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8161',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp15
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:81",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8065',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10065',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp15
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:1b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8014',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10014',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp15
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:13",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8010',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10010',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp15
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:0d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8135',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10135',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:42 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:42", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:81 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:81", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:1b --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:1b", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:13 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:13", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:0d --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:0d", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf14 #####
  config.vm.define "leaf14" do |device|

    device.vm.hostname = "leaf14"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp15
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:e6",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10115',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8115',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp14
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:67",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8052',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10052',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp14
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:3f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8160',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10160',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp14
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:65",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8051',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10051',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp14
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:11",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8137',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10137',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:e6 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:e6", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:67 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:67", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:3f --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:3f", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:65 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:65", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:11 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:11", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf17 #####
  config.vm.define "leaf17" do |device|

    device.vm.hostname = "leaf17"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp18
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:a4",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10082',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8082',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp17
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:eb",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8118',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10118',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp17
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:ad",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8087',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10087',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp17
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:1b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8142',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10142',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp17
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:cb",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8102',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10102',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:a4 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:a4", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:eb --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:eb", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:ad --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:ad", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:1b --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:1b", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:cb --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:cb", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf16 #####
  config.vm.define "leaf16" do |device|

    device.vm.hostname = "leaf16"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp17
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:50",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10040',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8040',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp16
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:e3",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8114',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10114',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp16
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:33",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8026',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10026',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp16
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:49",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8165',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10165',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp16
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:b9",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8093',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10093',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:50 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:50", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:e3 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:e3", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:33 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:33", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:49 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:49", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:b9 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:b9", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf11 #####
  config.vm.define "leaf11" do |device|

    device.vm.hostname = "leaf11"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp12
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:52",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10169',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8169',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp11
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:91",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8073',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10073',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp11
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:0b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8006',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10006',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp11
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:e9",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8117',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10117',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp11
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:1f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8016',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10016',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:52 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:52", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:91 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:91", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:0b --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:0b", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:e9 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:e9", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:1f --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:1f", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf10 #####
  config.vm.define "leaf10" do |device|

    device.vm.hostname = "leaf10"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp11
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:c6",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10099',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8099',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp10
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:45",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8163',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10163',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp10
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:53",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8042',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10042',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp10
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:a7",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8084',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10084',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp10
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:27",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8148',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10148',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:c6 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:c6", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:45 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:45", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:53 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:53", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:a7 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:a7", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:27 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:27", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf13 #####
  config.vm.define "leaf13" do |device|

    device.vm.hostname = "leaf13"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp14
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:f2",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10121',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8121',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp13
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:c3",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8098',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10098',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp13
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:13",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8138',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10138',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp13
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:3b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8030',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10030',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp13
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:17",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8012',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10012',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:f2 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:f2", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:c3 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:c3", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:13 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:13", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:3b --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:3b", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:17 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:17", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf07 #####
  config.vm.define "leaf07" do |device|

    device.vm.hostname = "leaf07"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp8
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:2c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10150',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8150',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp7
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:9f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8080',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10080',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp7
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:19",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8141',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10141',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp7
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:19",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8013',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10013',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp7
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:c9",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8101',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10101',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:2c --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:2c", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:9f --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:9f", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:19 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:19", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:19 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:19", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:c9 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:c9", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf19 #####
  config.vm.define "leaf19" do |device|

    device.vm.hostname = "leaf19"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp20
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:f8",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10124',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8124',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp19
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:35",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8027',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10027',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp19
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:45",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8035',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10035',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp19
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:03",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8130',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10130',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp19
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:2f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8024',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10024',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:f8 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:f8", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:35 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:35", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:45 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:45", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:03 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:03", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:2f --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:2f", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf18 #####
  config.vm.define "leaf18" do |device|

    device.vm.hostname = "leaf18"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp19
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:a2",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10081',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8081',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp18
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:7b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8062',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10062',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp18
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:57",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8172',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10172',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp18
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:cf",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8104',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10104',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp18
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:37",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8156',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10156',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:a2 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:a2", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:7b --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:7b", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:57 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:57", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:cf --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:cf", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:37 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:37", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf31 #####
  config.vm.define "leaf31" do |device|

    device.vm.hostname = "leaf31"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp32
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:b0",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10088',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8088',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp31
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:c7",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8100',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10100',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp31
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:85",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8067',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10067',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp31
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:8d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8071',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10071',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp31
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:a9",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8085',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10085',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:b0 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:b0", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:c7 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:c7", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:85 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:85", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:8d --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:8d", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:a9 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:a9", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf30 #####
  config.vm.define "leaf30" do |device|

    device.vm.hostname = "leaf30"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp31
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:8a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10069',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8069',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp30
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:a5",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8083',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10083',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp30
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:77",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8060',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10060',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp30
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:07",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8132',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10132',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp30
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:db",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8110',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10110',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:8a --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:8a", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:a5 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:a5", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:77 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:77", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:07 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:07", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:db --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:db", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf23 #####
  config.vm.define "leaf23" do |device|

    device.vm.hostname = "leaf23"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp24
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:10",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10008',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8008',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp23
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:55",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8171',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10171',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp23
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:b7",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8092',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10092',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp23
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:4d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8167',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10167',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp23
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:43",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8162',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10162',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:10 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:10", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:55 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:55", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:b7 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:b7", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:4d --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:4d", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:43 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:43", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf24 #####
  config.vm.define "leaf24" do |device|

    device.vm.hostname = "leaf24"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp25
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:f0",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10120',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8120',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp24
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:1d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8015',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10015',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp24
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:cd",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8103',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10103',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp24
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:4f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8168',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10168',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp24
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:8f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8072',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10072',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:f0 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:f0", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:1d --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:1d", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:cd --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:cd", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:4f --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:4f", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:8f --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:8f", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf03 #####
  config.vm.define "leaf03" do |device|

    device.vm.hostname = "leaf03"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:64",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10178',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8178',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:b1",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8089',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10089',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:4b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8166',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10166',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:05",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8131',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10131',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:d9",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8109',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10109',
            :libvirt__iface_name => 'swp4',
            auto_config: false
      # link for swp5 --> host03:eth1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:98",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10076',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8076',
            :libvirt__iface_name => 'swp5',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:64 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:64", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:b1 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:b1", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:4b --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:4b", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:05 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:05", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:d9 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:d9", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:98 --> swp5"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:98", NAME="swp5", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf20 #####
  config.vm.define "leaf20" do |device|

    device.vm.hostname = "leaf20"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp21
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:18",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10140',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8140',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp20
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:5b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8046',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10046',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp20
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:1f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8144',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10144',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp20
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:29",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8149',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10149',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp20
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:49",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8037',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10037',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:18 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:18", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:5b --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:5b", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:1f --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:1f", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:29 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:29", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:49 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:49", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf01 #####
  config.vm.define "leaf01" do |device|

    device.vm.hostname = "leaf01"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:22",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10145',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8145',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:df",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8112',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10112',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:43",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8034',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10034',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:3d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8031',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10031',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:47",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8036',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10036',
            :libvirt__iface_name => 'swp4',
            auto_config: false
      # link for swp5 --> host01:eth1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:3a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10029',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8029',
            :libvirt__iface_name => 'swp5',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:22 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:22", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:df --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:df", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:43 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:43", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:3d --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:3d", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:47 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:47", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:3a --> swp5"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:3a", NAME="swp5", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf32 #####
  config.vm.define "leaf32" do |device|

    device.vm.hostname = "leaf32"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp33
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:9e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10079',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8079',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp32
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:15",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8139',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10139',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp32
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:fb",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8126',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10126',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp32
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:15",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8011',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10011',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp32
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:e7",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8116',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10116',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:9e --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:9e", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:15 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:15", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:fb --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:fb", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:15 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:15", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:e7 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:e7", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf06 #####
  config.vm.define "leaf06" do |device|

    device.vm.hostname = "leaf06"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp7
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:60",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10048',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8048',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp6
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:5d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8175',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10175',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp6
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:11",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8009',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10009',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp6
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:09",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8133',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10133',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp6
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:53",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8170',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10170',
            :libvirt__iface_name => 'swp4',
            auto_config: false
      # link for swp5 --> host06:eth1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:08",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10004',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8004',
            :libvirt__iface_name => 'swp5',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:60 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:60", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:5d --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:5d", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:11 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:11", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:09 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:09", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:53 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:53", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:08 --> swp5"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:08", NAME="swp5", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf21 #####
  config.vm.define "leaf21" do |device|

    device.vm.hostname = "leaf21"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp22
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:04",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10002',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8002',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp21
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:3d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8159',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10159',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp21
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:6d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8055',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10055',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp21
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:4d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8039',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10039',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp21
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:23",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8018',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10018',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:04 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:04", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:3d --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:3d", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:6d --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:6d", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:4d --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:4d", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:23 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:23", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf04 #####
  config.vm.define "leaf04" do |device|

    device.vm.hostname = "leaf04"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp5
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:f4",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10122',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8122',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:51",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8041',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10041',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:9b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8078',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10078',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:6b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8054',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10054',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp4
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:95",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8075',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10075',
            :libvirt__iface_name => 'swp4',
            auto_config: false
      # link for swp5 --> host04:eth1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:d2",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10105',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8105',
            :libvirt__iface_name => 'swp5',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:f4 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:f4", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:51 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:51", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:9b --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:9b", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:6b --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:6b", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:95 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:95", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:d2 --> swp5"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:d2", NAME="swp5", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf05 #####
  config.vm.define "leaf05" do |device|

    device.vm.hostname = "leaf05"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp6
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:84",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10066',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8066',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp5
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:59",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8045',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10045',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp5
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:29",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8021',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10021',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp5
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:59",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8173',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10173',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp5
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:25",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8019',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10019',
            :libvirt__iface_name => 'swp4',
            auto_config: false
      # link for swp5 --> host05:eth1
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:10",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10136',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8136',
            :libvirt__iface_name => 'swp5',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:84 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:84", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:59 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:59", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:29 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:29", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:59 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:59", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:25 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:25", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:10 --> swp5"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:10", NAME="swp5", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf02 #####
  config.vm.define "leaf02" do |device|

    device.vm.hostname = "leaf02"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp3
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:34",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10154',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8154',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:d3",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8106',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10106',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:b5",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8091',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10091',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:ab",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8086',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10086',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp2
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:3b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8158',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10158',
            :libvirt__iface_name => 'swp4',
            auto_config: false
      # link for swp5 --> host02:eth1
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:b4",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10090',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8090',
            :libvirt__iface_name => 'swp5',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:34 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:34", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:d3 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:d3", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:b5 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:b5", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:ab --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:ab", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:3b --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:3b", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:b4 --> swp5"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:b4", NAME="swp5", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf25 #####
  config.vm.define "leaf25" do |device|

    device.vm.hostname = "leaf25"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp26
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:24",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10146',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8146',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp25
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:01",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8001',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10001',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp25
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:2d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8151',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10151',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp25
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:3f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8032',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10032',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp25
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:93",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8074',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10074',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:24 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:24", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:01 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:01", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:2d --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:2d", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:3f --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:3f", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:93 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:93", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf26 #####
  config.vm.define "leaf26" do |device|

    device.vm.hostname = "leaf26"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp27
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:26",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10147',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8147',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp26
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:bb",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8094',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10094',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp26
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:5b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8174',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10174',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp26
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:21",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8017',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10017',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp26
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:7f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8064',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10064',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:26 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:26", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:bb --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:bb", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:5b --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:5b", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:21 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:21", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:7f --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:7f", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf27 #####
  config.vm.define "leaf27" do |device|

    device.vm.hostname = "leaf27"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp28
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:ee",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10119',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8119',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp27
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:d7",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8108',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10108',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp27
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:37",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8028',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10028',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp27
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:71",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8057',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10057',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp27
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:57",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8044',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10044',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:ee --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:ee", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:d7 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:d7", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:37 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:37", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:71 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:71", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:57 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:57", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf28 #####
  config.vm.define "leaf28" do |device|

    device.vm.hostname = "leaf28"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp29
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:62",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10177',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8177',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp28
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:1d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8143',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10143',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp28
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:7d",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8063',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10063',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp28
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:bd",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8095',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10095',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp28
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:31",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8153',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10153',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:62 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:62", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:1d --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:1d", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:7d --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:7d", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:bd --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:bd", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:31 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:31", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf29 #####
  config.vm.define "leaf29" do |device|

    device.vm.hostname = "leaf29"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp30
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:2c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10022',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8022',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp29
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:41",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8033',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10033',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp29
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:35",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8155',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10155',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp29
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:d5",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8107',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10107',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp29
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:0b",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8134',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10134',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:2c --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:2c", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:41 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:41", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:35 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:35", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:d5 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:d5", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:0b --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:0b", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf08 #####
  config.vm.define "leaf08" do |device|

    device.vm.hostname = "leaf08"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp9
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:6a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10053',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8053',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp8
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:47",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8164',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10164',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp8
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:01",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8129',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10129',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp8
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:87",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8068',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10068',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp8
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:31",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8025',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10025',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:6a --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:6a", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:47 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:47", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:01 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:01", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:87 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:87", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:31 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:31", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf09 #####
  config.vm.define "leaf09" do |device|

    device.vm.hostname = "leaf09"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp10
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:fe",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10127',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8127',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp9
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:c1",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8097',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10097',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp9
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:39",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8157',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10157',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp9
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:05",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8003',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10003',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp9
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:e1",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8113',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10113',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:fe --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:fe", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:c1 --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:c1", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:39 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:39", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:05 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:05", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:e1 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:e1", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf22 #####
  config.vm.define "leaf22" do |device|

    device.vm.hostname = "leaf22"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp23
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:28",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10020',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8020',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp22
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:ff",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8128',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10128',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp22
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:63",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8050',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10050',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp22
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:61",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8049',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10049',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp22
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:79",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8061',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10061',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:28 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:28", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:ff --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:ff", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:63 --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:63", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:61 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:61", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:79 --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:79", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for leaf12 #####
  config.vm.define "leaf12" do |device|

    device.vm.hostname = "leaf12"

    device.vm.box = "CumulusCommunity/cumulus-vx"
    device.vm.box_version = "3.5.1"

    device.vm.provider :libvirt do |v|
      v.memory = 768
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp13
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:70",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10056',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8056',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for swp1 --> spine01:swp12
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:5f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8176',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10176',
            :libvirt__iface_name => 'swp1',
            auto_config: false
      # link for swp2 --> spine02:swp12
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:dd",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8111',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10111',
            :libvirt__iface_name => 'swp2',
            auto_config: false
      # link for swp3 --> spine03:swp12
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:f9",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8125',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10125',
            :libvirt__iface_name => 'swp3',
            auto_config: false
      # link for swp4 --> spine04:swp12
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:bf",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8096',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10096',
            :libvirt__iface_name => 'swp4',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    #Copy over Topology.dot File
    device.vm.provision "file", source: "topology.dot", destination: "~/topology.dot"
    device.vm.provision :shell, privileged: false, inline: "sudo mv ~/topology.dot /etc/ptm.d/topology.dot"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_switch_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:70 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:70", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:5f --> swp1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:5f", NAME="swp1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:dd --> swp2"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:dd", NAME="swp2", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:f9 --> swp3"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:f9", NAME="swp3", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:bf --> swp4"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:bf", NAME="swp4", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for host01 #####
  config.vm.define "host01" do |device|

    device.vm.hostname = "host01"

    device.vm.box = "yk0/ubuntu-xenial"

    device.vm.provider :libvirt do |v|
      v.nic_model_type = 'e1000'
      v.memory = 512
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp34
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:5e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10047',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8047',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for eth1 --> leaf01:swp5
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:39",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8029',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10029',
            :libvirt__iface_name => 'eth1',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    # Shorten Boot Process - Applies to Ubuntu Only - remove \"Wait for Network\"
    device.vm.provision :shell , inline: "sed -i 's/sleep [0-9]*/sleep 1/' /etc/init/failsafe.conf 2>/dev/null || true"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_server_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:5e --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:5e", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:39 --> eth1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:39", NAME="eth1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for host02 #####
  config.vm.define "host02" do |device|

    device.vm.hostname = "host02"

    device.vm.box = "yk0/ubuntu-xenial"

    device.vm.provider :libvirt do |v|
      v.nic_model_type = 'e1000'
      v.memory = 512
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp35
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:0e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10007',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8007',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for eth1 --> leaf02:swp5
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:b3",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8090',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10090',
            :libvirt__iface_name => 'eth1',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    # Shorten Boot Process - Applies to Ubuntu Only - remove \"Wait for Network\"
    device.vm.provision :shell , inline: "sed -i 's/sleep [0-9]*/sleep 1/' /etc/init/failsafe.conf 2>/dev/null || true"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_server_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:0e --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:0e", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:b3 --> eth1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:b3", NAME="eth1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for host03 #####
  config.vm.define "host03" do |device|

    device.vm.hostname = "host03"

    device.vm.box = "yk0/ubuntu-xenial"

    device.vm.provider :libvirt do |v|
      v.nic_model_type = 'e1000'
      v.memory = 512
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp36
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:8c",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10070',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8070',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for eth1 --> leaf03:swp5
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:97",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8076',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10076',
            :libvirt__iface_name => 'eth1',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    # Shorten Boot Process - Applies to Ubuntu Only - remove \"Wait for Network\"
    device.vm.provision :shell , inline: "sed -i 's/sleep [0-9]*/sleep 1/' /etc/init/failsafe.conf 2>/dev/null || true"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_server_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:8c --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:8c", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:97 --> eth1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:97", NAME="eth1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for host05 #####
  config.vm.define "host05" do |device|

    device.vm.hostname = "host05"

    device.vm.box = "yk0/ubuntu-xenial"

    device.vm.provider :libvirt do |v|
      v.nic_model_type = 'e1000'
      v.memory = 512
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp38
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:2e",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10023',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8023',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for eth1 --> leaf05:swp5
      device.vm.network "private_network",
            :mac => "44:38:39:00:01:0f",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8136',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10136',
            :libvirt__iface_name => 'eth1',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    # Shorten Boot Process - Applies to Ubuntu Only - remove \"Wait for Network\"
    device.vm.provision :shell , inline: "sed -i 's/sleep [0-9]*/sleep 1/' /etc/init/failsafe.conf 2>/dev/null || true"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_server_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:2e --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:2e", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:01:0f --> eth1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:01:0f", NAME="eth1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for host06 #####
  config.vm.define "host06" do |device|

    device.vm.hostname = "host06"

    device.vm.box = "yk0/ubuntu-xenial"

    device.vm.provider :libvirt do |v|
      v.nic_model_type = 'e1000'
      v.memory = 512
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp39
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:0a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10005',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8005',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for eth1 --> leaf06:swp5
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:07",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8004',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10004',
            :libvirt__iface_name => 'eth1',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    # Shorten Boot Process - Applies to Ubuntu Only - remove \"Wait for Network\"
    device.vm.provision :shell , inline: "sed -i 's/sleep [0-9]*/sleep 1/' /etc/init/failsafe.conf 2>/dev/null || true"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_server_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:0a --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:0a", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:07 --> eth1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:07", NAME="eth1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for host04 #####
  config.vm.define "host04" do |device|

    device.vm.hostname = "host04"

    device.vm.box = "yk0/ubuntu-xenial"

    device.vm.provider :libvirt do |v|
      v.nic_model_type = 'e1000'
      v.memory = 512
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp37
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:9a",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '10077',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '8077',
            :libvirt__iface_name => 'eth0',
            auto_config: false
      # link for eth1 --> leaf04:swp5
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:d1",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '127.0.0.1',
            :libvirt__tunnel_local_port => '8105',
            :libvirt__tunnel_ip => '127.0.0.1',
            :libvirt__tunnel_port => '10105',
            :libvirt__iface_name => 'eth1',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false

    # Shorten Boot Process - Applies to Ubuntu Only - remove \"Wait for Network\"
    device.vm.provision :shell , inline: "sed -i 's/sleep [0-9]*/sleep 1/' /etc/init/failsafe.conf 2>/dev/null || true"


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_server_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:9a --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:9a", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule
     device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:d1 --> eth1"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:d1", NAME="eth1", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end

  ##### DEFINE VM for netq-ts #####
  config.vm.define "netq-ts" do |device|

    device.vm.hostname = "netq-ts"

    device.vm.box = "cumulus/ts"

    device.vm.provider :libvirt do |v|
      v.nic_model_type = 'e1000'
      v.memory = 1024*16
-     v.cpus = 4
    end
    #   see note here: https://github.com/pradels/vagrant-libvirt#synced-folders
    device.vm.synced_folder ".", "/vagrant", disabled: true



    # NETWORK INTERFACES
      # link for eth0 --> oob-mgmt-switch:swp44
      device.vm.network "private_network",
            :mac => "44:38:39:00:00:74",
            :libvirt__tunnel_type => 'udp',
            :libvirt__tunnel_local_ip => '10.14.0.1',
            :libvirt__tunnel_local_port => '10058',
            :libvirt__tunnel_ip => '10.13.0.1',
            :libvirt__tunnel_port => '8058',
            :libvirt__iface_name => 'eth0',
            auto_config: false



    # Fixes "stdin: is not a tty" and "mesg: ttyname failed : Inappropriate ioctl for device"  messages --> https://github.com/mitchellh/vagrant/issues/1673
    device.vm.provision :shell , inline: "(sudo grep -q 'mesg n' /root/.profile 2>/dev/null && sudo sed -i '/mesg n/d' /root/.profile  2>/dev/null) || true;", privileged: false


    # Run the Config specified in the Node Attributes
    device.vm.provision :shell , privileged: false, :inline => 'echo "$(whoami)" > /tmp/normal_user'
    device.vm.provision :shell , path: "./helper_scripts/extra_server_config.sh"


    # Install Rules for the interface re-map
    device.vm.provision :shell , :inline => <<-delete_udev_directory
if [ -d "/etc/udev/rules.d/70-persistent-net.rules" ]; then
    rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
fi
rm -rfv /etc/udev/rules.d/70-persistent-net.rules &> /dev/null
delete_udev_directory

device.vm.provision :shell , :inline => <<-udev_rule
echo "  INFO: Adding UDEV Rule: 44:38:39:00:00:74 --> eth0"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{address}=="44:38:39:00:00:74", NAME="eth0", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
udev_rule

      device.vm.provision :shell , :inline => <<-vagrant_interface_rule
echo "  INFO: Adding UDEV Rule: Vagrant interface = vagrant"
echo 'ACTION=="add", SUBSYSTEM=="net", ATTR{ifindex}=="2", NAME="vagrant", SUBSYSTEMS=="pci"' >> /etc/udev/rules.d/70-persistent-net.rules
echo "#### UDEV Rules (/etc/udev/rules.d/70-persistent-net.rules) ####"
cat /etc/udev/rules.d/70-persistent-net.rules
vagrant_interface_rule

# Run Any Platform Specific Code and Apply the interface Re-map
    #   (may or may not perform a reboot depending on platform)
    device.vm.provision :shell , :inline => $script

end



end
