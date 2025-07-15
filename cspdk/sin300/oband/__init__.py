# """sin300 pdk."""

# from functools import lru_cache

# from gdsfactory.config import CONF
# from gdsfactory.cross_section import get_cross_sections
# from gdsfactory.get_factories import get_cells
# from gdsfactory.pdk import Pdk

# from cspdk.sin300.oband import cells, config, tech
# from cspdk.sin300.oband.config import PATH
# from cspdk.sin300.oband.models import get_models
# from cspdk.sin300.oband.tech import LAYER, LAYER_STACK, LAYER_VIEWS, routing_strategies

# _models = get_models()
# _cells = get_cells(cells)
# _cross_sections = get_cross_sections(tech)

# CONF.pdk = "cspdk.sin300.oband"
# CONF.max_cellname_length = 100 

# @lru_cache
# def get_pdk() -> Pdk:
#     """Return CSAC PDK."""
#     return Pdk(
#         name="cspdk.sin300.oband",
#         cells=_cells,
#         cross_sections=_cross_sections,  # type: ignore
#         layers=LAYER,
#         layer_stack=LAYER_STACK,
#         layer_views=LAYER_VIEWS,
#         models=_models,
#         routing_strategies=routing_strategies,
#     )


# def activate_pdk() -> None:
#     """Activate CSAC SiN PDK."""
#     pdk = get_pdk()
#     pdk.activate()


# PDK = get_pdk()

# __all__ = [
#     "LAYER",
#     "LAYER_STACK",
#     "LAYER_VIEWS",
#     "PATH",
#     "cells",
#     "config",
#     "tech",
# ]
