from cosmo import *

sim = hysys_simulation.simulation(filename='Test_1')

if sim:
    sim.stream_set_pressure('C12', 150.0, 'kPa')
    print(sim.component_list)
