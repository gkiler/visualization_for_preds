# Edge Styling and Toggle System Analysis

## Current Implementation Overview

### Edge Data Model (`src/data/models.py`)
- **ChemicalEdge** class with the following attributes:
  - `source: str` - Source node ID
  - `target: str` - Target node ID  
  - `edge_type: EdgeType` - Enum (INTERACTION, ACTIVATION, INHIBITION, BINDING, OTHER)
  - `properties: Dict[str, Any]` - Custom key-value properties
  - `weight: float = 1.0` - Edge weight/strength
  - `color: Optional[str] = None` - Custom color override
  - `width: Optional[float] = None` - Custom width override

### Edge Visualization (`src/visualization/network.py`)
- **NetworkVisualizer.add_edges_to_pyvis()** method handles edge rendering
- Current edge styling logic:
  1. **Color**: Tries edge.color -> edge_colors dict -> default type colors -> fallback
  2. **Width**: Tries edge.width -> edge_widths dict -> weight * default_width
  3. **Special handling**: Activation edges get arrows, inhibition edges get strikethrough arrows
  4. **Tooltip**: Shows type, weight, and all properties

### Current Edge Color Configuration (`config.yaml`)
```yaml
colors:
  edge_types:
    interaction: "#666666"
    activation: "#4CAF50" 
    inhibition: "#F44336"
    binding: "#2196F3"
    default: "#999999"
```

### Current Edge Styling Systems

#### 1. Type-Based Coloring (app.py lines 201-209)
- Only supports coloring by weight currently
- Uses rgba with alpha based on normalized weight
- Missing: coloring by edge type or properties

#### 2. Edge Filtering (`src/ui/sidebar.py`)
- **Type Filter**: Multi-select dropdown for edge types
- **Property Filter**: Single property with operator and value
- Missing: Batch property filtering, toggle-based filtering

#### 3. Existing Toggle Systems
- **Node Type Filter**: Multi-select with default all selected
- **Physics Toggle**: Simple checkbox for physics on/off
- **Node Property Coloring**: Dropdown selection with auto color mapping
- **Node Size Scaling**: Property-based with min/max sliders

## Gap Analysis

### Missing Edge Styling Features
1. **Edge coloring by type** - Infrastructure exists but not exposed in UI
2. **Edge coloring by properties** - Method exists but not used in main app
3. **Edge width/thickness controls** - No UI controls for width scaling
4. **Edge toggle system** - No easy on/off toggles for edge types
5. **Property-based edge width** - Not implemented in UI

### Current Edge Property Support
- Properties are stored and displayed in tooltips
- GraphML loader preserves all edge attributes as properties
- Sample data includes properties like "affinity", "strength", "importance"
- Filtering by properties exists but limited to single property at a time

## Key Files for Implementation

### Primary Files to Modify
1. **`src/ui/sidebar.py`** - Add edge styling controls and toggles
2. **`chemical_viz_app/app.py`** - Integrate new edge styling logic (lines 201-217)
3. **`src/visualization/network.py`** - Enhance edge styling methods (lines 86-142)
4. **`config.yaml`** - Add edge styling configuration options

### Secondary Files
5. **`src/data/models.py`** - Potentially add edge styling methods
6. **`src/visualization/filters.py`** - Enhance edge filtering if needed

## Implementation Strategy

### Phase 1: Edge Type Toggle System
- Add multi-toggle component for edge types (similar to node types)
- Each edge type gets individual on/off toggle with color indicator
- Maintain existing multi-select as alternative interface

### Phase 2: Enhanced Edge Styling
- Add edge coloring by property with color picker/scheme selection
- Add edge width/thickness scaling by numeric properties
- Add preset edge styling themes (scientific, network analysis, etc.)

### Phase 3: Advanced Edge Controls
- Batch edge property filtering with AND/OR logic
- Edge opacity controls
- Advanced edge shape/style options (dashed, dotted, etc.)
- Edge label display options

## Technical Considerations

### PyVis Limitations
- PyVis edge styling is somewhat limited compared to nodes
- Arrow styles are fixed (cannot easily customize arrowheads)
- Edge smoothing options are basic
- Performance with many styled edges needs testing

### Data Flow
1. Edge filters applied in sidebar → app.py
2. Edge styling options selected → app.py  
3. App.py calls NetworkVisualizer methods with styling parameters
4. NetworkVisualizer applies styles to PyVis network
5. PyVis renders edges with applied styles

### Current Integration Points
- Line 201-209 in app.py: Edge color by weight
- Lines 164-168 in network.py: add_edges_to_pyvis call
- Lines 102-152 in sidebar.py: Edge filtering controls
- Lines 207-224 in network.py: get_edge_colors_by_property method (unused)