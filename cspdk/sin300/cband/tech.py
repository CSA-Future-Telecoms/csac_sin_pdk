"""Technology definitions."""

from collections.abc import Callable
from functools import partial, wraps
from typing import Any
from gdsfactory.technology import lyp_to_dataclass

import gdsfactory as gf
from doroutes.bundles import add_bundle_astar
from gdsfactory.cross_section import (
    CrossSection,
    cross_section,
    port_names_electrical,
    port_types_electrical,
)
from gdsfactory.technology import (
    LayerLevel,
    LayerMap,
    LayerStack,
    LayerViews,
    LogicalLayer,
)
from gdsfactory.typings import (
    ConnectivitySpec,
    Floats,
    Layer,
    LayerSpec,
    LayerSpecs,
)

from cspdk.sin300.cband.config import PATH

nm = 1e-3


class LayerMapFab(LayerMap):
    ETCH: Layer = (204, 0)
    HEATER: Layer = (39, 0)
    MTL_KPOUT: Layer = (2, 10)
    OPT_IO: Layer = (1, 10)
    PAD: Layer = (41, 0)
    QD: Layer = (50, 0)
    WG: Layer = (203, 0)
    floorplan: Layer = (99, 0)
    labels: Layer = (100, 0)
    oxide_window: Layer = (22, 0)


LAYER = LayerMapFab
# exec(LayerMapCSAC_SiN)

def get_layer_stack(
    thickness_wg: float = 220 * nm,
    thickness_slab: float = 100 * nm,
    zmin_heater: float = 1.1,
    thickness_heater: float = 700 * nm,
    zmin_metal: float = 1.1,
    thickness_metal: float = 700 * nm,
) -> LayerStack:
    """Returns LayerStack.

    based on paper https://www.degruyter.com/document/doi/10.1515/nanoph-2013-0034/html

    Args:
        thickness_wg: waveguide thickness in um.
        thickness_slab: slab thickness in um.
        zmin_heater: TiN heater.
        thickness_heater: TiN thickness.
        zmin_metal: metal thickness in um.
        thickness_metal: top metal thickness.
    """
    return LayerStack(
        layers=dict(
            core=LayerLevel(
                layer=LogicalLayer(layer=LAYER.WG),
                thickness=thickness_wg,
                zmin=0.0,
                material="sin",
                info={"mesh_order": 1},
                sidewall_angle=10,
                width_to_z=0.5,
            ),
            heater=LayerLevel(
                layer=LogicalLayer(layer=LAYER.HEATER),
                thickness=thickness_heater,
                zmin=zmin_heater,
                material="TiN",
                info={"mesh_order": 1},
            ),
            metal=LayerLevel(
                layer=LogicalLayer(layer=LAYER.PAD),
                thickness=thickness_metal,
                zmin=zmin_metal + thickness_metal,
                material="Aluminum",
                info={"mesh_order": 2},
            ),
        )
    )


LAYER_STACK = get_layer_stack()
LAYER_VIEWS = gf.technology.LayerViews(PATH.lyp)
LAYER_VIEWS.to_yaml(PATH.lyp_yaml)

class Tech:
    """Technology parameters."""
    radius = 30
    radius_strip = 30
    radius_ro = 25
    width = 1.2
    width_ro = 0.5

    width_heater = 2.5
    width_metal = 10

    gap_strip = 0.27


TECH = Tech()

############################
# Cross-sections functions
############################

cross_sections: dict[str, Callable[..., CrossSection]] = {}
_cross_section_default_names: dict[str, str] = {}


def xsection(func: Callable[..., CrossSection]) -> Callable[..., CrossSection]:
    """Returns decorated to register a cross section function.

    Ensures that the cross-section name matches the name of the function that generated it when created using default parameters

    .. code-block:: python

        @xsection
        def strip(width=TECH.width_strip, radius=TECH.radius_strip):
            return gf.cross_section.cross_section(width=width, radius=radius)
    """
    default_xs = func()
    _cross_section_default_names[default_xs.name] = func.__name__

    @wraps(func)
    def newfunc(**kwargs: Any) -> CrossSection:
        xs = func(**kwargs)
        if xs.name in _cross_section_default_names:
            xs._name = _cross_section_default_names[xs.name]
        return xs

    cross_sections[func.__name__] = newfunc
    return newfunc


@xsection
def strip(
    width: float = TECH.width,
    layer: LayerSpec = "WG",
    radius: float = TECH.radius,
    radius_min: float = TECH.radius,
) -> CrossSection:
    """Return Strip cross_section."""
    return gf.cross_section.cross_section(
        width=width,
        layer=layer,
        radius=radius,
        radius_min=radius_min,
    )


@xsection
def strip_heater_metal(
    width: float = TECH.width,
    layer: LayerSpec = "WG",
    heater_width: float = TECH.width_heater,
    layer_heater: LayerSpec = "HEATER",
) -> CrossSection:
    """Returns strip cross_section with top heater metal."""
    return gf.cross_section.strip_heater_metal(
        width=width,
        layer=layer,
        heater_width=heater_width,
        layer_heater=layer_heater,
    )


@xsection
def metal_routing(
    width: float = 10,
    layer: LayerSpec = "PAD",
    radius: float | None = None,
) -> CrossSection:
    """Return Metal Strip cross_section."""
    return cross_section(
        width=width,
        layer=layer,
        radius=radius,
        port_names=port_names_electrical,
        port_types=port_types_electrical,
    )


@xsection
def heater_metal(width=TECH.width_heater) -> CrossSection:
    """Heater cross-section."""
    return gf.cross_section.heater_metal(width=width, layer=LAYER.HEATER)


############################
# Routing functions
############################

route_single = partial(gf.routing.route_single, cross_section="strip")
route_bundle = partial(gf.routing.route_bundle, cross_section="strip")


route_bundle_metal = partial(
    route_bundle,
    straight="straight_metal",
    bend="bend_metal",
    taper=None,
    cross_section="metal_routing",
    port_type="electrical",
)
route_bundle_metal_corner = partial(
    route_bundle,
    straight="straight_metal",
    bend="wire_corner",
    taper=None,
    cross_section="metal_routing",
    port_type="electrical",
)

route_astar = partial(
    add_bundle_astar,
    layers=["WG"],
    bend="bend_euler",
    straight="straight",
    grid_unit=500,
    spacing=3,
)

route_astar_metal = partial(
    add_bundle_astar,
    layers=["PAD"],
    bend="wire_corner",
    straight="straight_metal",
    grid_unit=500,
    spacing=15,
)


routing_strategies = dict(
    route_bundle=route_bundle,
    route_bundle_metal=route_bundle_metal,
    route_bundle_metal_corner=route_bundle_metal_corner,
    route_astar=route_astar,
    route_astar_metal=route_astar_metal,
)

if __name__ == "__main__":
    from typing import cast

    from gdsfactory.technology.klayout_tech import KLayoutTechnology

    LAYER_VIEWS = LayerViews(PATH.lyp_yaml)
    # LAYER_VIEWS.to_lyp(PATH.lyp)

    connectivity = cast(list[ConnectivitySpec], [("HEATER", "HEATER", "PAD")])

    t = KLayoutTechnology(
        name="CSAC",
        layer_map=LAYER,
        layer_views=LAYER_VIEWS,
        layer_stack=LAYER_STACK,
        connectivity=connectivity,
    )
    t.write_tech(tech_dir=PATH.klayout)
    # print(DEFAULT_CROSS_SECTION_NAMES)
    # print(strip() is strip())
    # print(strip().name, strip().name)
    # c = gf.c.bend_euler(cross_section="metal_routing")
    # c.pprint_ports()
