#!/bin/bash
sudo mn -c
sleep 1
sudo python fattree.py
#all correct commandline arguments to be moved to python-only
#script
#sudo mn --mac --arp --custom fattree.py --topo fattree --switch ovs,protocols=OpenFlow13 --controller remote
