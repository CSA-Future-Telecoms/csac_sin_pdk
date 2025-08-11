
import numpy as np
import matplotlib.pyplot as plt

# Material coefficients dictionary
SELLMEIER_COEFFS = {
    'silicon': {
        'coeffs': {
            'A': 11.6858,
            'B1': 0.939816,
            'B2': 8.10461e-3,
            'B3': 1.09709,
            'C1': 1.1071e-2,  # μm²
            'C2': 1.2025,     # μm²
            'C3': 1.5931e3    # μm²
        },
        'valid_range': (1.2, 14),  # μm
        'equation_type': 'silicon',
        'reference': """Edwards, D.F. (1985). Silicon (Si). In Handbook of Optical Constants 
of Solids, edited by E.D. Palik, Academic Press.
Available at: https://refractiveindex.info/?shelf=main&book=Si&page=Edwards"""
    },
    'sio2': {
        'coeffs': {
            'B1': 0.696166300,
            'B2': 0.407942600,
            'B3': 0.897479400,
            'C1': 4.67914826e-3,  # μm²
            'C2': 1.35120631e-2,  # μm²
            'C3': 97.9340025      # μm²
        },
        'valid_range': (0.21, 6.7),  # μm
        'equation_type': 'standard',
        'reference': """Malitson, I.H. (1965). "Interspecimen comparison of the refractive index 
of fused silica," Journal of the Optical Society of America, 55(10), 1205-1209.
DOI: https://doi.org/10.1364/JOSA.55.001205
Available at: https://refractiveindex.info/?shelf=main&book=SiO2&page=Malitson"""
    },
    'silica': 'sio2',  # Alias
    'fused_silica': 'sio2',  # Alias
    'si': 'silicon',  # Alias
}

def sellmeier_refractive_index(material, wavelength):
    """
    Calculate refractive index using Sellmeier equation for specified material.
    
    Parameters:
    -----------
    material : str
        Material name. Supported materials:
        - 'silicon', 'si': Silicon
        - 'sio2', 'silica', 'fused_silica': Silicon dioxide (fused silica)
    wavelength : float or array-like
        Wavelength in micrometers
    
    Returns:
    --------
    float or ndarray
        Refractive index
        
    Raises:
    -------
    ValueError
        If material is not supported
    """
    # Handle aliases
    material_key = material.lower()
    if material_key in SELLMEIER_COEFFS and isinstance(SELLMEIER_COEFFS[material_key], str):
        material_key = SELLMEIER_COEFFS[material_key]
    
    if material_key not in SELLMEIER_COEFFS:
        supported = [k for k in SELLMEIER_COEFFS.keys() if not isinstance(SELLMEIER_COEFFS[k], str)]
        raise ValueError(f"Material '{material}' not supported. Supported materials: {supported}")
    
    material_data = SELLMEIER_COEFFS[material_key]
    coeffs = material_data['coeffs']
    valid_range = material_data['valid_range']
    
    lam = np.asarray(wavelength)
    lam2 = lam**2
    
    # Check wavelength range
    if np.any(lam < valid_range[0]) or np.any(lam > valid_range[1]):
        print(f"Warning: Wavelength outside valid range ({valid_range[0]}-{valid_range[1]} μm) for {material}")
    
    # Calculate n² based on equation type
    if material_data['equation_type'] == 'silicon':
        # Silicon: n²(λ) = A + B₁λ²/(λ² - C₁) + B₂λ²/(λ² - C₂) + B₃λ²/(λ² - C₃)
        n_squared = (coeffs['A'] + 
                     coeffs['B1'] * lam2 / (lam2 - coeffs['C1']) +
                     coeffs['B2'] * lam2 / (lam2 - coeffs['C2']) +
                     coeffs['B3'] * lam2 / (lam2 - coeffs['C3']))
    else:
        # Standard Sellmeier: n²(λ) = 1 + B₁λ²/(λ² - C₁) + B₂λ²/(λ² - C₂) + B₃λ²/(λ² - C₃)
        n_squared = (1 + 
                     coeffs['B1'] * lam2 / (lam2 - coeffs['C1']) +
                     coeffs['B2'] * lam2 / (lam2 - coeffs['C2']) +
                     coeffs['B3'] * lam2 / (lam2 - coeffs['C3']))
    
    return np.sqrt(n_squared)

def get_material_info(material):
    """
    Get information about a supported material.
    
    Parameters:
    -----------
    material : str
        Material name
        
    Returns:
    --------
    dict
        Material information including coefficients, valid range, and reference
    """
    material_key = material.lower()
    if material_key in SELLMEIER_COEFFS and isinstance(SELLMEIER_COEFFS[material_key], str):
        material_key = SELLMEIER_COEFFS[material_key]
    
    if material_key not in SELLMEIER_COEFFS:
        supported = [k for k in SELLMEIER_COEFFS.keys() if not isinstance(SELLMEIER_COEFFS[k], str)]
        raise ValueError(f"Material '{material}' not supported. Supported materials: {supported}")
    
    return SELLMEIER_COEFFS[material_key].copy()

def list_supported_materials():
    """List all supported materials and their aliases."""
    materials = {}
    for key, value in SELLMEIER_COEFFS.items():
        if isinstance(value, str):
            # This is an alias
            if value not in materials:
                materials[value] = [value]
            materials[value].append(key)
        else:
            # This is a primary material
            if key not in materials:
                materials[key] = [key]
    
    print("Supported materials and aliases:")
    for primary, aliases in materials.items():
        print(f"  {primary.upper()}: {', '.join(aliases)}")