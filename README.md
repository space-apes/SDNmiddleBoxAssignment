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
	and a set of hosts as leaves to the tree, then arbitrarily designates a subset of the switches to be considered 
	"middleboxes". The hosts are paired up but must route all traffic between each other through one of the
	middleboxes. 

	The goal of this project is to explore the efficiency of different algorithms in selecting which middlebox 
	that pairs of hosts should be routed through to minimize network traffic latency and load on
	each middlebox.  

	For the purposes of the project the terms "VM" and "host" will be used interchangeably because the hosts 
	are virtual in the experiment.

	The 3 algorithms explored are:
		-Host-Based: for each host select the first middlebox that has not met its load cap
		-MB-Based: for each MB sort unassigned host-pairs and assign until MB meets load cap
		-Host-MB-Based: in multiple rounds, cycle through all combinations of non-maxed MB and unassigned VMpair
			and assign lowest cost combination. It is assumed that this will lead to the best results.

		



	To start the experiment, run startMininet, wait for the prompt to start the controller, then start the controller. 


	FILES:
		-fattree.py: script for mininet to create fattree topology with switches using K ports 
		-loadBalanceMBFattreeRyuController.py: all logic for associating MBs to host pairs and routing traffic
		-utils.py: helper functions
