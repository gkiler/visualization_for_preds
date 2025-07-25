"""
Annotation Manager for handling SMILES annotation persistence and state management.

This module manages the storage, retrieval, and persistence of user SMILES annotations
across sessions and graph updates.
"""

import json
import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from ..data.models import ChemicalNetwork, ChemicalNode


class AnnotationManager:
    """
    Manages SMILES annotations with persistence and state tracking.
    
    Handles storing user annotations in session state and persisting them
    to local files for cross-session availability.
    """
    
    ANNOTATIONS_FILE = "smiles_annotations.json"
    
    def __init__(self):
        self.annotations_dir = Path("annotations")
        self.annotations_dir.mkdir(exist_ok=True)
        self.annotations_path = self.annotations_dir / self.ANNOTATIONS_FILE
    
    @staticmethod
    def initialize_session_state():
        """Initialize annotation-related session state variables."""
        if 'node_annotations' not in st.session_state:
            st.session_state.node_annotations = {}
        
        if 'annotation_mode' not in st.session_state:
            st.session_state.annotation_mode = False
        
        if 'last_annotation_update' not in st.session_state:
            st.session_state.last_annotation_update = None
        
        if 'pending_annotations' not in st.session_state:
            st.session_state.pending_annotations = {}
    
    def create_annotation(
        self,
        node_id: str,
        new_smiles: str,
        original_smiles: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new annotation record.
        
        Args:
            node_id: ID of the node being annotated
            new_smiles: New SMILES string
            original_smiles: Original SMILES if updating existing
            metadata: Additional metadata for the annotation
            
        Returns:
            Annotation record dictionary
        """
        timestamp = datetime.now().isoformat()
        
        annotation = {
            'node_id': node_id,
            'original_smiles': original_smiles,
            'new_smiles': new_smiles,
            'timestamp': timestamp,
            'status': 'pending',  # pending, applied, error
            'metadata': metadata or {}
        }
        
        return annotation
    
    def add_annotation(
        self,
        node_id: str,
        new_smiles: str,
        original_smiles: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a new annotation to session state.
        
        Args:
            node_id: ID of the node being annotated
            new_smiles: New SMILES string
            original_smiles: Original SMILES if updating existing
            metadata: Additional metadata
            
        Returns:
            True if annotation was added successfully
        """
        try:
            annotation = self.create_annotation(
                node_id, new_smiles, original_smiles, metadata
            )
            
            # Add to session state
            st.session_state.node_annotations[node_id] = annotation
            st.session_state.last_annotation_update = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            print(f"Error adding annotation: {e}")
            return False
    
    def get_annotation(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get annotation for a specific node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Annotation record or None if not found
        """
        return st.session_state.node_annotations.get(node_id)
    
    def has_annotation(self, node_id: str) -> bool:
        """
        Check if a node has an annotation.
        
        Args:
            node_id: ID of the node
            
        Returns:
            True if node has annotation
        """
        return node_id in st.session_state.node_annotations
    
    def get_effective_smiles(self, node: ChemicalNode) -> Optional[str]:
        """
        Get the effective SMILES for a node (annotation takes precedence).
        
        Args:
            node: The chemical node
            
        Returns:
            Effective SMILES string (annotated or original)
        """
        # Check for annotation first
        annotation = self.get_annotation(node.id)
        if annotation and annotation.get('status') == 'applied':
            return annotation['new_smiles']
        
        # Fall back to original SMILES
        return node.properties.get('library_SMILES')
    
    def update_annotation_status(self, node_id: str, status: str, error_msg: str = None):
        """
        Update the status of an annotation.
        
        Args:
            node_id: ID of the node
            status: New status ('pending', 'applied', 'error')
            error_msg: Error message if status is 'error'
        """
        if node_id in st.session_state.node_annotations:
            st.session_state.node_annotations[node_id]['status'] = status
            if error_msg:
                st.session_state.node_annotations[node_id]['error'] = error_msg
    
    def get_annotated_nodes(self, status: Optional[str] = None) -> List[str]:
        """
        Get list of annotated node IDs.
        
        Args:
            status: Filter by annotation status (optional)
            
        Returns:
            List of node IDs with annotations
        """
        if status:
            return [
                node_id for node_id, annotation in st.session_state.node_annotations.items()
                if annotation['status'] == status
            ]
        else:
            return list(st.session_state.node_annotations.keys())
    
    def remove_annotation(self, node_id: str) -> bool:
        """
        Remove an annotation.
        
        Args:
            node_id: ID of the node
            
        Returns:
            True if annotation was removed
        """
        if node_id in st.session_state.node_annotations:
            del st.session_state.node_annotations[node_id]
            return True
        return False
    
    def clear_all_annotations(self):
        """Clear all annotations from session state."""
        st.session_state.node_annotations.clear()
        st.session_state.last_annotation_update = None
    
    def save_annotations_to_file(self) -> bool:
        """
        Save current annotations to file for persistence.
        
        Returns:
            True if save was successful
        """
        try:
            annotations_data = {
                'annotations': st.session_state.node_annotations,
                'last_update': st.session_state.last_annotation_update,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.annotations_path, 'w') as f:
                json.dump(annotations_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving annotations: {e}")
            return False
    
    def load_annotations_from_file(self) -> bool:
        """
        Load annotations from file into session state.
        
        Returns:
            True if load was successful
        """
        try:
            if not self.annotations_path.exists():
                return False
            
            with open(self.annotations_path, 'r') as f:
                annotations_data = json.load(f)
            
            # Load into session state
            if 'annotations' in annotations_data:
                st.session_state.node_annotations.update(annotations_data['annotations'])
            
            if 'last_update' in annotations_data:
                st.session_state.last_annotation_update = annotations_data['last_update']
            
            return True
            
        except Exception as e:
            print(f"Error loading annotations: {e}")
            return False
    
    def get_annotation_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics about current annotations.
        
        Returns:
            Dictionary with annotation statistics
        """
        annotations = st.session_state.node_annotations
        
        summary = {
            'total_annotations': len(annotations),
            'pending': len([a for a in annotations.values() if a['status'] == 'pending']),
            'applied': len([a for a in annotations.values() if a['status'] == 'applied']),
            'error': len([a for a in annotations.values() if a['status'] == 'error']),
            'last_update': st.session_state.last_annotation_update
        }
        
        return summary
    
    def apply_annotations_to_network(self, network: ChemicalNetwork) -> ChemicalNetwork:
        """
        Apply all valid annotations to a network by updating node properties.
        
        Args:
            network: The chemical network to update
            
        Returns:
            Updated network with annotations applied
        """
        applied_count = 0
        
        for node in network.nodes:
            annotation = self.get_annotation(node.id)
            if annotation and annotation.get('status') in ['pending', 'applied']:
                # Update node properties with annotated SMILES
                node.properties['library_SMILES'] = annotation['new_smiles']
                
                # Mark node as annotated
                node.properties['annotation_status'] = 'user_annotated'
                node.properties['annotation_timestamp'] = annotation['timestamp']
                
                # Update annotation status
                self.update_annotation_status(node.id, 'applied')
                applied_count += 1
        
        print(f"Applied {applied_count} annotations to network")
        
        # Debug: Check what annotations we have in session state
        if hasattr(st, 'session_state') and hasattr(st.session_state, 'node_annotations'):
            print(f"DEBUG: Session state has {len(st.session_state.node_annotations)} annotations")
            for node_id, annotation in st.session_state.node_annotations.items():
                print(f"DEBUG: Annotation for {node_id}: status={annotation.get('status')}, smiles={annotation.get('new_smiles', '')[:20]}...")
        
        return network
    
    def get_nodes_needing_smiles(self, network: ChemicalNetwork) -> List[ChemicalNode]:
        """
        Get list of nodes that are missing SMILES and could benefit from annotation.
        
        Args:
            network: The chemical network
            
        Returns:
            List of nodes missing SMILES
        """
        nodes_needing_smiles = []
        
        for node in network.nodes:
            # Check if node has SMILES (either original or annotated)
            effective_smiles = self.get_effective_smiles(node)
            
            if not effective_smiles or not str(effective_smiles).strip():
                nodes_needing_smiles.append(node)
        
        return nodes_needing_smiles