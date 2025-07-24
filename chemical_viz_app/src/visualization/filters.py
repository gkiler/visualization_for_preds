from typing import Dict, List, Any, Callable, Optional, Set, Tuple
from ..data.models import ChemicalNetwork, ChemicalNode, ChemicalEdge, NodeType, EdgeType
import operator


class NetworkFilter:
    
    def __init__(self):
        self.operators = {
            '==': operator.eq,
            '!=': operator.ne,
            '>': operator.gt,
            '>=': operator.ge,
            '<': operator.lt,
            '<=': operator.le,
            'in': lambda x, y: x in y,
            'not in': lambda x, y: x not in y,
            'contains': lambda x, y: y in str(x),
            'not contains': lambda x, y: y not in str(x)
        }
    
    def create_property_filter(
        self, 
        property_name: str, 
        operator_str: str, 
        value: Any
    ) -> Callable:
        op = self.operators.get(operator_str, operator.eq)
        
        def filter_func(item):
            if hasattr(item, 'properties') and property_name in item.properties:
                item_value = item.properties[property_name]
                try:
                    if operator_str in ['>', '>=', '<', '<=']:
                        return op(float(item_value), float(value))
                    return op(item_value, value)
                except (TypeError, ValueError):
                    return False
            return False
        
        return filter_func
    
    def filter_nodes_by_type(
        self, 
        network: ChemicalNetwork, 
        node_types: List[NodeType]
    ) -> List[ChemicalNode]:
        return [node for node in network.nodes if node.node_type in node_types]
    
    def filter_edges_by_type(
        self, 
        network: ChemicalNetwork, 
        edge_types: List[EdgeType]
    ) -> List[ChemicalEdge]:
        return [edge for edge in network.edges if edge.edge_type in edge_types]
    
    def filter_nodes_by_property(
        self, 
        network: ChemicalNetwork, 
        property_name: str, 
        operator_str: str, 
        value: Any
    ) -> List[ChemicalNode]:
        filter_func = self.create_property_filter(property_name, operator_str, value)
        return network.filter_nodes(filter_func)
    
    def filter_edges_by_property(
        self, 
        network: ChemicalNetwork, 
        property_name: str, 
        operator_str: str, 
        value: Any
    ) -> List[ChemicalEdge]:
        filter_func = self.create_property_filter(property_name, operator_str, value)
        return network.filter_edges(filter_func)
    
    def filter_nodes_by_connectivity(
        self,
        network: ChemicalNetwork,
        min_connections: Optional[int] = None,
        max_connections: Optional[int] = None
    ) -> List[ChemicalNode]:
        node_connections = {}
        
        for edge in network.edges:
            node_connections[edge.source] = node_connections.get(edge.source, 0) + 1
            node_connections[edge.target] = node_connections.get(edge.target, 0) + 1
        
        filtered_nodes = []
        for node in network.nodes:
            connections = node_connections.get(node.id, 0)
            
            if min_connections is not None and connections < min_connections:
                continue
            if max_connections is not None and connections > max_connections:
                continue
            
            filtered_nodes.append(node)
        
        return filtered_nodes
    
    def filter_connected_component(
        self,
        network: ChemicalNetwork,
        start_node_ids: List[str],
        max_depth: int = 2
    ) -> Tuple[List[ChemicalNode], List[ChemicalEdge]]:
        if max_depth < 1:
            return [], []
        
        visited_nodes = set(start_node_ids)
        nodes_to_process = list(start_node_ids)
        current_depth = 0
        
        while current_depth < max_depth and nodes_to_process:
            next_nodes = []
            
            for node_id in nodes_to_process:
                for edge in network.edges:
                    if edge.source == node_id and edge.target not in visited_nodes:
                        visited_nodes.add(edge.target)
                        next_nodes.append(edge.target)
                    elif edge.target == node_id and edge.source not in visited_nodes:
                        visited_nodes.add(edge.source)
                        next_nodes.append(edge.source)
            
            nodes_to_process = next_nodes
            current_depth += 1
        
        filtered_nodes = [
            node for node in network.nodes 
            if node.id in visited_nodes
        ]
        
        filtered_edges = [
            edge for edge in network.edges
            if edge.source in visited_nodes and edge.target in visited_nodes
        ]
        
        return filtered_nodes, filtered_edges
    
    def filter_nodes_connected_to_library_smiles_with_con(
        self,
        network: ChemicalNetwork,
        target_letters: List[str] = ["C", "O", "N"]
    ) -> Tuple[List[ChemicalNode], List[ChemicalEdge]]:
        """Filter nodes that are connected to nodes with library_SMILES containing specified letters."""
        # Find nodes with library_SMILES containing target letters
        target_node_ids = set()
        for node in network.nodes:
            if "library_SMILES" in node.properties:
                smiles = str(node.properties["library_SMILES"])
                if any(letter in smiles for letter in target_letters):
                    target_node_ids.add(node.id)
        
        # Find all nodes connected to target nodes
        connected_node_ids = set(target_node_ids)  # Include the target nodes themselves
        for edge in network.edges:
            if edge.source in target_node_ids:
                connected_node_ids.add(edge.target)
            if edge.target in target_node_ids:
                connected_node_ids.add(edge.source)
        
        # Filter nodes and edges
        filtered_nodes = [
            node for node in network.nodes 
            if node.id in connected_node_ids
        ]
        
        filtered_edges = [
            edge for edge in network.edges
            if edge.source in connected_node_ids and edge.target in connected_node_ids
        ]
        
        return filtered_nodes, filtered_edges
    
    def filter_edges_by_molecular_networking(
        self,
        network: ChemicalNetwork,
        molecular_networking_enabled: bool = True,
        edit_distance_enabled: bool = True
    ) -> List[ChemicalEdge]:
        """Filter edges based on molecular networking property values."""
        if not molecular_networking_enabled and not edit_distance_enabled:
            return []  # No edges should be shown
        
        if molecular_networking_enabled and edit_distance_enabled:
            return list(network.edges)  # Show all edges
        
        filtered_edges = []
        for edge in network.edges:
            if "molecular_networking" in edge.properties:
                try:
                    mol_net_value = int(edge.properties["molecular_networking"])
                    if molecular_networking_enabled and mol_net_value == 1:
                        filtered_edges.append(edge)
                    elif edit_distance_enabled and mol_net_value == 0:
                        filtered_edges.append(edge)
                except (ValueError, TypeError):
                    # If we can't parse the value, include the edge
                    filtered_edges.append(edge)
            else:
                # If no molecular_networking property, include the edge
                filtered_edges.append(edge)
        
        return filtered_edges
    
    def apply_multiple_filters(
        self,
        network: ChemicalNetwork,
        node_filters: Optional[List[Dict[str, Any]]] = None,
        edge_filters: Optional[List[Dict[str, Any]]] = None,
        filter_mode: str = "AND"
    ) -> Tuple[List[ChemicalNode], List[ChemicalEdge]]:
        filtered_nodes = list(network.nodes)
        filtered_edges = list(network.edges)
        
        if node_filters:
            if filter_mode == "AND":
                for filter_spec in node_filters:
                    if filter_spec['type'] == 'node_type':
                        filtered_nodes = [
                            n for n in filtered_nodes 
                            if n.node_type in filter_spec['values']
                        ]
                    elif filter_spec['type'] == 'property':
                        temp_network = ChemicalNetwork(nodes=filtered_nodes)
                        filtered_nodes = self.filter_nodes_by_property(
                            temp_network,
                            filter_spec['property'],
                            filter_spec['operator'],
                            filter_spec['value']
                        )
                    elif filter_spec['type'] == 'connectivity':
                        temp_network = ChemicalNetwork(
                            nodes=filtered_nodes, 
                            edges=network.edges
                        )
                        filtered_nodes = self.filter_nodes_by_connectivity(
                            temp_network,
                            filter_spec.get('min_connections'),
                            filter_spec.get('max_connections')
                        )
            else:  # OR mode
                all_filtered_nodes = set()
                for filter_spec in node_filters:
                    if filter_spec['type'] == 'node_type':
                        nodes = self.filter_nodes_by_type(
                            network, 
                            filter_spec['values']
                        )
                    elif filter_spec['type'] == 'property':
                        nodes = self.filter_nodes_by_property(
                            network,
                            filter_spec['property'],
                            filter_spec['operator'],
                            filter_spec['value']
                        )
                    elif filter_spec['type'] == 'connectivity':
                        nodes = self.filter_nodes_by_connectivity(
                            network,
                            filter_spec.get('min_connections'),
                            filter_spec.get('max_connections')
                        )
                    all_filtered_nodes.update(n.id for n in nodes)
                
                filtered_nodes = [
                    n for n in network.nodes 
                    if n.id in all_filtered_nodes
                ]
        
        node_ids = {n.id for n in filtered_nodes}
        filtered_edges = [
            e for e in filtered_edges
            if e.source in node_ids and e.target in node_ids
        ]
        
        if edge_filters:
            temp_edges = filtered_edges if filter_mode == "AND" else list(network.edges)
            
            if filter_mode == "AND":
                for filter_spec in edge_filters:
                    if filter_spec['type'] == 'edge_type':
                        filtered_edges = [
                            e for e in filtered_edges 
                            if e.edge_type in filter_spec['values']
                        ]
                    elif filter_spec['type'] == 'property':
                        temp_network = ChemicalNetwork(edges=filtered_edges)
                        filtered_edges = self.filter_edges_by_property(
                            temp_network,
                            filter_spec['property'],
                            filter_spec['operator'],
                            filter_spec['value']
                        )
            else:  # OR mode
                all_filtered_edges = set()
                for filter_spec in edge_filters:
                    if filter_spec['type'] == 'edge_type':
                        edges = self.filter_edges_by_type(
                            network, 
                            filter_spec['values']
                        )
                    elif filter_spec['type'] == 'property':
                        edges = self.filter_edges_by_property(
                            network,
                            filter_spec['property'],
                            filter_spec['operator'],
                            filter_spec['value']
                        )
                    all_filtered_edges.update(
                        (e.source, e.target) for e in edges
                    )
                
                filtered_edges = [
                    e for e in network.edges 
                    if (e.source, e.target) in all_filtered_edges
                ]
            
            filtered_edges = [
                e for e in filtered_edges
                if e.source in node_ids and e.target in node_ids
            ]
        
        return filtered_nodes, filtered_edges