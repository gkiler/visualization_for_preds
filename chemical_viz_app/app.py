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
from src.ui.resizable_columns import ResizableColumns
from src.utils.annotation_manager import AnnotationManager
from src.data.annotation_processor import AnnotationProcessor


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
    if 'selected_edge_id' not in st.session_state:
        st.session_state.selected_edge_id = None
    if 'labeling_settings' not in st.session_state:
        st.session_state.labeling_settings = {
            'node_label_column': 'library_compound_name',
            'edge_labels_enabled': False,
            'edge_label_column': 'type'
        }
    if 'column_ratio' not in st.session_state:
        st.session_state.column_ratio = [3, 1]  # Default 3:1 ratio for main columns
    if 'show_modifinder_viz' not in st.session_state:
        st.session_state.show_modifinder_viz = False
    
    # Initialize annotation-related session state
    AnnotationManager.initialize_session_state()


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
                    st.session_state.selected_edge_id = None  # Clear edge selection
                    st.session_state.show_modifinder_viz = False  # Reset ModiFinder visualization
                    st.rerun()


def render_edge_click_buttons(network: ChemicalNetwork):
    """Render invisible buttons for each edge to handle clicks."""
    if not network or not network.edges:
        return
    
    # Create a container for invisible buttons
    with st.container():
        # Use columns to minimize visual impact
        button_cols = st.columns(min(len(network.edges), 10))  # Max 10 columns
        
        for i, edge in enumerate(network.edges):
            col_idx = i % len(button_cols)
            with button_cols[col_idx]:
                # Create unique edge ID using index to handle multiple edges between same nodes
                edge_id = f"{edge.source}-{edge.target}-{i}"
                display_id = f"{edge.source}-{edge.target}"
                button_key = f"edge_click_{edge_id}"
                if st.button(
                    f"Select {display_id}", 
                    key=button_key,
                    help=f"Click to select edge {edge.source} → {edge.target} (#{i})",
                    type="secondary",
                    use_container_width=True
                ):
                    st.session_state.selected_edge_id = edge_id
                    st.session_state.selected_node_id = None  # Clear node selection
                    st.session_state.show_modifinder_viz = False  # Reset ModiFinder visualization
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
            
            # Set current project for new GraphML uploads
            annotation_manager = AnnotationManager()
            annotation_manager.set_current_project(graphml_file.name)
            
            # Store GraphML filename in session state for later use
            st.session_state.current_graphml_filename = graphml_file.name
            
            # MISSING STEP 1: Apply existing user annotations to network
            print(f"DEBUG: Applying existing annotations to network...")
            original_annotations = len([n for n in network.nodes if n.properties.get('annotation_status') == 'user_annotated'])
            
            try:
                network = annotation_manager.apply_annotations_to_network(network)
                applied_annotations = len([n for n in network.nodes if n.properties.get('annotation_status') == 'user_annotated'])
                print(f"DEBUG: Applied {applied_annotations - original_annotations} user annotations to network")
                
                # MISSING STEP 2: Generate ModiFinder links for annotated nodes
                from .src.data.annotation_processor import AnnotationProcessor
                processor = AnnotationProcessor()
                modifinder_results = processor.generate_modifinder_links_for_existing_annotations(network)
                print(f"DEBUG: Generated {modifinder_results['links_created']} ModiFinder links for annotated nodes")
                
            except Exception as e:
                print(f"DEBUG: Error during annotation processing: {str(e)}")
                # Set default values for display
                applied_annotations = original_annotations
                modifinder_results = {'links_created': 0}
            
            UIComponents.render_success_message(
                f"GraphML file loaded successfully! Detected {len(network.nodes)} nodes and {len(network.edges)} edges with attributes. Applied {applied_annotations - original_annotations} annotations and generated {modifinder_results['links_created']} ModiFinder links."
            )
            return network
        
        elif upload_data[0] == "project":
            _, project_filename = upload_data
            
            # Load the project annotations
            annotation_manager = AnnotationManager()
            success = annotation_manager.load_project(project_filename)
            
            if success:
                # Load project data
                project_path = annotation_manager.annotations_dir / project_filename
                with open(project_path, 'r') as f:
                    project_data = json.load(f)
                
                graphml_source = project_data.get('graphml_source', 'Unknown')
                annotation_count = len(project_data.get('annotations', {}))
                
                UIComponents.render_success_message(
                    f"Project loaded successfully! {annotation_count} annotations restored from {graphml_source}"
                )
                
                # Note: We return None here because the project only contains annotations
                # The user needs to upload the corresponding GraphML file or we need to store it
                UIComponents.render_info_message(
                    "Project annotations loaded. Please upload the corresponding GraphML file to visualize the network."
                )
                return None
            else:
                UIComponents.render_error_message(f"Failed to load project: {project_filename}")
                return None
    
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
                
                # Load existing annotations
                annotation_manager = AnnotationManager()
                annotation_manager.load_annotations_from_file()
                
            else:
                for error in errors:
                    UIComponents.render_error_message(error)
    
    if st.session_state.network:
        # Apply any existing annotations to the base network before filtering
        annotation_manager = AnnotationManager()
        st.session_state.network = annotation_manager.apply_annotations_to_network(st.session_state.network)
        
        sidebar_controls = SidebarControls()
        
        # Add column width control
        column_ratio = sidebar_controls.render_column_width_control()
        
        # Move Special Filters to the top - check for library_SMILES filter toggle first
        library_smiles_filter = sidebar_controls.render_library_smiles_toggle(st.session_state.network)
        
        # Add molecular networking filters
        molecular_networking_filters = sidebar_controls.render_molecular_networking_filters(st.session_state.network)
        
        # Use default values for removed controls
        viz_controls = {"physics": True, "height": "750px"}
        st.session_state.visualization_settings.update(viz_controls)
        
        labeling_options = sidebar_controls.render_labeling_controls(st.session_state.network)
        st.session_state.labeling_settings.update(labeling_options)
        
        # Set empty filters since filtering sections are removed
        node_filters = []
        edge_filters = []
        
        st.session_state.active_filters['node_filters'] = node_filters
        st.session_state.active_filters['edge_filters'] = edge_filters
        
        # Use default values for removed coloring and selection controls
        coloring_options = {"node_color_by": "Type", "edge_color_by": "Type"}
        sizing_options = sidebar_controls.render_node_sizing_controls(st.session_state.network)
        
        selected_nodes = None
        
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
        
        # Apply molecular networking filters
        filter_handler = NetworkFilter()
        filtered_edges = filter_handler.filter_edges_by_molecular_networking(
            st.session_state.filtered_network,
            molecular_networking_filters.get("molecular_networking", True),
            molecular_networking_filters.get("edit_distance", True)
        )
        
        # Update the network with filtered edges and corresponding nodes
        if filtered_edges:
            edge_node_ids = set()
            for edge in filtered_edges:
                edge_node_ids.add(edge.source)
                edge_node_ids.add(edge.target)
            
            filtered_nodes = [
                node for node in st.session_state.filtered_network.nodes
                if node.id in edge_node_ids
            ]
            
            st.session_state.filtered_network = ChemicalNetwork(
                nodes=filtered_nodes,
                edges=filtered_edges,
                metadata=st.session_state.network.metadata
            )
        else:
            # If no edges match, keep all nodes but remove all edges
            st.session_state.filtered_network = ChemicalNetwork(
                nodes=st.session_state.filtered_network.nodes,
                edges=[],
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
        
        # Network visualization takes full width at the top
        # Enhanced network visualization header
        st.markdown("""
        <div class="content-section">
            <h2>Network Visualization</h2>
            <div style="background: #e3f2fd; border: 1px solid #2196f3; border-radius: 4px; padding: 0.75rem; margin: 0.5rem 0;">
                <strong>Interaction Guide:</strong>
                <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
                    <li>Click nodes to view detailed molecular information</li>
                    <!-- <li>Click edges to see spectrum alignments and molecular formulas</li> -->
                    <li>Drag nodes to rearrange the network layout</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        visualizer = NetworkVisualizer()
        
        # Use default node coloring (library_SMILES-based green/grey implemented in NetworkVisualizer)
        node_colors = None
        node_sizes = None
        edge_colors = None
        
        if sizing_options.get('size_by') == 'Property':
            prop = sizing_options.get('size_property')
            if prop:
                node_sizes = visualizer.get_node_sizes_by_property(
                    st.session_state.filtered_network,
                    prop,
                    sizing_options.get('min_size', 10),
                    sizing_options.get('max_size', 50)
                )
        
        # Use default edge coloring (type-based from config)
        
        html_file = visualizer.visualize_network(
            st.session_state.filtered_network,
            height=st.session_state.visualization_settings.get('height', '750px'),
            physics=st.session_state.visualization_settings.get('physics', True),
            node_colors=node_colors,
            node_sizes=node_sizes,
            edge_colors=edge_colors,
            node_label_column=st.session_state.labeling_settings.get('node_label_column', 'label'),
            show_edge_labels=st.session_state.labeling_settings.get('edge_labels_enabled', False),
            edge_label_column=st.session_state.labeling_settings.get('edge_label_column', 'type')
        )
        
        visualizer.display_in_streamlit(html_file)
        
        # Render hidden buttons for node and edge clicking (below visualization)
        with st.expander("Selection Interface", expanded=False):
            st.info("These buttons can be clicked programmatically when you click nodes or edges in the network above")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                st.markdown("**Node Buttons**")
                render_node_click_buttons(st.session_state.filtered_network)
            
            with col_btn2:
                st.markdown("**Edge Buttons**")
                render_edge_click_buttons(st.session_state.filtered_network)
        
        # Add postMessage fallback listener
        postmessage_listener = """
        <script>
            window.addEventListener('message', function(event) {
                if (event.data && event.data.type === 'node_click') {
                    const nodeId = event.data.nodeId;
                    console.log('Received node click message:', nodeId);
                    
                    // Multiple strategies to find the button - consistent with edge handling
                    const buttons = document.querySelectorAll('button');
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
                        console.log('Found and clicking button for node:', nodeId);
                        targetButton.click();
                    } else {
                        console.log('Could not find button for node via postMessage:', nodeId);
                    }
                }
                else if (event.data && event.data.type === 'edge_click') {
                    const edgeId = event.data.edgeId;
                    console.log('Received edge click message:', edgeId);
                    
                    // Multiple strategies to find the button - match the PyVis handler logic
                    const buttons = document.querySelectorAll('button');
                    let targetButton = null;
                    const buttonKey = 'edge_click_' + edgeId;
                    
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
                        console.log('Found and clicking button for edge:', edgeId);
                        targetButton.click();
                    } else {
                        console.log('Could not find button for edge via postMessage:', edgeId);
                    }
                }
            });
        </script>
        """
        components.html(postmessage_listener, height=0)
        
        # Details section below the network visualization
        st.markdown("---")
        
        # Display details for selected node or edge
        if 'selected_node_id' in st.session_state and st.session_state.selected_node_id:
            selected_node = st.session_state.filtered_network.get_node_by_id(st.session_state.selected_node_id)
            if selected_node:
                UIComponents.render_node_detail_panel(selected_node)
            else:
                st.info("Selected node not found in current filtered network")
                
        elif 'selected_edge_id' in st.session_state and st.session_state.selected_edge_id:
            selected_edge = st.session_state.filtered_network.get_edge_by_id(st.session_state.selected_edge_id)
            if selected_edge:
                # Create two columns for edge details and ModiFinder visualization
                col_edge, col_modifinder = st.columns([1, 1])
                
                with col_edge:
                    UIComponents.render_edge_detail_panel(selected_edge, st.session_state.filtered_network)
                
                with col_modifinder:
                    st.markdown("""
                    <div class="content-section">
                        <h2>ModiFinder Visualization</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if selected_edge.properties.get('modifinder_link'):
                        if st.button("Visualize ModiFinder", type="primary", use_container_width=True):
                            st.session_state.show_modifinder_viz = True
                        
                        # Display the iframe if button was clicked
                        if st.session_state.show_modifinder_viz:
                            UIComponents.render_modifinder_visualization(selected_edge.properties['modifinder_link'])
                    else:
                        st.info("No ModiFinder link available for this edge")
            else:
                st.info("Selected edge not found in current filtered network")
        else:
            st.info("Select a node or edge in the network above to view details")
        
        # SMILES Annotation Processing Panel
        st.markdown("---")
        annotation_processor = AnnotationProcessor()
        annotation_processor.render_pending_updates_panel()
        
        # Network Statistics with improved styling
        st.markdown("""
        <div class="content-section">
            <h2>Network Statistics</h2>
        </div>
        """, unsafe_allow_html=True)
        
        col_stats1, col_stats2 = st.columns(2)
        
        with col_stats1:
            st.markdown("### Original Network")
            UIComponents.render_network_stats(st.session_state.network)
            
        with col_stats2:
            st.markdown("### Filtered Network")
            UIComponents.render_network_stats(st.session_state.filtered_network)
        
        UIComponents.render_data_tables(st.session_state.filtered_network)
        
        UIComponents.render_export_options()
    
    else:
        st.info("Please upload network data to begin visualization.")


if __name__ == "__main__":
    main()