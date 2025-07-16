from cspdk.sin300.cband.tech import LAYER_STACK
import tidy3d as td

target_wl = 1.55
target_bw = 0.1
um = 1e-6

material_data = {
    "sin" : td.Medium(name = "SiN", permittivity = 2.0),
    "sio2" : td.Medium(name = "SiO2", permittivity = 1.44**2)
}
    # TiN = 3.23 + 5.2591j
    # Aluminium = 1.3474 + 14.133j # https://refractiveindex.info/?shelf=main&book=Al&page=McPeak




