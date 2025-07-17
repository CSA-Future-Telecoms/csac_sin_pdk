"""Ring Resonators."""

import gdsfactory as gf
from gdsfactory.typings import CrossSectionSpec

from cspdk.sin300.cband.tech import TECH


@gf.cell
def SiN300nm_1550nm_TE_CSAC_Euler_bend(
    radius: float = 40.0,
    angle: float = 90.0,
    p: float = 1.0,
    cross_section: CrossSectionSpec = "strip",

) -> gf.Component:
    """Creates an Euler bend with specified parameters.
    Args:
        radius: Bend radius in micrometers.
        angle: Bend angle in degrees.
        p: Parameter for the Euler bend, typically related to the curvature.
        cross_section: Cross-section specification, defaults to "strip".
    Returns:
        A GDSFactory component representing the Euler bend.
    """
    return gf.components.bend_euler(
        radius = radius,
        angle = angle,
        p = p,
        cross_section=cross_section,
    )





    


if __name__ == "__main__":
    from cspdk.sin300.cband import PDK

    PDK.activate()
    c = csac_euler
    c.show()