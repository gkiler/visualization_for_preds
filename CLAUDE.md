# Chemical Data Visualization Project Specifications

## Project Overview
Streamlit-based application for visualizing chemical data networks with interactive filtering, coloring, and external figure integration. Built to replace Cytoscape-based workflows with custom requirements and modular functionality.

## Core Requirements

### 1. Network Visualization
- **Primary Goal**: Cytoscape-style network visualization using PyVis
- **Interactive Features**: Physics simulation, drag/drop nodes, zoom/pan
- **Customization**: Node/edge coloring and sizing based on data attributes
- **Performance**: Handle networks up to 1000 nodes, 5000 edges efficiently

### 2. Data Input Formats
- **CSV Files**: Separate nodes.csv and edges.csv with standard columns
- **JSON Files**: Structured format with nodes/edges arrays and metadata
- **GraphML Files**: Full compatibility with Cytoscape, Gephi, yEd exports
- **Sample Data**: Built-in chemical network example for testing

### 3. Filtering System
- **Node Filters**: By type, properties, connectivity (min/max connections)
- **Edge Filters**: By type, properties, weight ranges
- **Selection Tools**: Pick specific nodes with neighbor depth control
- **Filter Logic**: AND/OR combinations for complex filtering
- **Real-time Updates**: Instant visualization updates on filter changes

### 4. Attribute-Based Styling
- **Node Coloring**: By type, custom properties, or fixed colors
- **Node Sizing**: Fixed size or scaled by numeric properties
- **Edge Coloring**: By type, weight, or custom properties
- **Edge Width**: Based on weight or custom attributes
- **Color Maps**: Automatic color mapping for categorical/numeric data

### 5. External Figure Integration
- **URL Fetching**: Retrieve and display figures from web links
- **Local Upload**: Support for PNG, JPG, GIF, BMP, SVG formats
- **Gallery View**: Multiple figures with captions and management
- **Professional Display**: Accessible, responsive figure presentation
- **Caching**: 30-minute cache for web-fetched images

### 6. User Interface
- **Layout**: Wide layout with sidebar controls and main visualization area
- **Controls**: Interactive sidebar with expandable sections
- **Responsive**: Adapts to different screen sizes
- **Accessibility**: Clear labels, helpful tooltips, error messages
- **Export Options**: Framework for HTML/PNG/data export

## Technical Architecture

### Project Structure
```
chemical_viz_app/
├── app.py                 # Main Streamlit application
├── config.yaml           # Configuration settings
├── requirements.txt       # Python dependencies
├── src/
│   ├── data/             # Data models and loading
│   │   ├── models.py     # ChemicalNode, ChemicalEdge, ChemicalNetwork classes
│   │   └── loader.py     # DataLoader with CSV/JSON/GraphML support
│   ├── visualization/    # Network visualization and filtering
│   │   ├── network.py    # NetworkVisualizer with PyVis integration
│   │   └── filters.py    # NetworkFilter with complex filtering logic
│   ├── ui/              # User interface components
│   │   ├── components.py # UIComponents for common elements
│   │   └── sidebar.py    # SidebarControls for all interactive controls
│   └── utils/           # Utility functions
│       └── figures.py   # FigureHandler for external image management
└── tests/               # Unit tests (planned)
```

### Key Technologies
- **Frontend**: Streamlit 1.29+ with components and session state
- **Visualization**: PyVis 0.3.2+ for interactive network graphs
- **Data Processing**: NetworkX 3.2+, Pandas 2.1+, NumPy 1.25+
- **File Formats**: YAML config, JSON/CSV/GraphML data, LXML for GraphML
- **Image Handling**: Pillow 10.0+, Requests for URL fetching
- **Performance**: Built-in Streamlit caching (@st.cache_data)

### Data Models
- **NodeType Enum**: MOLECULE, PROTEIN, REACTION, PATHWAY, OTHER
- **EdgeType Enum**: INTERACTION, ACTIVATION, INHIBITION, BINDING, OTHER
- **ChemicalNode**: ID, label, type, properties dict, optional x/y/size/color
- **ChemicalEdge**: Source, target, type, properties dict, weight, optional color/width
- **ChemicalNetwork**: Nodes list, edges list, metadata dict with validation

## Configuration Management
- **YAML Config**: Centralized settings for visualization, colors, data limits
- **Physics Options**: Configurable network physics parameters
- **Color Schemes**: Default color maps for node/edge types
- **Performance Limits**: Max nodes/edges, cache TTL settings

## Performance Optimizations
- **Caching Strategy**: 1-hour cache for data loading, 30-min for images
- **Modular Loading**: Lazy loading of visualization components
- **Data Validation**: Input validation with user-friendly error messages
- **Memory Management**: Efficient data structures, temp file cleanup

## Future Enhancements (Planned)
- **Export Functionality**: HTML, PNG, SVG export of visualizations
- **Advanced Analytics**: Network metrics, centrality measures
- **Custom Layouts**: Force-directed, hierarchical, circular layouts
- **Collaboration**: Share/save visualization configurations
- **API Integration**: Connect to chemical databases
- **Performance**: Support for larger networks (10K+ nodes)

## Usage Patterns
1. **Data Upload**: Load network from CSV/JSON/GraphML files
2. **Initial Visualization**: View full network with default settings
3. **Interactive Filtering**: Use sidebar controls to focus on subsets
4. **Attribute Styling**: Color/size nodes by chemical properties
5. **Figure Integration**: Add external figures for context
6. **Export/Share**: Save visualizations and configurations

## Development Notes
- **Code Style**: Modular, typed Python with dataclasses
- **Error Handling**: Comprehensive validation with user feedback
- **Documentation**: Inline comments, README, and specification docs
- **Testing**: Unit tests for core functionality (in development)
- **Security**: Validated file uploads, safe URL fetching