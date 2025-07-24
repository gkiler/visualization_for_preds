# Chemical Data Visualization App - Codebase Analysis

## Current Structure Summary

### 1. Main Application Flow (app.py)
- **Layout**: Streamlit app with wide layout, sidebar controls, and main visualization area
- **Session State**: Manages network data, filtered network, visualization settings, and active filters
- **Data Loading**: Supports CSV, JSON, GraphML, and sample data loading
- **Two-column layout**: Main visualization (col1) + Additional figures (col2)
- **Network rendering**: Uses NetworkVisualizer to create PyVis HTML and display via Streamlit components

### 2. Network Visualization (src/visualization/network.py)
- **Core Library**: PyVis Network for interactive visualization
- **Rendering Process**:
  1. Creates PyVis network with physics settings
  2. Adds nodes with tooltips, colors, sizes
  3. Adds edges with colors, widths, special styling
  4. Saves to temporary HTML file
  5. Displays in Streamlit via components.html()
- **Special Features**:
  - Edge styling based on edit_distance (-1 = dashed, 1 = solid, >1 = jagged)
  - Shadow effects for modifinder edges
  - Molecular networking color mapping
  - Dynamic node/edge coloring and sizing

### 3. Data Models (src/data/models.py)
- **ChemicalNode**:
  - `id`: Unique identifier
  - `label`: Display name
  - `node_type`: Enum (MOLECULE, PROTEIN, REACTION, PATHWAY, OTHER)
  - `properties`: Dict[str, Any] - flexible attribute storage
  - `x, y`: Optional coordinates
  - `size, color`: Optional visual overrides
- **ChemicalEdge**:
  - `source, target`: Node IDs
  - `edge_type`: Enum (INTERACTION, ACTIVATION, INHIBITION, BINDING, OTHER)
  - `properties`: Dict[str, Any] - flexible attribute storage
  - `weight`: Numeric weight (default 1.0)
  - `color, width`: Optional visual overrides
- **ChemicalNetwork**: Container with nodes list, edges list, metadata dict

### 4. UI Structure (src/ui/)
- **components.py**: Data upload, network stats, data tables, export options
- **sidebar.py**: All interactive controls in collapsible sections
  - Visualization settings (physics, height)
  - Node/edge filters by type, connectivity, properties
  - Coloring controls (by type/property/custom)
  - Node sizing controls (fixed or by property)
  - Node selection with neighbor depth
  - Special library_SMILES filter

## Available Data Fields

### Node Properties Available:
- **Core Fields**: id, label, node_type
- **Visual Fields**: x, y, size, color
- **Custom Properties**: Any arbitrary key-value pairs in properties dict
- **Common Properties** (based on code analysis):
  - library_SMILES (for chemical filtering)
  - Various numeric properties for sizing
  - Any domain-specific attributes loaded from files

### Edge Properties Available:
- **Core Fields**: source, target, edge_type, weight
- **Visual Fields**: color, width
- **Custom Properties**: Any arbitrary key-value pairs in properties dict
- **Special Properties** (based on code analysis):
  - molecular_networking (0/1 for special coloring)
  - edit_distance (-1, 1, >1 for line styling)
  - modifinder (boolean for glow effects)

## Current Interaction Features

### Existing Interactions:
1. **PyVis Built-ins**: Drag nodes, zoom, pan, physics simulation
2. **Filtering**: Real-time network filtering with immediate re-rendering
3. **Visual Customization**: Dynamic coloring and sizing based on data
4. **Node Selection**: Multi-select with neighbor expansion
5. **Data Exploration**: Expandable data tables with sanitized columns

### No Click Handling Currently:
- **Missing**: No custom click event handling for nodes/edges
- **Current Method**: Uses PyVis default interactions only
- **Tooltip Display**: Hover tooltips show node/edge properties
- **Selection Method**: Only via sidebar multiselect, not direct clicking

## Key Technical Details

### Rendering Pipeline:
1. Load/filter network data → ChemicalNetwork object
2. Apply visual settings (colors, sizes) → dicts of node/edge properties
3. Create PyVis network → add nodes/edges with styling
4. Save to temp HTML → display via components.html()
5. Clean up temp files

### Performance Considerations:
- Default limits: 1000 nodes, 5000 edges
- GraphML files have unlimited nodes
- Temp file cleanup after rendering
- Streamlit caching for data loading

### Configuration:
- YAML-based config for colors, physics, defaults
- Molecular networking special colors
- Node/edge type default styling
- Physics simulation parameters