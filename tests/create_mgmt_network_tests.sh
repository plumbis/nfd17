#!/bin/bash

check_state(){
if [ "$?" != "0" ]; then
    echo "ERROR Test Failed!"
    exit 1
fi
}

echo "####################################"
echo "############# TEST 1 ###############"
echo "####################################"
python ./topology_converter.py ./examples/2switch_auto_mgmt.dot && vagrant status

check_state

echo "####################################"
echo "############# TEST 2 ###############"
echo "####################################"
python ./topology_converter.py ./examples/2switch_auto_mgmt.dot -p libvirt && vagrant status

check_state

echo "####################################"
echo "############# TEST 3 ###############"
echo "####################################"
python ./topology_converter.py ./examples/2switch_auto_mgmt.dot -c && vagrant status

check_state

echo "####################################"
echo "############# TEST 4 ###############"
echo "####################################"
python ./topology_converter.py ./examples/2switch_auto_mgmt.dot -c -p libvirt && vagrant status

check_state

echo "####################################"
echo "############# TEST 5 ###############"
echo "####################################"
python ./topology_converter.py ./examples/2switch_auto_mgmt_ip.dot -c && vagrant status

check_state

echo "####################################"
echo "############# TEST 6 ###############"
echo "####################################"
python ./topology_converter.py ./examples/2switch_auto_mgmt_ip.dot -c -p libvirt && vagrant status

check_state


