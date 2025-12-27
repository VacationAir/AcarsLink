#
# This creates and manages the pirep of the flight,
# from the begining to the end and send of pirep
#
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db.database_manager_phpvms import login_phpvms, initialize_pirep, get_reservation

def start_pirep(email, password,  zfw, fuel):
    user_id = login_phpvms(email, password)
    reservation = get_reservation(user_id)
    pirep_id = initialize_pirep(
        user_id=user_id,
        airline_id=1,  
        aircraft_id=reservation['aircraft']['id'] if reservation['aircraft'] else None,
        flight_id=reservation['flight_id'],
        flight_number=reservation['flight_number'],
        flight_type = reservation.get("transport_type"),  
        departure=reservation['departure']['id'],
        arrival=reservation['arrival']['id'],
        zfw=zfw,       
        block_fuel= fuel, 
        route=f"{reservation['departure']['id']} DCT {reservation['arrival']['id']}"
    )
    return pirep_id
