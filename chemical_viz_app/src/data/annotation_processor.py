"""
Annotation Processor for handling SMILES annotation processing and ModiFinder link generation.

This module processes user SMILES annotations, updates the network, and generates
ModiFinder links for connected edges.
"""

import streamlit as st
from typing import List, Dict, Any, Tuple
from datetime import datetime
from ..data.models import ChemicalNetwork, ChemicalNode, ChemicalEdge
from ..utils.annotation_manager import AnnotationManager
from ..utils.modifinder_link_generator import ModiFinderLinkGenerator


class AnnotationProcessor:
    """
    Processes SMILES annotations and updates network accordingly.
    
    Handles applying user annotations to nodes, updating connected nodes,
    and generating ModiFinder links for relevant edges.
    """
    
    def __init__(self):
        self.annotation_manager = AnnotationManager()
        self.link_generator = ModiFinderLinkGenerator()
    
    def process_pending_annotations(self, network: ChemicalNetwork) -> Tuple[ChemicalNetwork, Dict[str, Any]]:
        """
        Process all pending SMILES annotations and update the network.
        
        Args:
            network: The chemical network to update
            
        Returns:
            Tuple of (updated_network, processing_results)
        """
        if 'pending_smiles_updates' not in st.session_state:
            return network, {'processed': 0, 'errors': []}
        
        results = {
            'processed': 0,
            'errors': [],
            'modifinder_links_created': 0,
            'nodes_updated': [],
            'edges_updated': []
        }
        
        pending_updates = st.session_state.pending_smiles_updates.copy()
        
        for node_id, update_info in pending_updates.items():
            try:
                print(f"DEBUG: Processing annotation for node {node_id} with SMILES: {update_info['new_smiles'][:20]}...")
                
                # Process the annotation
                success, details = self._process_single_annotation(
                    network, 
                    node_id, 
                    update_info['new_smiles']
                )
                
                if success:
                    results['processed'] += 1
                    results['nodes_updated'].append(node_id)
                    results['modifinder_links_created'] += details.get('links_created', 0)
                    results['edges_updated'].extend(details.get('edges_updated', []))
                    
                    # Remove from pending updates
                    del st.session_state.pending_smiles_updates[node_id]
                    
                else:
                    results['errors'].append(f"Node {node_id}: {details.get('error', 'Unknown error')}")
            
            except Exception as e:
                results['errors'].append(f"Node {node_id}: {str(e)}")
        
        return network, results
    
    def _process_single_annotation(
        self, 
        network: ChemicalNetwork, 
        node_id: str, 
        new_smiles: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a single SMILES annotation.
        
        Args:
            network: The chemical network
            node_id: ID of the annotated node
            new_smiles: New SMILES string
            
        Returns:
            Tuple of (success, details_dict)
        """
        details = {
            'links_created': 0,
            'edges_updated': [],
            'error': None
        }
        
        try:
            print(f"DEBUG: _process_single_annotation called for {node_id}")
            
            # Get the annotated node
            annotated_node = network.get_node_by_id(node_id)
            if not annotated_node:
                details['error'] = f"Node {node_id} not found in network"
                print(f"DEBUG: Node {node_id} not found in network!")
                return False, details
            
            print(f"DEBUG: Found annotated node {node_id}")
            
            # Update the node with new SMILES
            timestamp = datetime.now().isoformat()
            success = network.apply_annotation_to_node(node_id, new_smiles, timestamp)
            
            if not success:
                details['error'] = "Failed to apply annotation to node"
                return False, details
            
            # Update annotation manager status
            self.annotation_manager.update_annotation_status(node_id, 'applied')
            print(f"DEBUG: Annotation applied successfully, now generating ModiFinder links...")
            
            # Generate ModiFinder links for connected edges
            links_created = self._generate_modifinder_links_for_node(
                network, 
                annotated_node, 
                new_smiles
            )
            
            print(f"DEBUG: ModiFinder link generation completed: {links_created}")
            
            details['links_created'] = links_created['count']
            details['edges_updated'] = links_created['edge_ids']
            
            return True, details
            
        except Exception as e:
            details['error'] = str(e)
            return False, details
    
    def _generate_modifinder_links_for_node(
        self, 
        network: ChemicalNetwork, 
        annotated_node: ChemicalNode, 
        new_smiles: str
    ) -> Dict[str, Any]:
        """
        Generate ModiFinder links for all edges connected to an annotated node.
        
        Args:
            network: The chemical network
            annotated_node: The node that was annotated
            new_smiles: The new SMILES string
            
        Returns:
            Dictionary with generation results
        """
        results = {
            'count': 0,
            'edge_ids': [],
            'errors': []
        }
        
        # Get all edges connected to the annotated node
        connected_edges = network.get_edges_for_node(annotated_node.id)
        print(f"DEBUG: Found {len(connected_edges)} edges connected to {annotated_node.id}")
        
        for edge in connected_edges:
            try:
                # Determine which node is which
                if edge.source == annotated_node.id:
                    primary_node = annotated_node
                    secondary_node = network.get_node_by_id(edge.target)
                else:
                    primary_node = annotated_node
                    secondary_node = network.get_node_by_id(edge.source)
                
                if not secondary_node:
                    continue
                
                # Check if we can generate ModiFinder link
                can_generate = self.link_generator.can_generate_link(primary_node, secondary_node, new_smiles, edge)
                print(f"DEBUG: Can generate link for {edge.source}-{edge.target}? {can_generate}")
                
                if can_generate:
                    print(f"DEBUG: Primary node USI: {primary_node.properties.get('usi')}")
                    print(f"DEBUG: Secondary node USI: {secondary_node.properties.get('usi')}")
                    print(f"DEBUG: Edge adduct_1: {edge.properties.get('adduct_1')}")
                
                # Generate ModiFinder link
                modifinder_link = self.link_generator.generate_modifinder_link(
                    primary_node,
                    secondary_node,
                    new_smiles,
                    edge
                )
                
                print(f"DEBUG: Generated ModiFinder link for {edge.source}-{edge.target}: {modifinder_link is not None}")
                if modifinder_link:
                    print(f"DEBUG: Link length: {len(modifinder_link)}")
                
                if modifinder_link:
                    # Update edge properties
                    edge.properties['modifinder_link'] = modifinder_link
                    edge.properties['modifinder_generated'] = datetime.now().isoformat()
                    edge.properties['modifinder_source_node'] = annotated_node.id
                    
                    results['count'] += 1
                    edge_id = f"{edge.source}-{edge.target}"
                    results['edge_ids'].append(edge_id)
                    print(f"DEBUG: Added ModiFinder link to edge {edge_id}")
                else:
                    print(f"DEBUG: No ModiFinder link generated for {edge.source}-{edge.target}")
                
            except Exception as e:
                error_msg = f"Edge {edge.source}-{edge.target}: {str(e)}"
                results['errors'].append(error_msg)
        
        return results
    
    def apply_all_pending_updates(self, network: ChemicalNetwork) -> Dict[str, Any]:
        """
        Apply all pending SMILES updates to the network.
        
        Args:
            network: The chemical network to update
            
        Returns:
            Results dictionary with processing statistics
        """
        print(f"DEBUG: apply_all_pending_updates called")
        
        # Process pending annotations
        updated_network, results = self.process_pending_annotations(network)
        
        print(f"DEBUG: process_pending_annotations completed with results: {results}")
        
        # Mark nodes as annotated (blue color)
        self._mark_annotated_nodes(updated_network)
        
        # Save annotation state
        self.annotation_manager.save_annotations_to_file()
        
        return results
    
    def _mark_annotated_nodes(self, network: ChemicalNetwork):
        """
        Mark annotated nodes with blue color for visualization.
        
        Args:
            network: The chemical network
        """
        for node in network.nodes:
            if node.is_annotated():
                # Set blue color for annotated nodes
                node.color = "#2196F3"  # Blue color
                node.properties['visual_annotation_marker'] = True
    
    def get_pending_updates_summary(self) -> Dict[str, Any]:
        """
        Get summary of pending SMILES updates.
        
        Returns:
            Summary dictionary
        """
        if 'pending_smiles_updates' not in st.session_state:
            return {'count': 0, 'nodes': []}
        
        pending = st.session_state.pending_smiles_updates
        
        return {
            'count': len(pending),
            'nodes': list(pending.keys()),
            'details': pending
        }
    
    def clear_pending_updates(self):
        """Clear all pending updates."""
        if 'pending_smiles_updates' in st.session_state:
            st.session_state.pending_smiles_updates.clear()
    
    def preview_annotation_impact(self, network: ChemicalNetwork, node_id: str) -> Dict[str, Any]:
        """
        Preview the impact of annotating a specific node.
        
        Args:
            network: The chemical network
            node_id: ID of the node to annotate
            
        Returns:
            Impact preview dictionary
        """
        node = network.get_node_by_id(node_id)
        if not node:
            return {'error': 'Node not found'}
        
        # Get connected nodes
        connected_nodes = network.get_connected_nodes(node_id)
        connected_edges = network.get_edges_for_node(node_id)
        
        # Check which connections can generate ModiFinder links
        potential_links = 0
        for connected_node in connected_nodes:
            if self.link_generator.can_generate_link(node, connected_node, "dummy_smiles"):
                potential_links += 1
        
        return {
            'connected_nodes': len(connected_nodes),
            'connected_edges': len(connected_edges),
            'potential_modifinder_links': potential_links,
            'node_has_required_data': node.can_generate_modifinder_links()
        }
    
    def render_pending_updates_panel(self):
        """Render a panel showing pending updates with apply button."""
        summary = self.get_pending_updates_summary()
        print(f"DEBUG: render_pending_updates_panel - found {summary['count']} pending updates")
        
        if summary['count'] > 0:
            st.markdown("### Pending SMILES Updates")
            st.info(f"📝 {summary['count']} annotation(s) pending processing")
            
            # Show pending updates
            for node_id, update_info in summary['details'].items():
                with st.expander(f"Node: {node_id}"):
                    st.markdown(f"**New SMILES:** `{update_info['new_smiles']}`")
                    st.markdown(f"**Time:** {update_info['timestamp']}")
            
            # Apply button
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Apply All Updates", type="primary", key="apply_all_annotations"):
                    print("DEBUG: Apply All Updates button clicked!")
                    if st.session_state.network:
                        print("DEBUG: Network found, processing annotations...")
                        with st.spinner("Processing annotations and generating ModiFinder links..."):
                            results = self.apply_all_pending_updates(st.session_state.network)
                        
                        # Show results
                        if results['processed'] > 0:
                            st.success(f"✅ Processed {results['processed']} annotation(s)")
                            st.info(f"🔗 Generated {results['modifinder_links_created']} ModiFinder link(s)")
                            
                            if results['nodes_updated']:
                                st.write("**Updated nodes:**", ", ".join(results['nodes_updated']))
                                
                                # Debug: Check if nodes are actually updated
                                for node_id in results['nodes_updated']:
                                    node = st.session_state.network.get_node_by_id(node_id)
                                    if node:
                                        st.write(f"DEBUG - Node {node_id}: annotation_status = {node.properties.get('annotation_status')}, has SMILES = {node.has_smiles()}")
                                    else:
                                        st.write(f"DEBUG - Node {node_id}: NOT FOUND in network")
                        
                        if results['errors']:
                            st.error("⚠️ Some errors occurred:")
                            for error in results['errors']:
                                st.write(f"- {error}")
                        
                        # Force network update by clearing filtered network
                        # This will cause the main app to recreate it with updated annotations
                        if 'filtered_network' in st.session_state:
                            del st.session_state.filtered_network
                        st.rerun()
            
            with col2:
                if st.button("Clear Pending", type="secondary", key="clear_pending_annotations"):
                    self.clear_pending_updates()
                    st.success("Pending updates cleared")
                    st.rerun()
        
        else:
            st.info("No pending SMILES annotations")