"""
Mass Decomposition Utility for Chemical Network Analysis.

This module provides functionality to decompose delta_mz values into possible
molecular formulas using combinatorial approaches with natural product elements.
"""

import hashlib
import json
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import os
from pathlib import Path

# Try to import required libraries with fallbacks
try:
    import emzed
    EMZED_AVAILABLE = True
except ImportError:
    EMZED_AVAILABLE = False

try:
    import msbuddy
    MSBUDDY_AVAILABLE = True
except ImportError:
    MSBUDDY_AVAILABLE = False

try:
    import molmass
    MOLMASS_AVAILABLE = True
except ImportError:
    MOLMASS_AVAILABLE = False


@dataclass
class FormulaCandidate:
    """Represents a possible molecular formula for a mass difference."""
    formula: str
    exact_mass: float
    mass_error_ppm: float
    mass_error_da: float
    element_counts: Dict[str, int]
    confidence_score: float
    rule_compliance: Dict[str, bool]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'formula': self.formula,
            'exact_mass': self.exact_mass,
            'mass_error_ppm': self.mass_error_ppm,
            'mass_error_da': self.mass_error_da,
            'element_counts': self.element_counts,
            'confidence_score': self.confidence_score,
            'rule_compliance': self.rule_compliance
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FormulaCandidate':
        """Create from dictionary."""
        return cls(**data)


class MassDecompositionConfig:
    """Configuration for mass decomposition parameters."""
    
    def __init__(
        self,
        tolerance_ppm: float = 5.0,
        tolerance_da: float = 0.003,
        max_formulas: int = 10,
        elements: Optional[Dict[str, Tuple[int, int]]] = None,
        apply_golden_rules: bool = True,
        cache_enabled: bool = True
    ):
        self.tolerance_ppm = tolerance_ppm
        self.tolerance_da = tolerance_da
        self.max_formulas = max_formulas
        self.apply_golden_rules = apply_golden_rules
        self.cache_enabled = cache_enabled
        
        # Default element ranges for natural products
        if elements is None:
            self.elements = {
                'C': (0, 100),   # Carbon
                'H': (0, 200),   # Hydrogen  
                'N': (0, 50),    # Nitrogen
                'O': (0, 50),    # Oxygen
                'P': (0, 10),    # Phosphorus
                'S': (0, 10),    # Sulfur
                'F': (0, 20),    # Fluorine
                'Cl': (0, 10),   # Chlorine
                'Br': (0, 5),    # Bromine
                'I': (0, 3)      # Iodine
            }
        else:
            self.elements = elements


class MassDecomposer:
    """Main class for mass decomposition functionality."""
    
    def __init__(self, config: Optional[MassDecompositionConfig] = None):
        self.config = config or MassDecompositionConfig()
        self.cache = {}
        self.cache_file = Path("annotations/mass_decomposition_cache.json")
        self.cache_file.parent.mkdir(exist_ok=True)
        
        # Load cache if enabled
        if self.config.cache_enabled:
            self._load_cache()
    
    def _load_cache(self):
        """Load decomposition cache from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Convert back to FormulaCandidate objects
                    for key, candidates in cache_data.items():
                        self.cache[key] = [
                            FormulaCandidate.from_dict(c) for c in candidates
                        ]
        except Exception as e:
            print(f"Warning: Could not load mass decomposition cache: {e}")
    
    def _save_cache(self):
        """Save decomposition cache to file."""
        if not self.config.cache_enabled:
            return
            
        try:
            cache_data = {}
            for key, candidates in self.cache.items():
                cache_data[key] = [c.to_dict() for c in candidates]
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save mass decomposition cache: {e}")
    
    def _get_cache_key(self, delta_mz: float) -> str:
        """Generate cache key for a mass value."""
        # Include configuration in cache key to avoid invalid cached results
        config_str = f"{self.config.tolerance_ppm}_{self.config.tolerance_da}_{self.config.max_formulas}"
        mass_str = f"{delta_mz:.6f}"
        return hashlib.md5(f"{mass_str}_{config_str}".encode()).hexdigest()
    
    def is_available(self) -> Tuple[bool, List[str]]:
        """Check if mass decomposition libraries are available."""
        available_libs = []
        if EMZED_AVAILABLE:
            available_libs.append("emzed")
        if MSBUDDY_AVAILABLE:
            available_libs.append("msbuddy")
        if MOLMASS_AVAILABLE:
            available_libs.append("molmass")
        
        return len(available_libs) > 0, available_libs
    
    def decompose_mass(self, delta_mz: float) -> List[FormulaCandidate]:
        """
        Decompose a mass difference into possible molecular formulas.
        
        Args:
            delta_mz: Mass difference value in Da
            
        Returns:
            List of possible formula candidates
        """
        # Check cache first
        cache_key = self._get_cache_key(delta_mz)
        if self.config.cache_enabled and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Skip decomposition for very small or negative masses
        if delta_mz < 0.1:
            return []
        
        candidates = []
        
        # Try emzed first (preferred method)
        if EMZED_AVAILABLE:
            candidates = self._decompose_with_emzed(delta_mz)
        elif MSBUDDY_AVAILABLE:
            candidates = self._decompose_with_msbuddy(delta_mz)
        elif MOLMASS_AVAILABLE:
            candidates = self._decompose_with_molmass(delta_mz)
        else:
            print("Warning: No mass decomposition libraries available")
            return []
        
        # Cache results
        if self.config.cache_enabled:
            self.cache[cache_key] = candidates
            self._save_cache()
        
        return candidates
    
    def _decompose_with_emzed(self, delta_mz: float) -> List[FormulaCandidate]:
        """Decompose mass using emzed library."""
        try:
            # Calculate mass range with tolerance
            tolerance_da = max(
                self.config.tolerance_da,
                delta_mz * self.config.tolerance_ppm / 1e6
            )
            
            min_mass = delta_mz - tolerance_da
            max_mass = delta_mz + tolerance_da
            
            # Prepare element ranges for emzed
            element_kwargs = {}
            for element, (min_count, max_count) in self.config.elements.items():
                if element.lower() in ['c', 'h', 'n', 'o', 'p', 's']:
                    element_kwargs[f"{element.lower()}_range"] = (min_count, max_count)
            
            # Generate formula table using emzed
            formula_table = emzed.chemistry.formula_table(
                min_mass,
                max_mass,
                apply_rules=self.config.apply_golden_rules,
                **element_kwargs
            )
            
            candidates = []
            for row in formula_table.rows[:self.config.max_formulas]:
                formula_str = str(row.formula)
                exact_mass = float(row.mass)
                mass_error_da = exact_mass - delta_mz
                mass_error_ppm = (mass_error_da / delta_mz) * 1e6 if delta_mz > 0 else 0
                
                # Extract element counts
                element_counts = self._parse_formula_elements(formula_str)
                
                # Calculate confidence score (simplified)
                confidence_score = self._calculate_confidence_score(
                    mass_error_ppm, element_counts
                )
                
                # Rule compliance (simplified - would need more detailed analysis)
                rule_compliance = {
                    'golden_rules': self.config.apply_golden_rules,
                    'mass_tolerance': abs(mass_error_ppm) <= self.config.tolerance_ppm
                }
                
                candidate = FormulaCandidate(
                    formula=formula_str,
                    exact_mass=exact_mass,
                    mass_error_ppm=mass_error_ppm,
                    mass_error_da=mass_error_da,
                    element_counts=element_counts,
                    confidence_score=confidence_score,
                    rule_compliance=rule_compliance
                )
                
                candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            print(f"Error in emzed decomposition: {e}")
            return []
    
    def _decompose_with_msbuddy(self, delta_mz: float) -> List[FormulaCandidate]:
        """Decompose mass using msbuddy library."""
        try:
            # msbuddy expects m/z values, so we'll treat delta_mz as neutral mass
            config = msbuddy.MsbuddyConfig(
                ppm=self.config.tolerance_ppm,
                instrument=None  # Generic instrument
            )
            
            # Use mass_to_formula for neutral mass
            result = msbuddy.mass_to_formula(delta_mz, config=config)
            
            candidates = []
            if result and hasattr(result, 'formula_list'):
                for formula_info in result.formula_list[:self.config.max_formulas]:
                    formula_str = str(formula_info.formula)
                    exact_mass = float(formula_info.mass)
                    mass_error_da = exact_mass - delta_mz
                    mass_error_ppm = (mass_error_da / delta_mz) * 1e6 if delta_mz > 0 else 0
                    
                    element_counts = self._parse_formula_elements(formula_str)
                    
                    confidence_score = getattr(formula_info, 'score', 0.5)
                    
                    rule_compliance = {
                        'msbuddy_score': confidence_score > 0.3,
                        'mass_tolerance': abs(mass_error_ppm) <= self.config.tolerance_ppm
                    }
                    
                    candidate = FormulaCandidate(
                        formula=formula_str,
                        exact_mass=exact_mass,
                        mass_error_ppm=mass_error_ppm,
                        mass_error_da=mass_error_da,
                        element_counts=element_counts,
                        confidence_score=confidence_score,
                        rule_compliance=rule_compliance
                    )
                    
                    candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            print(f"Error in msbuddy decomposition: {e}")
            return []
    
    def _decompose_with_molmass(self, delta_mz: float) -> List[FormulaCandidate]:
        """Fallback decomposition using molmass (basic functionality)."""
        try:
            # molmass is primarily for mass calculation, not decomposition
            # This is a basic fallback - generate some common formulas and check masses
            
            common_formulas = [
                "CH2", "CH4", "NH", "NH2", "OH", "H2O", "CO", "CO2", 
                "CHO", "CH2O", "C2H4", "C2H6", "NO", "NO2", "SO", "SO2",
                "CH3", "C2H2", "C2H5", "C3H6", "PO3", "HPO3"
            ]
            
            candidates = []
            tolerance_da = max(
                self.config.tolerance_da,
                delta_mz * self.config.tolerance_ppm / 1e6
            )
            
            for formula_str in common_formulas:
                try:
                    mol = molmass.Formula(formula_str)
                    exact_mass = mol.isotope.mass
                    mass_error_da = exact_mass - delta_mz
                    
                    if abs(mass_error_da) <= tolerance_da:
                        mass_error_ppm = (mass_error_da / delta_mz) * 1e6 if delta_mz > 0 else 0
                        
                        element_counts = dict(mol.composition())
                        
                        confidence_score = max(0.1, 1.0 - abs(mass_error_ppm) / self.config.tolerance_ppm)
                        
                        rule_compliance = {
                            'common_formula': True,
                            'mass_tolerance': abs(mass_error_ppm) <= self.config.tolerance_ppm
                        }
                        
                        candidate = FormulaCandidate(
                            formula=formula_str,
                            exact_mass=exact_mass,
                            mass_error_ppm=mass_error_ppm,
                            mass_error_da=mass_error_da,
                            element_counts=element_counts,
                            confidence_score=confidence_score,
                            rule_compliance=rule_compliance
                        )
                        
                        candidates.append(candidate)
                
                except Exception:
                    continue  # Skip invalid formulas
            
            # Sort by mass error and take top candidates
            candidates.sort(key=lambda x: abs(x.mass_error_ppm))
            return candidates[:self.config.max_formulas]
            
        except Exception as e:
            print(f"Error in molmass decomposition: {e}")
            return []
    
    def _parse_formula_elements(self, formula_str: str) -> Dict[str, int]:
        """Parse molecular formula string to extract element counts."""
        import re
        
        element_counts = {}
        
        # Regular expression to match element symbol followed by optional number
        pattern = r'([A-Z][a-z]?)(\d*)'
        matches = re.findall(pattern, formula_str)
        
        for element, count_str in matches:
            count = int(count_str) if count_str else 1
            element_counts[element] = element_counts.get(element, 0) + count
        
        return element_counts
    
    def _calculate_confidence_score(
        self, 
        mass_error_ppm: float, 
        element_counts: Dict[str, int]
    ) -> float:
        """Calculate a confidence score for a formula candidate."""
        # Start with mass accuracy score
        mass_score = max(0.0, 1.0 - abs(mass_error_ppm) / self.config.tolerance_ppm)
        
        # Chemical reasonableness score (simplified)
        chem_score = 1.0
        total_atoms = sum(element_counts.values())
        
        # Penalize very large or very small formulas
        if total_atoms > 50:
            chem_score *= 0.5
        elif total_atoms < 2:
            chem_score *= 0.7
        
        # Favor formulas with carbon
        if 'C' in element_counts:
            chem_score *= 1.1
        
        # Penalize formulas with too many heteroatoms
        heteroatoms = sum(count for elem, count in element_counts.items() 
                         if elem not in ['C', 'H'])
        if heteroatoms > total_atoms * 0.5:
            chem_score *= 0.8
        
        return min(1.0, mass_score * chem_score)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the decomposition cache and performance."""
        available, libs = self.is_available()
        
        return {
            'libraries_available': libs,
            'cache_size': len(self.cache),
            'cache_enabled': self.config.cache_enabled,
            'tolerance_ppm': self.config.tolerance_ppm,
            'tolerance_da': self.config.tolerance_da,
            'max_formulas': self.config.max_formulas,
            'supported_elements': list(self.config.elements.keys())
        }


# Factory function for easy instantiation
def create_mass_decomposer(config: Optional[Dict[str, Any]] = None) -> MassDecomposer:
    """Create a MassDecomposer with optional configuration."""
    if config:
        decomp_config = MassDecompositionConfig(
            tolerance_ppm=config.get('tolerance_ppm', 5.0),
            tolerance_da=config.get('tolerance_da', 0.003),
            max_formulas=config.get('max_formulas', 10),
            elements=config.get('elements'),
            apply_golden_rules=config.get('apply_golden_rules', True),
            cache_enabled=config.get('cache_enabled', True)
        )
    else:
        decomp_config = MassDecompositionConfig()
    
    return MassDecomposer(decomp_config)