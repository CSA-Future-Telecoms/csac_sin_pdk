"""Ring Resonators."""

import gdsfactory as gf
from gdsfactory.typings import CrossSectionSpec

from cspdk.sin300.cband.tech import TECH


@gf.cell
def csac_euler(
    radius: float = 80.0,
    angle: float = 90.0,
    p: float = 1.0,
    cross_section: CrossSectionSpec = "strip",

) -> gf.Component:
    """Returns a single ring.

    ring coupler (cb: bottom) connects to two vertical straights (sl: left, sr: right),
    two bends (bl, br) and horizontal straight (wg: top)

    Args:
        gap: gap between for coupler.
        radius: for the bend and coupler.
        length_x: ring coupler length.
        length_y: vertical straight length.
        coupler_ring: ring coupler spec.
        bend: 90 degrees bend spec.
        straight: straight spec.
        coupler_ring: ring coupler spec.
        cross_section: cross_section spec.

    .. code::

                    xxxxxxxxxxxxx
                xxxxx           xxxx
              xxx                   xxx
            xxx                       xxx
           xx                           xxx
           x                             xxx
          xx                              xx▲
          xx                              xx│length_y
          xx                              xx▼
          xx                             xx
           xx          length_x          x
            xx     ◄───────────────►    x
             xx                       xxx
               xx                   xxx
                xxx──────▲─────────xxx
                         │gap
                 o1──────▼─────────o2
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