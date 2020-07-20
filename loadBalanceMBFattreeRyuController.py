#Brian Smith
#CSUDH
#csc-541
#Fall 2019

#loadbalanced middlebox assignment solution implementation 
#using 3 algorithms:
#	-VM based
#	-MB based
#	-VM-MB based
#
#across 3 randomized scenarios


#TODO: add in command line arguments for picking scenario, random scenario, and algorithm choice
#TODO: determine how to integrate iperf tests seamlessly into user experience

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, arp
from utils import hToMac, MACToH, indexOfSecondInstance
from ryu.lib import stplib
import networkx

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link, get_host, get_all_host

from mbSelectionAlgorithms import hostBasedMBSelection, MBBasedMBSelection, hostAndMBBasedMBSelection

class loadBalanceMBFattree(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

	def __init__(self, *args, **kwargs):
		super(loadBalanceMBFattree, self).__init__(*args, **kwargs)
		


		self.packetCounter = 0
#		app-wide mac_to_port dictionary. 
#		honestly not sure where this is used. i see entries added but never retrieved
#		i think elements in this are dicts themselves	
#		we don't use this too much because we rely on networkx's digraph
#		to maintain node -> port -> node information for the network
		self.mac_to_port = {}

#		initialize the app-wide graph to represent all nodes in network
		self.net=networkx.DiGraph()
#
#
#		controller will have global reference to middleboxes 
#		DPID will be set by populateScenarioValues
#		and load will be set by the MB assignment methods
#		format for each MB element in list: 
#			{'dpid':0, load:0}
		self.MBList = [{'dpid': 0, 'load':0}, {'dpid':0, 'load':0}]
#		
#		self.currentMBIndex = 0
#		
#		maximum load in terms of VM pairs assigned to the middleBoxes
		self.maxVMPairsPerMB = 4;
#		global reference to all VM pairs. contains 
#			-macAddresses for source and destination of vm pairs 	
#			-the final selected DPID of best choice of MB
#			-two lists of shortest paths from vm0->mb0->vm1 and vm1->mb1->vm0
#		example entry in the list: 
#			{
#				'vm0': '00:00:00:00:00:10', 
#				'vm1': '00:00:00:00:00:03', 
#				'bestMBDPID': -1,
#				'shortestPaths': [[1,3,6,8],[2,5,3,7]]
#			}
		self.VMPairList = []
		
#		hard-coded initialization values for self.MB1, self.MB2, and self.VMPairs
		scenarioA = {'MB0': 9, 'MB1':3, 'VMPairs': [16, 3, 8, 5, 10, 11, 12, 4, 14, 6, 9, 2, 15, 1, 7, 13]  }
		scenarioB = {'MB0': 4, 'MB1':11, 'VMPairs': [12, 9, 4, 15, 11, 16, 7, 14, 5, 10, 13, 2, 1, 3, 6, 8]  }
		scenarioC = {'MB0': 5, 'MB1':4, 'VMPairs': [4, 16, 11, 13, 1, 3, 6, 7, 5, 10, 14, 8, 12, 15, 9, 2]  }

		self.afterMB = {}

#		boolean that flips to true only when all possible shortest paths vm0->mbX->vm1 have been determined
		self.allPathsCalculated = False

#		boolean that flips to true only when MBs for all VMPairs have been selected
#		and all values for self.vmPairList[x][bestMBDPID] are no longer -1
		self.allMBsSelected = False

		#CHOOSE DIFFERENT SCENARIOS HERE
		self.populateScenarioValues(scenarioA)
		
		#CHOOSE DIFFERENT MB SELECTION ALGORITHM HERE
		#1: vm-based
		#2: mb-based
		#3: vm/mb-based
		self.algoChoice = 3
		
#	NAME: populateScenarioValues
#	SIGNATURE: (scenarioDict)->
#	DESCRIPTION: populates main data structures for the working version of which switches are selected to be MBs 
#	(self.MBList) and 
#	which hosts are to be paired together (self.VMPairList) with hardcoded arbitrary "scenario" dicts
#	so we can test efficacy of different middle box selection algorithms across different conditions. 
#	This is called in init method for class. 
#	
	def populateScenarioValues(self, scenario):
		self.MBList[0] = {'dpid': scenario['MB0'], 'load':0}
		self.MBList[1] = {'dpid': scenario['MB1'], 'load':0}
		for x in range(0, 16, 2):
			self.VMPairList.append({'VM0': hToMac(scenario['VMPairs'][x]),'VM1': hToMac(scenario['VMPairs'][x+1]), 'bestMBDPID': -1, 'shortestPaths': [[],[]], })
	
#	
#	NAME: fillShortestPathsForAllVMPairs
#	SIGNATURE: ()->
#	DESCRIPTION: fills in global lists of shortest paths for use in later MB selection algorithms.
#	Until all shortest paths for each VMPair for each MB are discovered, this will be triggered on each packet in.	
#	
#	PSEUDOCODE:
#	
#	for all VMpairs
#		for all middleboxes
#			find shortest path from source to middlebox
#			find shortest path from middlebox to destination
#			concatenate the two lists
#			set the global path for that mb for that pair to the list	

	def fillShortestPathsForAllVMPairs(self):
	
		for VMPairIndex in range(len(self.VMPairList)):
			for MBIndex in range (len(self.MBList)):
				if len(self.VMPairList[VMPairIndex]['shortestPaths'][MBIndex]) == 0: 
					self.currentMBIndex = MBIndex
					theSource = self.VMPairList[VMPairIndex]['VM0']
					theDestination = self.VMPairList[VMPairIndex]['VM1']
					firstHalf = networkx.shortest_path(self.net, theSource, self.MBList[MBIndex]['dpid'])
					secondHalf = networkx.shortest_path(self.net, self.MBList[MBIndex]['dpid'], theDestination)
					shortestPath = firstHalf+secondHalf[1:]
					self.VMPairList[VMPairIndex]['shortestPaths'][MBIndex] = shortestPath 
					#print("self.VMPairList[%d]['shortestPaths'][%d] is %s" % (VMPairIndex, MBIndex, shortestPath))	
		self.allPathsCalculated = True

#	NAME: selectMBForAllVMPairs
#	SIGNATURE: (int)->
#	DESCRIPTION: This method's purpose is to finally associate each VMpair with a middlebox. 
#	It assumes that: 
#		1. that all hosts and switches have been added to the networkx graph
#		2. that shortest paths have been determined for all combinations host->mb->host
#	
#	Once these criteria are met this method is called just once per experiment and performs 
#	the following steps:
#		1. using a switch case using the argument value run through appropriate algorithm
#			(1. VMbased, 2. MBbased, 3. VM/MBbased) 
#		2. update value for each self.VMPairList[x]['bestMBDPID'] from -1
#		3. update value for each self.MBList['load'] from 0
#		4. set self.allMBsSelected to True
#		5. return the total cost across all paths


	#FAKE VERSION
	def selectMBForAllVMPairs(self, algoChoice):
		if algoChoice == 1:
			print("selecting MBs for host pairs using host-based algorithm")
			hostBasedMBSelection(self.VMPairList, self.MBList, self.maxVMPairsPerMB)
		elif algoChoice == 2:
			print("selecting MBs for host pairs using MB-based algorithm")
			MBBasedMBSelection(self.VMPairList, self.MBList, self.maxVMPairsPerMB)
		elif algoChoice == 3:
			print("selecting MBs for host pairs using host and MB based algorithm")
			hostAndMBBasedMBSelection(self.VMPairList, self.MBList, self.maxVMPairsPerMB)
		else:
			print("invalid MB selection algorithm. defaulting to host-based MB selection algorithm")
			hostBasedMBSelection(self.VMPairList, self.MBList, self.maxVMPairsPerMB)
		self.allMBsSelected = True
		self.printSelectionsAndCosts()
		



#	NAME: printSelectionsAndCosts
#	SIGNATURE: ()->
#	DESCRIPTION: This method should be called after selectMBForAllVMPairs to 
#	display, for all MBs, which VMPairs were selected, what paths do they take, what is the cost in 
#	network hops, what is the load on the MB, and finally what is the overall cost in hops for the entire instance
#	of the experiment. 
#
#	TODO: finish it. make it pretty. 
	def printSelectionsAndCosts(self):
		totalCost = 0
		for MBIndex in range(len(self.MBList)):
			print("MB: {}".format(self.MBList[MBIndex]['dpid']))
			for hostPairIndex in range(len(self.VMPairList)):
				curHostPair = self.VMPairList[hostPairIndex]
				if curHostPair['bestMBDPID'] == self.MBList[MBIndex]['dpid']:
					curPath = curHostPair['shortestPaths'][MBIndex]
					totalCost += len(curPath)-1
					host1 = MACToH(self.VMPairList[hostPairIndex]['VM0'])
					host2 = MACToH(self.VMPairList[hostPairIndex]['VM1'])
					print("{}->{}->{}: {}  cost: {}".format(host1, self.MBList[MBIndex]['dpid'], host2, curPath, len(curPath)))
		print("TOTAL COST: {:>}".format(str(totalCost)))
	


#	NAME: getPairIndexAndDirection
#	SIGNATURE: (String, String)-> (int, String)
#	DESCRIPTION: get the vmPairList index and path direction from source to destination using 
#	the shortest paths generated by self.fillShortestPathsForAllVMPairs(). 
#	This function takes in strings for host destination and source
#	MAC address in the format: '00:00:00:00:00:0B'
#	
#	PSEUDOCODE: 
#
#		for all vmPairs 
#			if the given sourceMac matches vm0
#				return the shortest path 
#			if the given sourceMac matches vm1
#				return the reverse of the shortest path
#			else
#				print some error and return an empty list
	def getPairIndexAndDirection(self, src, dst):
		for i in range(len(self.VMPairList)):
			if src == self.VMPairList[i]['VM0'] and dst == self.VMPairList[i]['VM1']:
				#print("found a pair for src %s and dst %s" % (src,dst))
				return (i, 'forward')
			
			if src == self.VMPairList[i]['VM1'] and dst == self.VMPairList[i]['VM0']:
				#print("found a pair for src %s and dst %s" % (src,dst))
				return (i, 'backward')

		print ('when getting pair from list,  src %s and dst%s not found' % (src, dst))
		return (-1, 'noDirection')

	#event handler for when switch is added 
	#adds a default flow entry with lowest priority (0)
	#that forwards packets to the controller
	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def switch_features_handler(self, ev):
		

		datapath = ev.msg.datapath
		#definitions for a specific openflow implementation?
		ofproto = datapath.ofproto
		#parser to be able to pull apart
		#event objects from this particular 
		#version of openflow
		parser = datapath.ofproto_parser
		
		#OFPMATCH with no arguments means it matches all conditions
		match = parser.OFPMatch()

		actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
		
		self.add_flow(datapath, 0, match, actions)

	#A helper function for adding flow entries
	#datapath.send_msg(mod) adds the flow entry to the switch. i think we can avoid buffer_id stuff in this problem. 	
	def add_flow(self, datapath, priority, match, actions, buffer_id=None):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

		if buffer_id:
			mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id, priority=priority, match=match, instructions=inst)
		else:
			mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)
		
		datapath.send_msg(mod)


	
	#handler for when messages are sent to CONTROLLER
	#OVERALL GOALS:
	#	1. extract data-link level information from (host src/host dst MAC switch ports)
	#	2. populate networkx graph representing all switches/hosts/links in network by flooting ports
	#	3. if graph is populated, determine best MB for given src and dst, else flood all ports
	#	4. if graph populated, and best MB chosen, determine shortest path host->MB->host
	#	5. add flow entry for that given source and destination to skip controller processing next time. 
	
	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		self.packetCounter += 1


		#this is some protection against 
		#losing data in transit i think..
		
		#the example comment here is:
		#if you hit this you might want to increase
		#the "miss_send_length" of your switch

		if ev.msg.msg_len < ev.msg.total_len:
			self.logger.debug("packet truncated: only %s of %s bytes", ev.msg.msg_len, ev.msg.total_len)


		#the following lines extract 
		#information from the incoming packet
		#we wil end up with a pkt, a destination
		#mac address and a source mac address. 
		#all mac adresses are strings expressing hex in format 'xx:xx:xx:xx:xx:xx'	
		msg = ev.msg
		datapath = msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		in_port = msg.match['in_port']

		pkt = packet.Packet(msg.data)
		
		#let's try testing for arp packets
		#for p in pkt.protocols:
		#	print("protocol for packet # %d is: %s" % (self.packetCounter, p.protocol_name))
		eth = pkt.get_protocols(ethernet.ethernet)[0]	
		
		#if link layer discovery frame exit
		if eth.ethertype == ether_types.ETH_TYPE_LLDP:
			#ignore lldp packet
			return

		dst = eth.dst
		src = eth.src
			
		
		dpid = datapath.id
		
#		Add entry to controller's macaddress to port dictionary. 
#		remember this is a multidimensional dictionary where the first Key indicates the 
#		switch's DPID, then the next key indicates
		self.mac_to_port.setdefault(dpid, {})
		
		#print("packet in DPID:%s SRC:%s DST:%s IN_PORT:%s" % (dpid, src, dst, in_port))
			
		
		
		#if the source is not in our graph, let's 
		#	1. add it to graph
		#	2. add an edge between this switch and the src including the incoming port on destination node
		#	3. add reciprocal link
		
		if src not in self.net:
			print("src %s was not in network adding a link in graph between that and current switch, %s" %(src, dpid))
			self.net.add_node(src)
			self.net.add_edge(dpid, src, port=in_port)
			self.net.add_edge(src, dpid)

		

		#print("edges from 11")
		#print(self.net[11])	
#		if destination is not in the graph, we still want logic here for 
#		flooding in order to populate the network graph. 
#		however if the destination _is_ in the network use one of the algorithms to determine 
#		the path. 
#		
		if (dst in self.net):
			firstHalf = []
			secondHalf = []
			path = []
			next = -1
			#currentMBDPID = self.MBList[self.currentMBIndex]['dpid']
			
			#if we have not calculated all vm->mb-vm shortest paths already
			#calculate this one specific one. this might not even be necessary since 
			#we will use paths from the list eventually and we just need to 
			#make sure topo is fully represented
			if self.allPathsCalculated == False:
				try:
					self.fillShortestPathsForAllVMPairs()
				except Exception as e:
					"""cool stuff"""
					#print("filling all paths failed. exception: %s" % e)
				
				"""try:
					firstHalf = networkx.shortest_path(self.net, src, currentMBDPID)
					secondHalf = networkx.shortest_path(self.net, currentMBDPID, dst)[1:]
					path = firstHalf+secondHalf
				except Exception as e:
					print("finding single path failed. exception: %s" % e)"""
			else:
				
				#print("***ALL SHORTEST PATHS HOST->MB-HOST ARE CALCULATED***")
				#run appropriate MB selection algorithm to select correct MB for VMPair
				if self.allMBsSelected == False: 
					self.selectMBForAllVMPairs(self.algoChoice)
				#get shortest path from host->selectedmb->host
				VMPairIndexAndDirection = self.getPairIndexAndDirection(src, dst) 	
				pairIndex = VMPairIndexAndDirection[0]
				direction = VMPairIndexAndDirection[1] 
				MBIndex = -1
				for i in range(len(self.MBList)):
					if self.MBList[i]['dpid'] == self.VMPairList[pairIndex]['bestMBDPID']:
						MBIndex = i
				if MBIndex == -1:
				 	print("can't find appropriate MBIndex to determine best path. packetInHandler returning")
				 	return
				if pairIndex == -1:
					print("network only supports traffic between designated pairs. packetInHandler returning")
					return
				#still using pre-calculated vm->mb->vm path 
				#but if dst/src are flipped, then flip the path
				if direction == 'forward':
					#print('going forward')
					path = self.VMPairList[pairIndex]['shortestPaths'][MBIndex] 
				else:
					#print('going backward')
					path = self.VMPairList[pairIndex]['shortestPaths'][MBIndex][::-1] 
				#firstHalf = path[:path.index(currentMBDPID)+1]
				#secondHalf = path[path.index(currentMBDPID)+1:]
				
			#when determining the next hop in the shortest path from from vm0->mb->vm1
			#we will often have multiple instances of the same DPID switch
			# where, when encountering the second instance of the same switch, 
			# the next hop will be calculated from the first instance, causing a loop.
			#
			#within all paths in a fattree from vm->mb->vm we will encounter 3 possible cases:
			#	0 instances of a switch dpid 
			#		-return because current switch is not relevant to path
			#	1 instance of a switch dpid (no potential loop)
			#		-find first instance of current dpid in path and add 1 to index
			#	2 instances of a switch dpid (potential loop)
			#		-create a boolean switch for each src mac, dst mac, and dpid (eventually need to add
			#		one for each instance of MB also that checks whether that particular
			#		dpid has been seen before. 
			
			#
			
			if path.count(dpid) == 0:
				#print("current dpid %s not in path so packetInHandler returning" % dpid)
				return
			elif path.count(dpid) == 1:
				#print("current dpid %s is in path %s once. not accounting for loop"% (dpid, path))
				next = path[path.index(dpid)+1]
			elif path.count(dpid) == 2:
				#print("current dpid %s is in path %s twice accounting for loop" % (dpid, path))
				
				if src not in self.afterMB:
					self.afterMB[src] = {}
				if dst not in self.afterMB[src]:
					self.afterMB[src][dst] = {}
				if dpid not in self.afterMB[src][dst]:
					self.afterMB[src][dst][dpid] = False
				
				if self.afterMB[src][dst][dpid] == False:
					#print("beforeMB")
					next = path[path.index(dpid)+1]
					self.afterMB[src][dst][dpid] = True
				else:
					#print("afterMB")
					next = path[indexOfSecondInstance(dpid, path)+1]
					self.afterMB[src][dst][dpid] = False
				
			else:
				print("greater than 2 instances of DPID %s! ERROR. packetInHandler returning." %(dpid))
				return
			
			#IF DESTINATION IS IN THE GRAPH, ALWAYS END WITH THESE STEPS	
			out_port=self.net[dpid][next]['port']

			#THE MISSING LINE THAT FIXED EVERYTHING!
			if in_port == out_port:
				#print("but because in_port and out_port are equal, we will use special port ofproto.OFPP_IN_PORT")
				out_port = ofproto.OFPP_IN_PORT
			
			#print("PICKED NEXT in_port = %s, DPID: %s, next: %s, out_port: %s" %(in_port, dpid, next, out_port))
			actions = [parser.OFPActionOutput(out_port)]
			#print("SUCCESS! (DPID: %s)%s->MB(%s)->%s path found: %s " % (dpid, src, currentMBDPID, dst, path))				
		else:
			print("destination %s is not in graph. flooding." % dst)
			out_port = ofproto.OFPP_FLOOD
			actions = [parser.OFPActionOutput(out_port)]

		
		#if the outgoing port is not flood (meaning the destination is a mac address in digraph)
		#add a flow entry to bypass controller next time
		if out_port != ofproto.OFPP_FLOOD and self.allPathsCalculated == True and self.allMBsSelected == True:
			#print("ADDING FLOW: DPID: %s, MATCHING SRC: %s, DST: %s, in_port: %s, out_port: %s"% (dpid, src, dst, in_port, out_port))
			match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)
			
			#if we have valid buffer_id means the switch has buffered the packet
			# and is waiting for the controller to tell it where to send it
			
			#so if buffered, just add a flow entry and when switch gets to it, it will have entry
			#dont need to tell switch to send packet because rule will be added by the time it gets 
			#to packet
			
			if msg.buffer_id != ofproto.OFP_NO_BUFFER:
				self.add_flow(datapath, 1, match, actions, msg.buffer_id)
				print("returning at bufferIDpart")
				return
			#if the packet not buffered in switch that means it needs to know where to go, so 
			#we will add a flow entry but also send instructions to switch to send packet on 
			#to next port
			else:
				self.add_flow(datapath, 1, match, actions)
		#so we have decided if flooding, or known out_port and added any flow entries if known out_port.
		
		#ITHINK that the next part sets data to None in the case that this packet is buffered already
		#so we don't send it again.
		
		data = None
		if msg.buffer_id == ofproto.OFP_NO_BUFFER:
			data = msg.data

		out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port, actions=actions, data=data)
		datapath.send_msg(out)	

	#topology discovery. not sure when this event 
	#handler gets triggered. decorator says 'switch enter' is it any time a switch is added? I think so 
	#because i see it get added 20 times for the 4-ary fattree

	@set_ev_cls(event.EventSwitchEnter)
	
	def get_topology_data(self, ev):
		switch_list = get_switch(self, None)
		switches = [switch.dp.id for switch in switch_list]	
		#hosts = [get_host(self, switch.dp.id) for switch in switch_list]
		links_list = get_link(self, None)
		links = [(link.src.dpid, link.dst.dpid, {'port':link.src.port_no}) for link in links_list]
		
		#print("list of hosts. is this from single switch or global?")
		#print(hosts)
		#may need to specify the port number 
		#when adding hosts. so maybe
		#include a counter for each or 
		#use topology api like links above

		#hosts_list = get_host(self, None)	
		self.net.add_nodes_from(switches)
		self.net.add_edges_from(links)
		#test out the topology getter!
		#print("LIST OF SWITCHES")
		#print(switches)
		#print("LIST OF LINKS")
		#print(links)
		
