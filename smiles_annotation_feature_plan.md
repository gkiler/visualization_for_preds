# SMILES Annotation Feature - Implementation Plan

## Feature Overview
Add functionality for users to input missing SMILES for nodes, visualize the SMILES when entered, update the graph with new SMILES data, reprocess connected nodes, and persist annotations across sessions.

## Key Requirements Analysis
1. **SMILES Input Interface**: Form for each node to input missing SMILES
2. **Real-time SMILES Visualization**: Show molecular structure as user types/enters SMILES
3. **Update Button**: Apply new SMILES and trigger graph reprocessing
4. **Graph Reprocessing**: Update preprocessing pipeline to use new SMILES data
5. **Node Annotation**: Mark annotated nodes as blue
6. **State Persistence**: Maintain annotations across graph updates and sessions

## Current System Analysis

### Technology Stack
- **Frontend**: Streamlit with PyVis for network visualization
- **Data Models**: ChemicalNetwork, ChemicalNode, ChemicalEdge dataclasses
- **Molecular Processing**: ModiFinder package for SMILES/molecule visualization
- **State Management**: Streamlit session state
- **File Formats**: CSV, JSON, GraphML support

### Current Architecture
- **app.py**: Main application with network visualization and node/edge selection
- **src/data/models.py**: Core data models (ChemicalNode has properties dict)
- **src/ui/components.py**: UI components including node detail panels
- **src/ui/sidebar.py**: Sidebar controls for filtering and settings
- **src/visualization/network.py**: PyVis network visualization with click handling
- **src/utils/modifinder_utils.py**: Molecular structure and spectrum visualization

### Current Node Selection System
- Nodes are clickable in PyVis network
- Selected node ID stored in `st.session_state.selected_node_id`
- Node details displayed in right panel via `UIComponents.render_node_detail_panel()`
- ModiFinder integration for molecular structure visualization from existing SMILES

## Implementation Plan

### Phase 1: SMILES Input Interface
**Files to Modify**: `src/ui/components.py`

1. **Extend `render_node_detail_panel()` method**:
   - Add SMILES annotation section at the top (after visualizations)
   - Check if node has `library_SMILES` property
   - If missing or empty, show SMILES input form
   - If present, show current SMILES with option to edit/override

2. **SMILES Input Form Components**:
   - Text input field for SMILES string
   - Real-time validation (basic SMILES format check)
   - Preview button to show molecular structure
   - Update button to apply changes
   - Cancel/reset functionality

### Phase 2: Real-time SMILES Visualization
**Files to Modify**: `src/ui/components.py`, potentially `src/utils/modifinder_utils.py`

1. **Live SMILES Preview**:
   - Use ModiFinder's molecule generation capabilities
   - Display molecular structure as user types (with debouncing)
   - Show validation messages for invalid SMILES
   - Handle RDKit/chemical parsing errors gracefully

2. **Enhanced User Experience**:
   - Loading indicators during molecule generation
   - Error states for invalid SMILES
   - Comparison view (old vs new if editing existing SMILES)

### Phase 3: State Management and Persistence
**Files to Modify**: `app.py`, new file `src/utils/annotation_manager.py`

1. **Create AnnotationManager Class**:
   - Track node annotations in session state
   - Persist annotations to local storage/file
   - Load annotations on app startup
   - Handle annotation merging with loaded data

2. **Session State Extensions**:
   - `st.session_state.node_annotations`: Dict[node_id, annotation_data]
   - `st.session_state.annotation_active`: Bool for UI state
   - Annotation metadata (timestamp, user, etc.)

### Phase 4: Graph Processing Integration
**Files to Modify**: `app.py`, `src/data/models.py`, potentially new `src/data/preprocessor.py`

1. **Node Update Mechanism**:
   - Create method to update node properties with new SMILES
   - Trigger connected node reprocessing
   - Update network visualization immediately

2. **Preprocessing Pipeline**:
   - Identify nodes connected to newly annotated node
   - Apply annotation logic to connected nodes based on new SMILES
   - Mark annotated nodes (change color to blue)

### Phase 5: Visual Feedback System
**Files to Modify**: `src/visualization/network.py`, `src/data/models.py`

1. **Node Color System Enhancement**:
   - Add annotation status to ChemicalNode model
   - Extend color configuration for annotated nodes
   - Update PyVis color mapping logic

2. **Visual Indicators**:
   - Blue color for annotated nodes
   - Special border/glow for recently updated nodes
   - Legend/indicator showing annotation status

### Phase 6: Update Button and Graph Reprocessing
**Files to Modify**: `app.py`, new `src/data/annotation_processor.py`

1. **Update Button Handler**:
   - Validate new SMILES input
   - Update node properties in network
   - Trigger connected node processing
   - Update visualization
   - Show success/error feedback

2. **Connected Node Processing**:
   - Find all nodes connected to annotated node
   - Apply preprocessing logic based on new SMILES
   - Update node properties and colors
   - Maintain existing connections

## Technical Implementation Details

### Data Structure Extensions

```python
# Add to ChemicalNode class
@dataclass
class ChemicalNode:
    # ... existing fields ...
    annotation_status: Optional[str] = None  # "user_annotated", "auto_processed", etc.
    annotation_metadata: Dict[str, Any] = field(default_factory=dict)
```

### Session State Structure
```python
{
    'node_annotations': {
        'node_id_1': {
            'original_smiles': 'old_smiles_or_none',
            'new_smiles': 'CC(=O)Oc1ccccc1C(=O)O',
            'timestamp': '2024-01-01T12:00:00Z',
            'status': 'pending'  # pending, applied, error
        }
    },
    'annotation_mode': False,  # UI state for showing/hiding annotation features
    'last_annotation_update': 'timestamp'
}
```

### UI Flow
1. User clicks node → Node detail panel opens
2. If SMILES missing → Show annotation form
3. User enters SMILES → Real-time preview appears
4. User clicks "Update" → Processing starts
5. Node and connected nodes update → Visualization refreshes
6. Success message shown → Annotation persisted

### File Structure Changes
```
src/
├── data/
│   ├── annotation_processor.py  # NEW: Handle annotation processing logic
│   └── models.py               # MODIFIED: Add annotation fields
├── ui/
│   └── components.py           # MODIFIED: Add SMILES input forms
├── utils/
│   ├── annotation_manager.py   # NEW: Manage annotation persistence
│   └── modifinder_utils.py     # POSSIBLY MODIFIED: Enhanced SMILES handling
└── visualization/
    └── network.py              # MODIFIED: Enhanced color system for annotations
```

## Risk Analysis & Mitigation

### Potential Issues
1. **Performance**: Real-time SMILES visualization could be slow
   - **Mitigation**: Implement debouncing, caching, loading states

2. **Data Persistence**: Annotations lost on app restart
   - **Mitigation**: Save to local files, session storage, or database

3. **Graph Consistency**: Updates might break existing connections
   - **Mitigation**: Careful validation, rollback mechanisms

4. **UI Complexity**: Too many features in node detail panel
   - **Mitigation**: Progressive disclosure, tabbed interface

### Testing Strategy
1. **Unit Tests**: SMILES validation, annotation manager
2. **Integration Tests**: Full annotation workflow
3. **User Testing**: UI/UX validation with real users

## Success Metrics
1. Users can successfully add SMILES to nodes
2. Real-time visualization works smoothly
3. Graph updates correctly with new annotations
4. Annotations persist across sessions
5. No performance regression in network visualization

## Implementation Timeline
- **Phase 1-2**: 2-3 days (SMILES input + visualization)
- **Phase 3**: 1-2 days (State management)
- **Phase 4-5**: 2-3 days (Graph processing + visual feedback)
- **Phase 6**: 1-2 days (Integration + testing)
- **Total**: 6-10 days

This plan provides a comprehensive approach to implementing the SMILES annotation feature while maintaining the existing functionality and performance of the chemical visualization application.