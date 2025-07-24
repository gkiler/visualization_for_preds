# Node Click Implementation Plan

## Problem Analysis
The current implementation uses PyVis for network visualization, which generates HTML/JS that runs in an iframe through Streamlit's `components.html()`. PyVis doesn't have built-in click event handling that can communicate back to Streamlit.

## Solution Approach
We need to inject custom JavaScript into the PyVis-generated HTML to:
1. Listen for node click events
2. Extract node data 
3. Communicate the clicked node ID back to Streamlit
4. Display node details in a side panel

## Technical Implementation

### Phase 1: Custom JavaScript Injection
- Modify the NetworkVisualizer to inject custom JS into PyVis HTML
- Add event listeners for node click events
- Use postMessage API to communicate with Streamlit

### Phase 2: Streamlit Communication
- Use `streamlit.components.v1.html()` with proper bidirectional communication
- Store clicked node ID in session state
- Create a side panel component that reacts to node selection

### Phase 3: Node Detail Panel
- Create a new UI component for displaying node details
- Map the requested field aliases to node properties
- Add placeholder for Spectrum Visualizer image

## Required Fields Mapping
Based on the user request, map these aliases to node properties:
- library_SMILES → SMILES
- library_compound_name → Compound Name  
- library_InChI → InChI
- rt → Retention Time
- mz → Precursor Mass
- library_classfire_superclass → ClassyFire Superclass
- library_classyfire_class → ClassyFire Class
- library_classyfire_subclass → ClassyFire Subclass
- library_npclassifier_superclass → npclassifier Super Class
- library_npclassifier_class → npclassifier Class
- library_npclassifier_pathway → npclassifier Pathway
- SpectrumID → Spectrum ID
- Compound_Name → Compound Name
- Adduct → Adduct
- molecular_formula → Molecular Formula

## Files to Modify/Create
1. `src/visualization/network.py` - Add custom JS injection
2. `src/ui/components.py` - Add node detail panel component
3. `app.py` - Integrate side panel into layout
4. Create JavaScript template for node click handling

## Key Challenges
1. Cross-iframe communication between PyVis and Streamlit
2. Handling dynamic layout changes when side panel appears
3. Ensuring the solution works across different browsers
4. Performance considerations for large networks