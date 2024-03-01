from hens import *

filename = r'C:\Users\may3r\OneDrive\Documents\GitHub\COSMO\hens\data\original_problems\23sp1.dat'
minup: Min_Utility_Problem = Min_Utility_Problem.generate_from_file(filename)

#print(minup)

minup.print_temperature_interval()
minup.plot_composite_diagram()
minup.plot_grand_composite_curve()
