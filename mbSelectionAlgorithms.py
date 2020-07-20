#*******IMPLEMENTATION OF 3 MIDDLEBOX SELECTION ALGORITHMS
#SIGNATURE: (listHostPairDicts, listMBDicts, intMaxMBLoad)->intTotalCost
#
#GOAL: 
#	-given a set of host pairs 
#	-given a set of switches designated as middleboxes
#	-given pre-calculated shortest paths in list form 
#		for each combination vm->mb->vm
#
#while minimizing the total cost (number of network hops)
#across all paths and balancing the load on each middle box and maintaining a load under the maximum for each MB,
#select and associate a middlebox for each host pair.
#
#eventually the final selections will be evaluated
#for total cost, total network latency, total network
#throughput capabilities
#
#
#MAIN DATASTRUCTURES (for reference):
#	1. list of host pairs, each a dict with the following form:
#                       {
#                               'vm0': '00:00:00:00:00:10', 
#                               'vm1': '00:00:00:00:00:03', 
#                               'bestMBDPID': -1,
#                               'shortestPaths': [[1,3,6,8],[2,5,3,7]]
#                       }
#	2. list of middleboxes, each a dict with the following form: 
#			{
#				'dpid': 7,
#				'load': 3
#			}
#
#
#MIDDLEBOX SELECTION ALGORITHM VARIANTS:
#	1. hostBasedMBSelection(): for each hostpair, iterate through middleboxes 
#		and assign middlebox that is not at max capacity to host pair with lowest cost
#	2. MBBasedMBSelection(): for each middlebox, iterate through unassigned host pairs 
#		and assign host pair with lowest cost each iteration until MB reaches capacity
#	3. hostAndMBBasedMBSelection(): iterate through all host/mb combinations, associating 
#		the lowest cost combination of unassigned host and non-maxed out MB each iteration
#
#################################################################################################################


import sys

#NAME: hostBasedMBSelection()
#SIGNATURE: (listHostPairDicts, listMBDicts, intMaxLoadPerMB)->intTotalCost
#DESCRIPTION:for each host pair, select nonMaxed MB with lowest cost
#PSEUDOCODE: 
#
#hostBasedMBSelection(hostPairList, MBList, maxLoadPerMB):
#	totalCost = 0
#	FOREACH pairIndex in hostPairList
#		leastExpensiveMBIndex = -1
#		leastExpensivePathCost = MAXVALUE	
#		FOREACH MBIndex in MBlist
#			IF MBList[MBIndex]['load'] < maxLoadPerMB and costOfPath < leastExpensivePathCost
#				leastExpensiveMBIndex = MBIndex
#				leastExpensivePathCost = costOfPath
#			End If
#		ENDFOR
#		MBList[leastExpensiveMBIndex].load +=1 
#		hostPairList[pairIndex]['BESTMBDPID'] = MBList[MBIndex]['dpid']
#		totalCost += leastExpensivePathCost
#	ENDFOR
#
#	RETURN totalCost

def hostBasedMBSelection(hostPairList, MBList, maxLoadPerMB):
	totalCost = 0
	for pairIndex in range(len(hostPairList)):
		leastExpensiveMBIndex = -1
		leastExpensivePathCost = sys.maxsize
		for MBIndex in range(len(MBList)):
			curPathCost = len(hostPairList[pairIndex]['shortestPaths'][MBIndex])
			if MBList[MBIndex]['load'] < maxLoadPerMB and curPathCost < leastExpensivePathCost:
				leastExpensiveMBIndex = MBIndex
				leastExpensivePathCost = curPathCost
		MBList[leastExpensiveMBIndex]['load'] +=1
		hostPairList[pairIndex]['bestMBDPID'] = MBList[leastExpensiveMBIndex]['dpid']
		totalCost += leastExpensivePathCost
	return totalCost

#NAME: MBBasedMBSelection()
#SIGNATURE: (listHostPairDicts, listMBDicts, intMaxLoadPerMB)->intTotalCost
#DESCRIPTION: for each MB until maxed out, assign unassigned host pair with lowest cost  
#PSEUDOCODE: 
#
#MBBasedMBSelection(hostPairList, MBList, maxLoadPerMB)
#	totalCost = 0
#	FOREACH MB
#		WHILE this.mb.load < maxLoadPerMB
#	  		leastExpensivePairIndex = -1
#			leastExpensivePathCost = MAXVALUE
#			FOREACH host pair 
#				if hostPair.mb != -1 AND curCost < leastExpensivePathCost 
#					leastExpensivePairIndex = curIndex
#					leastExpensivePathCost = curPathCost	  
#			
#			this.mb.load +=1 
#			leastExpensivePairIndex.mb = this.mb
#			totalCost += leastExpensivePathCost
#	return totalCost

def MBBasedMBSelection(hostPairList, MBList, maxLoadPerMB):
	totalCost = 0
	for MBIndex in range(len(MBList)):
		while MBList[MBIndex]['load'] < maxLoadPerMB:
			leastExpensivePairIndex = -1
			leastExpensivePathCost = sys.maxsize
			for pairIndex in range(len(hostPairList)):
				curPair = hostPairList[pairIndex]
				curPathCost = len(hostPairList[pairIndex]['shortestPaths'][MBIndex])
				if curPair['bestMBDPID'] == -1 and curPathCost < leastExpensivePathCost:
					leastExpensivePairIndex = pairIndex
					leastExpensivePathCost = curPathCost
			
			hostPairList[leastExpensivePairIndex]['bestMBDPID'] = MBList[MBIndex]['dpid']
			MBList[MBIndex]['load'] += 1
			totalCost += leastExpensivePathCost
	
	return totalCost

#NAME: hostAndMBBasedMBSelection()
#SIGNATURE: (listHostPairDicts, listMBDicts, intMaxLoadPerMB)->intTotalCost
#DESCRIPTION: until all host pairs have been assigned, cycle through all combinations of unassigned 
#	host pair and unmaxed MB in multiple passes. each pass, associate the mb and host pair 
#	that contributes the lowest cost.
#PSEUDOCODE: 
#
#hostAndMBBasedMBSelection(hostPairList, MBList, maxLoadPerMB):
#	totalCost = 0
#	pairsAssigned = 0
#	while pairsAssigned < len(hostPairList):
#		leastExpensivePairIndex = -1
#		leastExpensiveMBIndex = -1
#		leastExpensivePathCost = MAXVALUE
#		for pairIndex in hostPairList:
#			for mbIndex in MBlist: 
#				curCost = length(pairList[pairIndex]['shortestPaths'][MBIndex])
#				if pair is unassigned and mb is unmaxed and curCost < leastExpensivePathCost:
#					leastExpensivePairIndex = pairIndex
#					leastExpensiveMBIndex = MBIndex
#					leastExpensivePathCost = curCost
#		leastExpensivePair.mb = leastExpensiveMB
#		pairsAssigned += 1
#		leastExpensiveMB['load'] += 1
#		totalCost += leastExpensivePathCost
#	return totalCost
def hostAndMBBasedMBSelection(hostPairList, MBList, maxLoadPerMB):
	totalCost = 0
	pairsAssigned = 0
	while pairsAssigned < len(hostPairList):
		leastExpensivePairIndex = -1
		leastExpensiveMBIndex = -1
		leastExpensivePathCost = sys.maxsize
		for pairIndex in range(len(hostPairList)):
			for MBIndex in range(len(MBList)):
				curPair = hostPairList[pairIndex]
				curMB = MBList[MBIndex]
				curPathCost = len(curPair['shortestPaths'][MBIndex])
				if curPair['bestMBDPID'] == -1 and curMB['load'] < maxLoadPerMB and curPathCost < leastExpensivePathCost:
					leastExpensivePairIndex = pairIndex
					leastExpensiveMBIndex = MBIndex
					leastExpensivePathCost = curPathCost
		hostPairList[leastExpensivePairIndex]['bestMBDPID'] = MBList[leastExpensiveMBIndex]['dpid']
		MBList[leastExpensiveMBIndex]['load'] += 1
		pairsAssigned += 1
		totalCost += leastExpensivePathCost

	return totalCost


