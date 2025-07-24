import streamlit as st
from typing import Dict, Any, List, Optional
import pandas as pd
import re
from ..data.models import ChemicalNetwork


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
        
        # Display basic node info
        st.markdown(f"**Node ID:** {node.id}")
        st.markdown(f"**Node Type:** {node.node_type.value}")
        
        # Display mapped fields if they exist in properties
        st.markdown("### Chemical Properties")
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
        
        # Placeholder for Spectrum Visualizer
        st.markdown("### Spectrum Visualizer")
        with st.container():
            st.info("🔬 Spectrum visualization will be available here in a future update")
            # Placeholder image area
            st.empty()
        
        st.markdown("---")
        if st.button("Close Details", key=f"close_details_{node.id}"):
            if 'selected_node_id' in st.session_state:
                del st.session_state.selected_node_id
            st.rerun()
    
