'''Code to take a cross-section from the PDK and simulate it using Tidy3Ds mode solver. Useful for complex cross-sections'''
import tkinter as tk
from tkinter import ttk, messagebox
import gdsfactory as gf
import inspect
from functools import wraps
import traceback
import gplugins.tidy3d as gt
### Because it is not 
# from gplugins.femwell.mode_solver import compute_cross_section_modes
import numpy as np
from cspdk.sin300.cband import PDK

PDK.activate()

def safe_callback_from_selfroot(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            print("[FATAL ERROR in callback]")
            traceback.print_exc()
            messagebox.showerror("Error", f"Something went wrong:\n{str(e)}")
            if hasattr(self, "root"):
                self.root.destroy()
    return wrapper

class mode_tidy3D_interface():
    def __init__(self):

        self.root = tk.Tk()
        self.root.title("Xsection Selector")
        self.root.geometry("700x450")

        self._build_gui()

    @safe_callback_from_selfroot
    def _build_gui(self):
        # Label
        label = ttk.Label(self.root, text="Select an Cell:")
        label.pack(pady=10)

        # Dropdown
        self.combo = ttk.Combobox(self.root, values=[name.strip('"').strip(",") for name in list(gf.get_active_pdk().cross_sections.keys())], state="readonly")
        self.combo.pack()
        ## For each parameter, add the parameter here:
        # Button
        submit_btn = ttk.Button(self.root, text="Choose", command=self._on_choice)
        submit_btn.pack(pady=10)

    @safe_callback_from_selfroot
    def _on_choice(self):
        print("DEBUG ON CHOICE")
        self.comp_selection = self.combo.get()
        print(self.combo.get())
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
        print(gf.get_active_pdk().get_cross_section(self.comp_selection))
        try:
            xs_factory = gf.get_active_pdk().cross_sections[self.comp_selection]
            self.entries = {}
        except Exception:
            raise LookupError("Failed to find cross-section factory")

        # Now get default values from signature
        signature = inspect.signature(xs_factory)
        defaults = {
            k: v.default
            for k, v in signature.parameters.items()
            if v.default is not inspect.Parameter.empty
        }

        # Now build the actual cross-section (to inspect its sections)
        self.xsection = xs_factory()

        for i, section in enumerate(self.xsection.sections):
            layer_label = ttk.Label(self.secondary_frame, text=f"Layer {section.layer}")
            layer_label.grid(row=2*i+1, column=0, columnspan=2)

            width_label = ttk.Label(self.secondary_frame, text="Width:")
            width_label.grid(row=2*i+2, column=0)
            width_entry = ttk.Entry(self.secondary_frame)
            width_entry.insert(0, str(section.width))
            width_entry.grid(row=2*i+2, column=1)

            offset_label = ttk.Label(self.secondary_frame, text="Offset:")
            offset_label.grid(row=2*i+2, column=2)
            offset_entry = ttk.Entry(self.secondary_frame)
            offset_entry.insert(0, str(section.offset))
            offset_entry.grid(row=2*i+2, column=3)

            self.entries[section.layer] = {
                "width": width_entry,
                "offset": offset_entry,
            }

        

        submit_btn = ttk.Button(self.secondary_frame, text="Submit", command=lambda: self._on_submit_cross_section())
        submit_btn.grid(row=len(self.xsection.sections)+2, column=0, columnspan=2, pady=10)

    @safe_callback_from_selfroot
    def _on_submit_cross_section(self):

        def parse_param(value):
            def convert_scalar(val):
                val = val.strip().lower()
                if val in {"true", "yes", "on", "1"}:
                    return True
                elif val in {"false", "no", "off", "0"}:
                    return False
                try:
                    return float(val) if "." in val else int(val)
                except ValueError:
                    return val  # leave as string if not numeric
            if "," in value:
                return [convert_scalar(v) for v in value.split(",")]
            return convert_scalar(value)

        # Gather all parameter sets
        parsed_entries = {
            layer: {
                k: parse_param(w.get())
                for k, w in widgets.items()
            }
            for layer, widgets in self.entries.items()
        }

        # Check if any fields are lists
        sweep_lengths = {
            layer: max(
                len(v) if isinstance(v, list) else 1
                for v in layer_dict.values()
            )
            for layer, layer_dict in parsed_entries.items()
        }

        if len(set(sweep_lengths.values())) > 1:
            print("[ERROR] All parameter lists must be of the same length per layer")
            self.root.destroy()
            return

        n_sweeps = next(iter(sweep_lengths.values()))

        for sweep_index in range(n_sweeps):
            modified_sections = []

            for layer, param_dict in parsed_entries.items():
                width = param_dict["width"]
                offset = param_dict["offset"]

                if isinstance(width, list):
                    width = width[sweep_index]
                if isinstance(offset, list):
                    offset = offset[sweep_index]

                original = next(s for s in self.xsection.sections if s.layer == layer)

                modified_sections.append(
                    gf.Section(
                        layer=layer,
                        width=width,
                        offset=offset,
                        port_types=original.port_types,
                        port_names=original.port_names,
                        name=original.name,
                        hidden=original.hidden
                    )
                )

            new_xs = gf.CrossSection(sections=tuple(modified_sections))
            c = gf.components.straight(cross_section=new_xs).copy()
            c.show()  # or c.write_gds(...), etc.

            ## For now let's just use the FEMWELL - unclear if we can actually save the 
            strip = gt.modes.Waveguide(
                wavelength=1.55,
                core_width=0.5,
                core_thickness=0.3,
                slab_thickness=0.0,
                core_material=2,
                clad_material=1.44,
            )
            w = np.linspace(0.4, 1, 5)
            neff = gt.modes.sweep_n_eff(strip, core_width=w)
            print(neff)


        self.root.destroy()
    
    @safe_callback_from_selfroot
    def run(self):
        self.root.mainloop()
    
if __name__ == "__main__":
    print(gf.get_active_pdk().name)
    app = mode_tidy3D_interface()
    app.run()