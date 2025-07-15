import pathlib
import time
from collections.abc import Awaitable
from functools import cached_property
from typing import Any, Literal
import gdsfactory as gf

import matplotlib.pyplot as plt
import numpy as np
import tidy3d as td
import gplugins.tidy3d as gft3d
from gdsfactory.component import Component
from gdsfactory.pdk import get_layer_stack
from gdsfactory.technology import LayerStack
from pydantic import NonNegativeFloat
from tidy3d.components.geometry.base import from_shapely
from tidy3d.components.types import Symmetry
from tidy3d.plugins.smatrix import ComponentModeler, Port
import pydantic

from gplugins.common.base_models.component import LayeredComponentBase
from gplugins.tidy3d.get_results import _executor
from gplugins.tidy3d.types import (
    Sparameters,
    Tidy3DElementMapping,
    Tidy3DMedium,
)
from gplugins.tidy3d.materials import MaterialSpecTidy3d, get_medium
from collections.abc import Sequence
from gplugins.tidy3d.util import get_mode_solvers, get_port_normal, sort_layers
from tidy3d.web.api.webapi import upload

PathType = pathlib.Path | str

home = pathlib.Path.home()
dirpath_default = home / ".gdsfactory" / "sparameters"

material_name_to_medium = {
    "si": td.Medium(name="Si", permittivity=3.47**2),
    "sio2": td.Medium(name="SiO2", permittivity=1.47**2),
    "sin": td.Medium(name="SiN", permittivity=2.0**2),
}

def CSAC_t3d_write_params(
    component: Component,
    layer_stack: LayerStack | None = None,
    material_mapping: dict[str, Tidy3DMedium] = material_name_to_medium,
    extend_ports: NonNegativeFloat = 0.5,
    port_offset: float = 0.2,
    pad_xy_inner: NonNegativeFloat = 2.0,
    pad_xy_outer: NonNegativeFloat = 2.0,
    pad_z_inner: float = 0.0,
    pad_z_outer: NonNegativeFloat = 0.0,
    dilation: float = 0.0,
    wavelength: float = 1.55,
    bandwidth: float = 0.2,
    num_freqs: int = 21,
    min_steps_per_wvl: int = 30,
    center_z: float | str | None = None,
    sim_size_z: float = 4.0,
    port_size_mult: float | tuple[float, float] = (4.0, 3.0),
    run_only: tuple[tuple[str, int], ...] | None = None,
    element_mappings: Tidy3DElementMapping = (),
    extra_monitors: tuple[Any, ...] | None = None,
    mode_spec: td.ModeSpec = td.ModeSpec(num_modes=1, filter_pol="te"),
    boundary_spec: td.BoundarySpec = td.BoundarySpec.all_sides(boundary=td.PML()),
    symmetry: tuple[Symmetry, Symmetry, Symmetry] = (0, 0, 0),
    run_time: float = 1e-12,
    run : bool = False,
    shutoff: float = 1e-5,
    folder_name: str = "default",
    dirpath: PathType = dirpath_default,
    verbose: bool = True,
    plot_simulation_layer_name: str | None = None,
    plot_simulation_port_index: int = 0,
    plot_simulation_z: float | None = None,
    plot_simulation_x: float | None = None,
    plot_mode_index: int | None = 0,
    plot_mode_port_name: str | None = None,
    plot_epsilon: bool = False,
    filepath: PathType | None = None,
    overwrite: bool = False,
    **kwargs: Any,
) -> Sparameters:
    """Writes the S-parameters for a component.

    Args:
        component: gdsfactory component to write the S-parameters for.
        layer_stack: The layer stack for the component. If None, uses active pdk layer_stack.
        material_mapping: A mapping of material names to Tidy3DMedium instances. Defaults to material_name_to_medium.
        extend_ports: The extension length for ports.
        port_offset: The offset for ports. Defaults to 0.2.
        pad_xy_inner: The inner padding in the xy-plane. Defaults to 2.0.
        pad_xy_outer: The outer padding in the xy-plane. Defaults to 2.0.
        pad_z_inner: The inner padding in the z-direction. Defaults to 0.0.
        pad_z_outer: The outer padding in the z-direction. Defaults to 0.0.
        dilation: Dilation of the polygon in the base by shifting each edge along its normal outwards direction by a distance;
        wavelength: The wavelength for the ComponentModeler. Defaults to 1.55.
        bandwidth: The bandwidth for the ComponentModeler. Defaults to 0.2.
        num_freqs: The number of frequencies for the ComponentModeler. Defaults to 21.
        min_steps_per_wvl: The minimum number of steps per wavelength for the ComponentModeler. Defaults to 30.
        center_z: The z-coordinate for the center of the ComponentModeler.
            If None, the z-coordinate of the component is used. Defaults to None.
        sim_size_z: simulation size um in the z-direction for the ComponentModeler. Defaults to 4.
        port_size_mult: The size multiplier for the ports in the ComponentModeler. Defaults to (4.0, 3.0).
        run_only: The run only specification for the ComponentModeler. Defaults to None.
        element_mappings: The element mappings for the ComponentModeler. Defaults to ().
        extra_monitors: The extra monitors for the ComponentModeler. Defaults to None.
        mode_spec: The mode specification for the ComponentModeler. Defaults to td.ModeSpec(num_modes=1, filter_pol="te").
        boundary_spec: The boundary specification for the ComponentModeler.
            Defaults to td.BoundarySpec.all_sides(boundary=td.PML()).
        symmetry (tuple[Symmetry, Symmetry, Symmetry], optional): The symmetry for the simulation. Defaults to (0,0,0).
        run_time: The run time for the ComponentModeler.
        shutoff: The shutoff value for the ComponentModeler. Defaults to 1e-5.
        folder_name: The folder name for the ComponentModeler in flexcompute website. Defaults to "default".
        dirpath: Optional directory path for writing the Sparameters. Defaults to "~/.gdsfactory/sparameters".
        verbose: Whether to print verbose output for the ComponentModeler. Defaults to True.
        plot_simulation_layer_name: Optional layer name to plot. Defaults to None.
        plot_simulation_port_index: which port index to plot. Defaults to 0.
        plot_simulation_z: which z coordinate to plot. Defaults to None.
        plot_simulation_x: which x coordinate to plot. Defaults to None.
        plot_mode_index: which mode index to plot. Defaults to 0.
        plot_mode_port_name: which port name to plot. Defaults to None.
        plot_epsilon: whether to plot epsilon. Defaults to False.
        filepath: Optional file path for the S-parameters. If None, uses hash of simulation.
        overwrite: Whether to overwrite existing S-parameters. Defaults to False.
        kwargs: Additional keyword arguments for the tidy3d Simulation constructor.

    """
    layer_stack = layer_stack or get_layer_stack()

    c = gft3d.Tidy3DComponent(
        component=component,
        layer_stack=layer_stack,
        material_mapping=material_mapping,
        extend_ports=extend_ports,
        port_offset=port_offset,
        pad_xy_inner=pad_xy_inner,
        pad_xy_outer=pad_xy_outer,
        pad_z_inner=pad_z_inner,
        pad_z_outer=pad_z_outer,
        dilation=dilation,
    )

    modeler = c.get_component_modeler(
        wavelength=wavelength,
        bandwidth=bandwidth,
        num_freqs=num_freqs,
        min_steps_per_wvl=min_steps_per_wvl,
        center_z=center_z,
        sim_size_z=sim_size_z,
        port_size_mult=port_size_mult,
        run_only=run_only,
        element_mappings=element_mappings,
        extra_monitors=extra_monitors,
        mode_spec=mode_spec,
        boundary_spec=boundary_spec,
        run_time=run_time,
        shutoff=shutoff,
        folder_name=folder_name,
        verbose=verbose,
        symmetry=symmetry,
        **kwargs,
    )

    path_dir = pathlib.Path(dirpath) / modeler._hash_self()
    modeler = modeler.updated_copy(path_dir=str(path_dir))

    sp = {}

    if plot_simulation_layer_name or plot_simulation_z or plot_simulation_x:
        if plot_simulation_layer_name is None and plot_simulation_z is None:
            raise ValueError(
                "You need to specify plot_simulation_z or plot_simulation_layer_name"
            )
        z = plot_simulation_z or c.get_layer_center(plot_simulation_layer_name)[2]
        x = plot_simulation_x or c.ports[plot_simulation_port_index].dcenter[0]

        modeler = c.get_component_modeler(
            center_z=plot_simulation_layer_name,
            port_size_mult=port_size_mult,
            sim_size_z=sim_size_z,
        )
        _, ax = plt.subplots(2, 1)
        if plot_epsilon:
            modeler.plot_sim_eps(z=z, ax=ax[0])
            modeler.plot_sim_eps(x=x, ax=ax[1])

        else:
            modeler.plot_sim(z=z, ax=ax[0])
            modeler.plot_sim(x=x, ax=ax[1])
        plt.show()
        return sp

    elif plot_mode_index is not None and plot_mode_port_name:
        modes = get_mode_solvers(modeler, port_name=plot_mode_port_name)
        mode_solver = modes[f"smatrix_{plot_mode_port_name}_{plot_mode_index}"]
        mode_data = mode_solver.solve()

        _, ax = plt.subplots(1, 3, tight_layout=True, figsize=(10, 3))
        abs(mode_data.Ex.isel(mode_index=plot_mode_index, f=0)).plot(
            x="y", y="z", ax=ax[0], cmap="magma"
        )
        abs(mode_data.Ey.isel(mode_index=plot_mode_index, f=0)).plot(
            x="y", y="z", ax=ax[1], cmap="magma"
        )
        abs(mode_data.Ez.isel(mode_index=plot_mode_index, f=0)).plot(
            x="y", y="z", ax=ax[2], cmap="magma"
        )
        ax[0].set_title("|Ex(x, y)|")
        ax[1].set_title("|Ey(x, y)|")
        ax[2].set_title("|Ez(x, y)|")
        plt.setp(ax, aspect="equal")
        plt.show()
        return sp

    dirpath = pathlib.Path(dirpath)
    dirpath.mkdir(parents=True, exist_ok=True)
    filepath = filepath or dirpath / f"{modeler._hash_self()}.npz"
    filepath = pathlib.Path(filepath)
    if filepath.suffix != ".npz":
        filepath = filepath.with_suffix(".npz")

    if filepath.exists() and not overwrite:
        print(f"Simulation loaded from {filepath!r}")
        return dict(np.load(filepath))
    else:
        time.sleep(0.2)
        if run: 
            s = modeler.run()
            for port_in in s.port_in.values:
                for port_out in s.port_out.values:
                    for mode_index_in in s.mode_index_in.values:
                        for mode_index_out in s.mode_index_out.values:
                            sp[f"{port_in}@{mode_index_in},{port_out}@{mode_index_out}"] = (
                                s.sel(
                                    port_in=port_in,
                                    port_out=port_out,
                                    mode_index_in=mode_index_in,
                                    mode_index_out=mode_index_out,
                                ).values
                            )

            frequency = s.f.values
            sp["wavelengths"] = td.constants.C_0 / frequency
            np.savez_compressed(filepath, **sp)
            print(f"Simulation saved to {filepath!r}")
            return sp
        else: ## Don't run: instead save the created simulation
            for key, value in modeler.sim_dict.items():
                upload(value, folder_name = folder_name, task_name = key)
            return
        

# class Waveguide(BaseModel, extra="forbid"):
#     """Waveguide Model.

#     All dimensions must be specified in μm (1e-6 m).

#     Parameters:
#         wavelength: wavelength in free space.
#         core_width: waveguide core width.
#         core_thickness: waveguide core thickness (height).
#         core_material: core material. One of:
#             - string: material name.
#             - float: refractive index.
#             - float, float: refractive index real and imaginary part.
#             - td.Medium: tidy3d medium.
#             - function: function of wavelength.
#         clad_material: top cladding material.
#         box_material: bottom cladding material.
#         slab_thickness: thickness of the slab region in a rib waveguide.
#         clad_thickness: thickness of the top cladding.
#         box_thickness: thickness of the bottom cladding.
#         side_margin: domain extension to the side of the waveguide core.
#         sidewall_angle: angle of the core sidewall w.r.t. the substrate
#             normal.
#         sidewall_thickness: thickness of a layer on the sides of the
#             waveguide core to model side-surface losses.
#         sidewall_k: absorption coefficient added to the core material
#             index on the side-surface layer.
#         surface_thickness: thickness of a layer on the top of the
#             waveguide core and slabs to model top-surface losses.
#         surface_k: absorption coefficient added to the core material
#             index on the top-surface layer.
#         bend_radius: radius to simulate circular bend.
#         num_modes: number of modes to compute.
#         group_index_step: if set to `True`, indicates that the group
#             index must also be calculated. If set to a positive float
#             it defines the fractional frequency step used for the
#             numerical differentiation of the effective index.
#         precision: computation precision.
#         grid_resolution: wavelength resolution of the computation grid.
#         max_grid_scaling: grid scaling factor in cladding regions.
#         cache_path: Optional path to the cache directory. None disables cache.
#         overwrite: overwrite cache.

#     ::

#         ________________________________________________
#                                                 ^
#                                                 ¦
#                                                 ¦
#                                           clad_thickness
#                        |<--core_width-->|       ¦
#                                                 ¦
#                        .________________.      _v_
#                        |       ^        |
#         <-side_margin->|       ¦        |
#                        |       ¦        |
#         _______________'       ¦        '_______________
#               ^          core_thickness
#               ¦                ¦
#         slab_thickness         ¦
#               ¦                ¦
#               v                v
#         ________________________________________________
#                                ^
#                                ¦
#                          box_thickness
#                                ¦
#                                v
#         ________________________________________________
#     """

#     wavelength: float | Sequence[float] | Any
#     layer_sections: list(gf.Section)
#     layer_mapping: dict(MaterialSpecTidy3d)
#     slab_thickness: float = 0.0
#     clad_thickness: float | None = None
#     box_thickness: float | None = None
#     side_margin: float | None = None
#     sidewall_angle: float = 0.0
#     sidewall_thickness: float = 0.0
#     sidewall_k: float = 0.0
#     surface_thickness: float = 0.0
#     surface_k: float = 0.0
#     bend_radius: float | None = None
#     num_modes: int = 2
#     group_index_step: bool | float = False
#     precision: Precision = "double"
#     grid_resolution: int = 20
#     max_grid_scaling: float = 1.2
#     cache_path: PathType | None = PATH.modes
#     overwrite: bool = False

#     _cached_data = pydantic.PrivateAttr()
#     _waveguide = pydantic.PrivateAttr()

#     @pydantic.validator("wavelength")
#     def _fix_wavelength_type(cls, v: Any) -> NDArrayF:
#         return np.array(v, dtype=float)

#     @property
#     def filepath(self) -> pathlib.Path | None:
#         """Cache file path."""
#         if not self.cache_path:
#             return None
#         cache_path = pathlib.Path(self.cache_path)
#         cache_path.mkdir(exist_ok=True, parents=True)

#         settings = [
#             f"{setting}={custom_serializer(getattr(self, setting))}"
#             for setting in sorted(self.__fields__.keys())
#         ]
#         named_args_string = "_".join(settings)
#         h = hashlib.md5(named_args_string.encode()).hexdigest()[:16]
#         return cache_path / f"{self.__class__.__name__}_{h}.npz"

#     @property
#     def waveguide(self):
#         """Tidy3D waveguide used by this instance."""
#         # if (not hasattr(self, "_waveguide")
#         #         or isinstance(self.core_material, td.CustomMedium)):
#         if not hasattr(self, "_waveguide"):
#             # To include a dn -> custom medium
#             if isinstance(self.core_material, td.CustomMedium | td.Medium):
#                 core_medium = self.core_material
#             else:
#                 core_medium = get_medium(self.core_material)

#             if isinstance(self.clad_material, td.CustomMedium | td.Medium):
#                 clad_medium = self.clad_material
#             else:
#                 clad_medium = get_medium(self.clad_material)

#             if self.box_material:
#                 if isinstance(self.box_material, td.CustomMedium | td.Medium):
#                     box_medium = self.box_material
#                 else:
#                     box_medium = get_medium(self.box_material)
#             else:
#                 box_medium = None

#             freq0 = td.C_0 / np.mean(self.wavelength)
#             n_core = core_medium.eps_model(freq0) ** 0.5
#             n_clad = clad_medium.eps_model(freq0) ** 0.5

#             sidewall_medium = (
#                 td.Medium.from_nk(
#                     n=n_clad.real, k=n_clad.imag + self.sidewall_k, freq=freq0
#                 )
#                 if self.sidewall_k != 0.0
#                 else None
#             )
#             surface_medium = (
#                 td.Medium.from_nk(
#                     n=n_clad.real, k=n_clad.imag + self.surface_k, freq=freq0
#                 )
#                 if self.surface_k != 0.0
#                 else None
#             )

#             mode_spec = td.ModeSpec(
#                 num_modes=self.num_modes,
#                 target_neff=n_core.real,
#                 bend_radius=self.bend_radius,
#                 bend_axis=1,
#                 num_pml=(12, 12) if self.bend_radius else (0, 0),
#                 precision=self.precision,
#                 group_index_step=self.group_index_step,
#             )

#             self._waveguide = waveguide.RectangularDielectric(
#                 wavelength=self.wavelength,
#                 core_width=self.core_width,
#                 core_thickness=self.core_thickness,
#                 core_medium=core_medium,
#                 clad_medium=clad_medium,
#                 box_medium=box_medium,
#                 slab_thickness=self.slab_thickness,
#                 clad_thickness=self.clad_thickness,
#                 box_thickness=self.box_thickness,
#                 side_margin=self.side_margin,
#                 sidewall_angle=self.sidewall_angle,
#                 sidewall_thickness=self.sidewall_thickness,
#                 sidewall_medium=sidewall_medium,
#                 surface_thickness=self.surface_thickness,
#                 surface_medium=surface_medium,
#                 propagation_axis=2,
#                 normal_axis=1,
#                 mode_spec=mode_spec,
#                 grid_resolution=self.grid_resolution,
#                 max_grid_scaling=self.max_grid_scaling,
#             )

#         return self._waveguide