#!/bin/bash

check_state(){
if [ "$?" != "0" ]; then
    echo "ERROR Test Failed!"
    exit 1
fi
}

echo "####################################"
echo "############# TEST 1: 1switch_1server.dot Vbox ###############"
echo "####################################"
python ./topology_converter.py ./examples/1switch_1server.dot && vagrant status

check_state

echo "####################################"
echo "############# TEST 2: 1switch_1server.dot libvirt ###############"
echo "####################################"
python ./topology_converter.py ./examples/1switch_1server.dot -p libvirt && vagrant status

check_state

echo "####################################"
echo "############# TEST 3: 3switch_circular.dot Vbox ###############"
echo "####################################"
python ./topology_converter.py ./examples/3switch_circular.dot && vagrant status

check_state

echo "####################################"
echo "############# TEST 4: 3switch_circular.dot libvirt ###############"
echo "####################################"
python ./topology_converter.py ./examples/3switch_circular.dot -p libvirt && vagrant status

check_state

echo "####################################"
echo "############# TEST 5: customer_topology.dot Vbox ###############"
echo "####################################"
python ./topology_converter.py ./examples/customer_topology.dot && vagrant status

check_state

echo "####################################"
echo "############# TEST 6: customer_topology.dot libvirt ###############"
echo "####################################"
python ./topology_converter.py ./examples/customer_topology.dot -p libvirt && vagrant status

check_state

echo "####################################"
echo "############# TEST 7: 2switch_tun_ip.dot libvirt ###############"
echo "####################################"
python ./topology_converter.py ./examples/2switch_tun_ip.dot -p libvirt && vagrant status

check_state

echo "####################################"
echo "############# TEST 8: 2switch.dot Vbox ###############"
echo "####################################"
python ./topology_converter.py ./examples/2switch.dot && vagrant status

check_state

echo "####################################"
echo "############# TEST 9: 2switch.dot libvirt ###############"
echo "####################################"
python ./topology_converter.py ./examples/2switch.dot -p libvirt && vagrant status

check_state


