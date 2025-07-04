import cspdk.sin300.cband.cells as cells
from simulation_settings import material_data as mapping
import gplugins.tidy3d as gt
import tkinter as tk
from tkinter import ttk
import inspect
from cspdk.sin300.cband.tech import LAYER_STACK
import tidy3d as td
import gdsfactory as gf
from tidy3d.web.api.webapi import upload
from matplotlib import pyplot as plt
### Make a GUI that allows you to select a component and then simulate it directly, 
# setup the tidy3d component


class tidy3D_simulation_interface():
    def __init__(self, options):
        self.options = options

        self.root = tk.Tk()
        self.root.title("Function Selector")
        self.root.geometry("300x450")

        self._build_gui()

    def _build_gui(self):
        # Label
        label = ttk.Label(self.root, text="Select an Cell:")
        label.pack(pady=10)

        # Dropdown
        self.combo = ttk.Combobox(self.root, values=self.options, state="readonly")
        self.combo.pack()
        ## For each parameter, add the parameter here:
    

        # Button
        submit_btn = ttk.Button(self.root, text="Choose", command=self._on_choice)
        submit_btn.pack(pady=10)



    def _on_choice(self):
        print("DEBUG ON CHOICE")
        self.comp_selection = self.combo.get()
        if not self.comp_selection: 
            print("No selection made")
            return
        if hasattr(self, "secondary_frame"):
            print("Secondary frame exists")
            self.secondary_frame.destroy()
        print("Generating 2nd frame...")
        # Create new frame for parameter inputs
        self.secondary_frame = ttk.Frame(self.root)
        self.secondary_frame.pack(pady=10)

        param_label = ttk.Label(self.secondary_frame, text="Enter parameters:")
        param_label.grid(row=0, column=0, columnspan=2)
        print("Generated second frame")

        # Example static parameters — could be dynamic per function
        try:
            param_names = gf.get_active_pdk().get_component(self.comp_selection).settings.model_dump().keys()
            self.entries = {}   
        except:
            raise LookupError("Failed to find component")         
        comp = gf.get_active_pdk().get_cell(self.comp_selection)
        signature = inspect.signature(comp)
        defaults = {
            k: v.default
            for k, v in signature.parameters.items()
            if v.default is not inspect.Parameter.empty
        }

        for i, param in enumerate(param_names, start=1):
            label = ttk.Label(self.secondary_frame, text=param + ":")
            label.grid(row=i, column=0, padx=5, pady=3, sticky='e')
            entry = ttk.Entry(self.secondary_frame)
            entry.grid(row=i, column=1, padx=5, pady=3)
            default_val = defaults.get(param, "")
            entry.insert(0, str(default_val))
            self.entries[param] = entry
        

        submit_btn = ttk.Button(self.secondary_frame, text="Submit", command=lambda: self._on_submit(self.comp_selection))
        submit_btn.grid(row=len(param_names)+1, column=0, columnspan=2, pady=10)
        


    def _on_submit(self, selection_name):

        # 2. Collect parameters from entry widgets
        raw_params = {k: v.get() for k, v in self.entries.items()}


        # 3. Build component
        comp = gf.get_active_pdk().get_cell(selection_name)

        def parse_param(value):
                if ',' in value:
                    try:
                        return [float(x) if '.' in x else int(x) for x in value.split(',')]
                    except:
                        return [x.strip() for x in value.split(',')]
                else:
                    try:
                        return float(value) if '.' in value else int(value)
                    except:
                        return value.strip()

        raw_params = {k: parse_param(v.get()) for k, v in self.entries.items()}
        sweep_params = {k: v for k, v in raw_params.items() if isinstance(v, list)}
        scalar_params = {k: v for k, v in raw_params.items() if not isinstance(v, list)}

        if sweep_params:
            lengths = [len(v) for v in sweep_params.values()]
            if len(set(lengths)) != 1:
                print("[ERROR] All array parameters must have the same length!")
                return
            sweep_len = lengths[0]
        else:
            sweep_len = 1

        for i in range(sweep_len):
            param_set = {k: v[i] for k, v in sweep_params.items()}
            param_set.update(scalar_params)
            print(f"[INFO] Running simulation {i+1}/{sweep_len}: {param_set}")
            try:
                component = comp(**param_set)
            except Exception as e:
                print(f"[ERROR] Failed to build component: {e}")
                continue


 

        # 4. Run your Tidy3D stuff
        c = gt.Tidy3DComponent(
            component=component,
            layer_stack=LAYER_STACK,
            material_mapping=mapping,
            pad_xy_inner=2.0,
            pad_xy_outer=2.0,
            pad_z_inner=0,
            pad_z_outer=0,
            extend_ports=2.0,
        )

        self.plot(c)

        modeler = c.get_component_modeler(
            center_z="core", port_size_mult=(6, 4), sim_size_z=3.0
        )
        save_name = selection_name + "_" + "_".join([f"{k[:3]}={v}" for k, v in param_set.items()])
        save_name = save_name[:96]
        print(dir(LAYER_STACK.layers))
        # thicknesses = LAYER_STACK.get_layer_to_thickness()
        # print(dir_thicknes)
        upload(c.get_simulation(grid_spec=td.GridSpec.auto(wavelength=1.55e-6, min_steps_per_wvl=30), 
                                center_z = LAYER_STACK.layers["core"].thickness/2, 
                                sim_size_z = 2e-6, 
                                boundary_spec = td.BoundarySpec.pml(x=True, y=True, z=True)), 
                task_name = save_name, 
                folder_name = self.comp_selection)  


        ## TODO: Save name is not working properly
        ## Background medium is not being submitted
        modeler = modeler.updated_copy(path_dir = save_name)
        # sp = gt.write_sparameters(
        #     component,
        #     folder_name=save_name,
        #     filepath=save_name + ".npz",
        #     plot_mode_index=0,
        #     plot_simulation_z = 0,
        #     sim_size_z=0,
        #     center_z="core",
        # )

        self.root.destroy()

    

    def plot(self, c):
        fig = plt.figure(constrained_layout=True)
        gs = fig.add_gridspec(ncols=2, nrows=3, width_ratios=(3, 1))
        ax0 = fig.add_subplot(gs[0, 0])
        ax1 = fig.add_subplot(gs[1, 0])
        ax2 = fig.add_subplot(gs[2, 0])
        axl = fig.add_subplot(gs[1, 1])
        c.plot_slice(x="core", ax=ax0)
        c.plot_slice(y="core", ax=ax1)
        c.plot_slice(z="core", ax=ax2)
        axl.legend(*ax0.get_legend_handles_labels(), loc="center")
        axl.axis("off")
        plt.show()

    def run(self):
        self.root.mainloop()
 

def get_callable_names(module):
    return [
        name for name, obj in inspect.getmembers(module)
        if callable(obj) and not name.startswith("_")
    ]


def handle_selection(selection_name):
    cell_function = getattr(cells, selection_name, None)
    if cell_function:
        print(f"Running cell: {selection_name}")
        result = cell_function()
        print(f"Result: {result}")
    else:
        print(f"No function found for: {selection_name}")

def foo():
    print("foo")

if __name__ == "__main__":
    cell_names = get_callable_names(cells)
    app = tidy3D_simulation_interface(cell_names)
    app.run()
