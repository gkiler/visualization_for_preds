import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path
import tempfile
import json

from src.data.loader import DataLoader
from src.data.models import ChemicalNetwork
from src.visualization.network import NetworkVisualizer
from src.visualization.filters import NetworkFilter
from src.ui.components import UIComponents
from src.ui.sidebar import SidebarControls
from src.utils.figures import FigureHandler


def initialize_session_state():
    if 'network' not in st.session_state:
        st.session_state.network = None
    if 'filtered_network' not in st.session_state:
        st.session_state.filtered_network = None
    if 'visualization_settings' not in st.session_state:
        st.session_state.visualization_settings = {}
    if 'active_filters' not in st.session_state:
        st.session_state.active_filters = {
            'node_filters': [],
            'edge_filters': []
        }
    if 'selected_node_id' not in st.session_state:
        st.session_state.selected_node_id = None


def render_node_click_buttons(network: ChemicalNetwork):
    """Render invisible buttons for each node to handle clicks."""
    if not network or not network.nodes:
        return
    
    # Create a container for invisible buttons
    with st.container():
        # Use columns to minimize visual impact
        button_cols = st.columns(min(len(network.nodes), 10))  # Max 10 columns
        
        for i, node in enumerate(network.nodes):
            col_idx = i % len(button_cols)
            with button_cols[col_idx]:
                # Create button with zero height and hidden text
                button_key = f"node_click_{node.id}"
                if st.button(
                    f"Select {node.id}", 
                    key=button_key,
                    help=f"Click to select node {node.label}",
                    type="secondary",
                    use_container_width=True
                ):
                    st.session_state.selected_node_id = node.id
                    st.rerun()


def load_network_data(upload_data):
    try:
        if upload_data == "sample":
            network = DataLoader.create_sample_network()
            UIComponents.render_success_message("Sample network loaded successfully!")
            return network
        
        elif upload_data[0] == "csv":
            _, nodes_file, edges_file = upload_data
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_nodes:
                tmp_nodes.write(nodes_file.read())
                nodes_path = tmp_nodes.name
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_edges:
                tmp_edges.write(edges_file.read())
                edges_path = tmp_edges.name
            
            network = DataLoader.load_network_from_csv(nodes_path, edges_path)
            UIComponents.render_success_message("CSV files loaded successfully!")
            return network
        
        elif upload_data[0] == "json":
            _, json_file = upload_data
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_json:
                tmp_json.write(json_file.read())
                json_path = tmp_json.name
            
            network = DataLoader.load_network_from_json(json_path)
            UIComponents.render_success_message("JSON file loaded successfully!")
            return network
        
        elif upload_data[0] == "graphml":
            _, graphml_file = upload_data
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.graphml') as tmp_graphml:
                tmp_graphml.write(graphml_file.read())
                graphml_path = tmp_graphml.name
            
            network = DataLoader.load_network_from_graphml(graphml_path)
            UIComponents.render_success_message(
                f"GraphML file loaded successfully! Detected {len(network.nodes)} nodes and {len(network.edges)} edges with attributes."
            )
            return network
    
    except Exception as e:
        UIComponents.render_error_message(f"Error loading data: {str(e)}")
        return None


def apply_filters(network, node_filters, edge_filters):
    if not node_filters and not edge_filters:
        return network
    
    filter_handler = NetworkFilter()
    filtered_nodes, filtered_edges = filter_handler.apply_multiple_filters(
        network,
        node_filters=node_filters if node_filters else None,
        edge_filters=edge_filters if edge_filters else None,
        filter_mode="AND"
    )
    
    filtered_network = ChemicalNetwork(
        nodes=filtered_nodes,
        edges=filtered_edges,
        metadata=network.metadata
    )
    
    return filtered_network


def main():
    UIComponents.render_header()
    initialize_session_state()
    
    upload_data = UIComponents.render_data_upload()
    
    if upload_data:
        network = load_network_data(upload_data)
        if network:
            is_valid, errors = DataLoader.validate_network(network)
            if is_valid:
                st.session_state.network = network
                st.session_state.filtered_network = network
            else:
                for error in errors:
                    UIComponents.render_error_message(error)
    
    if st.session_state.network:
        UIComponents.render_network_stats(st.session_state.network)
        
        sidebar_controls = SidebarControls()
        
        viz_controls = sidebar_controls.render_visualization_controls()
        st.session_state.visualization_settings.update(viz_controls)
        
        node_filters = sidebar_controls.render_node_filters(st.session_state.network)
        edge_filters = sidebar_controls.render_edge_filters(st.session_state.network)
        
        st.session_state.active_filters['node_filters'] = node_filters
        st.session_state.active_filters['edge_filters'] = edge_filters
        
        coloring_options = sidebar_controls.render_coloring_controls(st.session_state.network)
        sizing_options = sidebar_controls.render_node_sizing_controls(st.session_state.network)
        
        selected_nodes = sidebar_controls.render_selection_controls(st.session_state.network)
        
        # Check for library_SMILES filter toggle
        library_smiles_filter = sidebar_controls.render_library_smiles_toggle(st.session_state.network)
        
        st.session_state.filtered_network = apply_filters(
            st.session_state.network,
            node_filters,
            edge_filters
        )
        
        # Apply library_SMILES filter if enabled
        if library_smiles_filter:
            filter_handler = NetworkFilter()
            nodes, edges = filter_handler.filter_nodes_connected_to_library_smiles_with_con(
                st.session_state.filtered_network
            )
            st.session_state.filtered_network = ChemicalNetwork(
                nodes=nodes,
                edges=edges,
                metadata=st.session_state.network.metadata
            )
        
        if selected_nodes and 'neighbor_depth' in st.session_state:
            filter_handler = NetworkFilter()
            nodes, edges = filter_handler.filter_connected_component(
                st.session_state.filtered_network,  # Use already filtered network
                selected_nodes,
                st.session_state['neighbor_depth']
            )
            st.session_state.filtered_network = ChemicalNetwork(
                nodes=nodes,
                edges=edges,
                metadata=st.session_state.network.metadata
            )
        
        # Create layout columns - adjust the ratio to add space for node details
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.subheader("Network Visualization")
            st.info("💡 Click on any node in the network to view detailed information in the right panel")
            
            visualizer = NetworkVisualizer()
            
            node_colors = None
            node_sizes = None
            edge_colors = None
            
            if coloring_options.get('node_color_by') == 'Property':
                prop = coloring_options.get('node_color_property')
                if prop:
                    unique_values = set()
                    for node in st.session_state.filtered_network.nodes:
                        if prop in node.properties:
                            unique_values.add(node.properties[prop])
                    
                    import matplotlib.cm as cm
                    import matplotlib.colors as mcolors
                    
                    cmap = cm.get_cmap('viridis')
                    color_map = {}
                    for i, value in enumerate(sorted(unique_values)):
                        color = mcolors.rgb2hex(cmap(i / len(unique_values)))
                        color_map[value] = color
                    
                    node_colors = visualizer.get_node_colors_by_property(
                        st.session_state.filtered_network,
                        prop,
                        color_map
                    )
            
            if sizing_options.get('size_by') == 'Property':
                prop = sizing_options.get('size_property')
                if prop:
                    node_sizes = visualizer.get_node_sizes_by_property(
                        st.session_state.filtered_network,
                        prop,
                        sizing_options.get('min_size', 10),
                        sizing_options.get('max_size', 50)
                    )
            
            if coloring_options.get('edge_color_by') == 'Weight':
                edge_colors = {}
                weights = [e.weight for e in st.session_state.filtered_network.edges]
                if weights:
                    min_w, max_w = min(weights), max(weights)
                    for edge in st.session_state.filtered_network.edges:
                        normalized = (edge.weight - min_w) / (max_w - min_w) if max_w > min_w else 0.5
                        color = f"rgba(0, 0, 255, {normalized})"
                        edge_colors[(edge.source, edge.target)] = color
            
            html_file = visualizer.visualize_network(
                st.session_state.filtered_network,
                height=st.session_state.visualization_settings.get('height', '750px'),
                physics=st.session_state.visualization_settings.get('physics', True),
                node_colors=node_colors,
                node_sizes=node_sizes,
                edge_colors=edge_colors
            )
            
            visualizer.display_in_streamlit(html_file)
            
            # Render hidden buttons for node clicking (below visualization)
            with st.expander("🔧 Node Selection Interface", expanded=False):
                st.info("These buttons can be clicked programmatically when you click nodes in the network above")
                render_node_click_buttons(st.session_state.filtered_network)
            
            # Add postMessage fallback listener
            postmessage_listener = """
            <script>
                window.addEventListener('message', function(event) {
                    if (event.data && event.data.type === 'node_click') {
                        const nodeId = event.data.nodeId;
                        console.log('Received node click message:', nodeId);
                        
                        // Try to find and click the button
                        const buttons = document.querySelectorAll('button');
                        for (let button of buttons) {
                            if (button.textContent && button.textContent.includes(nodeId)) {
                                console.log('Found and clicking button for node:', nodeId);
                                button.click();
                                break;
                            }
                        }
                    }
                });
            </script>
            """
            components.html(postmessage_listener, height=0)
        
        with col2:
            st.subheader("Additional Figures")
            FigureHandler.render_figure_management_ui()
        
        with col3:
            # Display node details if a node is selected
            if 'selected_node_id' in st.session_state and st.session_state.selected_node_id:
                selected_node = st.session_state.filtered_network.get_node_by_id(st.session_state.selected_node_id)
                if selected_node:
                    UIComponents.render_node_detail_panel(selected_node)
                else:
                    st.info("Selected node not found in current filtered network")
            else:
                st.info("Select a node to view details")
        
        UIComponents.render_data_tables(st.session_state.filtered_network)
        
        UIComponents.render_export_options()
    
    else:
        st.info("Please upload network data to begin visualization.")


if __name__ == "__main__":
    main()