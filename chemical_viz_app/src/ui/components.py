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
        [data-testid="stFileUploader"] {
            background-color: white !important;
        }
        
        /* Dropdown/selectbox styling - white background */
        .stSelectbox > div > div {
            background-color: white !important;
            border: 1px solid #ced4da;
            border-radius: 4px;
            color: black !important;
        }
        .stSelectbox > div > div:focus-within {
            border-color: #007bff;
            box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
        }
        [data-testid="stSelectbox"] {
            background-color: white !important;
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
        
        st.title("🧪 Chemical Data Network Visualization")
        st.markdown("---")
    
    @staticmethod
    def render_data_upload() -> Optional[ChemicalNetwork]:
        with st.expander("📁 Data Upload", expanded=True):
            upload_type = st.radio(
                "Select data source:",
                ["Use Sample Data", "Upload CSV Files", "Upload JSON File", "Upload GraphML File"]
            )
            
            if upload_type == "Use Sample Data":
                if st.button("Load Sample Network"):
                    return "sample"
            
            elif upload_type == "Upload CSV Files":
                col1, col2 = st.columns(2)
                
                with col1:
                    nodes_file = st.file_uploader(
                        "Upload nodes CSV",
                        type=['csv'],
                        key="nodes_csv"
                    )
                
                with col2:
                    edges_file = st.file_uploader(
                        "Upload edges CSV",
                        type=['csv'],
                        key="edges_csv"
                    )
                
                if nodes_file and edges_file:
                    return ("csv", nodes_file, edges_file)
            
            elif upload_type == "Upload JSON File":
                json_file = st.file_uploader(
                    "Upload network JSON",
                    type=['json'],
                    key="network_json"
                )
                
                if json_file:
                    return ("json", json_file)
            
            elif upload_type == "Upload GraphML File":
                graphml_file = st.file_uploader(
                    "Upload GraphML file",
                    type=['graphml', 'xml'],
                    key="network_graphml",
                    help="GraphML files preserve all node and edge attributes from tools like Cytoscape, Gephi, or yEd"
                )
                
                if graphml_file:
                    return ("graphml", graphml_file)
        
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
        with st.expander("📊 View Data Tables"):
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
        with st.expander("💾 Export Options"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Export as HTML", key="export_html"):
                    st.info("HTML export functionality will be implemented")
            
            with col2:
                if st.button("Export as PNG", key="export_png"):
                    st.info("PNG export functionality will be implemented")
            
            with col3:
                if st.button("Export Network Data", key="export_data"):
                    st.info("Data export functionality will be implemented")
    
    @staticmethod
    def render_error_message(error: str):
        st.error(f"❌ Error: {error}")
    
    @staticmethod
    def render_success_message(message: str):
        st.success(f"✅ {message}")
    
    @staticmethod
    def render_info_message(message: str):
        st.info(f"ℹ️ {message}")
    
    @staticmethod
    def render_warning_message(message: str):
        st.warning(f"⚠️ {message}")
    
    @staticmethod
    def render_progress_bar(progress: float, text: str = "Processing..."):
        progress_bar = st.progress(progress)
        st.text(text)
        return progress_bar
    
    @staticmethod
    def render_node_detail_panel(node: 'ChemicalNode'):
        """Render detailed information panel for a selected node."""
        st.subheader(f"Node Details: {node.label}")
        
        # Display basic node info
        st.markdown(f"**Node ID:** {node.id}")
        st.markdown(f"**Node Type:** {node.node_type.value}")
        
        # Spectrum and Molecular Visualizations - MOVED TO TOP
        st.markdown("### Visualizations")
        
        # Import ModiFinder utilities
        from ..utils.modifinder_utils import ModiFinderUtils
        
        # Create tabs for different visualizations
        viz_tabs = []
        
        # Check if we have SMILES data for molecular structure
        smiles = node.properties.get('library_SMILES')
        if smiles and str(smiles).strip():
            viz_tabs.append("Molecular Structure")
        
        # Check if we have spectrum data
        spectrum_fields = ['spectrum_id', 'SpectrumID', 'usi', 'USI']
        has_spectrum = any(node.properties.get(field) for field in spectrum_fields)
        if has_spectrum:
            viz_tabs.append("Spectrum")
        
        if viz_tabs:
            # Create tabs for available visualizations
            if len(viz_tabs) == 1:
                # Single visualization - no tabs needed
                if viz_tabs[0] == "Molecular Structure":
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
                        
                elif viz_tabs[0] == "Spectrum":
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
            else:
                # Multiple visualizations - use tabs
                tab_objects = st.tabs(viz_tabs)
                
                for i, tab_name in enumerate(viz_tabs):
                    with tab_objects[i]:
                        if tab_name == "Molecular Structure":
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
                                
                        elif tab_name == "Spectrum":
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
        else:
            # No visualization data available
            st.info("🔬 No spectrum or molecular structure data available for visualization")
        
        # Chemical Properties - MOVED BELOW VISUALIZATIONS
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
        
        for property_key, display_name in field_mappings.items():
            if property_key in node.properties:
                value = node.properties[property_key]
                if value is not None and str(value).strip():
                    # Special handling for SMILES and InChI to prevent auto-linking
                    if property_key in ['library_SMILES', 'library_InChI']:
                        # Use st.code for better formatting of chemical strings
                        st.markdown(f"**{display_name}:**")
                        st.code(str(value), language=None)
                    else:
                        # Regular markdown for other fields
                        st.markdown(f"**{display_name}:** {value}")
                    displayed_fields.add(property_key)
        
        # Display any additional properties not in the mapping
        other_properties = {k: v for k, v in node.properties.items() 
                          if k not in displayed_fields and v is not None and str(v).strip()}
        
        if other_properties:
            st.markdown("### Additional Properties")
            for key, value in other_properties.items():
                formatted_key = key.replace('_', ' ').title()
                # Check if this might be a chemical formula or SMILES string
                value_str = str(value)
                if any(pattern in value_str.lower() for pattern in ['smiles', 'inchi']) or \
                   any(char in value_str for char in ['=', '+', '-', '(', ')', '[', ']', '@']):
                    # Likely chemical data - use code block for better formatting
                    st.markdown(f"**{formatted_key}:**")
                    st.code(value_str, language=None)
                else:
                    # Regular display
                    st.markdown(f"**{formatted_key}:** {value}")
        
        st.markdown("---")
        if st.button("Close Details", key=f"close_details_{node.id}"):
            if 'selected_node_id' in st.session_state:
                del st.session_state.selected_node_id
            st.rerun()
    
    @staticmethod
    def render_edge_detail_panel(edge: 'ChemicalEdge', network: 'ChemicalNetwork'):
        """Render detailed information panel for a selected edge."""
        st.subheader(f"Edge Details: {edge.source} → {edge.target}")
        
        # Display basic edge info
        st.markdown(f"**Edge Type:** {edge.edge_type.value}")
        st.markdown(f"**Weight:** {edge.weight}")
        
        # Spectrum Alignment Visualization - MOVED TO TOP
        st.markdown("### Spectrum Alignment")
        
        # Import ModiFinder utilities
        from ..utils.modifinder_utils import ModiFinderUtils
        
        # Get source and target nodes first to extract USI values
        source_node = network.get_node_by_id(edge.source)
        target_node = network.get_node_by_id(edge.target)
        
        # Extract USI from source node (usi1) and target node (usi2)
        usi1 = None  # Source node USI
        usi2 = None  # Target node USI
        
        if source_node:
            # Look for USI in source node properties
            usi1 = source_node.properties.get('usi') or source_node.properties.get('USI')
        
        if target_node:
            # Look for USI in target node properties  
            usi2 = target_node.properties.get('usi') or target_node.properties.get('USI')
        
        if usi1 and usi2:
            st.info(f"🔬 Generating spectrum alignment between {edge.source} and {edge.target}")
            
            if ModiFinderUtils.is_available():
                with st.spinner("Generating spectrum alignment visualization..."):
                    img_base64 = ModiFinderUtils.generate_alignment_image(usi1, usi2)
                    
                if img_base64:
                    ModiFinderUtils.display_image_from_base64(
                        img_base64, 
                        f"Spectrum Alignment: {edge.source} ↔ {edge.target}"
                    )
                    
                    # Display USI information
                    with st.expander("📊 USI Details"):
                        st.markdown("**USI 1 (Source):**")
                        st.code(usi1, language=None)
                        st.markdown("**USI 2 (Target):**")
                        st.code(usi2, language=None)
                else:
                    ModiFinderUtils.render_error_placeholder("Could not generate spectrum alignment")
            else:
                ModiFinderUtils.render_error_placeholder("ModiFinder package not available")
        else:
            st.info("🔬 No USI information found in node data for spectrum alignment")
            
            # Show what fields were searched
            with st.expander("🔍 Debug: Node USI Information"):
                st.write("Searched for USI data in node properties:")
                st.code("usi, USI")
                
                if source_node:
                    st.write(f"**Source Node ({edge.source}) properties:**")
                    st.json(source_node.properties)
                else:
                    st.write(f"❌ Source node ({edge.source}) not found")
                
                if target_node:
                    st.write(f"**Target Node ({edge.target}) properties:**")
                    st.json(target_node.properties)
                else:
                    st.write(f"❌ Target node ({edge.target}) not found")
        
        # Display edge properties - MOVED BELOW VISUALIZATION
        if edge.properties:
            st.markdown("### Edge Properties")
            for key, value in edge.properties.items():
                if value is not None and str(value).strip():
                    formatted_key = key.replace('_', ' ').title()
                    # Check if this might be a URL or special data
                    value_str = str(value)
                    
                    if any(pattern in value_str.lower() for pattern in ['http', 'gnps', 'usi']):
                        # Other URL data - use code block for better formatting
                        st.markdown(f"**{formatted_key}:**")
                        st.code(value_str, language=None)
                    else:
                        # Regular display
                        st.markdown(f"**{formatted_key}:** {value}")
        
        # Display connected nodes information (nodes already retrieved above)
        st.markdown("### Connected Nodes")
        
        if source_node and target_node:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Source Node: {source_node.label}**")
                st.markdown(f"ID: {source_node.id}")
                st.markdown(f"Type: {source_node.node_type.value}")
                
                # Show key properties
                if 'library_compound_name' in source_node.properties:
                    st.markdown(f"Compound: {source_node.properties['library_compound_name']}")
                if 'library_SMILES' in source_node.properties:
                    st.markdown("SMILES:")
                    st.code(str(source_node.properties['library_SMILES']), language=None)
            
            with col2:
                st.markdown(f"**Target Node: {target_node.label}**")
                st.markdown(f"ID: {target_node.id}")
                st.markdown(f"Type: {target_node.node_type.value}")
                
                # Show key properties
                if 'library_compound_name' in target_node.properties:
                    st.markdown(f"Compound: {target_node.properties['library_compound_name']}")
                if 'library_SMILES' in target_node.properties:
                    st.markdown("SMILES:")
                    st.code(str(target_node.properties['library_SMILES']), language=None)
        else:
            st.warning("Could not find complete node information for this edge")
        
        st.markdown("---")
        if st.button("Close Details", key=f"close_edge_details_{edge.source}_{edge.target}"):
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
        st.markdown("### 🔬 ModiFinder Spectrum Alignment")
        
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
        st.markdown(f"[🔗 Open in new tab]({modifinder_url})")
        
        # Add button to hide the visualization
        if st.button("Hide Visualization", key="hide_modifinder"):
            st.session_state.show_modifinder_viz = False
            st.rerun()
    
