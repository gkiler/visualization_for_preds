"""
ModiFinder Link Generator for creating spectrum alignment links.

This module generates ModiFinder URLs for spectrum alignment visualization
based on node USI data and SMILES annotations.
"""

import re
from typing import Optional, Dict, Any
from ..data.models import ChemicalNode


class ModiFinderLinkGenerator:
    """
    Generates ModiFinder links for spectrum alignment visualization.
    
    Uses the pattern from GNPS molecular networking to create links
    for spectrum comparison between annotated nodes.
    """
    
    GNPS_TASK = "43ab1bb3ce8d468a8dce177763c0ffb1"
    BASE_URL = "https://modifinder.gnps2.org/"
    
    @classmethod
    def generate_usi(cls, node_usi_field: str) -> str:
        """
        Generate full USI from node's usi field.
        
        Args:
            node_usi_field: The usi field value from node properties
            
        Returns:
            Full USI string in GNPS format
        """
        return f"mzspec:GNPS2:TASK-{cls.GNPS_TASK}-input_spectra/{node_usi_field}"
    
    @staticmethod
    def normalize_adduct(adduct: str) -> str:
        """
        Normalize adduct string for ModiFinder URL.
        
        Based on the original pattern:
        - Remove whitespace and the word 'adduct'
        - Insert '1' before the last '+'
        
        Args:
            adduct: Raw adduct string from node properties
            
        Returns:
            Normalized adduct string
        """
        if not adduct or not isinstance(adduct, str):
            return ""
        
        # Remove whitespace and the word 'adduct'
        adduct_clean = re.sub(r'\s+|adduct', '', adduct.lower())
        
        # Insert '1' before the last '+'
        adduct_norm = re.sub(r'\+(?!.*\+)', '1+', adduct_clean)
        
        return adduct_norm
    
    @classmethod
    def can_generate_link(cls, node1: ChemicalNode, node2: ChemicalNode, smiles: str, edge=None) -> bool:
        """
        Check if we have all required data to generate a ModiFinder link.
        
        Args:
            node1: First node (typically the annotated one)
            node2: Second node (connected to the first)
            smiles: SMILES string for the primary node
            edge: Edge object containing adduct_1 (optional for backward compatibility)
            
        Returns:
            True if link can be generated, False otherwise
        """
        # Check if we have required fields
        node1_usi = node1.properties.get('usi')
        node2_usi = node2.properties.get('usi')
        
        # Get adduct from edge if provided, otherwise fallback to node
        if edge and 'adduct_1' in edge.properties:
            adduct = edge.properties.get('adduct_1')
        else:
            adduct = node1.properties.get('adduct_1')
        
        # We need USI for both nodes, adduct from edge, and SMILES
        return all([
            node1_usi and str(node1_usi).strip(),
            node2_usi and str(node2_usi).strip(),
            adduct and str(adduct).strip(),
            smiles and str(smiles).strip()
        ])
    
    @classmethod
    def generate_modifinder_link(
        cls, 
        node1: ChemicalNode, 
        node2: ChemicalNode, 
        smiles: str,
        edge=None,
        ppm_tolerance: int = 40,
        filter_peaks_variable: float = 0.01
    ) -> Optional[str]:
        """
        Generate ModiFinder link for spectrum alignment between two nodes.
        
        Args:
            node1: Primary node (with SMILES annotation)
            node2: Secondary node (connected to primary)
            smiles: SMILES string for primary node
            edge: Edge object containing adduct_1
            ppm_tolerance: PPM tolerance for spectrum matching
            filter_peaks_variable: Peak filtering threshold
            
        Returns:
            ModiFinder URL string or None if generation fails
        """
        # Check if we can generate the link
        if not cls.can_generate_link(node1, node2, smiles, edge):
            print(f"DEBUG ModiFinder: Cannot generate link - missing required data")
            print(f"  Node1 USI: {node1.properties.get('usi')}")
            print(f"  Node2 USI: {node2.properties.get('usi')}")
            if edge and 'adduct_1' in edge.properties:
                print(f"  Edge adduct_1: {edge.properties.get('adduct_1')}")
            else:
                print(f"  Node1 adduct_1: {node1.properties.get('adduct_1')}")
                print(f"  Edge provided: {edge is not None}")
            print(f"  SMILES: {smiles[:20] if smiles else 'None'}...")
            return None
        
        try:
            # Generate USIs
            usi1 = cls.generate_usi(node1.properties['usi'])
            usi2 = cls.generate_usi(node2.properties['usi'])
            
            # Get adduct from edge if provided, otherwise fallback to node
            if edge and 'adduct_1' in edge.properties:
                raw_adduct = edge.properties['adduct_1']
            else:
                raw_adduct = node1.properties['adduct_1']
            
            # Normalize adduct
            adduct = cls.normalize_adduct(str(raw_adduct))
            
            # Clean SMILES (remove newlines)
            clean_smiles = str(smiles).replace('\n', '').strip()
            
            # Build ModiFinder URL
            link = (
                f"{cls.BASE_URL}?"
                f"USI1={usi1}&"
                f"USI2={usi2}&"
                f"Helpers=&"
                f"Adduct={adduct}&"
                f"ppm_tolerance={ppm_tolerance}&"
                f"filter_peaks_variable={filter_peaks_variable}&"
                f"SMILES1={clean_smiles}"
            )
            
            print(f"DEBUG ModiFinder: Successfully generated link")
            print(f"  USI1: {usi1}")
            print(f"  USI2: {usi2}")
            print(f"  Adduct: {adduct}")
            print(f"  SMILES: {clean_smiles[:30]}...")
            print(f"  Link: {link[:100]}...")
            
            return link
            
        except Exception as e:
            print(f"Error generating ModiFinder link: {e}")
            return None
    
    @classmethod
    def generate_links_for_annotated_node(
        cls,
        annotated_node: ChemicalNode,
        connected_nodes: list[ChemicalNode],
        new_smiles: str
    ) -> Dict[str, str]:
        """
        Generate ModiFinder links for all valid connections to an annotated node.
        
        Args:
            annotated_node: The node that received new SMILES annotation
            connected_nodes: List of nodes connected to the annotated node
            new_smiles: The newly annotated SMILES string
            
        Returns:
            Dictionary mapping node_id pairs to ModiFinder URLs
        """
        links = {}
        
        for connected_node in connected_nodes:
            # Generate link with annotated node as primary
            link = cls.generate_modifinder_link(
                annotated_node, 
                connected_node, 
                new_smiles
            )
            
            if link:
                # Create key for the node pair
                pair_key = f"{annotated_node.id}-{connected_node.id}"
                links[pair_key] = link
        
        return links
    
    @classmethod
    def update_edge_with_modifinder_link(
        cls,
        edge_properties: Dict[str, Any],
        node1: ChemicalNode,
        node2: ChemicalNode,
        smiles: str
    ) -> bool:
        """
        Update edge properties with ModiFinder link if possible.
        
        Args:
            edge_properties: Dictionary of edge properties to update
            node1: First node of the edge
            node2: Second node of the edge  
            smiles: SMILES string for link generation
            
        Returns:
            True if link was generated and added, False otherwise
        """
        link = cls.generate_modifinder_link(node1, node2, smiles)
        
        if link:
            edge_properties['modifinder_link'] = link
            return True
        
        return False