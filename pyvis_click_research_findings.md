# PyVis Network Click Events Research Findings

## Current Implementation Analysis

### Existing Codebase Structure
- **Network Visualizer**: `src/visualization/network.py` uses PyVis to generate networks and displays them via `components.html()`
- **JavaScript Utils**: `lib/bindings/utils.js` contains neighborhood highlighting and node selection functions
- **Main App**: Already has a node detail panel (column 3) that shows when `st.session_state.selected_node_id` is set
- **UI Components**: Has a node selector dropdown as a fallback method

### Current PyVis Integration Method
The existing implementation:
1. Creates PyVis networks and saves them as temporary HTML files
2. Displays the HTML using `components.html(html_content, height=800, scrolling=True)`
3. Cleans up temporary files after rendering
4. Uses a dropdown selector as the current method for node selection

## Research Findings on PyVis Click Events

### 1. PyVis Limitations
- **No Native Click Events**: PyVis doesn't provide built-in support for JavaScript callbacks that can communicate back to Streamlit
- **HTML-Only Output**: PyVis generates standalone HTML files with embedded JavaScript, making bidirectional communication difficult
- **vis.js Wrapper**: PyVis is a wrapper around vis.js, but doesn't expose all interactive features

### 2. Streamlit Components Bidirectional Communication

#### Available Methods:
1. **Custom Streamlit Components**: Full control over JavaScript-Python communication
2. **streamlit-agraph**: Third-party component with built-in click event support
3. **stvis**: PyVis wrapper component, but no clear click event documentation
4. **streamlit-visgraph**: Alternative vis.js-based component

#### Bidirectional Communication Requirements:
- Components must call `Streamlit.setComponentReady()` 
- Subscribe to `Streamlit.RENDER_EVENT` for redraws
- Use `Streamlit.setComponentValue()` to send data back to Python
- Python side receives data via component return values

### 3. Practical Implementation Approaches

#### Option A: Modify PyVis HTML Output
**Pros**: 
- Keeps existing PyVis integration
- Minimal changes to current architecture

**Cons**: 
- Requires parsing and modifying PyVis-generated HTML
- Fragile - breaks when PyVis updates
- Complex JavaScript injection

**Implementation**:
1. Generate PyVis HTML as normal
2. Parse HTML content and inject custom JavaScript
3. Add event listeners for node clicks
4. Use `window.parent.postMessage()` to communicate with Streamlit
5. Listen for messages in Streamlit using custom component wrapper

#### Option B: Custom Streamlit Component
**Pros**:
- Full control over visualization and interactions
- Proper bidirectional communication
- Future-proof and maintainable

**Cons**:
- Significant development effort
- Requires JavaScript/TypeScript knowledge
- Need to recreate PyVis styling and physics

**Implementation**:
1. Create custom component using Streamlit component template
2. Use vis.js directly instead of PyVis
3. Implement proper click event handlers
4. Use Streamlit's communication API

#### Option C: Third-Party Component Migration
**Pros**:
- Established solutions with click events
- Community support and documentation
- Less development overhead

**Cons**:
- May require data format changes
- Different API and styling
- Dependency on external packages

**Components to Evaluate**:
- `streamlit-agraph`: Most mature, has click events
- `streamlit-visgraph`: vis.js-based, supports customization
- `stvis`: PyVis wrapper, unclear click support

#### Option D: Hybrid Approach
**Pros**:
- Minimal disruption to existing code
- Progressive enhancement possible

**Cons**:
- Complex implementation
- Potential synchronization issues

**Implementation**:
1. Keep existing PyVis visualization
2. Add hidden custom component for event handling
3. Overlay invisible click areas on PyVis network
4. Coordinate between PyVis display and event component

## Technical Implementation Details

### For Option A (Modified PyVis HTML):
```javascript
// Inject into PyVis HTML
network.on("click", function (params) {
    if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        window.parent.postMessage({
            type: 'nodeClick',
            nodeId: nodeId
        }, '*');
    }
});
```

### For Option B (Custom Component):
```typescript
// In component frontend
const handleNodeClick = (params: any) => {
    if (params.nodes.length > 0) {
        Streamlit.setComponentValue({
            type: 'node_click',
            nodeId: params.nodes[0],
            timestamp: Date.now()
        });
    }
};
```

### For Option C (streamlit-agraph):
```python
# Example with streamlit-agraph
from streamlit_agraph import agraph, Node, Edge, Config

# Convert ChemicalNetwork to agraph format
nodes = [Node(id=node.id, label=node.label) for node in network.nodes]
edges = [Edge(source=edge.source, target=edge.target) for edge in network.edges]

# Render with click events
selected_node = agraph(nodes=nodes, edges=edges, config=config)
if selected_node:
    st.session_state.selected_node_id = selected_node
```

## Existing JavaScript Utilities Analysis

The current `lib/bindings/utils.js` contains:
- `neighbourhoodHighlight()`: Highlights connected nodes
- `filterHighlight()`: Shows/hides nodes based on filters
- `selectNode()` and `selectNodes()`: Programmatic selection functions

These functions operate on vis.js network objects directly, suggesting the PyVis output is already using vis.js underneath. This could be leveraged for click event implementation.

## Recommendations

### Short-term (Quick Implementation):
1. **Hybrid Approach with HTML Modification**
   - Parse PyVis HTML and inject click event handlers
   - Use `window.parent.postMessage()` for communication
   - Create small wrapper component to receive messages

### Medium-term (Better Architecture):
1. **Migrate to streamlit-agraph**
   - Provides built-in click events
   - Well-maintained and documented
   - Requires data format conversion

### Long-term (Full Control):
1. **Custom Streamlit Component**
   - Use vis.js directly with full customization
   - Implement all required features from scratch
   - Future-proof solution

## Next Steps for Implementation

1. **Evaluate streamlit-agraph compatibility** with existing ChemicalNetwork data structure
2. **Test HTML modification approach** with a simple click event handler injection
3. **Create proof-of-concept** for the chosen approach
4. **Update NetworkVisualizer class** to support click event handling
5. **Integrate with existing node detail panel** in the main app

## Code Integration Points

Key files that would need modification:
- `src/visualization/network.py`: Add click event handling
- `chemical_viz_app/app.py`: Update visualization display logic
- `src/ui/components.py`: Enhance node detail panel
- New component files if creating custom solution

The existing session state management (`st.session_state.selected_node_id`) is already set up to handle node selection, making integration relatively straightforward once click events are captured.