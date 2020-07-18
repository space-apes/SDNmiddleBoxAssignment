The OpenFlow protocol defines the interface between an OpenFlow Controller and an OpenFlow switch. 
The OpenFlow protocol allows the OpenFlow Controller to instruct the OpenFlow switch on how to handle incoming data packets.

The OpenFlow instructions transmitted from an OpenFlow Controller to an OpenFlow switch are structured as “flows”. 
Each individual flow contains packet match fields, flow priority, various counters, packet processing 
instructions, flow timeouts and a cookie. The flows are organized in tables. 
An incoming packet may be processed by flows in multiple “pipelined” tables before 
exiting on an egress port.


