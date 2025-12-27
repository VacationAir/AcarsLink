import socket
import struct
from find_x_plane import find_xp

# Crear socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", 0))  

# Dataref
cmd = b"RREF"
freq = 5
index = 1
dataref_string = {
    1 : "sim/flightmodel/position/latitude", # decimal degrees
    2:  "sim/flightmodel/position/longitude", # decimal degrees
    3: "sim/flightmodel/position/elevation", # elevation in meters
    4: "sim/flightmodel/position/groundspeed", # groundspeed in m/s
    5:  "sim/flightmodel/position/mag_psi", # real magnetic heading of the aircraf in degrees    
    6: "sim/flightmodel/weight/m_fuel_total", # total fuel remaining in Kg
    7:  "sim/flightmodel/position/indicated_airspeed", # Air speed indicated - this takes into account air density and wind direction in knots
    8: "sim/flightmodel/position/vh_ind_fpm", # vertical speed in feet/minute
    9: "sim/cockpit2/engine/indicators/fuel_flow_kg_sec", # total fuel flow in kg/second 
    10: "sim/cockpit2/controls/flap_system_deploy_ratio", # Current flap deployment percentage from 0 to 1
    11: "sim/cockpit/switches/gear_handle_status" # gear handle in cockpit is up or down
}

# IP de X-Plane
beacon = find_xp()
if not beacon:
    print("Couldn´t connect to X-Plane. Check that the sim is running")

xp_ip = beacon["ip"]
xp_port = beacon['port'] 

def request_all_datrefs():
    results = {}
    for idx, ref in dataref_string.items():
        ref_bytes = ref.encode("utf-8")
        message = struct.pack("<4sxii400s", cmd, freq, idx, ref_bytes)
        sock.sendto(message, (xp_ip, xp_port))

    # Recibir N respuestas
    for _ in range(len(dataref_string)):
        data, addr = sock.recvfrom(1024)
        header = data[0:4]
        idx, value = struct.unpack("<if", data[5:13])
        results[idx] = value

    return results

request_all_datrefs()




