from cosmo import *

sim = hysys_simulation.Simulation()

#sim.Stream_SetPressure('C12', 150.0, 'kPa')

print(sim.Operations(1).name)
