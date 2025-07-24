import streamlit as st
import requests
from typing import Optional, Dict, Any, List
from PIL import Image
from io import BytesIO
import base64
from urllib.parse import urlparse
import tempfile
import os


class FigureHandler:
    
    @staticmethod
    @st.cache_data(ttl=1800)  # Cache for 30 minutes
    def fetch_figure_from_url(url: str) -> Optional[bytes]:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            if 'image' in content_type:
                return response.content
            else:
                st.error(f"URL does not point to an image. Content-Type: {content_type}")
                return None
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching image from URL: {str(e)}")
            return None
    
    @staticmethod
    def display_figure(
        image_data: bytes, 
        caption: Optional[str] = None,
        width: Optional[int] = None,
        use_container_width: bool = True
    ):
        try:
            image = Image.open(BytesIO(image_data))
            st.image(
                image, 
                caption=caption, 
                width=width,
                use_container_width=use_container_width
            )
        except Exception as e:
            st.error(f"Error displaying image: {str(e)}")
    
    @staticmethod
    def create_figure_gallery(
        figures: List[Dict[str, Any]], 
        columns: int = 3
    ):
        cols = st.columns(columns)
        
        for idx, figure in enumerate(figures):
            col_idx = idx % columns
            
            with cols[col_idx]:
                if 'url' in figure:
                    image_data = FigureHandler.fetch_figure_from_url(figure['url'])
                    if image_data:
                        FigureHandler.display_figure(
                            image_data,
                            caption=figure.get('caption', f"Figure {idx + 1}"),
                            use_container_width=True
                        )
                elif 'data' in figure:
                    FigureHandler.display_figure(
                        figure['data'],
                        caption=figure.get('caption', f"Figure {idx + 1}"),
                        use_container_width=True
                    )
    
    @staticmethod
    def render_figure_input_ui() -> Optional[Dict[str, Any]]:
        # "Add External Figure" UI has been disabled - the expander section has been removed
        # This method now returns None to maintain compatibility with existing code
        # All other figure functionality (display, gallery, management) remains intact
        return None
    
    @staticmethod
    def save_figure_to_temp(image_data: bytes, format: str = "PNG") -> str:
        try:
            image = Image.open(BytesIO(image_data))
            
            with tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=f".{format.lower()}"
            ) as tmp:
                image.save(tmp.name, format=format)
                return tmp.name
        except Exception as e:
            st.error(f"Error saving image: {str(e)}")
            return None
    
    @staticmethod
    def create_download_link(
        image_data: bytes, 
        filename: str = "figure.png",
        link_text: str = "Download Figure"
    ) -> str:
        b64 = base64.b64encode(image_data).decode()
        href = f'<a href="data:image/png;base64,{b64}" download="{filename}">{link_text}</a>'
        return href
    
    @staticmethod
    def render_figure_management_ui(
        session_key: str = "stored_figures"
    ) -> List[Dict[str, Any]]:
        if session_key not in st.session_state:
            st.session_state[session_key] = []
        
        figure_data = FigureHandler.render_figure_input_ui()
        
        if figure_data:
            st.session_state[session_key].append(figure_data)
            st.success("Figure added successfully!")
            st.rerun()
        
        if st.session_state[session_key]:
            st.subheader("📸 Stored Figures")
            
            for idx, figure in enumerate(st.session_state[session_key]):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    FigureHandler.display_figure(
                        figure['data'],
                        caption=figure.get('caption'),
                        use_container_width=True
                    )
                
                with col2:
                    if st.button(f"Remove", key=f"remove_{idx}"):
                        st.session_state[session_key].pop(idx)
                        st.rerun()
                    
                    if 'data' in figure:
                        download_link = FigureHandler.create_download_link(
                            figure['data'],
                            filename=f"figure_{idx + 1}.png"
                        )
                        st.markdown(download_link, unsafe_allow_html=True)
        
        return st.session_state[session_key]