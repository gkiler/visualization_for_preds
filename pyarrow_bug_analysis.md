# PyArrow Serialization Error Analysis

## Error Summary
The application is experiencing PyArrow serialization errors when displaying dataframes in Streamlit:

1. `ArrowTypeError for column '#ClusterIdx'` - "Expected bytes, got a 'float' object"
2. `ArrowTypeError for column 'library_smiles_x'` - "Expected bytes, got a 'int' object"

## Key Findings

### 1. Data Display Location
The primary location where dataframes are displayed is in `/Users/gwenkiler/Documents/Projects/research/visualization_for_preds/chemical_viz_app/src/ui/components.py`:

- **Lines 110-115**: Node data displayed using `st.dataframe(nodes_df)`
- **Lines 129-134**: Edge data displayed using `st.dataframe(edges_df)`

### 2. Data Flow Analysis

#### GraphML Data Loading Process:
1. **File Loading**: GraphML files are loaded using NetworkX in `loader.py:load_network_from_graphml()`
2. **Data Processing**: Node and edge attributes are extracted and processed (lines 99-113 for nodes, 158-172 for edges)
3. **Type Conversion**: String values are converted to numeric types when possible
4. **DataFrame Creation**: Data is converted to DataFrames in `components.py:render_data_tables()`

#### DataFrame Creation Process:
1. **Node DataFrame**: Created by iterating through nodes and building dictionaries (lines 100-108)
2. **Edge DataFrame**: Created by iterating through edges and building dictionaries (lines 118-127)
3. **Property Merging**: Node/edge properties are merged directly into the dictionaries using `dict.update()`

### 3. Root Cause Analysis

#### Problem 1: Mixed Data Types in Properties
The GraphML loader attempts to convert string values to numeric types (lines 102-113 in loader.py):
```python
if isinstance(value, str):
    try:
        if '.' in value:
            properties[key] = float(value)
        else:
            properties[key] = int(value)
    except ValueError:
        properties[key] = value
else:
    properties[key] = value
```

However, this conversion may be inconsistent across different nodes/edges, leading to mixed data types in the same column.

#### Problem 2: DataFrame Column Type Inference
When pandas creates DataFrames from the dictionaries, it infers column types based on the first few values. If later values have different types, PyArrow (used by Streamlit for serialization) fails because it expects consistent types.

#### Problem 3: Special Characters in Column Names
The `#ClusterIdx` column name contains a `#` character, which may cause additional serialization issues.

### 4. Specific Issues Identified

#### Column '#ClusterIdx'
- Contains mixed float/string data types
- Special character `#` in column name may cause PyArrow issues
- Error: "Expected bytes, got a 'float' object" suggests type confusion

#### Column 'library_smiles_x' 
- Contains mixed int/string data types
- Error: "Expected bytes, got a 'int' object" suggests similar type confusion
- The `_x` suffix suggests pandas merge operation may have occurred

### 5. Data Processing Locations

#### GraphML Processing:
- `/Users/gwenkiler/Documents/Projects/research/visualization_for_preds/chemical_viz_app/src/data/loader.py` lines 99-172
- Type conversion logic may create inconsistent types

#### DataFrame Display:
- `/Users/gwenkiler/Documents/Projects/research/visualization_for_preds/chemical_viz_app/src/ui/components.py` lines 95-134
- Direct property merging without type validation

## Recommended Solutions

### 1. Consistent Type Handling
- Implement consistent type validation and conversion
- Ensure all values in a column have the same data type
- Convert problematic columns to strings if mixed types are needed

### 2. Column Name Sanitization
- Remove or replace special characters in column names
- Implement column name validation

### 3. DataFrame Type Enforcement
- Explicitly specify column data types when creating DataFrames
- Use pandas `astype()` to ensure consistent types

### 4. Error Handling
- Add try-catch blocks around DataFrame display operations
- Provide fallback display methods for problematic data