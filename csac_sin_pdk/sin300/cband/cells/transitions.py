import pandas as pd
import os
from csac_sin_pdk.sin300.cband.config import PATH
import numpy as np
from matplotlib import pyplot as plt
from scipy import interpolate
import gdsfactory as gf






def get_transition_data(width : float) -> np.ndarray:
    """Returns the effective index for a given width."""
    transition_data = pd.read_csv(PATH.cells / "2025-08-04T17_13_02_mode_properties_with_width.csv")
    spline = interpolate.CubicSpline(transition_data["width(um)"], transition_data["neff"])
    return spline(width)

@gf.cell
def sim_adiab_taper(width1 = 1.2, width2 = 5, **kwargs) -> gf.Component:
    """
    Returns a taper with adiabatic transition for silicon nitride 300nm thick strip waveguide
    Aditional kwargs are same as in gdsfactory.components.taper_adiabatic.
    """
    return gf.components.taper_adiabatic(width1 = width1,
                                        width2 = width2,
                                        neff_w = get_transition_data, 
                                        wavelength = 1.55, 
                                        cross_section = "strip", 
                                        max_length = 500, 
                                        **kwargs)

if __name__ == "__main__":
    # We are doing it here so that we don't load the data and do the fit every time the component is created
    transition_data = pd.read_csv(PATH.cells / "2025-08-04T17_13_02_mode_properties_with_width.csv")
    z = np.polyfit(transition_data["width(um)"], transition_data["neff"], deg = 10)
    spline = interpolate.CubicSpline(transition_data["width(um)"], transition_data["neff"])
    p = np.poly1d(z)
    plt.plot(transition_data["width(um)"], transition_data["neff"], marker = "o", label = "Data")
    fine_grained_widths = np.linspace(min(transition_data["width(um)"]), max(transition_data["width(um)"]), 100)
    plt.plot(fine_grained_widths, p(fine_grained_widths), label = "polyfit")
    plt.plot(fine_grained_widths, spline(fine_grained_widths), label = "polyfit")
    print(spline)
    plt.show()
    # with open("width_vs_neff_coeffs.txt", "w") as f:
        

