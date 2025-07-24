# ModiFinder Integration Plan

## Overview
This plan outlines the integration of modifinder package functionality into the chemical visualization app. The goal is to add spectrum visualization and molecular structure drawing capabilities for both node and edge interactions.

## Required ModiFinder Functions

### 1. Node Click Enhancements
- **draw_molecule**: Display molecular structures when nodes have `library_SMILES` data
- **draw_spectrum**: Display spectrum visualizations for nodes

### 2. Edge Click Implementation
- **draw_alignment**: Display spectrum alignment between two nodes connected by an edge
- **USI Extraction**: Parse USI (Universal Spectrum Identifier) from edge URLs

## URL Format Analysis
The example URL format:
```
https://metabolomics-usi.gnps2.org/dashinterface/?usi1=mzspec:GNPS2:TASK-43ab1bb3ce8d468a8dce177763c0ffb1-input_spectra/Pool5_20230523020517.mzML:scan:5595&usi2=mzspec:GNPS2:TASK-43ab1bb3ce8d468a8dce177763c0ffb1-input_spectra/Pool8_20230523031251.mzML:scan:5921&width=10.0&height=6.0&mz_min=None&mz_max=None&max_intensity=125&annotate_precision=4&annotation_rotation=90&cosine=standard&fragment_mz_tolerance=0.1&grid=True&annotate_peaks=%5B%5B%5D%2C%20%5B%5D%5D
```

Extraction pattern:
- `usi1` = portion after `?usi1=` and before `&usi2`
- `usi2` = portion after `&usi2=` and before next `&` parameter

## Implementation Tasks

### Phase 1: Package Integration
1. **Add modifinder to requirements.txt**
2. **Create modifinder utility module** (`src/utils/modifinder_utils.py`)
3. **Add USI extraction functions**
4. **Create image generation functions**

### Phase 2: Node Enhancement
5. **Enhance node detail panel** to include:
   - Spectrum visualization (draw_spectrum)
   - Molecular structure (draw_molecule) if library_SMILES exists
6. **Add error handling** for missing data/invalid SMILES

### Phase 3: Edge Click Implementation
7. **Implement edge click handling**:
   - Extend JavaScript click detection for edges
   - Add edge session state tracking
   - Create edge click button system
8. **Create edge detail panel** showing:
   - Node 1 attributes
   - Node 2 attributes  
   - Edge attributes
   - Spectrum alignment visualization (draw_alignment)

### Phase 4: UI/UX Integration
9. **Update main app layout** to handle edge/node selection
10. **Add loading states** for image generation
11. **Implement caching** for generated images
12. **Add error handling** and fallback displays

## Technical Implementation Details

### USI Extraction Function
```python
def extract_usis_from_url(url: str) -> tuple[str, str]:
    """Extract usi1 and usi2 from GNPS URL format"""
    # Parse URL parameters to extract usi1 and usi2
```

### ModiFinder Image Generation
```python
def generate_spectrum_image(node_data: dict) -> str:
    """Generate spectrum image using draw_spectrum"""
    
def generate_molecule_image(smiles: str) -> str:
    """Generate molecule image using draw_molecule"""
    
def generate_alignment_image(usi1: str, usi2: str) -> str:
    """Generate spectrum alignment using draw_alignment"""
```

### Edge Detail Panel Structure
- **Top Section**: Edge metadata (source, target, type, weight)
- **Middle Section**: Node attributes side-by-side
- **Bottom Section**: Spectrum alignment visualization

## Data Requirements
- Nodes must have appropriate spectrum identifiers
- Edges must contain USI information for alignment
- Library_SMILES field required for molecular structure display

## Error Handling
- Graceful fallbacks when modifinder functions fail
- Clear user messages for missing data
- Logging for debugging image generation issues

## Caching Strategy
- Cache generated images using node/edge IDs as keys
- 30-minute TTL similar to existing figure caching
- Clear cache on network data reload