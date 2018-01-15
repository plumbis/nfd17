#!/bin/bash

echo "#################################"
echo "  Running pxehost_config.sh"
echo "#################################"
sudo su

echo -e "WIPING MBR of Box Image to Prep for PXE Boot"
dd if=/dev/zero of=/dev/sda count=1 &> ./dd_output
cat ./dd_output
echo -e "   done."


echo "#################################"
echo "   Finished"
echo "#################################"
