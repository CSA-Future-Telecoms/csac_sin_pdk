import gdsfactory as gf
import itertools
from cspdk.sin300.cband import cells
import cspdk.sin300.cband
from cspdk.sin300.cband.config import PATH
import os
from shutil import copyfile
from cspdk.sin300.cband import PDK
from cspdk.sin300.cband.simulation_tools.simulation_settings import target_wl, target_bw

PDK.activate()

from gplugins.lumerical import write_sparameters_lumerical


def gen_lum_sim_inputs(
    cell,
    parameters_swept: dict[str, list],
    every_combo=True,
    sim_type="FDTD",
    layer_builder_settings: dict = {},
    port_buffer: float = 0,
    ymargin_top: float = 2,
    ymargin_bot: float = 2,
    xmargin_left: float = 2,
    xmargin_right: float = 2,
    distance_monitors_to_pml: float = 5,
    sim_center_wavelength : float = target_wl,
    sim_bw : float = target_bw
):
    um = 1e-6
    sweep_name = cell().name + "_".join(parameters_swept.keys())
    lumerical_script = ""
    filename = cell().name
    nl = ";\n"

    if not every_combo:
        # In this case, the values of the parameters should match exactly
        if any(
            len(param_values) != len(list(parameters_swept.values())[0])
            for param_values in parameters_swept.values()
        ):
            raise IndexError(
                "If not using a nested sweep, all parameter values should have the same length.\n"
                + f"Here the lengths were {[len(param_values) for param_values in parameters_swept.values]}"
            )

    if every_combo:
        for parameter_index, (param_name, param_values) in enumerate(
            parameters_swept.items()
        ):
            if parameter_index == 0:
                lumerical_script += "addsweep" + nl
            else:
                lumerical_script += f'insertsweep("{prev_param_name}")' + nl
            lumerical_script += f'setsweep("sweep", "name", "{param_name}")' + nl
            lumerical_script += f'setsweep("{param_name}", "type", "Values")' + nl
            lumerical_script += (
                f'setsweep("{param_name}", "number of points", {len(param_values)});'
                + "\n"
            )
            parameter_setting = "para = struct" + nl
            parameter_setting += f'para.Name = "{param_name}"' + nl
            # parameter_setting += f"para.Parameter = {param_name}" + nl
            parameter_setting += f'para.Type = "Number"' + nl
            for index, value in enumerate(param_values):
                parameter_setting += f"para.Value_{index+1} =  {value}" + nl

            parameter_setting += f'addsweepparameter("{param_name}", para)' + nl
            lumerical_script += parameter_setting
            prev_param_name = param_name

            # Now iterate through each of the sub files. Save them to a subfolder under the correct name, get them to each load the corresponding GDS file.

        keys = parameters_swept.keys()
        combinations = [
            dict(zip(keys, combo))
            for combo in (itertools.product(*parameters_swept.values()))
        ]

        # Also for each file, place a port wherever there is a port in this component
    else:
        pass  # TODO: implement the script for not doing nested loops here

    # Also create the GDSes that are needed:

    with open(
        os.path.join(
            os.path.dirname(__file__), "simulation_inputs", "sweep_builder.lsf"
        ),
        "w",
    ) as lsf:
        print(os.path.dirname(__file__))
        lsf.write(lumerical_script)

    component_sweep_folder_name = filename + "_" + list(parameters_swept.keys())[0]
    sweep_folder_name = os.path.join(
        os.path.dirname(__file__),
        "simulation_inputs",
        filename + "_" + list(parameters_swept.keys())[0],
    )

    master_script = ""
    master_script += f'addpath("{component_sweep_folder_name}")' + nl
    master_script += f"sweep_builder" + nl
    for param_combo in combinations:
        c = cell(**param_combo)
        # Some pre-processing on the cell:
        component_with_padding = gf.add_padding_container(
            c,
            default=0,
            top=ymargin_top,
            bottom=ymargin_bot,
            left=xmargin_left,
            right=xmargin_right,
        )

        component_extended = gf.components.extend_ports(
            component_with_padding, length=distance_monitors_to_pml + max([ymargin_top, ymargin_bot, xmargin_left, xmargin_right])
        )

        if not os.path.isdir(sweep_folder_name):
            os.makedirs(sweep_folder_name)
        sweep_file_name = ""
        for param_name in parameters_swept.keys():
            sweep_file_name += (
                param_name
                + "_"
                + str(parameters_swept[param_name].index(param_combo[param_name]) + 1)
            )
        component_extended.write_gds(
            os.path.join(
                os.path.dirname(__file__),
                sweep_folder_name,
                sweep_file_name + ".gds",
            )
        )
        """The final part is the hardest. We need a LUMERICAL script that will:
        1. Create a lumerical file
        2. Create a layer builder object
        3. Create a simulation region (start with FDTD, then move on to others?)
        4. Import the GDS and use the layer builder 
        A lot of this should be able to use the script that is used by GDSFactory+
        """
        layer_process_file = PATH.sim_tools  / "SiN_layer_builder_v2.lbr"
        copyfile(
            layer_process_file,
            os.path.join(
                os.path.dirname(__file__),
                "simulation_inputs",
                os.path.basename(layer_process_file),
            ),
        )
        generate_layout_script = ""
        generate_layout_script += "newproject" + nl
        generate_layout_script += "addlayerbuilder" + nl
        generate_layout_script += (
            f'loadprocessfile("{os.path.basename(layer_process_file)}")' + nl
        )
        generate_layout_script += f'loadgdsfile("{sweep_file_name + '.gds'}")' + nl
        generate_layout_script += 'select("layer group")' + nl
        generate_layout_script += (
            f'set("gds sidewall angle position reference", "Middle")' + nl
        )
        generate_layout_script += (
            f'set("gds position reference", "Centered at origin")' + nl
        )
        # generate_layout_script += (f'set("x", {component_extended.dbbox().center().x*um})' + nl)
        # generate_layout_script += (f'set("y", {component_extended.dbbox().center().y*um})' + nl)
        generate_layout_script += (f'set("x span", {(2*max([abs(component_extended.dbbox().p1.x), 
                                                           abs(component_extended.dbbox().p2.x)]) + 5)*um})' + nl)
        generate_layout_script += (f'set("y span", {(2*max([abs(component_extended.dbbox().p1.y), 
                                                           abs(component_extended.dbbox().p2.y)]) + 5)*um})' + nl)

        for param, value in layer_builder_settings.items():
            generate_layout_script += f"set({param}, {value})" + nl

        # That's the layer builder setup, now to focus on the actual simulation setup. First introduce a simulation region and ports.
        generate_layout_script += f"add{sim_type.lower()}" + nl
        generate_layout_script += f'set("x min", {(c.dbbox().p1.x - xmargin_left)*um})' + nl
        generate_layout_script += f'set("x max", {(c.dbbox().p2.x + xmargin_right)*um})' + nl
        generate_layout_script += f'set("y min", {(c.dbbox().p1.y - ymargin_bot)*um})' + nl
        generate_layout_script += f'set("y max", {(c.dbbox().p2.y + ymargin_top)*um})' + nl

        # Now for the ports:
        for port in c.ports:
            generate_layout_script += f"addport" + nl
            generate_layout_script += f'set("x", {port.x*um})' + nl
            generate_layout_script += f'set("y", {port.y*um})' + nl
            generate_layout_script += f'set("x span", {2*port.width*um})' + nl
            generate_layout_script += f'set("y span", {2*port.width*um})' + nl
            generate_layout_script += (nl.join(
                    [
                        f"set({port_prop}, {port_value})"
                        for port_prop, port_value in convert_port_angle(
                            port.orientation
                        ).items()
                    ]
                )
                + nl
            )
        generate_layout_script += f'setglobalsource("center wavelength", {sim_center_wavelength*um})' + nl
        generate_layout_script += f'setglobalsource("wavelength span", {sim_bw*um})' + nl
        generate_layout_script += f'save("{sweep_file_name}")' + nl
        with open(
            os.path.join(sweep_folder_name, sweep_file_name + "_generate_layout.lsf"),
            "w",
        ) as gen_layout_file:
            gen_layout_file.write(generate_layout_script)

        # Also include a master script, whose only purpose is to write the underlying scripts

        master_script += f'feval("{sweep_file_name + '_generate_layout.lsf'}")' + nl

    with open(
        os.path.join(
            os.path.dirname(__file__), "simulation_inputs", "master_script.lsf"
        ),
        "w",
    ) as master_file:
        master_file.write(master_script)


def lsf_write_command(command):
    if not isinstance(command, str):
        raise TypeError("Command must be string")
    return command


def convert_port_angle(angle):
    # Normalize angle to [0, 360)
    base_angle = angle % 360

    # Determine Manhattan base and theta
    if base_angle in [0, 90, 180, 270]:
        theta = 0
    else:
        # Find closest Manhattan angle
        manhattan_angles = [0, 90, 180, 270]
        closest = min(manhattan_angles, key=lambda x: abs(base_angle - x))
        theta = round(base_angle - closest)
        base_angle = closest

    # Map base angle to axis and direction
    mapping = {
        0: {'"injection axis"': '"x-axis"', '"direction"': '"Backward"'},
        90: {'"injection axis"': '"y-axis"', '"direction"': '"Forward"'},
        180: {'"injection axis"': '"x-axis"', '"direction"': '"Forward"'},
        270: {'"injection axis"': '"y-axis"', '"direction"': '"Backward"'},
    }

    result = mapping[base_angle]
    result['"theta"'] = theta
    return result


if __name__ == "__main__":
    gen_lum_sim_inputs(gf.partial(cells.coupler, gap = 0.5), parameters_swept={"length" : [20, 40]})

    c = gf.components.bend_circular()
    c.show()