from abc import ABC, abstractmethod
import networkx as nx
import numpy as np
import igraph as ig
from scipy.sparse import diags, coo_matrix

def igraph_adj_matrix(G, weighted=False): 
    length = len(G.es) 
    row_index, col_index = np.empty(length), np.empty(length)

    for ind, e in enumerate(G.es): 
        row_index[ind], col_index[ind] = e.tuple

    if weighted:
        if weighted not in G.es.attributes(): 
            raise ValueError("weighted argument not in graph edge attributes!")

        vals = G.es[weighted]

    else: 
        vals = np.ones(length)

    n_nodes = len(G.vs)

    adj = coo_matrix((vals, (row_index, col_index)), shape=(n_nodes, n_nodes))

    if not G.is_directed(): 
        adj += adj.T

    return adj


class Network(ABC): 
    """Base class for all network classes to inherit from
    
    This base class defines interfacing functionalities that 
    Nbgwas expects. 
    """

    def __init__(self, network, node_name = "name"): 
        self.network = network 
        self.node_name = node_name 
        super().__init__() 

    @abstractmethod
    def add_adjacency_matrix(self): 
        pass 

    @abstractmethod
    def add_laplacian_matrix(self): 
        pass 

    @abstractmethod
    def subgraph(self):
        pass 

    @abstractmethod
    def get_node_attributes(self): 
        pass

    @abstractmethod 
    def set_node_attributes(self, attr_map): 
        """set node attributes 

        attr_map is a dictionary of dictionaries"""

        pass 

    #TODO: add gene name conversion function


class NxNetwork(Network): 
    """Internal object to expose networkx functionalities"""

    def __init__(self, network, node_name="name"): 
        super().__init__(network, node_name=node_name)

        if network is not None:
            nodes = self.network.node.keys() 

            self.node_names = [
                self.network.node[n].get(self.node_name, n) \
                    for n in self.network.nodes()
            ]

            self.node_2_name = dict(zip(nodes, self.node_names))
            self.name_2_node = dict(zip(self.node_names, nodes))

        else: 
            self.node_names = None

    def add_adjacency_matrix(self, weights=None): 
        self.adjacency_matrix = nx.adjacency_matrix(
            self.network, weight=weights
        )

        return self

    def add_laplacian_matrix(self, weights=None): 
        self.laplacian = nx.laplacian_matrix(self.network, weight=weights)

        return self  

    def subgraph(self, node_ids=None, node_names=None): 
        if node_names is not None and node_ids is not None: 
            raise ValueError("Expected either node_names or node_ids. Both given.")

        elif node_names is not None: 
            node_ids = [self.node_2_name[n] for n in node_names]

        return self.network.subgraph(node_ids)

    def get_node_attributes(self): 
        return self.network.node

    def set_node_attributes(self, attr_map, namespace="nodenames"):
        for attr_name, d in attr_map.items():  
            if namespace == "nodenames": 
                d = {self.name_2_node[k]:v for k, v in d.items() if k in self.name_2_node}

            nx.set_node_attributes(
                self.network, 
                attr_name, 
                d
            )

        return self


class IgNetwork(Network): 
    """Internal object to expose igraph functionalities"""

    def __init__(self, network, node_name="name"): 
        super().__init__(network, node_name=node_name) 

        if network is not None: 
            nodes = [v.index for v in self.network.vs]
            if self.node_name in self.network.vs.attributes(): 
                self.node_names = self.network.vs[self.node_name]
            else: 
                self.node_names = nodes
            
            self.node_2_name = dict(zip(nodes, self.node_names))
            self.name_2_node = dict(zip(self.node_names, nodes))

        else: 
            self.node_names = None

    def add_adjacency_matrix(self, weights=None): 
        self.adjacency_matrix = igraph_adj_matrix(
            self.network, weighted=weights)

        return self

    def add_laplacian_matrix(self, weights=None): 
        if not hasattr(self, "adjacency_matrix"): 
            self.add_adjacency_matrix(weights=weights)

        D = diags(self.adjacency_matrix.sum(axis=1))
        
        #TODO: Need to test this functionality against networkx
        self.laplacian = D - self.adjacency_matrix

        return self
    
    def subgraph(self, node_ids=None, node_names=None): 
        if node_names is not None and node_ids is not None: 
            raise ValueError("Expected either node_names or node_ids. Both given.")

        elif node_names is not None: 
            node_ids = [self.node_2_name[n] for n in node_names]

        return self.network.subgraph(node_ids)

    def get_node_attributes(self): 
        attr = {}
        for a in self.network.attributes():  
            attr[a] = dict([(i.index, i.attributes()) for i in G.vs])

        return attr

    def set_node_attributes(self, attr_map, namespace="nodenames"): 
        for attr_name, d in attr_map.items():
            attr = [None]*len(self.network.vs)
            for ind, v in enumerate(self.network.vs): 
                if namespace == "nodenames": 
                    attr[ind] = d[v[self.node_name]]

                elif namespace == "nodeids": 
                    attr[ind] = d[v.index] 

                else: 
                    raise ValueError("namespace must be nodenames or nodeids")

            self.network.vs[attr_name] = attr

        return self