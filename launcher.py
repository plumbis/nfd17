#!/usr/bin/env python

leaf_count = 128
chassis_list = ["chassis01", "chassis02", "chassis03", "chassis04"]
linecard_list = ["lc1-1", "lc1-2", "lc2-1", "lc2-2", "lc3-1", "lc3-2", "lc4-1", "lc4-2"]
fabriccard_list = ["fc1-1", "fc2-1", "fc3-1", "fc4-1"]


output = []
current_leaf = 1

output.append("vagrant up oob-mgmt-server oob-mgmt-switch")
output.append("vagrant up netq-ts")
working_leaf_list = []

while current_leaf <= leaf_count:
    working_leaf_list.append("leaf" + str("%02d" % current_leaf))

    if not current_leaf % 6:
        output.append("vagrant up " +  " ".join(working_leaf_list))
        working_leaf_list = []
    current_leaf += 1

for chassis in chassis_list:
    chassis_string = []
    for linecard in linecard_list:
        chassis_string.append(chassis + "-" + linecard + " ")

    output.append("vagrant up " + " ".join(chassis_string))
    chassis_string = []

    for fabriccard in fabriccard_list:
        chassis_string.append(chassis + "-" + fabriccard + " ")

    output.append("vagrant up " + " ".join(chassis_string))

print "\n".join(output)
