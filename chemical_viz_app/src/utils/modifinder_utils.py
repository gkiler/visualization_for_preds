"""
ModiFinder integration utilities for spectrum and molecular visualization.

This module provides functions to:
1. Extract USI (Universal Spectrum Identifier) from GNPS URLs
2. Generate spectrum visualizations using modifinder
3. Generate molecular structure images
4. Handle image caching and error management
"""

import io
import base64
import logging
import re
import tempfile
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse, parse_qs
import streamlit as st
from PIL import Image

try:
    import modifinder.utilities.visualizer as mf_viz
    MODIFINDER_AVAILABLE = True
except ImportError as e:
    MODIFINDER_AVAILABLE = False
    logging.warning(f"ModiFinder not available: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModiFinderUtils:
    """Utility class for ModiFinder integration."""
    
    CACHE_TTL = 1800  # 30 minutes in seconds
    
    @staticmethod
    def is_available() -> bool:
        """Check if ModiFinder is available for use."""
        return MODIFINDER_AVAILABLE
    
    @staticmethod
    def extract_usis_from_url(url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract usi1 and usi2 from GNPS URL format.
        
        Args:
            url: URL containing USI parameters
            
        Returns:
            Tuple of (usi1, usi2) or (None, None) if extraction fails
            
        Example URL format:
        https://metabolomics-usi.gnps2.org/dashinterface/?usi1=mzspec:GNPS2:...&usi2=mzspec:GNPS2:...
        """
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            usi1 = query_params.get('usi1', [None])[0]
            usi2 = query_params.get('usi2', [None])[0]
            
            logger.info(f"Extracted USIs from URL: usi1={usi1 and usi1[:50]}..., usi2={usi2 and usi2[:50]}...")
            return usi1, usi2
            
        except Exception as e:
            logger.error(f"Error extracting USIs from URL: {e}")
            return None, None
    
    @staticmethod
    def extract_usis_from_edge_data(edge_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract USI information from edge properties.
        
        Args:
            edge_data: Dictionary containing edge properties
            
        Returns:
            Tuple of (usi1, usi2) or (None, None) if not found
        """
        # Look for URL in common edge property fields
        url_fields = ['url', 'link', 'gnps_url', 'usi_url', 'spectrum_url']
        
        for field in url_fields:
            if field in edge_data and edge_data[field]:
                url = str(edge_data[field])
                if 'usi1=' in url and 'usi2=' in url:
                    return ModiFinderUtils.extract_usis_from_url(url)
        
        # Look for direct USI fields
        usi1 = edge_data.get('usi1') or edge_data.get('USI1')
        usi2 = edge_data.get('usi2') or edge_data.get('USI2')
        
        if usi1 and usi2:
            return str(usi1), str(usi2)
            
        logger.warning("No USI information found in edge data")
        return None, None
    
    @staticmethod
    @st.cache_data(ttl=CACHE_TTL)
    def generate_spectrum_image(node_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate spectrum image using ModiFinder's draw_spectrum function.
        
        Args:
            node_data: Dictionary containing node properties
            
        Returns:
            Base64 encoded PNG image or None if generation fails
        """
        if not MODIFINDER_AVAILABLE:
            logger.error("ModiFinder not available for spectrum generation")
            return None
        
        try:
            # Look for spectrum identifier in node data
            spectrum_fields = ['spectrum_id', 'SpectrumID', 'usi', 'USI']
            spectrum_id = None
            
            for field in spectrum_fields:
                if field in node_data and node_data[field]:
                    spectrum_id = str(node_data[field])
                    break
            
            if not spectrum_id:
                logger.warning("No spectrum identifier found in node data")
                return None
            
            logger.info(f"Attempting to generate spectrum for ID: {spectrum_id}")
            
            # Generate spectrum plot using ModiFinder
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                # Call ModiFinder's draw_spectrum function
                result = mf_viz.draw_spectrum(spectrum_id)
                logger.info(f"ModiFinder draw_spectrum returned type: {type(result)}")
                logger.info(f"ModiFinder draw_spectrum result attributes: {dir(result)}")
                
                # Handle different return types
                if hasattr(result, 'savefig'):
                    # It's a matplotlib figure
                    logger.info("Result is a matplotlib figure, using savefig")
                    result.savefig(tmp_file.name, format='png', dpi=150, bbox_inches='tight')
                elif hasattr(result, 'shape'):
                    # It's a numpy array (image data)
                    logger.info(f"Result is numpy array with shape: {result.shape}")
                    from PIL import Image
                    import numpy as np
                    
                    # Convert numpy array to PIL Image and save
                    if result.dtype != np.uint8:
                        # Normalize to 0-255 range if needed
                        if result.max() <= 1.0:
                            result = (result * 255).astype(np.uint8)
                        else:
                            result = result.astype(np.uint8)
                    
                    if len(result.shape) == 3 and result.shape[2] == 3:
                        # RGB image
                        img = Image.fromarray(result, 'RGB')
                    elif len(result.shape) == 3 and result.shape[2] == 4:
                        # RGBA image
                        img = Image.fromarray(result, 'RGBA')
                    elif len(result.shape) == 2:
                        # Grayscale image
                        img = Image.fromarray(result, 'L')
                    else:
                        logger.error(f"Unsupported array shape: {result.shape}")
                        return None
                    
                    img.save(tmp_file.name, format='PNG')
                else:
                    logger.error(f"Unknown result type from draw_spectrum: {type(result)}")
                    return None
                
                # Convert to base64
                with open(tmp_file.name, 'rb') as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    
                logger.info(f"Successfully generated spectrum image for spectrum_id: {spectrum_id}")
                return img_base64
                
        except Exception as e:
            logger.error(f"Error generating spectrum image: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    @staticmethod
    @st.cache_data(ttl=CACHE_TTL)
    def generate_molecule_image(smiles: str) -> Optional[str]:
        """
        Generate molecular structure image using ModiFinder's draw_molecule function.
        
        Args:
            smiles: SMILES string representing the molecule
            
        Returns:
            Base64 encoded PNG image or None if generation fails
        """
        if not MODIFINDER_AVAILABLE:
            logger.error("ModiFinder not available for molecule generation")
            return None
        
        if not smiles or not smiles.strip():
            logger.warning("Empty or invalid SMILES string provided")
            return None
        
        try:
            logger.info(f"Attempting to generate molecule image for SMILES: {smiles[:50]}...")
            
            # Generate molecular structure using ModiFinder
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                # Call ModiFinder's draw_molecule function
                result = mf_viz.draw_molecule(smiles.strip())
                logger.info(f"ModiFinder draw_molecule returned type: {type(result)}")
                logger.info(f"ModiFinder draw_molecule result attributes: {dir(result)}")
                
                # Handle different return types
                if hasattr(result, 'savefig'):
                    # It's a matplotlib figure
                    logger.info("Result is a matplotlib figure, using savefig")
                    result.savefig(tmp_file.name, format='png', dpi=150, bbox_inches='tight')
                elif hasattr(result, 'shape'):
                    # It's a numpy array (image data)
                    logger.info(f"Result is numpy array with shape: {result.shape}")
                    from PIL import Image
                    import numpy as np
                    
                    # Convert numpy array to PIL Image and save
                    if result.dtype != np.uint8:
                        # Normalize to 0-255 range if needed
                        if result.max() <= 1.0:
                            result = (result * 255).astype(np.uint8)
                        else:
                            result = result.astype(np.uint8)
                    
                    if len(result.shape) == 3 and result.shape[2] == 3:
                        # RGB image
                        img = Image.fromarray(result, 'RGB')
                    elif len(result.shape) == 3 and result.shape[2] == 4:
                        # RGBA image
                        img = Image.fromarray(result, 'RGBA')
                    elif len(result.shape) == 2:
                        # Grayscale image
                        img = Image.fromarray(result, 'L')
                    else:
                        logger.error(f"Unsupported array shape: {result.shape}")
                        return None
                    
                    img.save(tmp_file.name, format='PNG')
                else:
                    logger.error(f"Unknown result type from draw_molecule: {type(result)}")
                    return None
                
                # Convert to base64
                with open(tmp_file.name, 'rb') as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    
                logger.info(f"Successfully generated molecule image for SMILES: {smiles[:50]}...")
                return img_base64
                
        except Exception as e:
            logger.error(f"Error generating molecule image for SMILES '{smiles}': {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    @staticmethod
    @st.cache_data(ttl=CACHE_TTL)
    def generate_alignment_image(usi1: str, usi2: str) -> Optional[str]:
        """
        Generate spectrum alignment image using ModiFinder's draw_alignment function.
        
        Args:
            usi1: First Universal Spectrum Identifier
            usi2: Second Universal Spectrum Identifier
            
        Returns:
            Base64 encoded PNG image or None if generation fails
        """
        if not MODIFINDER_AVAILABLE:
            logger.error("ModiFinder not available for alignment generation")
            return None
        
        if not usi1 or not usi2:
            logger.warning("Missing USI information for alignment")
            return None
        
        try:
            logger.info(f"Attempting to generate alignment for USIs: {usi1[:30]}... vs {usi2[:30]}...")
            
            # Generate spectrum alignment using ModiFinder
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                # Call ModiFinder's draw_alignment function
                result = mf_viz.draw_alignment(usi1.strip(), usi2.strip())
                logger.info(f"ModiFinder draw_alignment returned type: {type(result)}")
                logger.info(f"ModiFinder draw_alignment result attributes: {dir(result)}")
                
                # Handle different return types
                if hasattr(result, 'savefig'):
                    # It's a matplotlib figure
                    logger.info("Result is a matplotlib figure, using savefig")
                    result.savefig(tmp_file.name, format='png', dpi=150, bbox_inches='tight')
                elif hasattr(result, 'shape'):
                    # It's a numpy array (image data)
                    logger.info(f"Result is numpy array with shape: {result.shape}")
                    from PIL import Image
                    import numpy as np
                    
                    # Convert numpy array to PIL Image and save
                    if result.dtype != np.uint8:
                        # Normalize to 0-255 range if needed
                        if result.max() <= 1.0:
                            result = (result * 255).astype(np.uint8)
                        else:
                            result = result.astype(np.uint8)
                    
                    if len(result.shape) == 3 and result.shape[2] == 3:
                        # RGB image
                        img = Image.fromarray(result, 'RGB')
                    elif len(result.shape) == 3 and result.shape[2] == 4:
                        # RGBA image
                        img = Image.fromarray(result, 'RGBA')
                    elif len(result.shape) == 2:
                        # Grayscale image
                        img = Image.fromarray(result, 'L')
                    else:
                        logger.error(f"Unsupported array shape: {result.shape}")
                        return None
                    
                    img.save(tmp_file.name, format='PNG')
                else:
                    logger.error(f"Unknown result type from draw_alignment: {type(result)}")
                    return None
                
                # Convert to base64
                with open(tmp_file.name, 'rb') as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    
                logger.info(f"Successfully generated alignment image for USIs: {usi1[:30]}... vs {usi2[:30]}...")
                return img_base64
                
        except Exception as e:
            logger.error(f"Error generating alignment image: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    @staticmethod
    def render_error_placeholder(error_message: str) -> None:
        """
        Render an error placeholder when image generation fails.
        
        Args:
            error_message: Description of the error
        """
        st.error(f"⚠️ {error_message}")
        st.info("📊 Visualization could not be generated. Please check the data format and try again.")
    
    @staticmethod
    def render_loading_placeholder(message: str = "Generating visualization...") -> None:
        """
        Render a loading placeholder during image generation.
        
        Args:
            message: Loading message to display
        """
        with st.spinner(message):
            st.empty()
    
    @staticmethod
    def display_image_from_base64(img_base64: str, caption: str = "") -> None:
        """
        Display a base64 encoded image in Streamlit.
        
        Args:
            img_base64: Base64 encoded image data
            caption: Optional caption for the image
        """
        try:
            # Decode base64 to image
            img_data = base64.b64decode(img_base64)
            img = Image.open(io.BytesIO(img_data))
            
            # Display in Streamlit
            st.image(img, caption=caption, use_container_width=True)
            
        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            ModiFinderUtils.render_error_placeholder("Error displaying generated image")


# Convenience functions for direct use
def extract_usis_from_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract usi1 and usi2 from GNPS URL format."""
    return ModiFinderUtils.extract_usis_from_url(url)

def generate_spectrum_image(node_data: Dict[str, Any]) -> Optional[str]:
    """Generate spectrum image using ModiFinder."""
    return ModiFinderUtils.generate_spectrum_image(node_data)

def generate_molecule_image(smiles: str) -> Optional[str]:
    """Generate molecular structure image using ModiFinder."""
    return ModiFinderUtils.generate_molecule_image(smiles)

def generate_alignment_image(usi1: str, usi2: str) -> Optional[str]:
    """Generate spectrum alignment image using ModiFinder."""
    return ModiFinderUtils.generate_alignment_image(usi1, usi2)