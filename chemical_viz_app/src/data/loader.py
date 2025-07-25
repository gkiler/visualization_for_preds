import pandas as pd
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import streamlit as st
import networkx as nx
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote
from .models import ChemicalNetwork, ChemicalNode, ChemicalEdge, NodeType, EdgeType
from ..utils.mass_decomposition import create_mass_decomposer, MassDecompositionConfig


class DataLoader:
    
    @staticmethod
    def _process_mass_decomposition(network: ChemicalNetwork, config: Dict[str, Any]) -> ChemicalNetwork:
        """
        Process mass decomposition for edges with delta_mz values.
        
        Args:
            network: The chemical network to process
            config: Configuration dictionary
            
        Returns:
            Network with formula annotations added to edge properties
        """
        mass_config = config.get("mass_decomposition", {})
        
        # Check if mass decomposition is enabled
        if not mass_config.get("enabled", True):
            return network
        
        # Create mass decomposer with configuration
        decomp_config = {
            'tolerance_ppm': mass_config.get('tolerance_ppm', 5.0),
            'tolerance_da': mass_config.get('tolerance_da', 0.003),
            'max_formulas': mass_config.get('max_formulas', 10),
            'apply_golden_rules': mass_config.get('apply_golden_rules', True),
            'cache_enabled': mass_config.get('cache_enabled', True)
        }
        
        # Convert element ranges from config format to tuple format
        if 'elements' in mass_config:
            elements = {}
            for element, range_list in mass_config['elements'].items():
                if isinstance(range_list, list) and len(range_list) == 2:
                    elements[element] = tuple(range_list)
            decomp_config['elements'] = elements
        
        try:
            decomposer = create_mass_decomposer(decomp_config)
            
            # Check if decomposition libraries are available
            available, libs = decomposer.is_available()
            if not available:
                print("Warning: No mass decomposition libraries available (emzed, msbuddy, molmass)")
                return network
            
            print(f"Mass decomposition using libraries: {', '.join(libs)}")
            
            # Process edges in batches for performance
            batch_size = mass_config.get('batch_size', 100)
            show_progress = mass_config.get('show_progress', True)
            skip_threshold = mass_config.get('skip_small_masses', 0.1)
            
            processed_count = 0
            skipped_count = 0
            total_edges = len(network.edges)
            
            if show_progress and hasattr(st, 'progress'):
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            for i, edge in enumerate(network.edges):
                # Update progress
                if show_progress and hasattr(st, 'progress') and i % 10 == 0:
                    progress = i / total_edges
                    progress_bar.progress(progress)
                    status_text.text(f"Processing mass decomposition: {i}/{total_edges} edges")
                
                # Check for delta_mz in edge properties
                delta_mz = None
                for key in ['delta_mz', 'deltamz', 'mass_diff', 'mass_difference']:
                    if key in edge.properties:
                        try:
                            delta_mz = float(edge.properties[key])
                            break
                        except (ValueError, TypeError):
                            continue
                
                if delta_mz is None or delta_mz < skip_threshold:
                    skipped_count += 1
                    continue
                
                # Decompose the mass difference
                try:
                    formula_candidates = decomposer.decompose_mass(delta_mz)
                    
                    if formula_candidates:
                        # Store formula candidates in edge properties
                        edge.properties['formula_candidates'] = [
                            candidate.to_dict() for candidate in formula_candidates
                        ]
                        
                        # Store the best candidate as the primary formula
                        best_candidate = formula_candidates[0]
                        edge.properties['primary_formula'] = best_candidate.formula
                        edge.properties['formula_mass_error_ppm'] = best_candidate.mass_error_ppm
                        edge.properties['formula_confidence'] = best_candidate.confidence_score
                        
                        processed_count += 1
                    
                except Exception as e:
                    print(f"Error processing mass decomposition for edge {edge.source}-{edge.target}: {e}")
                    continue
            
            # Clear progress indicators
            if show_progress and hasattr(st, 'progress'):
                progress_bar.progress(1.0)
                status_text.text(f"Mass decomposition complete: {processed_count} edges processed, {skipped_count} skipped")
            
            print(f"Mass decomposition results: {processed_count} edges processed, {skipped_count} skipped")
            
            # Update network metadata
            network.metadata['mass_decomposition'] = {
                'processed_edges': processed_count,
                'skipped_edges': skipped_count,
                'total_edges': total_edges,
                'libraries_used': libs,
                'config': decomp_config
            }
            
        except Exception as e:
            print(f"Error in mass decomposition processing: {e}")
        
        return network
    
    @staticmethod
    def _process_graph_links(graph):
        """
        Process a networkx graph to update node 'link' attributes based on edge 'link' attributes.
        Source nodes get usi1, target nodes get usi2 (renamed as usi1).
        Also assigns usi values directly as node properties.
        """
        
        for source, target, edge_data in graph.edges(data=True):
            # Check if edge has usi1 and usi2 properties directly
            if 'usi1' in edge_data and 'usi2' in edge_data:
                # Assign USI values directly to nodes
                graph.nodes[source]['usi'] = edge_data['usi1']
                graph.nodes[target]['usi'] = edge_data['usi2']
                continue
            
            # Check if edge has a 'link' attribute for URL-based processing
            if 'link' not in edge_data:
                continue
                
            edge_link = edge_data['link']
            
            # Parse the URL
            try:
                parsed_url = urlparse(edge_link)
                query_params = parse_qs(parsed_url.query, keep_blank_values=True)
                
                # Extract usi1 and usi2 values
                if 'usi1' not in query_params or 'usi2' not in query_params:
                    continue
                    
                usi1_value = query_params['usi1'][0]
                usi2_value = query_params['usi2'][0]
                
                # Assign USI values directly to nodes
                graph.nodes[source]['usi'] = usi1_value
                graph.nodes[target]['usi'] = usi2_value
                
                # Create source node link (usi1 only)
                source_params = query_params.copy()
                source_params.pop('usi2', None)  # Remove usi2
                source_query = urlencode(source_params, doseq=True)
                source_link = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    source_query,
                    parsed_url.fragment
                ))
                
                # Create target node link (usi2 as usi1)
                target_params = query_params.copy()
                target_params['usi1'] = [usi2_value]  # Replace usi1 with usi2 value
                target_params.pop('usi2', None)  # Remove usi2
                target_query = urlencode(target_params, doseq=True)
                target_link = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    target_query,
                    parsed_url.fragment
                ))
                
                # Update node attributes
                graph.nodes[source]['link'] = source_link
                graph.nodes[target]['link'] = target_link
                
            except Exception as e:
                # Skip this edge if URL parsing fails, but continue processing others
                print(f"Warning: Failed to process link for edge {source}->{target}: {str(e)}")
                continue
    
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
        
        # Process edge links to update node link attributes and assign USI values
        DataLoader._process_graph_links(G)
        
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
            else:
                edge_data = edge_data.copy()
            
            # Remove unwanted columns from edge data
            unwanted_edge_columns = [
                'spectrum_id_1_y', 'spectrum_id_2_y', 'inv_proba', 'prediction',
                'charge_1', 'charge_2', 'precursor_intensity_1', 'precursor_intensity_2',
                'library_smiles_x', 'library_smiles_y', 'cluster_id_1', 'cluster_id_2', 
                'index', 'component', 'deltamz_int', 'scan1', 'scan2'
            ]
            for col in unwanted_edge_columns:
                edge_data.pop(col, None)
            
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
            
            # Special handling for modifinder_link - add adduct parameter if adduct_1 exists
            if 'modifinder_link' in properties and properties['modifinder_link'] and 'adduct_1' in properties:
                modifinder_link = str(properties['modifinder_link'])
                adduct_1 = str(properties['adduct_1'])
                
                if adduct_1:
                    # Transform adduct_1: remove "Adduct" and whitespace, add "1" before last "+"
                    # Example: "[M+H]+ Adduct" -> "[M+H]1+"
                    adduct_transformed = adduct_1.replace('Adduct', '').strip()
                    # Find the last '+' and insert '1' before it
                    if adduct_transformed.endswith('+'):
                        adduct_transformed = adduct_transformed[:-1] + '1+'
                    
                    # Add adduct parameter to URL with proper encoding
                    separator = '&' if '?' in modifinder_link else '?'
                    properties['modifinder_link'] = f"{modifinder_link}{separator}adduct={quote(adduct_transformed)}"
            
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
        
        # Process mass decomposition for delta_mz values if enabled
        network = DataLoader._process_mass_decomposition(network, config)
        
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