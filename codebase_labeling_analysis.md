# Codebase Labeling Analysis for Chemical Data Visualization Project

## Current Labeling System Analysis

### 1. Node Labels
**Current Implementation:**
- **Primary Label**: Node labels are set via the `label` field in `ChemicalNode` (line 26 in models.py)
- **Display in PyVis**: Labels are displayed using the `label` parameter in `add_nodes_to_pyvis()` (line 77 in network.py)
- **Tooltip Content**: Comprehensive hover tooltips include node type and all properties (lines 70-73 in network.py)
- **No Column Selection**: Labels are currently fixed to the `label` field with no user customization

**Current Label Sources:**
- CSV: Uses the column specified by `node_label_col` parameter (default: "label")
- GraphML: Uses 'label' attribute if available, otherwise falls back to node ID (line 90 in loader.py)
- JSON: Uses the 'label' field from the data structure

### 2. Edge Labels
**Current Implementation:**
- **No Visual Labels**: Edges currently have NO visible labels in the visualization
- **Tooltip Only**: Edge information is only shown in hover tooltips via `_create_edge_title()` (lines 159-165 in network.py)
- **Tooltip Content**: Shows edge type, weight, and all properties
- **No Labeling Controls**: No user interface for selecting what to display as edge labels

### 3. Data Structure and Available Columns

**Node Data Structure (ChemicalNode - models.py lines 24-58):**
- `id`: Unique identifier
- `label`: Display label (currently the only option for visual labeling)
- `node_type`: NodeType enum
- `properties`: Dict[str, Any] - Contains all additional attributes from data files

**Edge Data Structure (ChemicalEdge - models.py lines 62-93):**
- `source`: Source node ID
- `target`: Target node ID
- `edge_type`: EdgeType enum
- `properties`: Dict[str, Any] - Contains all additional attributes
- `weight`: Numeric weight value
- `color`: Optional color override
- `width`: Optional width override

### 4. Current UI Structure

**Sidebar Controls (sidebar.py):**
- **Visualization Settings** (lines 12-24): Physics, height controls
- **Node Filters** (lines 26-100): Type, connectivity, property-based filtering
- **Edge Filters** (lines 102-152): Type and property-based filtering
- **Coloring Options** (lines 154-202): Node and edge coloring by type/property
- **Node Sizing** (lines 204-265): Fixed or property-based sizing
- **Node Selection** (lines 267-295): Multi-select with neighbor depth
- **Special Filters** (lines 297-320): Library SMILES filtering

**Main App Layout (app.py lines 200-312):**
- Column 1: Network visualization (2/4 width)
- Column 2: Network statistics (1/4 width)  
- Column 3: Node details panel (1/4 width)

### 5. Where Column Selection Should Be Added

**Optimal Location in Sidebar:**
- **NEW SECTION**: "Labeling Options" should be added after line 24 in sidebar.py
- **Position**: Between "Visualization Settings" and "Node Filters"
- **Expandable Section**: Should use `st.sidebar.expander()` like other sections

**Integration Points:**
1. **SidebarControls Class**: Add `render_labeling_controls()` method
2. **Main App**: Call labeling controls after visualization controls (around line 152 in app.py)
3. **NetworkVisualizer**: Modify `add_nodes_to_pyvis()` and `add_edges_to_pyvis()` to accept label column parameters
4. **Session State**: Store selected label columns in `st.session_state.labeling_settings`

## Implementation Requirements Analysis

### Node Label Column Selection Needs:
1. **Available Columns Detection**: Extract all available columns from node properties
2. **Default Selection**: Use current 'label' field as default
3. **UI Control**: Dropdown/selectbox to choose label column
4. **Fallback Handling**: Handle missing values gracefully
5. **Real-time Updates**: Update visualization when label column changes

### Edge Label Column Selection Needs:
1. **Enable Edge Labels**: Currently not implemented in PyVis integration
2. **Column Detection**: Extract available columns from edge properties
3. **UI Controls**: 
   - Checkbox to enable/disable edge labels
   - Dropdown to select label column when enabled
4. **PyVis Integration**: Modify edge creation to include labels
5. **Performance Considerations**: Edge labels can impact performance with large networks

### Technical Integration Points:
1. **New Sidebar Method**: `render_labeling_controls()` returning labeling settings dict
2. **NetworkVisualizer Updates**: Accept and use custom label columns
3. **Session State Schema**: Add labeling_settings to state management
4. **Error Handling**: Graceful handling of missing or invalid label columns

## Recommended Implementation Approach:
1. Add labeling controls to sidebar between visualization settings and filters
2. Store selections in session state for persistence
3. Modify NetworkVisualizer to accept dynamic label column parameters
4. Implement edge labels as an optional feature with performance warnings
5. Provide fallback mechanisms for missing or invalid label data