"""i took existing k-ary topology from this gentleman, Howar31
-brian-

this one relies on OVSSwitch module which I don't understand 
as well as the spanning tree protocol to avoid loops.
I'd like to only use things I understand. 

i took out some of the open vswitch code and it should work with just the mininet module
"""

"""FatTree topology by Howar31
Configurable K-ary FatTree topology
Only edit K should work
OVS Bridge with Spanning Tree Protocol
Note: STP bridges don't start forwarding until
after STP has converged, which can take a while!
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import info, setLogLevel
from time import sleep
def startNetwork():
	setLogLevel('info')
	net = Mininet(topo = FatTree(), controller=RemoteController('c0'), autoSetMacs=True, autoStaticArp=True)
	net.start()
	print("please start controller in next 10 seconds")	
	sleep(10)
	for node in net:
		if node[0] == 'h':
			hostNum = node[1:]
			if hostNum == '1':
				info (net[node].cmd('ping -c 1 -w 1 10.0.0.2'))
			else:
				info (net[node].cmd('ping -c 1 -w 1 10.0.0.'+str(int(hostNum)-1)))	
	#CLI(net, script = "allPingOnce.sh")
	CLI(net)
	net.stop()

class FatTree( Topo ):

    def __init__( self ):

        # Topology settings
        K = 4                           # K-ary FatTree
        podNum = K                      # Pod number in FatTree
        coreSwitchNum = pow((K/2),2)    # Core switches 
        aggrSwitchNum = ((K/2)*K)       # Aggregation switches
        edgeSwitchNum = ((K/2)*K)       # Edge switches
        hostNum = (K*pow((K/2),2))      # Hosts in K-ary FatTree

        # Initialize topology
        Topo.__init__( self )

        coreSwitches = []
        aggrSwitches = []
        edgeSwitches = []
	switchCount = 1
	hostCount = 1

        # Core
	for core in range(0, coreSwitchNum):
		coreSwitches.append(self.addSwitch("s"+str(switchCount), protocols='OpenFlow13'))
		switchCount += 1
        # Pod
        for pod in range(0, podNum):
        # Aggregate
            for aggr in range(0, aggrSwitchNum/podNum):
                aggrThis = self.addSwitch("s"+str(switchCount), protocols='OpenFlow13')
		switchCount+=1
                aggrSwitches.append(aggrThis)
                for x in range((K/2)*aggr, (K/2)*(aggr+1)):
#                    self.addLink(aggrSwitches[aggr+(aggrSwitchNum/podNum*pod)], coreSwitches[x])
                    self.addLink(aggrThis, coreSwitches[x])
        # Edge
            for edge in range(0, edgeSwitchNum/podNum):
                edgeThis = self.addSwitch("s"+str(switchCount), protocols='OpenFlow13')
		switchCount+=1
                edgeSwitches.append(edgeThis)
                for x in range((edgeSwitchNum/podNum)*pod, ((edgeSwitchNum/podNum)*(pod+1))):
                    self.addLink(edgeThis, aggrSwitches[x])
        # Host
                for x in range(0, (hostNum/podNum/(edgeSwitchNum/podNum))):
                    self.addLink(edgeThis, self.addHost("h"+str(hostCount) ))
		    hostCount+=1


if __name__ == '__main__':
	startNetwork()
