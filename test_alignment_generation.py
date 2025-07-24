#!/usr/bin/env python3
"""
Test script for spectrum alignment generation functionality.

This script tests the ModiFinder alignment generation with sample edge data
to verify that the implementation correctly handles USI extraction and 
spectrum alignment generation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'chemical_viz_app'))

from src.utils.modifinder_utils import ModiFinderUtils

def test_usi_extraction_from_edge_data():
    """Test USI extraction from different edge data formats."""
    print("=== Testing USI Extraction from Edge Data ===")
    
    # Test case 1: Direct USI fields
    edge_data_direct = {
        'usi1': 'mzspec:GNPS2:TASK-123:scan:456',
        'usi2': 'mzspec:GNPS2:TASK-789:scan:012',
        'weight': 0.85,
        'type': 'interaction'
    }
    
    usi1, usi2 = ModiFinderUtils.extract_usis_from_edge_data(edge_data_direct)
    print(f"Direct USI fields: usi1={usi1 and usi1[:30]}..., usi2={usi2 and usi2[:30]}...")
    
    # Test case 2: URL-based USI fields
    edge_data_url = {
        'link': 'https://metabolomics-usi.gnps2.org/dashinterface/?usi1=mzspec:GNPS2:TASK-123:scan:456&usi2=mzspec:GNPS2:TASK-789:scan:012',
        'weight': 0.72,
        'type': 'binding'
    }
    
    usi1_url, usi2_url = ModiFinderUtils.extract_usis_from_edge_data(edge_data_url)
    print(f"URL-based USI fields: usi1={usi1_url and usi1_url[:30]}..., usi2={usi2_url and usi2_url[:30]}...")
    
    # Test case 3: No USI fields
    edge_data_no_usi = {
        'weight': 0.65,
        'type': 'activation',
        'properties': {'score': 0.9}
    }
    
    usi1_none, usi2_none = ModiFinderUtils.extract_usis_from_edge_data(edge_data_no_usi)
    print(f"No USI fields: usi1={usi1_none}, usi2={usi2_none}")
    
    return edge_data_direct, edge_data_url

def test_alignment_generation():
    """Test spectrum alignment generation functionality."""
    print("\n=== Testing Spectrum Alignment Generation ===")
    
    # Check if ModiFinder is available
    if not ModiFinderUtils.is_available():
        print("❌ ModiFinder not available - cannot test alignment generation")
        print("💡 Install ModiFinder to enable spectrum alignment functionality")
        return
    
    print("✅ ModiFinder is available")
    
    # Test with sample USI data (these would need to be real USIs for actual generation)
    sample_usi1 = "mzspec:GNPS2:TASK-123:scan:456"
    sample_usi2 = "mzspec:GNPS2:TASK-789:scan:012"
    
    print(f"🧪 Testing alignment generation with sample USIs:")
    print(f"   USI1: {sample_usi1}")
    print(f"   USI2: {sample_usi2}")
    
    try:
        # Test alignment generation with default parameters
        img_base64 = ModiFinderUtils.generate_alignment_image(
            sample_usi1, 
            sample_usi2,
            normalize_peaks=True,
            ppm=40,
            draw_mapping_lines=True
        )
        
        if img_base64:
            print("✅ Alignment generation succeeded - returned base64 image data")
            print(f"   Image data length: {len(img_base64)} characters")
        else:
            print("⚠️ Alignment generation returned None - possibly invalid USI data")
            
    except Exception as e:
        print(f"❌ Error during alignment generation: {e}")
        print("💡 This is expected if the sample USIs don't correspond to real spectra")

def test_edge_alignment_generation():
    """Test the edge-specific alignment generation function."""
    print("\n=== Testing Edge Alignment Generation ===")
    
    edge_data_direct, edge_data_url = test_usi_extraction_from_edge_data()
    
    if not ModiFinderUtils.is_available():
        print("❌ ModiFinder not available - skipping edge alignment test")
        return
    
    print("🧪 Testing edge alignment generation with direct USI data...")
    try:
        img_base64 = ModiFinderUtils.generate_edge_alignment_image(
            edge_data_direct,
            normalize_peaks=True,
            ppm=40
        )
        
        if img_base64:
            print("✅ Edge alignment generation succeeded")
        else:
            print("⚠️ Edge alignment generation returned None")
            
    except Exception as e:
        print(f"❌ Error during edge alignment generation: {e}")

def main():
    """Run all tests."""
    print("🔬 ModiFinder Spectrum Alignment Test Suite")
    print("=" * 50)
    
    test_usi_extraction_from_edge_data()
    test_alignment_generation()
    test_edge_alignment_generation()
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
    print("\n💡 To use spectrum alignment in the application:")
    print("   1. Load a GraphML file with edge USI data")
    print("   2. Click on an edge in the network visualization")
    print("   3. View the generated spectrum alignment in the edge details panel")

if __name__ == "__main__":
    main()