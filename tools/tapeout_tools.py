import kfactory as kf
import gdsfactory as gf
import json
import csv
import pandas as pd
import os
gf.CONF.max_cellname_length = 1000  # increase the cell name length so that we always get the full length of the cellname - otherwise lose useful info

def generate_DOE_manifest():
    os.chdir(os.path.dirname(__file__))
    filepath = "test_chip.gds"

    # Open the file at the filepath
    top_cell = gf.read.import_gds(filepath)

    iterator = top_cell.kdb_cell.begin_instances_rec()

    # Now we are going to run through our manifest config
    testing_config = json.load(open("manifest_config.json", "r"))
    csvpath = "auto_design_manifest"

    for target_prefix, measurement_settings in testing_config.items():
        iterator.targets = target_prefix + "*"

        for iter, found_cell in enumerate(iterator):
            _c = top_cell.kcl[found_cell.inst_cell().cell_index()]
            _disp = (found_cell.trans() * found_cell.inst_trans()).disp
            new_cell_info = {"cell" : _c.name, "x"  :  _disp.x/1000, "y" : _disp.y/1000}
            new_cell_info.update({"function_name" : _c.function_name})
            new_cell_info.update({"info" : str(_c.info.model_dump())})

            new_cell_info.update({key : value for key, value in _c.settings.model_dump().items()})
            new_cell_info.update({"analysis" : ["[" + ",".join(measurement_settings.keys()) + "]"]})

            ## NOTE: Keep port name as is. It is only because we are using port names in a large DoE where they are getting named weirdly that it looks bad
            new_cell_info.update({"port_info" :  str([{"name" : port.name, "position" : kf.kdb.DTrans().from_s(port.trans), "port_type" : port.port_type} for port in _c.ports])})

            # TODO: add the ports information somewhere
            new_cell_info.update({"analysis_parameters" : str(list(measurement_settings.values()))})
            if iter == 0:
                output_dict = pd.DataFrame(new_cell_info)
            else:
                output_dict = output_dict.merge(pd.DataFrame(new_cell_info), how = "outer")
        output_dict.to_csv(csvpath + "_" + target_prefix + ".csv")


if __name__ == "__main__":
    generate_DOE_manifest()


    