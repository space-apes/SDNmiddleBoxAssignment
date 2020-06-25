import networkx

g = networkx.DiGraph()
g.add_nodes_from([1,2,3])

g.add_edge(1,2, port=1)
g.add_edge(1,3, port=2)
g.add_edge(2,1, port=1)
g.add_edge(2,3, port=2)
g.add_edge(3,1, port=1)
g.add_edge(3,2, port=2)
