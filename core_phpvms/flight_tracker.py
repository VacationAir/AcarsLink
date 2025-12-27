#
# This programm tracks all parameters at each time in the simulator
# to send it to acars, so it gets updated with current information
#

from x_plane_connector import request_all_datrefs
from pireps_manager import start_pirep
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db.database_manager_phpvms import initialize_acars


def start_track(email, password, zfw, fuel):
    pirep_id = start_pirep(email, password, zfw, fuel)
    datarefs = request_all_datrefs()
    initialize_acars(pirep_id, datarefs.get(1),datarefs.get(2), fuel)
    
start_track("vacationair.va@gmail.com", "Lolipop.1", "60000", "7400")