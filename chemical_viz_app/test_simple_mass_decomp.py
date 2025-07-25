#!/usr/bin/env python3
"""Test the new simple mass decomposition"""

import sys
sys.path.append('.')

from src.utils.mass_decomposition import decompose_mass

# Test known masses
test_cases = [
    15.994,  # O
    18.010,  # H2O
    28.006,  # CO/N2
    44.009,  # CO2
]

print("Testing new mass decomposition implementation:")

for mass in test_cases:
    print(f"\nMass {mass:.3f} Da:")
    candidates = decompose_mass(mass, tolerance_da=0.1)
    
    if candidates:
        for i, candidate in enumerate(candidates[:3], 1):
            print(f"  {i}. {candidate['formula']} (error: {candidate['mass_error']:.4f} Da, {candidate['mass_error_ppm']:.1f} ppm)")
    else:
        print("  No candidates found")