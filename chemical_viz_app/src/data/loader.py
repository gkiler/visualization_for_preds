import pandas as pd
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import streamlit as st
import networkx as nx
from .models import ChemicalNetwork, ChemicalNode, ChemicalEdge, NodeType, EdgeType


class DataLoader:
    
    @staticmethod
    def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def load_network_from_csv(
        nodes_file: Union[str, Path], 
        edges_file: Union[str, Path],
        node_id_col: str = "id",
        node_label_col: str = "label",
        node_type_col: str = "type",
        edge_source_col: str = "source",
        edge_target_col: str = "target",
        edge_type_col: str = "type"
    ) -> ChemicalNetwork:
        nodes_df = pd.read_csv(nodes_file)
        edges_df = pd.read_csv(edges_file)
        
        nodes_df = nodes_df.rename(columns={
            node_id_col: "id",
            node_label_col: "label",
            node_type_col: "type"
        })
        
        edges_df = edges_df.rename(columns={
            edge_source_col: "source",
            edge_target_col: "target",
            edge_type_col: "type"
        })
        
        return ChemicalNetwork.from_dataframes(nodes_df, edges_df)
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def load_network_from_graphml(file_path: Union[str, Path]) -> ChemicalNetwork:
        # Read GraphML file using NetworkX
        G = nx.read_graphml(file_path)
        
        # Load config to check if isolated nodes should be removed
        config = DataLoader.load_config()
        graphml_config = config.get("data", {}).get("graphml", {})
        remove_isolated = graphml_config.get("remove_isolated_nodes", True)
        
        initial_node_count = G.number_of_nodes()
        isolated_nodes = []
        
        # Remove isolated nodes (nodes with no edges) if configured
        if remove_isolated:
            isolated_nodes = [node for node, degree in G.degree() if degree == 0]
            G.remove_nodes_from(isolated_nodes)
            
            if isolated_nodes:
                print(f"Removed {len(isolated_nodes)} isolated nodes from GraphML network "
                      f"(reduced from {initial_node_count} to {G.number_of_nodes()} nodes)")
        
        network = ChemicalNetwork(
            metadata={
                "source": "GraphML",
                "directed": G.is_directed(),
                "multigraph": G.is_multigraph(),
                "initial_node_count": initial_node_count,
                "isolated_nodes_removed": len(isolated_nodes)
            }
        )
        
        # Convert nodes
        for node_id, node_data in G.nodes(data=True):
            # Extract type if available
            node_type_str = node_data.pop('type', 'other').lower()
            try:
                node_type = NodeType(node_type_str)
            except ValueError:
                node_type = NodeType.OTHER
            
            # Use label if available, otherwise use node_id
            label = node_data.pop('label', str(node_id))
            
            # Extract standard attributes
            x = node_data.pop('x', None)
            y = node_data.pop('y', None)
            size = node_data.pop('size', None)
            color = node_data.pop('color', None)
            
            # All remaining attributes go to properties
            properties = {}
            for key, value in node_data.items():
                # Convert numeric strings to appropriate types with better error handling
                if isinstance(value, str) and value.strip():
                    try:
                        # Only convert if the string looks clearly numeric
                        stripped_value = value.strip()
                        # Check if it's a valid number using a more robust method
                        try:
                            float(stripped_value)  # Test if it can be converted
                            if '.' in stripped_value or 'e' in stripped_value.lower():
                                properties[key] = float(stripped_value)
                            else:
                                properties[key] = int(stripped_value)
                        except ValueError:
                            # Keep as string if it doesn't look clearly numeric
                            properties[key] = stripped_value
                    except (ValueError, OverflowError):
                        # Keep as string if conversion fails
                        properties[key] = value.strip() if isinstance(value, str) else value
                elif value is None or (isinstance(value, str) and not value.strip()):
                    # Handle empty/null values consistently
                    properties[key] = ""
                else:
                    properties[key] = value
            
            node = ChemicalNode(
                id=str(node_id),
                label=label,
                node_type=node_type,
                properties=properties,
                x=x,
                y=y,
                size=size,
                color=color
            )
            network.add_node(node)
        
        # Convert edges
        for source, target, edge_data in G.edges(data=True):
            # Handle multigraph edge keys
            if G.is_multigraph():
                edge_data = edge_data.copy()
                edge_data.pop('key', None)
            
            # Extract type if available
            edge_type_str = edge_data.pop('type', 'other').lower()
            try:
                edge_type = EdgeType(edge_type_str)
            except ValueError:
                edge_type = EdgeType.OTHER
            
            # Extract standard attributes
            weight = edge_data.pop('weight', 1.0)
            if isinstance(weight, str):
                try:
                    weight = float(weight)
                except ValueError:
                    weight = 1.0
            
            color = edge_data.pop('color', None)
            width = edge_data.pop('width', None)
            if width and isinstance(width, str):
                try:
                    width = float(width)
                except ValueError:
                    width = None
            
            # All remaining attributes go to properties
            properties = {}
            for key, value in edge_data.items():
                # Convert numeric strings to appropriate types with better error handling
                if isinstance(value, str) and value.strip():
                    try:
                        # Only convert if the string looks clearly numeric
                        stripped_value = value.strip()
                        # Check if it's a valid number using a more robust method
                        try:
                            float(stripped_value)  # Test if it can be converted
                            if '.' in stripped_value or 'e' in stripped_value.lower():
                                properties[key] = float(stripped_value)
                            else:
                                properties[key] = int(stripped_value)
                        except ValueError:
                            # Keep as string if it doesn't look clearly numeric
                            properties[key] = stripped_value
                    except (ValueError, OverflowError):
                        # Keep as string if conversion fails
                        properties[key] = value.strip() if isinstance(value, str) else value
                elif value is None or (isinstance(value, str) and not value.strip()):
                    # Handle empty/null values consistently
                    properties[key] = ""
                else:
                    properties[key] = value
            
            edge = ChemicalEdge(
                source=str(source),
                target=str(target),
                edge_type=edge_type,
                properties=properties,
                weight=weight,
                color=color,
                width=width
            )
            network.add_edge(edge)
        
        return network
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def load_network_from_json(file_path: Union[str, Path]) -> ChemicalNetwork:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        network = ChemicalNetwork(metadata=data.get("metadata", {}))
        
        for node_data in data.get("nodes", []):
            node = ChemicalNode.from_dict(node_data)
            network.add_node(node)
        
        for edge_data in data.get("edges", []):
            edge = ChemicalEdge.from_dict(edge_data)
            network.add_edge(edge)
        
        return network
    
    @staticmethod
    def create_sample_network() -> ChemicalNetwork:
        network = ChemicalNetwork(
            metadata={"name": "Sample Chemical Network", "version": "1.0"}
        )
        
        nodes = [
            ChemicalNode("mol1", "Molecule A", NodeType.MOLECULE, 
                        {"formula": "C6H12O6", "weight": 180.16}),
            ChemicalNode("mol2", "Molecule B", NodeType.MOLECULE, 
                        {"formula": "C12H22O11", "weight": 342.30}),
            ChemicalNode("prot1", "Protein X", NodeType.PROTEIN, 
                        {"length": 450, "function": "enzyme"}),
            ChemicalNode("prot2", "Protein Y", NodeType.PROTEIN, 
                        {"length": 320, "function": "receptor"}),
            ChemicalNode("rxn1", "Reaction 1", NodeType.REACTION, 
                        {"rate": 0.5, "reversible": True}),
            ChemicalNode("path1", "Pathway Alpha", NodeType.PATHWAY, 
                        {"components": 5})
        ]
        
        edges = [
            ChemicalEdge("mol1", "prot1", EdgeType.BINDING, 
                        {"affinity": 0.8}),
            ChemicalEdge("mol2", "prot2", EdgeType.BINDING, 
                        {"affinity": 0.6}),
            ChemicalEdge("prot1", "rxn1", EdgeType.ACTIVATION, 
                        {"strength": 0.9}),
            ChemicalEdge("prot2", "rxn1", EdgeType.INHIBITION, 
                        {"strength": 0.7}),
            ChemicalEdge("rxn1", "path1", EdgeType.INTERACTION, 
                        {"importance": 0.85}),
            ChemicalEdge("mol1", "mol2", EdgeType.INTERACTION, 
                        {"type": "conversion"})
        ]
        
        for node in nodes:
            network.add_node(node)
        
        for edge in edges:
            network.add_edge(edge)
        
        return network
    
    @staticmethod
    def validate_network(network: ChemicalNetwork) -> tuple[bool, list[str]]:
        errors = []
        
        node_ids = {node.id for node in network.nodes}
        
        if len(node_ids) != len(network.nodes):
            errors.append("Duplicate node IDs found")
        
        for edge in network.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge source '{edge.source}' not found in nodes")
            if edge.target not in node_ids:
                errors.append(f"Edge target '{edge.target}' not found in nodes")
        
        config = DataLoader.load_config()
        data_config = config.get("data", {})
        max_nodes = data_config.get("max_nodes", 1000)
        max_edges = data_config.get("max_edges", 5000)
        
        # Check if this is a GraphML file with unlimited nodes enabled
        source_type = network.metadata.get("source", "").lower()
        graphml_config = data_config.get("graphml", {})
        unlimited_nodes = graphml_config.get("unlimited_nodes", False)
        
        # Apply node limit only if not GraphML or if GraphML doesn't have unlimited nodes
        if not (source_type == "graphml" and unlimited_nodes):
            if len(network.nodes) > max_nodes:
                errors.append(f"Network has {len(network.nodes)} nodes, exceeds limit of {max_nodes}")
        
        if len(network.edges) > max_edges:
            errors.append(f"Network has {len(network.edges)} edges, exceeds limit of {max_edges}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def export_network_to_graphml(
        network: ChemicalNetwork, 
        file_path: Union[str, Path],
        prettify: bool = True
    ) -> None:
        # Create NetworkX graph
        if network.metadata.get("directed", True):
            G = nx.DiGraph()
        else:
            G = nx.Graph()
        
        # Add nodes with attributes
        for node in network.nodes:
            node_attrs = {
                'type': node.node_type.value,
                'label': node.label
            }
            
            # Add optional attributes if they exist
            if node.x is not None:
                node_attrs['x'] = node.x
            if node.y is not None:
                node_attrs['y'] = node.y
            if node.size is not None:
                node_attrs['size'] = node.size
            if node.color is not None:
                node_attrs['color'] = node.color
            
            # Add all properties
            node_attrs.update(node.properties)
            
            G.add_node(node.id, **node_attrs)
        
        # Add edges with attributes
        for edge in network.edges:
            edge_attrs = {
                'type': edge.edge_type.value,
                'weight': edge.weight
            }
            
            # Add optional attributes if they exist
            if edge.color is not None:
                edge_attrs['color'] = edge.color
            if edge.width is not None:
                edge_attrs['width'] = edge.width
            
            # Add all properties
            edge_attrs.update(edge.properties)
            
            G.add_edge(edge.source, edge.target, **edge_attrs)
        
        # Write GraphML file
        nx.write_graphml(G, file_path, prettyprint=prettify, infer_numeric_types=True)