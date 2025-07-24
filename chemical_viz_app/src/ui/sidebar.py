import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
from ..data.models import NodeType, EdgeType, ChemicalNetwork
from ..visualization.filters import NetworkFilter


class SidebarControls:
    
    def __init__(self):
        self.filter = NetworkFilter()
    
    # COMMENTED OUT - Visualization Settings removed for cleaner UI
    # def render_visualization_controls(self) -> Dict[str, Any]:
    #     st.sidebar.header("Visualization Settings")
    #     
    #     with st.sidebar.expander("Layout Settings", expanded=True):
    #         physics_enabled = st.checkbox("Enable Physics", value=True)
    #         height = st.slider("Height (px)", 400, 1200, 750, 50)
    #         
    #     controls = {
    #         "physics": physics_enabled,
    #         "height": f"{height}px"
    #     }
    #     
    #     return controls
    
    # COMMENTED OUT - Node Filters removed for cleaner UI
    # def render_node_filters(self, network: ChemicalNetwork) -> List[Dict[str, Any]]:
    #     st.sidebar.header("Node Filters")
    #     node_filters = []
    #     
    #     with st.sidebar.expander("Filter by Node Type", expanded=True):
    #         available_types = list(set(node.node_type for node in network.nodes))
    #         selected_types = st.multiselect(
    #             "Select node types to display:",
    #             options=available_types,
    #             default=available_types,
    #             format_func=lambda x: x.value
    #         )
    #         
    #         if selected_types != available_types:
    #             node_filters.append({
    #                 "type": "node_type",
    #                 "values": selected_types
    #             })
    #     
    #     with st.sidebar.expander("Filter by Connectivity"):
    #         col1, col2 = st.columns(2)
    #         with col1:
    #             min_conn = st.number_input(
    #                 "Min connections", 
    #                 min_value=0, 
    #                 value=0,
    #                 key="min_conn"
    #             )
    #         with col2:
    #             max_conn = st.number_input(
    #                 "Max connections", 
    #                 min_value=0, 
    #                 value=100,
    #                 key="max_conn"
    #             )
    #         
    #         if min_conn > 0 or max_conn < 100:
    #             node_filters.append({
    #                 "type": "connectivity",
    #                 "min_connections": min_conn if min_conn > 0 else None,
    #                 "max_connections": max_conn if max_conn < 100 else None
    #             })
    #     
    #     all_properties = set()
    #     for node in network.nodes:
    #         all_properties.update(node.properties.keys())
    #     
    #     if all_properties:
    #         with st.sidebar.expander("Filter by Node Properties"):
    #             property_name = st.selectbox(
    #                 "Property:", 
    #                 options=list(all_properties),
    #                 key="node_prop_filter"
    #             )
    #             
    #             col1, col2 = st.columns([1, 2])
    #             with col1:
    #                 operator = st.selectbox(
    #                     "Operator:",
    #                     options=['==', '!=', '>', '>=', '<', '<=', 'contains'],
    #                     key="node_op_filter"
    #                 )
    #             with col2:
    #                 value = st.text_input("Value:", key="node_val_filter")
    #             
    #             if st.button("Add Node Property Filter"):
    #                 if value:
    #                     node_filters.append({
    #                         "type": "property",
    #                         "property": property_name,
    #                         "operator": operator,
    #                         "value": value
    #                     })
    #     
    #     return node_filters
    
    # COMMENTED OUT - Edge Filters removed for cleaner UI
    # def render_edge_filters(self, network: ChemicalNetwork) -> List[Dict[str, Any]]:
    #     st.sidebar.header("Edge Filters")
    #     edge_filters = []
    #     
    #     with st.sidebar.expander("Filter by Edge Type", expanded=True):
    #         available_types = list(set(edge.edge_type for edge in network.edges))
    #         selected_types = st.multiselect(
    #             "Select edge types to display:",
    #             options=available_types,
    #             default=available_types,
    #             format_func=lambda x: x.value
    #         )
    #         
    #         if selected_types != available_types:
    #             edge_filters.append({
    #                 "type": "edge_type",
    #                 "values": selected_types
    #             })
    #     
    #     all_properties = set()
    #     for edge in network.edges:
    #         all_properties.update(edge.properties.keys())
    #     
    #     if all_properties:
    #         with st.sidebar.expander("Filter by Edge Properties"):
    #             property_name = st.selectbox(
    #                 "Property:", 
    #                 options=list(all_properties),
    #                 key="edge_prop_filter"
    #             )
    #             
    #             col1, col2 = st.columns([1, 2])
    #             with col1:
    #                 operator = st.selectbox(
    #                     "Operator:",
    #                     options=['==', '!=', '>', '>=', '<', '<='],
    #                     key="edge_op_filter"
    #                 )
    #             with col2:
    #                 value = st.text_input("Value:", key="edge_val_filter")
    #             
    #             if st.button("Add Edge Property Filter"):
    #                 if value:
    #                     edge_filters.append({
    #                         "type": "property",
    #                         "property": property_name,
    #                         "operator": operator,
    #                         "value": value
    #                     })
    #     
    #     return edge_filters
    
    # COMMENTED OUT - Coloring Options removed for cleaner UI
    # def render_coloring_controls(self, network: ChemicalNetwork) -> Dict[str, Any]:
    #     st.sidebar.header("Coloring Options")
    #     coloring_options = {}
    #     
    #     with st.sidebar.expander("Node Coloring"):
    #         node_color_by = st.selectbox(
    #             "Color nodes by:",
    #             options=["Type", "Property", "Custom"],
    #             key="node_color_by"
    #         )
    #         
    #         if node_color_by == "Property":
    #             all_properties = set()
    #             for node in network.nodes:
    #                 all_properties.update(node.properties.keys())
    #             
    #             if all_properties:
    #                 property_name = st.selectbox(
    #                     "Select property:",
    #                     options=list(all_properties),
    #                     key="node_color_prop"
    #                 )
    #                 coloring_options["node_color_property"] = property_name
    #         
    #         coloring_options["node_color_by"] = node_color_by
    #     
    #     with st.sidebar.expander("Edge Coloring"):
    #         edge_color_by = st.selectbox(
    #             "Color edges by:",
    #             options=["Type", "Weight", "Property"],
    #             key="edge_color_by"
    #         )
    #         
    #         if edge_color_by == "Property":
    #             all_properties = set()
    #             for edge in network.edges:
    #                 all_properties.update(edge.properties.keys())
    #             
    #             if all_properties:
    #                 property_name = st.selectbox(
    #                     "Select property:",
    #                     options=list(all_properties),
    #                     key="edge_color_prop"
    #                 )
    #                 coloring_options["edge_color_property"] = property_name
    #         
    #         coloring_options["edge_color_by"] = edge_color_by
    #     
    #     return coloring_options
    
    def render_labeling_controls(self, network: ChemicalNetwork) -> Dict[str, Any]:
        st.sidebar.header("Labeling Options")
        labeling_options = {}
        
        with st.sidebar.expander("Node Labels", expanded=True):
            # Get all available columns from node properties
            all_node_columns = set(['id', 'label'])  # Base columns
            for node in network.nodes:
                all_node_columns.update(node.properties.keys())
            
            # Sort columns with library_compound_name first if it exists
            sorted_columns = sorted(all_node_columns)
            if 'library_compound_name' in sorted_columns:
                sorted_columns.remove('library_compound_name')
                sorted_columns.insert(0, 'library_compound_name')
            
            node_label_column = st.selectbox(
                "Display column for nodes:",
                options=sorted_columns,
                index=0 if 'library_compound_name' in sorted_columns else sorted_columns.index('label'),
                key="node_label_column",
                help="Choose which column to display as the node label"
            )
            labeling_options["node_label_column"] = node_label_column
        
        with st.sidebar.expander("Edge Labels"):
            edge_labels_enabled = st.checkbox(
                "Enable edge labels",
                value=False,
                key="edge_labels_enabled",
                help="Show labels on edges (may impact performance on large networks)"
            )
            labeling_options["edge_labels_enabled"] = edge_labels_enabled
            
            if edge_labels_enabled:
                # Get all available columns from edge properties
                all_edge_columns = set(['source', 'target', 'type', 'weight'])  # Base columns
                for edge in network.edges:
                    all_edge_columns.update(edge.properties.keys())
                
                edge_label_column = st.selectbox(
                    "Display column for edges:",
                    options=sorted(all_edge_columns),
                    key="edge_label_column",
                    help="Choose which column to display as the edge label"
                )
                labeling_options["edge_label_column"] = edge_label_column
                
                if len(network.edges) > 100:
                    st.warning("⚠️ Large network detected. Edge labels may impact performance.")
        
        return labeling_options
    
    def render_node_sizing_controls(self, network: ChemicalNetwork) -> Dict[str, Any]:
        st.sidebar.header("Node Sizing")
        sizing_options = {}
        
        with st.sidebar.expander("Node Size Options"):
            size_by = st.selectbox(
                "Size nodes by:",
                options=["Fixed", "Property"],
                key="node_size_by"
            )
            
            if size_by == "Fixed":
                fixed_size = st.slider(
                    "Node size:", 
                    min_value=10, 
                    max_value=100, 
                    value=25,
                    key="fixed_node_size"
                )
                sizing_options["fixed_size"] = fixed_size
            else:
                all_numeric_properties = set()
                for node in network.nodes:
                    for prop, value in node.properties.items():
                        try:
                            float(value)
                            all_numeric_properties.add(prop)
                        except (TypeError, ValueError):
                            pass
                
                if all_numeric_properties:
                    property_name = st.selectbox(
                        "Select property:",
                        options=list(all_numeric_properties),
                        key="node_size_prop"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        min_size = st.slider(
                            "Min size:", 
                            min_value=5, 
                            max_value=50, 
                            value=10,
                            key="min_node_size"
                        )
                    with col2:
                        max_size = st.slider(
                            "Max size:", 
                            min_value=20, 
                            max_value=100, 
                            value=50,
                            key="max_node_size"
                        )
                    
                    sizing_options["size_property"] = property_name
                    sizing_options["min_size"] = min_size
                    sizing_options["max_size"] = max_size
            
            sizing_options["size_by"] = size_by
        
        return sizing_options
    
    # COMMENTED OUT - Node Selection removed for cleaner UI
    # def render_selection_controls(self, network: ChemicalNetwork) -> Optional[List[str]]:
    #     st.sidebar.header("Node Selection")
    #     
    #     with st.sidebar.expander("Select Specific Nodes"):
    #         all_nodes = [(node.id, node.label) for node in network.nodes]
    #         
    #         selected_nodes = st.multiselect(
    #             "Select nodes to highlight:",
    #             options=[node_id for node_id, _ in all_nodes],
    #             format_func=lambda x: next(
    #                 label for node_id, label in all_nodes if node_id == x
    #             ),
    #             key="selected_nodes"
    #         )
    #         
    #         if selected_nodes:
    #             depth = st.slider(
    #                 "Include neighbors up to depth:",
    #                 min_value=0,
    #                 max_value=5,
    #                 value=1,
    #                 key="neighbor_depth"
    #             )
    #             
    #             if depth > 0:
    #                 st.session_state['neighbor_depth'] = depth
    #                 return selected_nodes
    #         
    #     return None
    
    def render_library_smiles_toggle(self, network: ChemicalNetwork) -> bool:
        """Render toggle for library_SMILES C/O/N filtering."""
        st.sidebar.header("Special Filters")
        
        with st.sidebar.expander("Library SMILES Filter"):
            # Check if any nodes have library_SMILES property 
            has_library_smiles = any(
                "library_SMILES" in node.properties 
                for node in network.nodes
            )
            
            if has_library_smiles:
                smiles_filter_enabled = st.checkbox(
                    "Show only nodes connected to library_SMILES containing C, O, or N",
                    value=False,
                    key="library_smiles_filter",
                    help="This will show only nodes that are connected to nodes with library_SMILES containing the letters C, O, or N"
                )
                return smiles_filter_enabled
            else:
                st.info("No nodes with library_SMILES property found in the current network.")
                return False
        
        return False

    def render_molecular_networking_filters(self, network: ChemicalNetwork) -> Dict[str, bool]:
        """Render molecular networking edge filters."""
        # Check if any edges have molecular_networking property
        has_molecular_networking = any(
            "molecular_networking" in edge.properties 
            for edge in network.edges
        )
        
        filters = {}
        
        if has_molecular_networking:
            with st.sidebar.expander("Molecular Networking Filters", expanded=True):
                # Molecular Networking Edges (molecular_networking = 1)
                molecular_networking_enabled = st.checkbox(
                    "Molecular Networking Edges",
                    value=True,  # Default on
                    key="molecular_networking_filter",
                    help="Show edges with molecular_networking = 1"
                )
                filters["molecular_networking"] = molecular_networking_enabled
                
                # Edit Distance 1 Predicted Edges (molecular_networking = 0)  
                edit_distance_enabled = st.checkbox(
                    "Edit Distance 1 Predicted Edges",
                    value=True,  # Default on
                    key="edit_distance_filter", 
                    help="Show edges with molecular_networking = 0"
                )
                filters["edit_distance"] = edit_distance_enabled
        else:
            st.info("No edges with molecular_networking property found in the current network.")
            filters["molecular_networking"] = True
            filters["edit_distance"] = True
        
        return filters