from cosmo import *

sim = hysys_simulation.Simulation()

sim.Stream_SetPressure('C12', 150.0, 'kPa')

CP = sim.Components()

for i in range(CP.Count):
    print(CP.Item(i).name, CP.Item(i).MolecularWeightValue)

print(sim.Streams(0).name)
