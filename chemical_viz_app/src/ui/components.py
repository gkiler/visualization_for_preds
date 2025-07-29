import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import pandas as pd
import re
from ..data.models import ChemicalNetwork

if TYPE_CHECKING:
    from ..data.models import ChemicalNode, ChemicalEdge


class UIComponents:
    
    @staticmethod
    def _sanitize_column_name(col_name: str) -> str:
        """Sanitize column names for Arrow compatibility."""
        # Replace special characters that cause issues
        sanitized = re.sub(r'[#@$%^&*()+=[\]{}|\\:";\'<>?/~`]', '_', str(col_name))
        # Remove leading/trailing underscores and spaces
        sanitized = sanitized.strip('_').strip()
        # Ensure it's not empty
        if not sanitized:
            sanitized = "column"
        return sanitized
    
    @staticmethod
    def _normalize_dataframe_types(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DataFrame column types for Arrow compatibility."""
        df_copy = df.copy()
        
        for col in df_copy.columns:
            # Check if column has mixed types
            column_data = df_copy[col]
            unique_types = set(type(x).__name__ for x in column_data.dropna())
            
            # If we have mixed types or problematic types, convert to string
            if len(unique_types) > 1 or any(t in ['float', 'int'] for t in unique_types):
                # Check if any values are actually numeric types mixed with strings
                has_numeric = any(isinstance(x, (int, float)) for x in column_data.dropna())
                has_string = any(isinstance(x, str) for x in column_data.dropna())
                
                if has_numeric and has_string:
                    # Mixed numeric and string - convert all to string
                    df_copy[col] = column_data.astype(str).replace('nan', '')
                elif has_numeric:
                    # All numeric but might have NaN - ensure consistent numeric type
                    try:
                        # Try to keep as float if possible
                        df_copy[col] = pd.to_numeric(column_data, errors='coerce')
                    except:
                        df_copy[col] = column_data.astype(str).replace('nan', '')
        
        return df_copy
    
    @staticmethod
    def render_header():
        st.set_page_config(
            page_title="Chemical Data Visualization",
            page_icon="🧪",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Add custom CSS for white background and improved styling
        st.markdown("""
        <style>
        /* Force white background on everything */
        .stApp {
            background-color: white !important;
        }
        .main .block-container {
            background-color: white !important;
            padding-top: 2rem;
            max-width: 100%;
        }
        
        /* Improved typography hierarchy */
        .main h1 {
            font-size: 2.5rem;
            font-weight: 600;
            color: #1e3a5f !important;
            margin-bottom: 0.5rem;
        }
        .main h2 {
            font-size: 1.8rem;
            font-weight: 500;
            color: #2c5aa0 !important;
            margin-top: 2rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 0.5rem;
        }
        .main h3 {
            font-size: 1.3rem;
            font-weight: 500;
            color: #495057 !important;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
        }
        .main h4 {
            font-size: 1.1rem;
            font-weight: 500;
            color: #6c757d !important;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        
        /* Enhanced section styling */
        .content-section {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .detail-panel {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 0.5rem 0;
        }
        
        .property-item {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 0.75rem;
            margin: 0.5rem 0;
            border-left: 4px solid #007bff;
        }
        
        .chemical-data {
            background: #f1f3f4;
            border: 1px solid #dadce0;
            border-radius: 4px;
            padding: 0.5rem;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            word-break: break-all;
        }
        
        /* Override Streamlit's default dark backgrounds */
        .stApp > div {
            background-color: white !important;
        }
        [data-testid="stAppViewContainer"] {
            background-color: white !important;
        }
        [data-testid="stHeader"] {
            background-color: white !important;
        }
        [data-testid="stToolbar"] {
            background-color: white !important;
        }
        
        /* Sidebar styling - white background */
        .sidebar .sidebar-content {
            background-color: white !important;
            border-right: 2px solid #e9ecef;
        }
        .sidebar .sidebar-header {
            background-color: white !important;
        }
        [data-testid="stSidebar"] {
            background-color: white !important;
        }
        [data-testid="stSidebar"] > div {
            background-color: white !important;
        }
        
        /* File upload styling - white background */
        .stFileUploader {
            background-color: white !important;
            border: 2px dashed #dee2e6;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        .stFileUploader:hover {
            border-color: #007bff;
            background-color: #f8f9ff !important;
        }
        .stFileUploader > div {
            background-color: white !important;
        }
        .stFileUploader > div > div {
            background-color: white !important;
        }
        .stFileUploader * {
            background-color: white !important;
            color: black !important;
        }
        [data-testid="stFileUploader"] {
            background-color: white !important;
        }
        [data-testid="stFileUploader"] > div {
            background-color: white !important;
        }
        [data-testid="stFileUploader"] * {
            background-color: white !important;
            color: black !important;
        }
        
        /* Dropdown/selectbox styling - white background */
        .stSelectbox {
            background-color: white !important;
        }
        .stSelectbox > div {
            background-color: white !important;
        }
        .stSelectbox > div > div {
            background-color: white !important;
            border: 1px solid #ced4da;
            border-radius: 4px;
            color: black !important;
        }
        .stSelectbox > div > div > div {
            background-color: white !important;
            color: black !important;
        }
        .stSelectbox > div > div:focus-within {
            border-color: #007bff;
            box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
        }
        .stSelectbox * {
            background-color: white !important;
            color: black !important;
        }
        [data-testid="stSelectbox"] {
            background-color: white !important;
        }
        [data-testid="stSelectbox"] > div {
            background-color: white !important;
        }
        [data-testid="stSelectbox"] * {
            background-color: white !important;
            color: black !important;
        }
        
        /* Additional dropdown menu styling */
        .stSelectbox [role="listbox"] {
            background-color: white !important;
            border: 1px solid #ced4da;
        }
        .stSelectbox [role="option"] {
            background-color: white !important;
            color: black !important;
        }
        .stSelectbox [role="option"]:hover {
            background-color: #f8f9fa !important;
            color: black !important;
        }
        
        /* Target the dropdown overlay and options more specifically */
        div[data-baseweb="select"] {
            background-color: white !important;
        }
        div[data-baseweb="select"] > div {
            background-color: white !important;
            color: black !important;
        }
        div[data-baseweb="select"] * {
            background-color: white !important;
            color: black !important;
        }
        div[data-baseweb="popover"] {
            background-color: white !important;
        }
        div[data-baseweb="popover"] > div {
            background-color: white !important;
            color: black !important;
        }
        div[data-baseweb="popover"] * {
            background-color: white !important;
            color: black !important;
        }
        
        /* More specific dropdown menu targeting */
        .css-1wa3eu0-placeholder {
            color: black !important;
        }
        .css-1uccc91-singleValue {
            color: black !important;
        }
        .css-26l3qy-menu {
            background-color: white !important;
        }
        .css-4ljt47-MenuList {
            background-color: white !important;
        }
        .css-1n7v3ny-option {
            background-color: white !important;
            color: black !important;
        }
        
        /* Comprehensive dropdown menu styling - catch all variations */
        [class*="css-"][class*="menu"] {
            background-color: white !important;
        }
        [class*="css-"][class*="option"] {
            background-color: white !important;
            color: black !important;
        }
        [class*="css-"][class*="MenuList"] {
            background-color: white !important;
        }
        
        /* Target any div that looks like a dropdown menu */
        div[role="listbox"],
        div[role="menu"],
        div[role="combobox"],
        ul[role="listbox"],
        ul[role="menu"] {
            background-color: white !important;
            color: black !important;
        }
        
        div[role="listbox"] *,
        div[role="menu"] *,
        div[role="combobox"] *,
        ul[role="listbox"] *,
        ul[role="menu"] * {
            background-color: white !important;
            color: black !important;
        }
        
        /* Catch any element with option role */
        [role="option"] {
            background-color: white !important;
            color: black !important;
        }
        [role="option"]:hover,
        [role="option"]:focus {
            background-color: #f8f9fa !important;
            color: black !important;
        }
        
        /* Nuclear option - target any element inside stSelectbox */
        .stSelectbox div,
        .stSelectbox span,
        .stSelectbox ul,
        .stSelectbox li {
            background-color: white !important;
            color: black !important;
        }
        
        /* Radio button styling - white background */
        .stRadio > div {
            background-color: white !important;
            padding: 0.5rem;
            border-radius: 4px;
            border: 1px solid #e9ecef;
        }
        [data-testid="stRadio"] {
            background-color: white !important;
        }
        
        /* Expander styling - white background */
        .streamlit-expanderHeader {
            background-color: white !important;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            color: black !important;
        }
        .streamlit-expanderHeader:hover {
            background-color: #f8f9fa !important;
        }
        .streamlit-expanderContent {
            background-color: white !important;
            border: 1px solid #dee2e6;
            border-top: none;
            border-radius: 0 0 4px 4px;
            padding: 1rem;
        }
        [data-testid="stExpander"] {
            background-color: white !important;
        }
        
        /* Button styling - keep colorful buttons but ensure text is readable */
        .stButton > button {
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.375rem 0.75rem;
            font-weight: 500;
        }
        .stButton > button:hover {
            background-color: #0056b3;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Secondary button styling */
        .stButton > button[kind="secondary"] {
            background-color: white !important;
            color: black !important;
            border: 1px solid #ced4da;
        }
        .stButton > button[kind="secondary"]:hover {
            background-color: #f8f9fa !important;
            color: black !important;
        }
        
        /* Ensure all containers have white background */
        .stContainer, .stColumns {
            background-color: white !important;
        }
        
        /* Override any dark text and make it black */
        .stApp, .stApp *, div, span, p, h1, h2, h3, h4, h5, h6 {
            color: black !important;
        }
        
        /* Metrics styling - white background */
        [data-testid="metric-container"] {
            background-color: white !important;
            padding: 1rem;
            border-radius: 4px;
            border: 1px solid #e9ecef;
            margin: 0.5rem 0;
        }
        
        /* DataFrame styling - white background */
        .stDataFrame {
            background-color: white !important;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }
        [data-testid="stDataFrame"] {
            background-color: white !important;
        }
        
        /* Tab styling - white background */
        .stTabs {
            background-color: white !important;
        }
        .stTabs > div {
            background-color: white !important;
        }
        .stTabs > div > div {
            background-color: white !important;
        }
        .stTabs > div > div > div {
            background-color: white !important;
            color: black !important;
        }
        .stTabs > div > div > div[data-baseweb="tab-highlight"] {
            background-color: #007bff !important;
            color: white !important;
        }
        
        /* Info/warning/error boxes - white background */
        .stAlert {
            background-color: white !important;
            border: 1px solid #dee2e6;
            color: black !important;
        }
        [data-testid="stAlert"] {
            background-color: white !important;
            color: black !important;
        }
        
        /* Code blocks - grey background */
        .stCode {
            background-color: #e9ecef !important;
            border: 1px solid #ced4da;
            color: black !important;
        }
        pre, code {
            background-color: #e9ecef !important;
            color: black !important;
            padding: 0.5rem;
            border-radius: 4px;
        }
        
        /* Spinner - ensure it's visible */
        .stSpinner {
            color: #007bff !important;
        }
        
        /* Input fields - white background */
        .stTextInput > div > div > input {
            background-color: white !important;
            color: black !important;
            border: 1px solid #ced4da;
        }
        
        /* Markdown content - ensure black text */
        .stMarkdown {
            color: black !important;
        }
        .stMarkdown * {
            color: black !important;
        }
        
        /* Success/info messages - white background */
        .stSuccess {
            background-color: white !important;
            border: 1px solid #28a745;
            color: black !important;
        }
        .stInfo {
            background-color: white !important;
            border: 1px solid #17a2b8;
            color: black !important;
        }
        .stWarning {
            background-color: white !important;
            border: 1px solid #ffc107;
            color: black !important;
        }
        .stError {
            background-color: white !important;
            border: 1px solid #dc3545;
            color: black !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.title("Chemical Data Network Visualization")
        st.markdown("---")
    
    @staticmethod
    def render_data_upload() -> Optional[ChemicalNetwork]:
        st.markdown("""
        <div class="content-section">
            <h2>Data Upload</h2>
            <p>Upload your GraphML network file to begin visualization</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("Load Network Data", expanded=True):
            upload_type = st.radio(
                "Choose your data source:",
                ["Upload GraphML File", "Load Previous Project", "Use Sample Data"],
                help="GraphML files preserve all node and edge attributes. Previous projects restore your annotations."
            )
            
            if upload_type == "Upload GraphML File":
                st.markdown("""
                <div class="detail-panel">
                    <p><strong>GraphML Format:</strong> Preserves all node and edge attributes</p>
                    <p>Compatible with Cytoscape, Gephi, yEd, and other network analysis tools</p>
                    <p><em>Drag and drop your .graphml file below or click to browse</em></p>
                </div>
                """, unsafe_allow_html=True)
                
                graphml_file = st.file_uploader(
                    "Select GraphML file",
                    type=['graphml', 'xml'],
                    key="network_graphml",
                    help="GraphML files preserve all node and edge attributes from tools like Cytoscape, Gephi, or yEd"
                )
                
                if graphml_file:
                    return ("graphml", graphml_file)
                    
            elif upload_type == "Load Previous Project":
                st.markdown("""
                <div class="detail-panel">
                    <p><strong>Previous Projects:</strong> Load your saved work with annotations</p>
                    <p>Select from previously worked on GraphML files with your SMILES annotations</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Import here to avoid circular imports
                from ..utils.annotation_manager import AnnotationManager
                annotation_manager = AnnotationManager()
                
                # Get available projects
                projects = annotation_manager.get_available_projects()
                
                if not projects:
                    st.info("No previous projects found. Upload a GraphML file and annotate some nodes to create your first project.")
                else:
                    # Create options for dropdown
                    project_options = {}
                    for project in projects:
                        display_name = f"{project['graphml_source']} ({project['annotation_count']} annotations) - {project['saved_at'][:16]}"
                        project_options[display_name] = project['filename']
                    
                    selected_display = st.selectbox(
                        "Select a previous project:",
                        options=list(project_options.keys()),
                        help="Projects are named after the original GraphML file and show creation time"
                    )
                    
                    if selected_display and st.button("Load Selected Project", use_container_width=True):
                        selected_filename = project_options[selected_display]
                        return ("project", selected_filename)
            
            elif upload_type == "Use Sample Data":
                st.markdown("""
                <div class="detail-panel">
                    <p><strong>Sample Dataset:</strong> Chemical molecular network with 275 nodes and 565 edges</p>
                    <p>Perfect for exploring the interface features and testing functionality</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Load Sample Network", use_container_width=True):
                    return "sample"
        
        return None
    
    @staticmethod
    def render_network_stats(network: ChemicalNetwork):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Nodes", len(network.nodes))
        
        with col2:
            st.metric("Total Edges", len(network.edges))
        
        with col3:
            node_types = set(node.node_type.value for node in network.nodes)
            st.metric("Node Types", len(node_types))
        
        with col4:
            edge_types = set(edge.edge_type.value for edge in network.edges)
            st.metric("Edge Types", len(edge_types))
    
    @staticmethod
    def render_data_tables(network: ChemicalNetwork):
        st.markdown("""
        <div class="content-section">
            <h2>Data Tables</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("View Raw Data Tables", expanded=False):
            tab1, tab2 = st.tabs(["Nodes", "Edges"])
            
            with tab1:
                try:
                    nodes_data = []
                    for node in network.nodes:
                        node_dict = {
                            "ID": node.id,
                            "Label": node.label,
                            "Type": node.node_type.value
                        }
                        # Sanitize property keys and add them
                        for key, value in node.properties.items():
                            sanitized_key = UIComponents._sanitize_column_name(key)
                            node_dict[sanitized_key] = value
                        nodes_data.append(node_dict)
                    
                    if nodes_data:
                        nodes_df = pd.DataFrame(nodes_data)
                        # Normalize column names
                        nodes_df.columns = [UIComponents._sanitize_column_name(col) for col in nodes_df.columns]
                        # Normalize data types
                        nodes_df = UIComponents._normalize_dataframe_types(nodes_df)
                        
                        st.dataframe(
                            nodes_df, 
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No node data to display")
                        
                except Exception as e:
                    st.error(f"Error displaying nodes table: {str(e)}")
                    # Fallback: show basic info
                    st.write(f"Nodes count: {len(network.nodes)}")
                    if network.nodes:
                        st.write("Sample node properties:", list(network.nodes[0].properties.keys())[:10])
            
            with tab2:
                try:
                    edges_data = []
                    for edge in network.edges:
                        edge_dict = {
                            "Source": edge.source,
                            "Target": edge.target,
                            "Type": edge.edge_type.value,
                            "Weight": edge.weight
                        }
                        # Sanitize property keys and add them
                        for key, value in edge.properties.items():
                            sanitized_key = UIComponents._sanitize_column_name(key)
                            edge_dict[sanitized_key] = value
                        edges_data.append(edge_dict)
                    
                    if edges_data:
                        edges_df = pd.DataFrame(edges_data)
                        # Normalize column names
                        edges_df.columns = [UIComponents._sanitize_column_name(col) for col in edges_df.columns]
                        # Normalize data types
                        edges_df = UIComponents._normalize_dataframe_types(edges_df)
                        
                        st.dataframe(
                            edges_df, 
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No edge data to display")
                        
                except Exception as e:
                    st.error(f"Error displaying edges table: {str(e)}")
                    # Fallback: show basic info
                    st.write(f"Edges count: {len(network.edges)}")
                    if network.edges:
                        st.write("Sample edge properties:", list(network.edges[0].properties.keys())[:10])
    
    @staticmethod
    def render_export_options():
        st.markdown("""
        <div class="content-section">
            <h2>Export Options</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("Export Data and Visualizations", expanded=False):
            st.markdown("### Export Formats")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("""
                <div class="detail-panel">
                    <h4>Annotated GraphML</h4>
                    <p>Export GraphML file including all your SMILES annotations</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Export GraphML + Annotations", key="export_annotated_graphml", use_container_width=True):
                    UIComponents._handle_graphml_export()
            
            with col2:
                st.markdown("""
                <div class="detail-panel">
                    <h4>Interactive Visualization</h4>
                    <p>Export the current network as an interactive HTML file</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Export as HTML", key="export_html", use_container_width=True):
                    st.info("HTML export functionality will be implemented")
            
            with col3:
                st.markdown("""
                <div class="detail-panel">
                    <h4>Static Image</h4>
                    <p>Save the network visualization as a high-quality PNG image</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Export as PNG", key="export_png", use_container_width=True):
                    st.info("PNG export functionality will be implemented")
            
            with col4:
                st.markdown("""
                <div class="detail-panel">
                    <h4>Raw Data</h4>
                    <p>Download the filtered network data in CSV or JSON format</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Export Network Data", key="export_data", use_container_width=True):
                    st.info("Data export functionality will be implemented")
    
    @staticmethod
    def _handle_graphml_export():
        """Handle GraphML export with annotations."""
        if 'network' not in st.session_state or not st.session_state.network:
            st.error("No network loaded. Please load a GraphML file first.")
            return
        
        try:
            from ..utils.annotation_manager import AnnotationManager
            
            annotation_manager = AnnotationManager()
            network = st.session_state.network
            
            # First, ensure all annotations are applied to the network
            network_with_annotations = annotation_manager.apply_annotations_to_network(network)
            
            # Export to GraphML
            with st.spinner("Exporting annotated GraphML file..."):
                output_path = annotation_manager.export_annotated_graphml(network_with_annotations)
            
            # Count annotations for user feedback
            annotated_nodes = [n for n in network_with_annotations.nodes 
                             if n.properties.get('annotation_status') == 'user_annotated']
            
            # Read the file for download
            with open(output_path, 'rb') as f:
                graphml_data = f.read()
            
            # Provide download button
            filename = output_path.split('/')[-1]  # Get just the filename
            st.download_button(
                label=f"📥 Download {filename}",
                data=graphml_data,
                file_name=filename,
                mime="application/xml",
                use_container_width=True
            )
            
            st.success(f"✅ GraphML exported successfully!")
            st.info(f"📊 Included {len(annotated_nodes)} user annotations in {len(network_with_annotations.nodes)} nodes")
            
            # Show some details about what's included
            if len(annotated_nodes) > 0:
                with st.expander("Annotation Details", expanded=False):
                    st.write("**Annotated nodes:**")
                    for node in annotated_nodes[:10]:  # Show first 10
                        smiles = node.properties.get('library_SMILES', 'Unknown')
                        st.write(f"- {node.label} ({node.id}): `{smiles[:50]}...`")
                    if len(annotated_nodes) > 10:
                        st.write(f"... and {len(annotated_nodes) - 10} more")
            
            # Clean up temporary file
            import os
            try:
                os.remove(output_path)
            except:
                pass  # Don't worry if cleanup fails
                
        except Exception as e:
            st.error(f"❌ Export failed: {str(e)}")
            print(f"ERROR: GraphML export failed: {str(e)}")
    
    @staticmethod
    def render_error_message(error: str):
        st.error(f"Error: {error}")
    
    @staticmethod
    def render_success_message(message: str):
        st.success(f"{message}")
    
    @staticmethod
    def render_info_message(message: str):
        st.info(f"{message}")
    
    @staticmethod
    def render_warning_message(message: str):
        st.warning(f"{message}")
    
    @staticmethod
    def render_progress_bar(progress: float, text: str = "Processing..."):
        progress_bar = st.progress(progress)
        st.text(text)
        return progress_bar
    
    @staticmethod
    def _render_smiles_annotation_section(node: 'ChemicalNode'):
        """Render SMILES annotation section for a node."""
        from ..utils.annotation_manager import AnnotationManager
        from ..utils.modifinder_utils import ModiFinderUtils
        
        # Initialize annotation manager
        annotation_manager = AnnotationManager()
        
        # Check current SMILES status
        current_smiles = node.properties.get('library_SMILES', '')
        has_smiles = current_smiles and str(current_smiles).strip()
        annotation = annotation_manager.get_annotation(node.id)
        
        st.markdown("### SMILES Annotation")
        
        # Show current status
        if node.is_annotated():
            st.success(f"✅ Node annotated by user")
            if annotation:
                st.caption(f"Annotated: {annotation.get('timestamp', 'Unknown time')}")
            # Debug info
            st.caption(f"DEBUG: annotation_status = {node.properties.get('annotation_status')}")
        elif has_smiles:
            st.info(f"SMILES data available: `{str(current_smiles)[:50]}...`")
        else:
            st.warning("No SMILES data - annotation needed")
        
        # Debug: Show all annotation-related properties
        with st.expander("Debug: Node Properties", expanded=False):
            annotation_props = {k: v for k, v in node.properties.items() if 'annotation' in k.lower() or k == 'library_SMILES'}
            if annotation_props:
                st.json(annotation_props)
            else:
                st.write("No annotation properties found")
        
        # SMILES input form
        with st.expander("Add/Edit SMILES", expanded=not has_smiles):
            # Input field
            placeholder_text = str(current_smiles) if has_smiles else "Enter SMILES string (e.g., CC(=O)Oc1ccccc1C(=O)O)"
            
            # Use session state for the input to enable real-time preview
            input_key = f"smiles_input_{node.id}"
            if input_key not in st.session_state:
                st.session_state[input_key] = str(current_smiles) if has_smiles else ""
            
            new_smiles = st.text_input(
                "SMILES String:",
                value=st.session_state[input_key],
                placeholder=placeholder_text,
                key=f"smiles_field_{node.id}",
                help="Enter a valid SMILES string for this molecule"
            )
            
            # Update session state
            st.session_state[input_key] = new_smiles
            
            # Real-time preview
            if new_smiles and new_smiles.strip() and new_smiles != current_smiles:
                st.markdown("#### Preview:")
                
                # Basic SMILES validation
                if UIComponents._validate_smiles_basic(new_smiles):
                    # Show molecular structure preview
                    if ModiFinderUtils.is_available():
                        try:
                            with st.spinner("Generating molecular structure preview..."):
                                img_base64 = ModiFinderUtils.generate_molecule_image(new_smiles.strip())
                                
                            if img_base64:
                                ModiFinderUtils.display_image_from_base64(
                                    img_base64,
                                    f"Preview: {node.label}",
                                    # width=300
                                )
                            else:
                                st.error("Could not generate molecular structure from SMILES")
                                
                        except Exception as e:
                            st.error(f"Error generating preview: {str(e)}")
                    else:
                        st.info("ModiFinder not available for preview")
                        st.code(new_smiles, language=None)
                else:
                    st.error("Invalid SMILES format")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Update SMILES", 
                           key=f"update_smiles_{node.id}",
                           type="primary",
                           disabled=not new_smiles or not new_smiles.strip() or new_smiles == current_smiles):
                    UIComponents._handle_smiles_update(node, new_smiles.strip())
            
            with col2:
                if st.button("Reset", key=f"reset_smiles_{node.id}"):
                    st.session_state[input_key] = str(current_smiles) if has_smiles else ""
                    st.rerun()
            
            with col3:
                if annotation and st.button("Remove Annotation", key=f"remove_annotation_{node.id}"):
                    annotation_manager.remove_annotation(node.id)
                    st.success("Annotation removed")
                    st.rerun()
    
    @staticmethod
    def _validate_smiles_basic(smiles: str) -> bool:
        """Basic SMILES validation."""
        if not smiles or not isinstance(smiles, str):
            return False
        
        smiles = smiles.strip()
        if len(smiles) < 2:
            return False
        
        # Basic character check - SMILES should contain valid characters
        valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789()[]{}=#+-.@/\\')
        if not all(c in valid_chars for c in smiles):
            return False
        
        # Basic bracket matching
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        for char in smiles:
            if char in brackets:
                stack.append(brackets[char])
            elif char in brackets.values():
                if not stack or stack.pop() != char:
                    return False
        
        return len(stack) == 0
    
    @staticmethod
    def _handle_smiles_update(node: 'ChemicalNode', new_smiles: str):
        """Handle SMILES update button click."""
        from ..utils.annotation_manager import AnnotationManager
        from datetime import datetime
        
        # Initialize annotation manager
        annotation_manager = AnnotationManager()
        
        try:
            # Get original SMILES
            original_smiles = node.properties.get('library_SMILES')
            
            # Add annotation
            success = annotation_manager.add_annotation(
                node.id,
                new_smiles,
                original_smiles,
                {
                    'node_label': node.label,
                    'update_method': 'user_input'
                }
            )
            
            if success:
                # Store pending update in session state for processing
                if 'pending_smiles_updates' not in st.session_state:
                    st.session_state.pending_smiles_updates = {}
                
                st.session_state.pending_smiles_updates[node.id] = {
                    'new_smiles': new_smiles,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'pending'
                }
                
                st.success(f"SMILES annotation added for {node.label}")
                
                # Auto-process the annotation immediately to generate ModiFinder links
                from ..data.annotation_processor import AnnotationProcessor
                processor = AnnotationProcessor()
                
                if st.session_state.network:
                    with st.spinner("Processing annotation and generating ModiFinder links..."):
                        # Process the single annotation immediately
                        updated_network, results = processor.process_pending_annotations(st.session_state.network)
                        
                        # Update the network in session state
                        st.session_state.network = updated_network
                        st.session_state.filtered_network = updated_network
                        
                        # Show results
                        if results['processed'] > 0:
                            st.info(f"🔗 Generated {results['modifinder_links_created']} ModiFinder link(s) for connected nodes")
                        else:
                            st.info("Annotation processed (no ModiFinder links generated - connected nodes may lack spectrum data)")
                
                # Save annotations to current project
                graphml_filename = getattr(st.session_state, 'current_graphml_filename', None)
                if not annotation_manager.save_current_project(graphml_filename):
                    # Fallback to legacy saving
                    annotation_manager.save_annotations_to_file()
                
            else:
                st.error("Failed to add annotation")
                
        except Exception as e:
            st.error(f"Error updating SMILES: {str(e)}")
    
    @staticmethod
    def render_node_detail_panel(node: 'ChemicalNode'):
        """Render detailed information panel for a selected node with two-column layout."""
        # Header with improved styling - spans full width above columns
        st.markdown(f"""
        <div class="content-section">
            <h2>{node.label}</h2>
            <div style="display: flex; gap: 2rem; margin-bottom: 1rem;">
                <div><strong>ID:</strong> <code>{node.id}</code></div>
                <div><strong>Type:</strong> <span style="background: #e3f2fd; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.9rem;">{node.node_type.value}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Create two-column layout
        col_info, col_viz = st.columns([1, 1])
        
        # LEFT COLUMN: Node Information
        with col_info:
            # SMILES Annotation Section
            UIComponents._render_smiles_annotation_section(node)
        
        # RIGHT COLUMN: Molecule Visualization
        with col_viz:
            # Import ModiFinder utilities
            from ..utils.modifinder_utils import ModiFinderUtils
            
            # Check if we have SMILES data for molecular structure
            smiles = node.properties.get('library_SMILES')
            has_smiles = smiles and str(smiles).strip()
            
            # Check if we have spectrum data
            spectrum_fields = ['spectrum_id', 'SpectrumID', 'usi', 'USI']
            has_spectrum = any(node.properties.get(field) for field in spectrum_fields)
            
            # Display molecular structure (priority)
            if has_smiles:
                st.markdown("#### Molecular Structure")
                ModiFinderUtils.render_loading_placeholder("Generating molecular structure...")
                
                if ModiFinderUtils.is_available():
                    img_base64 = ModiFinderUtils.generate_molecule_image(str(smiles).strip())
                    if img_base64:
                        ModiFinderUtils.display_image_from_base64(
                            img_base64, 
                            f"Molecular Structure: {node.label}"
                        )
                    else:
                        ModiFinderUtils.render_error_placeholder("Could not generate molecular structure")
                else:
                    ModiFinderUtils.render_error_placeholder("ModiFinder package not available")
            
            # Display spectrum visualization if available
            if has_spectrum:
                st.markdown("#### Spectrum Visualization")
                ModiFinderUtils.render_loading_placeholder("Generating spectrum visualization...")
                
                if ModiFinderUtils.is_available():
                    img_base64 = ModiFinderUtils.generate_spectrum_image(node.properties)
                    if img_base64:
                        ModiFinderUtils.display_image_from_base64(
                            img_base64, 
                            f"Spectrum: {node.label}"
                        )
                    else:
                        ModiFinderUtils.render_error_placeholder("Could not generate spectrum visualization")
                else:
                    ModiFinderUtils.render_error_placeholder("ModiFinder package not available")
            
            # Show message if no visualization data available
            if not has_smiles and not has_spectrum:
                st.info("No molecular structure or spectrum data available for visualization")
        
        # Back to LEFT COLUMN: Add Chemical Properties
        with col_info:
            st.markdown("### Chemical Properties")
            
            # Field mapping as requested by user
            field_mappings = {
                'library_SMILES': 'SMILES',
                'library_compound_name': 'Compound Name',
                'library_InChI': 'InChI',
                'rt': 'Retention Time',
                'mz': 'Precursor Mass',
                'library_classfire_superclass': 'ClassyFire Superclass',
                'library_classyfire_class': 'ClassyFire Class',
                'library_classyfire_subclass': 'ClassyFire Subclass',
                'library_npclassifier_superclass': 'npclassifier Super Class',
                'library_npclassifier_class': 'npclassifier Class',
                'library_npclassifier_pathway': 'npclassifier Pathway',
                'SpectrumID': 'Spectrum ID',
                'Compound_Name': 'Compound Name',
                'Adduct': 'Adduct',
                'molecular_formula': 'Molecular Formula'
            }
        
            displayed_fields = set()
            
            # Group properties into categories
            structural_props = []
            analytical_props = []
            classification_props = []
            
            for property_key, display_name in field_mappings.items():
                if property_key in node.properties:
                    value = node.properties[property_key]
                    if value is not None and str(value).strip():
                        prop_data = {
                            'key': property_key,
                            'name': display_name,
                            'value': value
                        }
                        
                        # Categorize properties
                        if property_key in ['library_SMILES', 'library_InChI', 'molecular_formula']:
                            structural_props.append(prop_data)
                        elif property_key in ['rt', 'mz', 'SpectrumID', 'Adduct']:
                            analytical_props.append(prop_data)
                        else:
                            classification_props.append(prop_data)
                        
                        displayed_fields.add(property_key)
            
            # Display categorized properties
            if structural_props:
                st.markdown("#### Structural Information")
                for prop in structural_props:
                    if prop['key'] in ['library_SMILES', 'library_InChI']:
                        st.markdown(f"""
                        <div class="property-item">
                            <strong>{prop['name']}:</strong>
                            <div class="chemical-data">{str(prop['value'])}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="property-item">
                            <strong>{prop['name']}:</strong> {prop['value']}
                        </div>
                        """, unsafe_allow_html=True)
            
            if analytical_props:
                st.markdown("#### Analytical Data")
                for prop in analytical_props:
                    st.markdown(f"""
                    <div class="property-item">
                        <strong>{prop['name']}:</strong> {prop['value']}
                    </div>
                    """, unsafe_allow_html=True)
            
            if classification_props:
                st.markdown("#### Classification")
                for prop in classification_props:
                    st.markdown(f"""
                    <div class="property-item">
                        <strong>{prop['name']}:</strong> {prop['value']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Display any additional properties not in the mapping
            other_properties = {k: v for k, v in node.properties.items() 
                              if k not in displayed_fields and v is not None and str(v).strip()}
            
            if other_properties:
                st.markdown("#### Additional Properties")
                for key, value in other_properties.items():
                    formatted_key = key.replace('_', ' ').title()
                    value_str = str(value)
                
                    # Check if this might be a chemical formula or SMILES string
                    if any(pattern in value_str.lower() for pattern in ['smiles', 'inchi']) or \
                       any(char in value_str for char in ['=', '+', '-', '(', ')', '[', ']', '@']):
                        # Likely chemical data - use improved styling
                        st.markdown(f"""
                        <div class="property-item">
                            <strong>{formatted_key}:</strong>
                            <div class="chemical-data">{value_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Regular display with improved styling
                        st.markdown(f"""
                        <div class="property-item">
                            <strong>{formatted_key}:</strong> {value}
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close content-section
        
        # Action button with improved styling - outside columns
        st.markdown("---")
        if st.button("Close Details", key=f"close_details_{node.id}", use_container_width=True):
            if 'selected_node_id' in st.session_state:
                del st.session_state.selected_node_id
            st.rerun()
    
    @staticmethod
    def render_edge_detail_panel(edge: 'ChemicalEdge', network: 'ChemicalNetwork'):
        """Render detailed information panel for a selected edge."""
        # Header with improved styling
        st.markdown(f"""
        <div class="content-section">
            <h2>Edge: {edge.source} → {edge.target}</h2>
            <div style="display: flex; gap: 2rem; margin-bottom: 1rem;">
                <div><strong>Type:</strong> <span style="background: #fff3cd; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.9rem;">{edge.edge_type.value}</span></div>
                <div><strong>Weight:</strong> <code>{edge.weight}</code></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # # Spectrum Alignment Visualization - MOVED TO TOP (COMMENTED OUT)
        # st.markdown("### Spectrum Alignment")
        # 
        # # Import ModiFinder utilities
        # from ..utils.modifinder_utils import ModiFinderUtils
        
        # Get source and target nodes (needed for later sections)
        source_node = network.get_node_by_id(edge.source)
        target_node = network.get_node_by_id(edge.target)
        # 
        # # Extract USI from source node (usi1) and target node (usi2)
        # usi1 = None  # Source node USI
        # usi2 = None  # Target node USI
        # 
        # if source_node:
        #     # Look for USI in source node properties
        #     usi1 = source_node.properties.get('usi') or source_node.properties.get('USI')
        # 
        # if target_node:
        #     # Look for USI in target node properties  
        #     usi2 = target_node.properties.get('usi') or target_node.properties.get('USI')
        # 
        # if usi1 and usi2:
        #     st.info(f"Generating spectrum alignment between {edge.source} and {edge.target}")
        #     
        #     if ModiFinderUtils.is_available():
        #         with st.spinner("Generating spectrum alignment visualization..."):
        #             img_base64 = ModiFinderUtils.generate_alignment_image(usi1, usi2)
        #             
        #         if img_base64:
        #             ModiFinderUtils.display_image_from_base64(
        #                 img_base64, 
        #                 f"Spectrum Alignment: {edge.source} ↔ {edge.target}"
        #             )
        #             
        #             # Display USI information
        #             with st.expander("📊 USI Details"):
        #                 st.markdown("**USI 1 (Source):**")
        #                 st.code(usi1, language=None)
        #                 st.markdown("**USI 2 (Target):**")
        #                 st.code(usi2, language=None)
        #         else:
        #             ModiFinderUtils.render_error_placeholder("Could not generate spectrum alignment")
        #     else:
        #         ModiFinderUtils.render_error_placeholder("ModiFinder package not available")
        # else:
        #     st.info("No USI information found in node data for spectrum alignment")
        #     
        #     # Show what fields were searched
        #     with st.expander("Debug: Node USI Information"):
        #         st.write("Searched for USI data in node properties:")
        #         st.code("usi, USI")
        #         
        #         if source_node:
        #             st.write(f"**Source Node ({edge.source}) properties:**")
        #             st.json(source_node.properties)
        #         else:
        #             st.write(f"Source node ({edge.source}) not found")
        #         
        #         if target_node:
        #             st.write(f"**Target Node ({edge.target}) properties:**")
        #             st.json(target_node.properties)
        #         else:
        #             st.write(f"Target node ({edge.target}) not found")
        
        # Display edge properties - MOVED BELOW VISUALIZATION
        if edge.properties:
            st.markdown('<div class="content-section">', unsafe_allow_html=True)
            st.markdown("### Edge Properties")
            
            # Check for mass decomposition results first
            if 'formula_candidates' in edge.properties:
                st.markdown("#### Possible Molecular Formulas")
                
                # Display delta_mz value if present
                delta_mz = edge.properties.get('delta_mz')
                if delta_mz:
                    st.markdown(f"""
                    <div class="property-item">
                        <strong>Delta m/z:</strong> {float(delta_mz):.4f} Da
                    </div>
                    """, unsafe_allow_html=True)
                    
                # Display primary formula
                primary_formula = edge.properties.get('primary_formula')
                if primary_formula:
                    mass_error = edge.properties.get('formula_mass_error', 0)
                    mass_error_ppm = edge.properties.get('formula_mass_error_ppm', 0)
                    st.markdown(f"""
                    <div class="property-item" style="border-left: 4px solid #28a745;">
                        <strong>Best Match:</strong> <code>{primary_formula}</code><br>
                        <small>Error: {mass_error:.4f} Da ({mass_error_ppm:.1f} ppm)</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Display all candidates
                candidates = edge.properties.get('formula_candidates', [])
                if len(candidates) > 1:
                    with st.expander(f"View all {len(candidates)} formula candidates", expanded=False):
                        st.markdown("""
                        <div style="background: #f8f9fa; padding: 1rem; border-radius: 4px; margin: 0.5rem 0;">
                        """, unsafe_allow_html=True)
                        
                        for i, candidate in enumerate(candidates, 1):
                            formula = candidate.get('formula', 'Unknown')
                            error_da = candidate.get('mass_error', 0)
                            error_ppm = candidate.get('mass_error_ppm', 0)
                            
                            # Color code based on ranking
                            border_color = "#28a745" if i == 1 else "#ffc107" if i <= 3 else "#6c757d"
                            
                            st.markdown(f"""
                            <div style="background: white; border: 1px solid #dee2e6; border-left: 4px solid {border_color}; border-radius: 4px; padding: 0.75rem; margin: 0.5rem 0; display: flex; justify-content: space-between; align-items: center;">
                                <div><strong>{i}. {formula}</strong></div>
                                <div style="text-align: right; font-size: 0.9rem; color: #6c757d;">
                                    <div>{error_da:.4f} Da</div>
                                    <div>{error_ppm:.1f} ppm</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
            
            # Display other properties
            st.markdown("#### Other Properties")
            other_props_found = False
            for key, value in edge.properties.items():
                # Skip mass decomposition fields as they're displayed separately
                if key in ['formula_candidates', 'primary_formula', 'formula_mass_error', 'formula_mass_error_ppm']:
                    continue
                    
                if value is not None and str(value).strip():
                    other_props_found = True
                    formatted_key = key.replace('_', ' ').title()
                    value_str = str(value)
                    
                    if any(pattern in value_str.lower() for pattern in ['http', 'gnps', 'usi']):
                        # URL or special identifier - use chemical-data styling
                        st.markdown(f"""
                        <div class="property-item">
                            <strong>{formatted_key}:</strong>
                            <div class="chemical-data">{value_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Regular display
                        st.markdown(f"""
                        <div class="property-item">
                            <strong>{formatted_key}:</strong> {value}
                        </div>
                        """, unsafe_allow_html=True)
            
            if not other_props_found:
                st.info("No additional properties found for this edge")
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close content-section
        
        # Display connected nodes information (nodes already retrieved above)
        st.markdown('<div class="content-section">', unsafe_allow_html=True)
        st.markdown("### Connected Nodes")
        
        if source_node and target_node:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="detail-panel">
                    <h4>Source: {source_node.label}</h4>
                    <div class="property-item">
                        <strong>ID:</strong> <code>{source_node.id}</code>
                    </div>
                    <div class="property-item">
                        <strong>Type:</strong> <span style="background: #e3f2fd; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.9rem;">{source_node.node_type.value}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # Show key properties
                if 'library_compound_name' in source_node.properties:
                    st.markdown(f"""
                    <div class="property-item">
                        <strong>Compound:</strong> {source_node.properties['library_compound_name']}
                    </div>
                    """, unsafe_allow_html=True)
                if 'library_SMILES' in source_node.properties:
                    st.markdown(f"""
                    <div class="property-item">
                        <strong>SMILES:</strong>
                        <div class="chemical-data">{str(source_node.properties['library_SMILES'])}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="detail-panel">
                    <h4>Target: {target_node.label}</h4>
                    <div class="property-item">
                        <strong>ID:</strong> <code>{target_node.id}</code>
                    </div>
                    <div class="property-item">
                        <strong>Type:</strong> <span style="background: #e3f2fd; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.9rem;">{target_node.node_type.value}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # Show key properties
                if 'library_compound_name' in target_node.properties:
                    st.markdown(f"""
                    <div class="property-item">
                        <strong>Compound:</strong> {target_node.properties['library_compound_name']}
                    </div>
                    """, unsafe_allow_html=True)
                if 'library_SMILES' in target_node.properties:
                    st.markdown(f"""
                    <div class="property-item">
                        <strong>SMILES:</strong>
                        <div class="chemical-data">{str(target_node.properties['library_SMILES'])}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("Could not find complete node information for this edge")
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close content-section
        
        # Action button with improved styling
        st.markdown("---")
        if st.button("Close Details", key=f"close_edge_details_{edge.source}_{edge.target}", use_container_width=True):
            if 'selected_edge_id' in st.session_state:
                del st.session_state.selected_edge_id
            st.rerun()
    
    @staticmethod
    def render_modifinder_visualization(modifinder_url: str):
        """
        Render ModiFinder visualization in an embedded iframe.
        
        Args:
            modifinder_url: The URL from the edge's modifinder_link property
        """
        st.markdown("### ModiFinder Spectrum Alignment")
        
        # Add some context
        st.caption("Interactive spectrum alignment visualization from ModiFinder")
        
        # Create iframe HTML with responsive design
        iframe_html = f"""
        <style>
            .modifinder-container {{
                width: 100%;
                height: 800px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                background-color: white;
            }}
            .modifinder-iframe {{
                width: 100%;
                height: 100%;
                border: none;
            }}
        </style>
        <div class="modifinder-container">
            <iframe
                src="{modifinder_url}"
                class="modifinder-iframe"
                frameborder="0"
                loading="lazy"
                allow="clipboard-write"
            ></iframe>
        </div>
        """
        
        # Display the iframe using components.html
        components.html(iframe_html, height=820)
        
        # Add a link to open in new tab
        st.markdown(f"[Open in new tab]({modifinder_url})")
        
        # Add button to hide the visualization
        if st.button("Hide Visualization", key="hide_modifinder"):
            st.session_state.show_modifinder_viz = False
            st.rerun()
    
