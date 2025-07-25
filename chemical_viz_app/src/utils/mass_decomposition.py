"""Simple mass decomposition using msbuddy with correct API"""

from typing import List, Dict, Any, Optional
from msbuddy import Msbuddy


def decompose_mass(mass: float, tolerance_da: float = 0.1) -> List[Dict[str, Any]]:
    """
    Decompose a mass into possible molecular formulas.
    
    Args:
        mass: Target mass in Da
        tolerance_da: Mass tolerance in Da (default 0.1)
        
    Returns:
        List of formula dictionaries with formula, mass_error, and mass_error_ppm
    """
    try:
        # Create msbuddy instance
        engine = Msbuddy()
        
        # Get formula results using the correct API
        formula_results = engine.mass_to_formula(
            mass=mass,
            mass_tol=tolerance_da,
            ppm=False,  # Using Da, not ppm
        )
        
        # Convert to simple dictionaries
        candidates = []
        for result in formula_results:
            candidate = {
                'formula': str(result.formula),
                'mass_error': result.mass_error,
                'mass_error_ppm': result.mass_error_ppm
            }
            candidates.append(candidate)
            
        return candidates
        
    except Exception as e:
        print(f"Error in mass decomposition: {e}")
        return []


def process_edge_mass_decomposition(edge, tolerance_da: float = 0.1) -> None:
    """
    Process mass decomposition for a single edge with delta_mz.
    
    Args:
        edge: ChemicalEdge object
        tolerance_da: Mass tolerance in Da
    """
    # Look for delta_mz field
    delta_mz = None
    for field_name in ['delta_mz', 'deltamz', 'mass_diff', 'mass_difference']:
        if field_name in edge.properties:
            try:
                delta_mz = float(edge.properties[field_name])
                break
            except (ValueError, TypeError):
                continue
    
    if delta_mz is None or abs(delta_mz) < 0.1:
        return
    
    # Decompose the mass
    candidates = decompose_mass(abs(delta_mz), tolerance_da)
    
    if candidates:
        # Store results in edge properties
        edge.properties['formula_candidates'] = candidates
        edge.properties['primary_formula'] = candidates[0]['formula']
        edge.properties['formula_mass_error'] = candidates[0]['mass_error']
        edge.properties['formula_mass_error_ppm'] = candidates[0]['mass_error_ppm']


def process_network_mass_decomposition(network, tolerance_da: float = 0.1) -> int:
    """
    Process mass decomposition for all edges in a network efficiently.
    Uses a single msbuddy engine and processes unique masses only.
    
    Args:
        network: ChemicalNetwork object
        tolerance_da: Mass tolerance in Da
        
    Returns:
        Number of edges processed
    """
    # Step 1: Collect all unique delta_mz values and their edges
    mass_to_edges = {}  # mass -> list of edges with that mass
    
    for edge in network.edges:
        # Look for delta_mz field
        delta_mz = None
        for field_name in ['delta_mz', 'deltamz', 'mass_diff', 'mass_difference']:
            if field_name in edge.properties:
                try:
                    delta_mz = float(edge.properties[field_name])
                    break
                except (ValueError, TypeError):
                    continue
        
        if delta_mz is not None and abs(delta_mz) >= 0.1:
            mass_key = abs(delta_mz)  # Use absolute value as key
            if mass_key not in mass_to_edges:
                mass_to_edges[mass_key] = []
            mass_to_edges[mass_key].append(edge)
    
    if not mass_to_edges:
        print("Mass decomposition: no edges with delta_mz values found")
        return 0
    
    print(f"Mass decomposition: found {len(mass_to_edges)} unique masses across {sum(len(edges) for edges in mass_to_edges.values())} edges")
    
    # Step 2: Create single msbuddy engine and process unique masses
    try:
        engine = Msbuddy()
        mass_to_formulas = {}  # mass -> formula candidates dict
        
        for mass in mass_to_edges.keys():
            try:
                # Get formula results using the correct API
                formula_results = engine.mass_to_formula(
                    mass=mass,
                    mass_tol=tolerance_da,
                    ppm=False,  # Using Da, not ppm
                )
                
                # Convert to simple dictionaries
                candidates = []
                for result in formula_results:
                    candidate = {
                        'formula': str(result.formula),
                        'mass_error': result.mass_error,
                        'mass_error_ppm': result.mass_error_ppm
                    }
                    candidates.append(candidate)
                
                mass_to_formulas[mass] = candidates
                
            except Exception as e:
                print(f"Error decomposing mass {mass}: {e}")
                mass_to_formulas[mass] = []
        
        # Step 3: Apply results to all edges with each mass
        processed_count = 0
        for mass, candidates in mass_to_formulas.items():
            if candidates:
                edges = mass_to_edges[mass]
                for edge in edges:
                    # Store results in edge properties
                    edge.properties['formula_candidates'] = candidates
                    edge.properties['primary_formula'] = candidates[0]['formula']
                    edge.properties['formula_mass_error'] = candidates[0]['mass_error']
                    edge.properties['formula_mass_error_ppm'] = candidates[0]['mass_error_ppm']
                    processed_count += 1
        
        print(f"Mass decomposition: processed {processed_count} edges with formula results")
        return processed_count
        
    except Exception as e:
        print(f"Error in mass decomposition processing: {e}")
        return 0