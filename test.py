from cosmo import hysys_simulation

sim = hysys_simulation.Simulation()

#sim.Stream_SetPressure('C12', 150.0, 'kPa')

for i in range(sim.Streams.Count):
    print(sim.Streams.Item(i).name)
