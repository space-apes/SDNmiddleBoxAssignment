***VM-BASED
*cycles through vms and greedily selects MB if it has lowest cost and load is not met

need shortest paths for all vm-mb-vm combos
totalCost = 0
FOREACH VMPair P
	initialize shortestPathCostSoFar = infinity
	FOREACH MB M
		if this vm-mb-vm.path.cost < shortestPathCostSoFar AND thisMB.load +1 <= thisMB.maxLoad 
			P.path = this.vm-mb-vm.path
			P.MB = M
	ENDMBFOR
	load(P.MB)++
	totalCost += p.path.length
ENDFOR
return totalCost


***MB-BASED
*cycles through MBS greedily assigning unassigned pairs to MBs based on lowest cost each iteration

calculate paths and costs for each VMpair/MB combination
bool VMassigned = []
int totalCost = 0
FOREACH MB M
	vmPairsAssignedToM = []
	FOREACH VMPair P
		IF assignedAtAll[P] == false
			vmPairsAssignedToM += P
			assignedAtAll[P] = true
		ENDIF
	ENDFOR
	sortByCost(vmPairsAssignedToM)
	FOREACH unit of load in M
		MB.pair = vmPairsAssignedToM[x+1]
		totalCost += vmPairsAssignedToM[x+1]
	ENDFOR
ENDFOR
Return totalCost
			
***VM-MB BASED
*does multiple passes through each VM and MB combination, sets MB/VM combo with lowest cost each round

bool VMassigned = []
int totalCost = 0
int assignedCount = 0
FOREACH VMPair P
	VMassigned[P] = false
ENDFOR

WHILE(assignedCount < VMPairCount)
	int lowstCost = infinity
	FOREACH VMPair P
		IF (VMassigned[P] == false)
			FOREACH MB M
				IF (load(M) < loadMax(M) AND cost(P, M) < currentCost)
					lowestCost = cost (P,M)
					lowestPair  = P
					lowestMB = M
				ENDIF
			ENDFOR
		ENDIF


	ENDFOR
	VMAssigned[lowestPair] = true
	lowestMB.pair = lowestPair
	load(lowestMB)++
	totalCost +=currentCost
ENDWHILE

Return totalCost



