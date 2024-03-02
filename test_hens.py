from hens import *

filename = r'C:\Users\may3r\OneDrive\Documents\GitHub\COSMO\hens\test.csv'
minup: MinUtilityProblem = MinUtilityProblem.generate_from_csv(filename)

#print(minup)

minup.print_temperature_interval()
minup.plot_composite_diagram()
minup.plot_grand_composite_curve()
