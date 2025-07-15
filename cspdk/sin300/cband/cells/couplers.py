"""Evanescent Couplers."""

import gdsfactory as gf
from gdsfactory.typings import ComponentSpec

from cspdk.sin300.cband.tech import TECH
from cspdk.sin300.cband.cells import bend_euler


@gf.cell
def coupler(length: float = 20, gap: float = TECH.gap_strip) -> gf.Component:
    """Returns Symmetric coupler.

    Args:
        length: of coupling region in um.
        gap: of coupling region in um.
    """
    return gf.c.coupler(
        length=length,
        gap=gap,
        dy=4.0,
        dx=20.0,
        cross_section="strip",
        allow_min_radius_violation=False,
    )


@gf.cell
def coupler_ring(
    length_x: float = 4,
    gap: float = TECH.gap_strip,
    radius: float = TECH.radius,
    bend: ComponentSpec = "bend_euler",
    straight: ComponentSpec = "straight",
    cross_section: str = "strip",
    length_extension=3,
) -> gf.Component:
    """Returns Coupler for ring.

    Args:
        length_x: length of the parallel coupled straight waveguides.
        gap: gap between for coupler.
        radius: for the bend and coupler.
        bend: 90 degrees bend spec.
        straight: straight spec.
        cross_section: cross_section spec.
    """
    return gf.c.coupler_ring(
        length_x=length_x,
        gap=gap,
        radius=radius,
        bend=bend,
        straight=straight,
        cross_section=cross_section,
        cross_section_bend=None,
        length_extension=3,
    )


if __name__ == "__main__":
    from cspdk.sin300.cband import PDK

    PDK.activate()
    c = coupler()
    c.show()