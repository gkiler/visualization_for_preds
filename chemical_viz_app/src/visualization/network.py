from pyvis.network import Network
import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any, Optional, List, Tuple
import tempfile
import os
import json
from ..data.models import ChemicalNetwork, ChemicalNode, ChemicalEdge, NodeType, EdgeType
from ..data.loader import DataLoader


class NetworkVisualizer:
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or DataLoader.load_config()
        self.network = None
        self.pyvis_net = None
    
    def create_pyvis_network(
        self, 
        height: str = "750px", 
        width: str = "100%",
        physics: bool = True
    ) -> Network:
        net = Network(
            height=height, 
            width=width, 
            bgcolor="#ffffff", 
            font_color="#000000",
            directed=True
        )
        
        if physics:
            physics_config = self.config["visualization"]["physics_options"]
            options = {"physics": physics_config}
            net.set_options(json.dumps(options))
        else:
            net.toggle_physics(False)
        
        return net
    
    def add_nodes_to_pyvis(
        self, 
        net: Network, 
        nodes: List[ChemicalNode],
        node_colors: Optional[Dict[str, str]] = None,
        node_sizes: Optional[Dict[str, float]] = None,
        node_label_column: str = 'label'
    ) -> None:
        default_colors = self.config["colors"]["node_categories"]
        default_node_config = self.config["visualization"]["node_defaults"]
        
        for node in nodes:
            color = node.color
            if not color:
                # Priority 1: Check if node is annotated by user (show in blue)
                if node.is_annotated():
                    color = self.config["colors"]["annotation"]["user_annotated"]
                elif node_colors and node.id in node_colors:
                    color = node_colors[node.id]
                else:
                    # Apply default library_SMILES coloring if available
                    color = self._get_default_library_smiles_color(node)
                    if not color:
                        color = default_colors.get(
                            node.node_type.value, 
                            default_colors["default"]
                        )
            
            size = node.size
            if not size:
                if node_sizes and node.id in node_sizes:
                    size = node_sizes[node.id]
                else:
                    size = default_node_config["size"]
            
            # Get the display label based on selected column
            if node_label_column == 'id':
                display_label = node.id
            elif node_label_column == 'label':
                display_label = node.label
            elif node_label_column in node.properties:
                display_label = str(node.properties[node_label_column]) if node.properties[node_label_column] is not None else ""
            else:
                display_label = node.label  # Fallback to default label
            
            title = f"<b>{display_label}</b><br>"
            title += f"Type: {node.node_type.value}<br>"
            
            # Add annotation status to title
            if node.is_annotated():
                title += f"<span style='color: #2196F3;'><b>✓ User Annotated</b></span><br>"
                if 'annotation_timestamp' in node.properties:
                    title += f"Annotated: {node.properties['annotation_timestamp'][:19]}<br>"
            
            for key, value in node.properties.items():
                # Skip internal annotation properties from tooltip
                if key.startswith('annotation_'):
                    continue
                title += f"{key}: {value}<br>"
            
            net.add_node(
                node.id,
                label=display_label,
                color=color,
                size=size,
                title=title,
                shape=default_node_config["shape"],
                borderWidth=default_node_config["borderWidth"],
                font=default_node_config["font"]
            )
    
    def add_edges_to_pyvis(
        self, 
        net: Network, 
        edges: List[ChemicalEdge],
        edge_colors: Optional[Dict[Tuple[str, str], str]] = None,
        edge_widths: Optional[Dict[Tuple[str, str], float]] = None,
        show_edge_labels: bool = False,
        edge_label_column: str = 'type'
    ) -> None:
        default_colors = self.config["colors"]["edge_types"]
        default_edge_config = self.config["visualization"]["edge_defaults"]
        
        for i, edge in enumerate(edges):
            color = edge.color
            if not color:
                if edge_colors and (edge.source, edge.target) in edge_colors:
                    color = edge_colors[(edge.source, edge.target)]
                else:
                    # Check for molecular_networking attribute
                    if "molecular_networking" in edge.properties:
                        mn_value = edge.properties["molecular_networking"]
                        molecular_colors = self.config["colors"].get("molecular_networking", {})
                        color = molecular_colors.get(mn_value, default_colors["default"])
                    else:
                        color = default_colors.get(
                            edge.edge_type.value, 
                            default_colors["default"]
                        )
            
            width = edge.width
            if not width:
                if edge_widths and (edge.source, edge.target) in edge_widths:
                    width = edge_widths[(edge.source, edge.target)]
                else:
                    width = edge.weight * default_edge_config["width"]
            
            # Determine line style based on edit_distance
            edge_options = {
                "color": color,
                "width": width,
                "title": self._create_edge_title(edge),
                "smooth": default_edge_config["smooth"]
            }
            
            # Handle edit_distance styling
            if "edit_distance" in edge.properties:
                edit_dist = edge.properties["edit_distance"]
                if edit_dist == -1:
                    edge_options["dashes"] = [5, 5]  # Dashed line
                elif edit_dist == 1:
                    edge_options["dashes"] = False  # Solid line (default)
                elif edit_dist > 1:
                    edge_options["dashes"] = [2, 2, 8, 2]  # Jagged pattern
            
            # Handle modifinder link glow effect
            if "modifinder" in edge.properties:
                edge_options["shadow"] = {"enabled": True, "color": color, "size": 3}
            
            # Add edge label if enabled
            if show_edge_labels:
                if edge_label_column == 'source':
                    edge_label = edge.source
                elif edge_label_column == 'target':
                    edge_label = edge.target
                elif edge_label_column == 'type':
                    edge_label = edge.edge_type.value
                elif edge_label_column == 'weight':
                    edge_label = str(edge.weight)
                elif edge_label_column == 'delta_mz' and 'delta_mz' in edge.properties:
                    # Format delta_mz with 3 decimal places of precision
                    try:
                        delta_mz_value = float(edge.properties['delta_mz'])
                        edge_label = f"{delta_mz_value:.3f}"
                    except (TypeError, ValueError):
                        edge_label = str(edge.properties['delta_mz']) if edge.properties['delta_mz'] is not None else ""
                elif edge_label_column in edge.properties:
                    edge_label = str(edge.properties[edge_label_column]) if edge.properties[edge_label_column] is not None else ""
                else:
                    edge_label = edge.edge_type.value  # Fallback to type
                
                edge_options["label"] = edge_label
            
            # Set explicit edge ID to match our format with index
            edge_id = f"{edge.source}-{edge.target}-{i}"
            edge_options["id"] = edge_id
            
            net.add_edge(edge.source, edge.target, **edge_options)
            
            if edge.edge_type == EdgeType.ACTIVATION:
                net.add_edge(
                    edge.source,
                    edge.target,
                    arrows="to",
                    arrowStrikethrough=False,
                    id=f"{edge_id}_arrow"
                )
            elif edge.edge_type == EdgeType.INHIBITION:
                net.add_edge(
                    edge.source,
                    edge.target,
                    arrows="to",
                    arrowStrikethrough=True,
                    id=f"{edge_id}_arrow"
                )
    
    def _create_edge_title(self, edge: ChemicalEdge) -> str:
        """Create tooltip title for edge with all properties."""
        title = f"Type: {edge.edge_type.value}<br>"
        title += f"Weight: {edge.weight}<br>"
        for key, value in edge.properties.items():
            title += f"{key}: {value}<br>"
        return title
    
    def _get_default_library_smiles_color(self, node: ChemicalNode) -> Optional[str]:
        """Get default color based on library_SMILES containing 'O'."""
        if "library_SMILES" in node.properties:
            smiles = node.properties["library_SMILES"]
            if isinstance(smiles, str) and smiles and "O" in smiles:
                return self.config["colors"]["library_smiles_default"]["contains_oxygen"]
            elif isinstance(smiles, str) and smiles:
                return self.config["colors"]["library_smiles_default"]["no_oxygen"]
        return None
    
    def visualize_network(
        self,
        network: ChemicalNetwork,
        height: str = "750px",
        width: str = "100%",
        physics: bool = True,
        node_colors: Optional[Dict[str, str]] = None,
        node_sizes: Optional[Dict[str, float]] = None,
        edge_colors: Optional[Dict[Tuple[str, str], str]] = None,
        edge_widths: Optional[Dict[Tuple[str, str], float]] = None,
        node_label_column: str = 'label',
        show_edge_labels: bool = False,
        edge_label_column: str = 'type'
    ) -> str:
        self.network = network
        self.pyvis_net = self.create_pyvis_network(height, width, physics)
        
        self.add_nodes_to_pyvis(
            self.pyvis_net, 
            network.nodes, 
            node_colors, 
            node_sizes,
            node_label_column
        )
        
        self.add_edges_to_pyvis(
            self.pyvis_net, 
            network.edges, 
            edge_colors, 
            edge_widths,
            show_edge_labels,
            edge_label_column
        )
        
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=".html", 
            mode='w'
        ) as tmp:
            self.pyvis_net.save_graph(tmp.name)
            return tmp.name
    
    def display_in_streamlit(self, html_file: str) -> None:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Inject JavaScript for click handling that triggers Streamlit buttons
        click_handler_js = """
        <script>
        // Add click handler after network is initialized
        function addPyVisClickHandler() {
            if (typeof network !== 'undefined' && network) {
                // Disable default drag behavior for better click detection
                network.setOptions({
                    interaction: {
                        dragNodes: false,  // Disable dragging to prevent interference
                        hover: true,
                        selectConnectedEdges: false
                    }
                });
                
                network.on('click', function(params) {
                    // Handle node clicks
                    if (params.nodes.length > 0) {
                        const nodeId = params.nodes[0];
                        console.log('Node clicked:', nodeId);
                        
                        // Try to find and click the corresponding Streamlit button
                        const buttonId = 'node_click_' + nodeId;
                        
                        // Look for the button in parent window (Streamlit)
                        if (window.parent && window.parent.document) {
                            try {
                                // Multiple strategies to find the button
                                const buttons = window.parent.document.querySelectorAll('button');
                                let targetButton = null;
                                const buttonKey = 'node_click_' + nodeId;
                                
                                // Strategy 1: Find by button key in data-testid
                                for (let button of buttons) {
                                    const testId = button.getAttribute('data-testid');
                                    if (testId && testId.includes(buttonKey)) {
                                        targetButton = button;
                                        break;
                                    }
                                }
                                
                                // Strategy 2: Find by button text content if first strategy fails
                                if (!targetButton) {
                                    for (let button of buttons) {
                                        if (button.textContent && button.textContent.includes(`Select ${nodeId}`)) {
                                            targetButton = button;
                                            break;
                                        }
                                    }
                                }
                                
                                // Strategy 3: Find by data attributes if available
                                if (!targetButton) {
                                    for (let button of buttons) {
                                        if (button.getAttribute('data-node-id') === nodeId) {
                                            targetButton = button;
                                            break;
                                        }
                                    }
                                }
                                
                                if (targetButton) {
                                    console.log('Clicking Streamlit button for node:', nodeId);
                                    targetButton.click();
                                } else {
                                    console.log('Could not find button for node:', nodeId);
                                    // Fallback: try to communicate via postMessage
                                    window.parent.postMessage({
                                        type: 'node_click',
                                        nodeId: nodeId
                                    }, '*');
                                }
                            } catch (e) {
                                console.log('Error clicking button:', e);
                                // Fallback: postMessage
                                window.parent.postMessage({
                                    type: 'node_click',
                                    nodeId: nodeId
                                }, '*');
                            }
                        }
                        
                        // Visual feedback - highlight the clicked node
                        if (typeof nodes !== 'undefined') {
                            try {
                                const clickedNode = nodes.get(nodeId);
                                if (clickedNode) {
                                    const highlightedNode = {...clickedNode};
                                    highlightedNode.borderWidth = 6;
                                    highlightedNode.color = {
                                        ...highlightedNode.color,
                                        border: '#ff6b35'
                                    };
                                    nodes.update([highlightedNode]);
                                    
                                    // Reset highlight after 1.5 seconds
                                    setTimeout(() => {
                                        nodes.update([clickedNode]);
                                    }, 1500);
                                }
                            } catch (e) {
                                console.log('Could not update node highlight:', e);
                            }
                        }
                    }
                    // Handle edge clicks
                    else if (params.edges.length > 0) {
                        const edgeId = params.edges[0];
                        console.log('Edge clicked:', edgeId);
                        
                        // The edgeId from PyVis should already be in the correct format: source-target-index
                        // Try to find and click the corresponding Streamlit button
                        const buttonKey = 'edge_click_' + edgeId;
                        
                        // Look for the button in parent window (Streamlit)
                        if (window.parent && window.parent.document) {
                            try {
                                // Multiple strategies to find the button
                                const buttons = window.parent.document.querySelectorAll('button');
                                let targetButton = null;
                                
                                // Strategy 1: Find by button key (most reliable)
                                for (let button of buttons) {
                                    // Check button's data-testid or other identifying attributes
                                    const testId = button.getAttribute('data-testid');
                                    if (testId && testId.includes(buttonKey)) {
                                        targetButton = button;
                                        break;
                                    }
                                }
                                
                                // Strategy 2: Find by button text content if first strategy fails
                                if (!targetButton) {
                                    // Extract source and target from edgeId for text matching
                                    const edgeParts = edgeId.split('-');
                                    if (edgeParts.length >= 3) {
                                        const source = edgeParts[0];
                                        const target = edgeParts[1];
                                        const displayId = `${source}-${target}`;
                                        
                                        for (let button of buttons) {
                                            if (button.textContent && button.textContent.includes(`Select ${displayId}`)) {
                                                targetButton = button;
                                                break;
                                            }
                                        }
                                    }
                                }
                                
                                // Strategy 3: Find by data attributes if available
                                if (!targetButton) {
                                    for (let button of buttons) {
                                        if (button.getAttribute('data-edge-id') === edgeId) {
                                            targetButton = button;
                                            break;
                                        }
                                    }
                                }
                                
                                if (targetButton) {
                                    console.log('Clicking Streamlit button for edge:', edgeId);
                                    targetButton.click();
                                } else {
                                    console.log('Could not find button for edge:', edgeId);
                                    console.log('Available buttons:', Array.from(buttons).map(b => b.textContent?.slice(0, 50)).filter(t => t));
                                    // Fallback: try to communicate via postMessage
                                    window.parent.postMessage({
                                        type: 'edge_click',
                                        edgeId: edgeId
                                    }, '*');
                                }
                            } catch (e) {
                                console.log('Error clicking edge button:', e);
                                // Fallback: postMessage
                                window.parent.postMessage({
                                    type: 'edge_click',
                                    edgeId: edgeId
                                }, '*');
                            }
                        }
                        
                        // Visual feedback - highlight the clicked edge
                        if (typeof edges !== 'undefined') {
                            try {
                                const clickedEdge = edges.get(edgeId);
                                if (clickedEdge) {
                                    console.log('Highlighting edge:', edgeId, clickedEdge);
                                    const highlightedEdge = {...clickedEdge};
                                    
                                    // Increase edge width for visibility
                                    const originalWidth = highlightedEdge.width || 2;
                                    highlightedEdge.width = Math.max(originalWidth * 2.5, 4);
                                    
                                    // Set highlight color - handle both string and object color formats
                                    if (typeof highlightedEdge.color === 'string') {
                                        highlightedEdge.color = '#ff6b35';
                                    } else if (typeof highlightedEdge.color === 'object') {
                                        highlightedEdge.color = {
                                            ...highlightedEdge.color,
                                            color: '#ff6b35',
                                            highlight: '#ff6b35'
                                        };
                                    } else {
                                        highlightedEdge.color = '#ff6b35';
                                    }
                                    
                                    // Add shadow for better visibility
                                    highlightedEdge.shadow = {
                                        enabled: true,
                                        color: '#ff6b35',
                                        size: 8,
                                        x: 0,
                                        y: 0
                                    };
                                    
                                    edges.update([highlightedEdge]);
                                    
                                    // Reset highlight after 1.5 seconds
                                    setTimeout(() => {
                                        try {
                                            edges.update([clickedEdge]);
                                        } catch (resetError) {
                                            console.log('Error resetting edge highlight:', resetError);
                                        }
                                    }, 1500);
                                } else {
                                    console.log('Edge not found for highlighting:', edgeId);
                                }
                            } catch (e) {
                                console.log('Could not update edge highlight:', e);
                                console.log('Available edges:', typeof edges !== 'undefined' ? edges.getIds() : 'edges undefined');
                            }
                        } else {
                            console.log('Edges dataset not available for highlighting');
                        }
                    }
                });
                console.log('PyVis click handler installed successfully');
            } else {
                console.log('Network not ready, retrying click handler installation...');
                setTimeout(addPyVisClickHandler, 500);
            }
        }
        
        // Wait for everything to load, then install click handler
        if (document.readyState === 'complete') {
            setTimeout(addPyVisClickHandler, 1000);
        } else {
            window.addEventListener('load', function() {
                setTimeout(addPyVisClickHandler, 1000);
            });
        }
        </script>
        """
        
        # Insert the click handler before closing body tag
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', click_handler_js + '\n</body>')
        else:
            html_content += click_handler_js
        
        # Display the enhanced HTML
        components.html(html_content, height=800, scrolling=True)
        
        # Clean up the temporary file
        if os.path.exists(html_file):
            os.unlink(html_file)
    
    @staticmethod
    def get_clicked_node_from_url():
        """Extract clicked node ID from URL hash if present."""
        try:
            # Check if we can access Streamlit's query params (this might not work in all cases)
            import streamlit as st
            
            # For now, we'll use a simple session state approach
            # In a full implementation, we'd need to check the URL hash
            # This is a placeholder - we'll implement proper click detection in the app
            return None
        except:
            return None
    
    def get_node_colors_by_property(
        self,
        network: ChemicalNetwork,
        property_name: str,
        color_map: Dict[Any, str],
        default_color: str = "#757575"
    ) -> Dict[str, str]:
        node_colors = {}
        
        for node in network.nodes:
            if property_name in node.properties:
                value = node.properties[property_name]
                color = color_map.get(value, default_color)
            else:
                color = default_color
            node_colors[node.id] = color
        
        return node_colors
    
    def get_edge_colors_by_property(
        self,
        network: ChemicalNetwork,
        property_name: str,
        color_map: Dict[Any, str],
        default_color: str = "#999999"
    ) -> Dict[Tuple[str, str], str]:
        edge_colors = {}
        
        for edge in network.edges:
            if property_name in edge.properties:
                value = edge.properties[property_name]
                color = color_map.get(value, default_color)
            else:
                color = default_color
            edge_colors[(edge.source, edge.target)] = color
        
        return edge_colors
    
    def get_node_sizes_by_property(
        self,
        network: ChemicalNetwork,
        property_name: str,
        min_size: float = 10,
        max_size: float = 50
    ) -> Dict[str, float]:
        node_sizes = {}
        values = []
        
        for node in network.nodes:
            if property_name in node.properties:
                try:
                    value = float(node.properties[property_name])
                    values.append(value)
                except (TypeError, ValueError):
                    pass
        
        if not values:
            return {node.id: 25 for node in network.nodes}
        
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            return {node.id: 25 for node in network.nodes}
        
        for node in network.nodes:
            if property_name in node.properties:
                try:
                    value = float(node.properties[property_name])
                    normalized = (value - min_val) / (max_val - min_val)
                    size = min_size + (max_size - min_size) * normalized
                    node_sizes[node.id] = size
                except (TypeError, ValueError):
                    node_sizes[node.id] = 25
            else:
                node_sizes[node.id] = 25
        
        return node_sizes