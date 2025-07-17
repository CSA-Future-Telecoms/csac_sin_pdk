from pathlib import Path
from functools import partial
import gdsfactory as gf

add_ports_optical = partial(
    gf.add_ports.add_ports_from_markers_inside, pin_layer=(1, 0), port_layer=(2, 0)
)
add_ports_electrical = partial(
    gf.add_ports.add_ports_from_markers_inside, pin_layer=(41, 0), port_layer=(1, 0)
)
def add_ports(component):
    add_ports_optical(component)
    add_ports_electrical(component)
    return component




gdsdir = Path(__file__).parent.parent / "gds"

import_gds = gf.import_gds



@gf.cell
def SiN300nm_1310nm_TE_STRIP_2x1_MMI()->gf.Component:
    '''Returns SiN300nm_1310nm_TE_STRIP_2x1_MMI fixed cell.

    .. plot::
      :include-source:

      import cspdk

      c = cspdk.sin300.oband.cells.SiN300nm_1310nm_TE_STRIP_2x1_MMI()
      c.plot()
    '''
    def add_ports(cell):
      cell.add_port(name = "o1", center = (-51, 0), width = 0.95, orientation=180, cross_section="strip" )
      cell.add_port(name = "o2", center = (51, 2), width = 0.95, orientation=0, cross_section="strip" )
      cell.add_port(name = "o3", center = (51, -2), width = 0.95, orientation=0, cross_section="strip" )
    return import_gds(gdspath = gdsdir/'SiN300nm_1310nm_TE_STRIP_2x1_MMI.gds', post_process=[add_ports])




@gf.cell
def SiN300nm_1310nm_TE_STRIP_2x2_MMI()->gf.Component:
    '''Returns SiN300nm_1310nm_TE_STRIP_2x2_MMI fixed cell.

    .. plot::
      :include-source:

      import cspdk

      c = cspdk.sin300.oband.cells.SiN300nm_1310nm_TE_STRIP_2x2_MMI()
      c.plot()
    '''
    def add_ports(c):
      c.add_port(name = "o1", center = (-93, -2.1), width = 0.95, orientation=180, cross_section="strip" )
      c.add_port(name = "o2", center = (-93, 2.1), width = 0.95, orientation=180, cross_section="strip" )
      c.add_port(name = "o3", center = (93, 2.1), width = 0.95, orientation=0, cross_section="strip" )
      c.add_port(name = "o4", center = (93, -2.1), width = 0.95, orientation=0, cross_section="strip" )
    return import_gds(gdsdir/'SiN300nm_1310nm_TE_STRIP_2x2_MMI.gds', post_process=[add_ports])




@gf.cell
def SiN300nm_1310nm_TE_STRIP_90_Degree_bend()->gf.Component:
    '''Returns SiN300nm_1310nm_TE_STRIP_90_Degr fixed cell.

    .. plot::
      :include-source:

      import cspdk

      c = cspdk.sin300.oband.cells.SiN300nm_1310nm_TE_STRIP_90_Degree_bend()
      c.plot()
    '''
    def add_ports(c): 
      c.add_port(name = "o1", center = (-60, 0), width = 0.95, orientation=270, cross_section="strip" )
      c.add_port(name = "o2", center = (0,  60), width = 0.95, orientation=0, cross_section="strip" )
    return import_gds(gdsdir/'SiN300nm_1310nm_TE_STRIP_90_Degree_bend.gds', post_process=[add_ports])



@gf.cell
def SiN300nm_1310nm_TE_STRIP_Grating()->gf.Component:
    '''Returns SiN300nm_1310nm_TE_STRIP_Grating fixed cell.

    .. plot::
      :include-source:

      import cspdk

      c = cspdk.sin300.oband.cells.SiN300nm_1310nm_TE_STRIP_Grating()
      c.plot()
    '''
    def add_ports(c):
        c.add_port(name = "fibre_in", center = (-225, 0), orientation = 0, width = 10, layer = gf.get_active_pdk().get_layer("OPT_IO"))
        c.add_port(name = "o1", center = (0,0), orientation = 0, width = 0.95, cross_section = "strip")
    return import_gds(gdsdir/'SiN300nm_1310nm_TE_STRIP_Grating.gds', post_process=[add_ports])





@gf.cell
def SiN300nm_1310nm_TE_STRIP_Waveguide()->gf.Component:
    '''Returns SiN300nm_1310nm_TE_STRIP_Wavegui fixed cell.

    .. plot::
      :include-source:

      import cspdk

      c = cspdk.sin300.oband.cells.SiN300nm_1310nm_TE_STRIP_Waveguide()
      c.plot()
    '''
    def add_ports(c):
        c.add_port(name = "o1", center = (-220, 0), orientation = 180, width = 0.95, cross_section = "strip")
        c.add_port(name = "o2", center = (220, 0), orientation = 0, width = 0.95, cross_section = "strip")
    return import_gds(gdsdir/'SiN300nm_1310nm_TE_STRIP_Waveguide.gds', post_process = [add_ports])