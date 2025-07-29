# SMILES Persistence to GraphML - Detailed Analysis & Implementation Plan

## Current Annotation Flow Analysis

### 1. Current Annotation Storage Mechanisms

**Dual Storage System Identified:**
- **Session State**: `pending_smiles_updates` (temporary, for processing)
- **Persistent JSON**: `annotations/smiles_annotations.json` (permanent storage)

**Flow Chain:**
1. **User Input** → `components.py` → `pending_smiles_updates` (session state)
2. **Apply Button** → `annotation_processor.py` → processes pending updates
3. **Processing** → updates network nodes → calls `annotation_manager.save_annotations_to_file()`
4. **Persistence** → saves to `smiles_annotations.json`

### 2. Property Management in models.py

**Key Node Methods:**
- `get_effective_smiles()`: Returns `properties.get('library_SMILES')`
- `apply_annotation_to_node()`: Sets `node.properties['library_SMILES'] = smiles`
- `set_annotation_status()`: Marks as `'user_annotated'`

**Current Property Structure:**
```python
node.properties = {
    'library_SMILES': str,           # Current SMILES (user or original)
    'annotation_status': str,        # 'user_annotated' if modified
    'annotation_timestamp': str,     # ISO timestamp
}
```

### 3. GraphML Structure Analysis

**Loading (loader.py):**
- Uses NetworkX `read_graphml()` 
- Maps all GraphML attributes to `node.properties` dict
- Converts numeric strings appropriately
- No special handling for annotation status

**Export (loader.py):**
- Uses NetworkX `write_graphml()`
- Exports all `node.properties` as GraphML attributes
- Preserves user annotations in exported files

### 4. Current Limitations

**Missing GraphML Persistence:**
- User annotations stored in JSON, not back to GraphML
- GraphML file remains unchanged after user input
- No mechanism to update original source files

**Data Consistency Issues:**
- Two sources of truth: GraphML file + JSON annotations
- Reloading GraphML loses user changes
- No preservation during file reprocessing

## Implementation Strategy

### Phase 1: GraphML Update Mechanism

**Create GraphML Persistence Manager**
```python
class GraphMLPersistenceManager:
    def update_graphml_with_annotations(self, 
                                       graphml_path: Path, 
                                       network: ChemicalNetwork) -> bool
    def backup_original_graphml(self, graphml_path: Path) -> Path
    def preserve_user_data_during_update(self, network: ChemicalNetwork) -> Dict
```

**Key Operations:**
1. **Backup Creation**: Always backup original before modification
2. **Selective Update**: Only update `library_SMILES` for annotated nodes
3. **Preservation**: Maintain all other GraphML attributes unchanged
4. **Validation**: Verify structure integrity after updates

### Phase 2: Integration Points

**Modify annotation_processor.py:**
```python
def apply_all_pending_updates(self, network: ChemicalNetwork) -> Dict[str, Any]:
    # Current processing...
    results = self.process_pending_annotations(network)
    
    # NEW: Update GraphML file if loaded from GraphML
    if self._is_graphml_source(network):
        success = self._update_source_graphml(network)
        results['graphml_updated'] = success
    
    return results
```

**Modify loader.py:**
```python
def reload_network_preserving_annotations(self, 
                                        file_path: Path, 
                                        existing_network: ChemicalNetwork) -> ChemicalNetwork:
    # Load fresh network from file
    fresh_network = self.load_network_from_graphml(file_path)
    
    # Apply preserved annotations
    self._apply_preserved_annotations(fresh_network, existing_network)
    
    return fresh_network
```

### Phase 3: Property Mapping Strategy

**Enhanced Property Management:**
```python
# In ChemicalNode class
def get_annotation_properties(self) -> Dict[str, Any]:
    """Extract only annotation-related properties for persistence"""
    return {
        'library_SMILES': self.properties.get('library_SMILES'),
        'annotation_status': self.properties.get('annotation_status'),
        'annotation_timestamp': self.properties.get('annotation_timestamp'),
        'annotation_metadata': self.properties.get('annotation_metadata', {})
    }

def apply_annotation_properties(self, annotation_props: Dict[str, Any]):
    """Apply annotation properties while preserving other data"""
    for key, value in annotation_props.items():
        if value is not None:
            self.properties[key] = value
```

## Detailed Implementation Plan

### Step 1: Create GraphML Persistence Manager

**File**: `src/utils/graphml_persistence.py`

```python
class GraphMLPersistenceManager:
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def update_graphml_with_annotations(self, 
                                       graphml_path: Path, 
                                       network: ChemicalNetwork) -> Tuple[bool, str]:
        """
        Update GraphML file with user annotations while preserving structure.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # 1. Create backup
            backup_path = self.create_backup(graphml_path)
            
            # 2. Load original NetworkX graph
            original_graph = nx.read_graphml(graphml_path)
            
            # 3. Update only annotated nodes
            updated_count = 0
            for node in network.nodes:
                if node.is_annotated():
                    if node.id in original_graph.nodes:
                        # Update library_SMILES and annotation metadata
                        original_graph.nodes[node.id]['library_SMILES'] = node.properties['library_SMILES']
                        original_graph.nodes[node.id]['annotation_status'] = 'user_annotated'
                        original_graph.nodes[node.id]['annotation_timestamp'] = node.properties.get('annotation_timestamp')
                        updated_count += 1
            
            # 4. Write updated GraphML
            nx.write_graphml(original_graph, graphml_path, prettyprint=True)
            
            return True, f"Updated {updated_count} annotated nodes in GraphML file"
            
        except Exception as e:
            return False, f"Failed to update GraphML: {str(e)}"
    
    def create_backup(self, graphml_path: Path) -> Path:
        """Create timestamped backup of GraphML file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{graphml_path.stem}_backup_{timestamp}.graphml"
        backup_path = self.backup_dir / backup_name
        
        import shutil
        shutil.copy2(graphml_path, backup_path)
        return backup_path
```

### Step 2: Modify annotation_processor.py

**Add GraphML update capability:**

```python
class AnnotationProcessor:
    def __init__(self):
        self.annotation_manager = AnnotationManager()
        self.link_generator = ModiFinderLinkGenerator()
        self.graphml_persistence = GraphMLPersistenceManager()  # NEW
    
    def apply_all_pending_updates(self, network: ChemicalNetwork) -> Dict[str, Any]:
        # Existing processing...
        results = self.process_pending_annotations(network)
        
        # NEW: Update source GraphML if applicable
        if self._should_update_graphml(network):
            graphml_path = self._get_source_graphml_path(network)
            if graphml_path:
                success, message = self.graphml_persistence.update_graphml_with_annotations(
                    graphml_path, network
                )
                results['graphml_updated'] = success
                results['graphml_message'] = message
                
                if success:
                    print(f"✅ GraphML updated: {message}")
                else:
                    print(f"❌ GraphML update failed: {message}")
        
        return results
    
    def _should_update_graphml(self, network: ChemicalNetwork) -> bool:
        """Check if network was loaded from GraphML and has annotations"""
        return (
            network.metadata.get("source") == "GraphML" and
            len(network.get_annotated_nodes()) > 0 and
            'source_file_path' in network.metadata
        )
    
    def _get_source_graphml_path(self, network: ChemicalNetwork) -> Optional[Path]:
        """Get path to source GraphML file"""
        source_path = network.metadata.get('source_file_path')
        if source_path:
            return Path(source_path)
        return None
```

### Step 3: Enhanced Network Loading

**Modify loader.py to track source file:**

```python
@staticmethod
@st.cache_data(ttl=3600)
def load_network_from_graphml(file_path: Union[str, Path]) -> ChemicalNetwork:
    # Existing loading logic...
    
    network = ChemicalNetwork(
        metadata={
            "source": "GraphML",
            "source_file_path": str(file_path),  # NEW: Track source file
            "directed": G.is_directed(),
            "multigraph": G.is_multigraph(),
            "initial_node_count": initial_node_count,
            "isolated_nodes_removed": len(isolated_nodes),
            "loaded_at": datetime.now().isoformat()  # NEW: Track load time
        }
    )
    
    # Rest of existing logic...
    return network
```

### Step 4: Annotation Preservation During Reload

**Add network reload capability:**

```python
class DataLoader:
    @staticmethod
    def reload_network_preserving_annotations(
        file_path: Union[str, Path], 
        existing_network: ChemicalNetwork
    ) -> ChemicalNetwork:
        """
        Reload network from file while preserving user annotations.
        
        Args:
            file_path: Path to GraphML file
            existing_network: Network with user annotations
            
        Returns:
            Fresh network with preserved annotations
        """
        # Extract annotations from existing network
        preserved_annotations = {}
        for node in existing_network.nodes:
            if node.is_annotated():
                preserved_annotations[node.id] = node.get_annotation_properties()
        
        # Load fresh network
        fresh_network = DataLoader.load_network_from_graphml(file_path)
        
        # Apply preserved annotations
        for node in fresh_network.nodes:
            if node.id in preserved_annotations:
                node.apply_annotation_properties(preserved_annotations[node.id])
        
        return fresh_network
```

### Step 5: UI Integration

**Add GraphML update status to UI:**

```python
# In annotation_processor.py render_pending_updates_panel()
if st.button("Apply All Updates", type="primary", key="apply_all_annotations"):
    if st.session_state.network:
        with st.spinner("Processing annotations and updating GraphML..."):
            results = self.apply_all_pending_updates(st.session_state.network)
        
        # Show results
        if results['processed'] > 0:
            st.success(f"✅ Processed {results['processed']} annotation(s)")
            
            # NEW: Show GraphML update status
            if 'graphml_updated' in results:
                if results['graphml_updated']:
                    st.success(f"📁 {results['graphml_message']}")
                else:
                    st.warning(f"⚠️ GraphML update failed: {results['graphml_message']}")
```

## Migration Strategy

### Phase 1: Backward Compatibility
- Maintain existing JSON annotation system
- Add GraphML updates as additional layer
- No breaking changes to current workflow

### Phase 2: Enhanced Features
- Add GraphML reload with annotation preservation
- Implement backup/restore functionality
- Add conflict resolution for external changes

### Phase 3: Optimization
- Cache GraphML parsing for performance
- Batch multiple annotation updates
- Add validation for GraphML structure integrity

## Risk Mitigation

### Data Safety
1. **Always backup original GraphML** before modification
2. **Validate structure** after updates
3. **Fallback to JSON** if GraphML update fails
4. **Version control integration** for tracking changes

### Performance Considerations
1. **Debounce updates** - don't update on every annotation
2. **Batch processing** - update GraphML once for multiple annotations
3. **Cache validation** - verify file hasn't changed externally
4. **Async updates** - don't block UI during file operations

### Error Handling
1. **Graceful degradation** - continue with JSON if GraphML fails
2. **Clear error messages** - inform user of update status
3. **Recovery mechanisms** - restore from backup if needed
4. **Logging** - detailed logs for debugging

## Testing Strategy

### Unit Tests
- GraphML persistence manager functionality
- Annotation property mapping
- Backup/restore operations
- Error condition handling

### Integration Tests
- End-to-end annotation flow with GraphML updates
- Network reload with preserved annotations
- ModiFinder link generation after GraphML updates
- UI feedback and error display

### Manual Testing
- Large GraphML files (performance)
- Complex annotation scenarios
- External GraphML modifications
- Backup/restore workflows

This implementation maintains existing functionality while adding robust GraphML persistence, ensuring user annotations are preserved across sessions and file updates.