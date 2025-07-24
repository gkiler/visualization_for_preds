# Chemical Data Visualization App

A Streamlit-based application for visualizing chemical data networks with interactive filtering, coloring, and external figure integration.

## Features

- **Network Visualization**: Cytoscape-style network visualization using PyVis
- **Dynamic Filtering**: Filter nodes and edges by type, properties, and connectivity
- **Attribute-Based Styling**: Color and size nodes/edges based on data attributes
- **Interactive Controls**: User-friendly sidebar controls for customization
- **External Figure Integration**: Fetch and display figures from URLs
- **Session State Management**: Persistent state across interactions
- **Performance Optimization**: Built-in caching for data loading

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd chemical_viz_app

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the application
streamlit run app.py
```

## Data Format

### CSV Format
- **Nodes CSV**: Must contain columns for `id`, `label`, and `type`
- **Edges CSV**: Must contain columns for `source`, `target`, and `type`

### JSON Format
```json
{
  "nodes": [
    {
      "id": "node1",
      "label": "Node 1",
      "type": "molecule",
      "properties": {"weight": 180.16}
    }
  ],
  "edges": [
    {
      "source": "node1",
      "target": "node2",
      "type": "interaction",
      "weight": 0.8
    }
  ]
}
```

### GraphML Format
GraphML files with full node and edge attribute support. Compatible with:
- Cytoscape
- Gephi
- yEd Graph Editor
- NetworkX

Key attributes automatically mapped:
- Node: `type`, `label`, `size`, `color`, `x`, `y`
- Edge: `type`, `weight`, `color`, `width`
- All other attributes preserved in `properties` dictionary

Example structure:
```xml
<node id="mol1">
  <data key="type">molecule</data>
  <data key="label">Glucose</data>
  <data key="formula">C6H12O6</data>
  <data key="weight">180.16</data>
</node>
```

## Project Structure

```
chemical_viz_app/
├── app.py                 # Main application
├── config.yaml           # Configuration settings
├── src/
│   ├── data/            # Data models and loading
│   ├── visualization/   # Network visualization and filtering
│   ├── ui/             # User interface components
│   └── utils/          # Utility functions
```

## Key Components

1. **Data Models**: Structured classes for nodes, edges, and networks
2. **Network Visualizer**: PyVis-based visualization with customization
3. **Filtering System**: Advanced filtering by properties and connectivity
4. **UI Components**: Modular interface elements
5. **Figure Handler**: External figure retrieval and display