def hToMac(hostInt):
	hexy = hex(hostInt).lstrip("00x")
	if len(hexy) == 1:
		hexy = '0'+hexy
	return '00:00:00:00:00:'+hexy
def MACToH(hostMAC):
	return "h"+str(int(hostMAC[-1], 16))
def indexOfSecondInstance(val, inList):
	count = 0 
	for x in range(len(inList)):
		if inList[x] == val:
			count+=1
		if count == 2:
			return x
	print("no second instance of %s in %s" % (val, inList))
	return -1
