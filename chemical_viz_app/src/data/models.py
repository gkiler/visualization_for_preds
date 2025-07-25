from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import pandas as pd


class NodeType(Enum):
    MOLECULE = "molecule"
    PROTEIN = "protein"
    REACTION = "reaction"
    PATHWAY = "pathway"
    OTHER = "other"


class EdgeType(Enum):
    INTERACTION = "interaction"
    ACTIVATION = "activation"
    INHIBITION = "inhibition"
    BINDING = "binding"
    OTHER = "other"


@dataclass
class ChemicalNode:
    id: str
    label: str
    node_type: NodeType
    properties: Dict[str, Any] = field(default_factory=dict)
    x: Optional[float] = None
    y: Optional[float] = None
    size: Optional[float] = None
    color: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type.value,
            "properties": self.properties,
            "x": self.x,
            "y": self.y,
            "size": self.size,
            "color": self.color
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChemicalNode':
        node_type = NodeType(data.get("type", "other"))
        return cls(
            id=data["id"],
            label=data["label"],
            node_type=node_type,
            properties=data.get("properties", {}),
            x=data.get("x"),
            y=data.get("y"),
            size=data.get("size"),
            color=data.get("color")
        )
    
    # Annotation-related methods
    def is_annotated(self) -> bool:
        """Check if this node has been annotated by user."""
        return self.properties.get('annotation_status') == 'user_annotated'
    
    def get_effective_smiles(self) -> Optional[str]:
        """Get the effective SMILES (annotated takes precedence over original)."""
        return self.properties.get('library_SMILES')
    
    def has_smiles(self) -> bool:
        """Check if node has any SMILES data."""
        smiles = self.get_effective_smiles()
        return smiles is not None and str(smiles).strip() != ''
    
    def set_annotation_status(self, status: str, timestamp: str = None, metadata: Dict[str, Any] = None):
        """Set annotation status and metadata."""
        self.properties['annotation_status'] = status
        if timestamp:
            self.properties['annotation_timestamp'] = timestamp
        if metadata:
            self.properties['annotation_metadata'] = metadata
    
    def can_generate_modifinder_links(self) -> bool:
        """Check if node has required data for ModiFinder link generation.
        
        Note: This only checks node-level requirements. Edge-level adduct_1 
        is checked separately during link generation.
        """
        return all([
            'usi' in self.properties and str(self.properties['usi']).strip(),
            self.has_smiles()
        ])


@dataclass
class ChemicalEdge:
    source: str
    target: str
    edge_type: EdgeType
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    color: Optional[str] = None
    width: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type.value,
            "properties": self.properties,
            "weight": self.weight,
            "color": self.color,
            "width": self.width
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChemicalEdge':
        edge_type = EdgeType(data.get("type", "other"))
        return cls(
            source=data["source"],
            target=data["target"],
            edge_type=edge_type,
            properties=data.get("properties", {}),
            weight=data.get("weight", 1.0),
            color=data.get("color"),
            width=data.get("width")
        )


@dataclass
class ChemicalNetwork:
    nodes: List[ChemicalNode] = field(default_factory=list)
    edges: List[ChemicalEdge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_node(self, node: ChemicalNode) -> None:
        self.nodes.append(node)
    
    def add_edge(self, edge: ChemicalEdge) -> None:
        self.edges.append(edge)
    
    def get_node_by_id(self, node_id: str) -> Optional[ChemicalNode]:
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_edge_by_id(self, edge_id: str) -> Optional[ChemicalEdge]:
        """Get edge by ID in format 'source-target-index'."""
        if '-' not in edge_id:
            return None
        
        # Check if this is the new format with index
        parts = edge_id.split('-')
        if len(parts) >= 3 and parts[-1].isdigit():
            # New format: source-target-index
            index = int(parts[-1])
            if 0 <= index < len(self.edges):
                return self.edges[index]
        else:
            # Old format: source-target (find first match)
            source, target = edge_id.split('-', 1)
            for edge in self.edges:
                if edge.source == source and edge.target == target:
                    return edge
        
        return None
    
    def get_edges_for_node(self, node_id: str) -> List[ChemicalEdge]:
        return [
            edge for edge in self.edges
            if edge.source == node_id or edge.target == node_id
        ]
    
    def get_connected_nodes(self, node_id: str) -> List[ChemicalNode]:
        """Get all nodes connected to the specified node."""
        connected_node_ids = set()
        
        for edge in self.edges:
            if edge.source == node_id:
                connected_node_ids.add(edge.target)
            elif edge.target == node_id:
                connected_node_ids.add(edge.source)
        
        return [self.get_node_by_id(nid) for nid in connected_node_ids if self.get_node_by_id(nid)]
    
    def filter_nodes(self, filter_func) -> List[ChemicalNode]:
        return [node for node in self.nodes if filter_func(node)]
    
    def filter_edges(self, filter_func) -> List[ChemicalEdge]:
        return [edge for edge in self.edges if filter_func(edge)]
    
    def to_dataframes(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        nodes_df = pd.DataFrame([node.to_dict() for node in self.nodes])
        edges_df = pd.DataFrame([edge.to_dict() for edge in self.edges])
        return nodes_df, edges_df
    
    @classmethod
    def from_dataframes(
        cls, 
        nodes_df: pd.DataFrame, 
        edges_df: pd.DataFrame,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ChemicalNetwork':
        network = cls(metadata=metadata or {})
        
        for _, row in nodes_df.iterrows():
            node = ChemicalNode.from_dict(row.to_dict())
            network.add_node(node)
        
        for _, row in edges_df.iterrows():
            edge = ChemicalEdge.from_dict(row.to_dict())
            network.add_edge(edge)
        
        return network
    
    # Annotation-related methods
    def get_annotated_nodes(self) -> List[ChemicalNode]:
        """Get all nodes that have been annotated by users."""
        return [node for node in self.nodes if node.is_annotated()]
    
    def get_nodes_needing_smiles(self) -> List[ChemicalNode]:
        """Get nodes that are missing SMILES and could benefit from annotation."""
        return [node for node in self.nodes if not node.has_smiles()]
    
    def apply_annotation_to_node(self, node_id: str, smiles: str, timestamp: str = None) -> bool:
        """Apply SMILES annotation to a specific node."""
        node = self.get_node_by_id(node_id)
        if node:
            node.properties['library_SMILES'] = smiles
            node.set_annotation_status('user_annotated', timestamp)
            return True
        return False