/*
   BRIAN REZA SMITH 
   CSUDH
   2020
 */


**Middlebox assignment and routing between hosts in Software Defined Data Center using Python, Ryu, OpenFlow, NetworkX 
in a Mininet environment. 

	Middleboxes are network appliances that transform, inspect, filter, and or manipulate traffic for purposes 
	other than packet forwarding. Using OpenFlow switches and Ryu as SDN controller, 
	this project emulates a data center by generating a fat tree topology of software defined switches 
	and a set of hosts as leaves then arbitrarily designating a subset of the switches to be considered 
	"middleboxes". The hosts are paired up but must route all traffic between each other through one of the
	middleboxes. 

	The goal of this project is to explore the efficiency of different algorithms in selecting which middlebox 
	that pairs of hosts should be routed through to minimize network traffic latency and load on
	each middlebox.  




	To start the experiment, run startMininet, wait for the prompt to start the controller, then start the controller. 


	FILES:
		-fattree.py: script for mininet to create fattree topology with switches using K ports 
		-loadBalanceMBFattreeRyuController.py: all logic for associating MBs to host pairs and routing traffic
		-utils.py: helper functions
