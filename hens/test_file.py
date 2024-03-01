# This file tests the implementation of the classes
from lib.classes.minimum_utility_problem import Min_Utility_Problem
from lib.classes.network import Network
from lib.solvers.min_utility_solver import solve_min_utility_instance
from lib.solvers.transshipment_solver import solve_transshipment_model, solve_transshipment_model_greedy
from lib.solvers.transport_solver import solve_transport_model, solve_transport_model_greedy

def display_matches_transshipment(network, model):
        
    for h in network.H:
        total_h = 0.0
        for c in network.C:
            if model.y[h, c].value != 0:
                print(f'matching {h.name} with {c.name}', end="")
                total_h = 0.0
                for t in network.T:
                    if model.q[h, c, t].value > 0.0:
                        #print(f'  {t} - {model.q[h, c, t].value:.2f}')
                        total_h += model.q[h, c, t].value
                        pass
                print(f' - q = {total_h:.2f}')

        #print(f'  {h.name}, q = {total_h:0.2f}')

def display_matches_transport(network, model):
        
    for h in network.H:
        total_h = 0.0
        for c in network.C:
            if model.y[h, c].value != 0:
                print(f'matching {h.name} with {c.name}', end="")
                total_h = 0.0
                for s in network.T:
                    for t in network.T:
                        if model.q[h, s, c, t].value > 0.0:
                            #print(f'  {t} - {model.q[h, c, t].value:.2f}')
                            total_h += model.q[h, s, c, t].value
                            pass
                print(f' - q = {total_h:.2f}')

        #print(f'  {h.name}, q = {total_h:0.2f}')

if __name__ == '__main__':

    # problems = ["balanced5", "balanced8", "balanced10", "balanced12", "balanced15"]
    # problems += ["unbalanced5", "unbalanced10", "unbalanced15", "unbalanced17", "unbalanced20"]

    problems = ["balanced5", "4sp1", "6sp-cf1", "6sp-gg1", "6sp1", "7sp-cm1", "7sp-s1", "7sp-torw1", "7sp1", "7sp2", "7sp4"]
    problems += ["8sp-fs1", "8sp1", "9sp-al1", "9sp-has1", "10sp-la1", "10sp-ol1", "10sp1", "12sp1", "14sp1", "15sp-tkm"] 
    # problems += ["20sp1", "22sp-ph", "22sp1", "23sp1", "28sp-as1", "37sp-yfyv"]

    problems = ["15sp-tkm"]

    for problem in problems:
        print("################################### {} #############################################".format(problem))
        minup: Min_Utility_Problem = Min_Utility_Problem.generate_from_data(problem)
        minup.print_minimum_demanded_utility()

        (sigma_HU, delta_HU) = solve_min_utility_instance(minup, debug=False)
        network = Network(minup, sigma_HU, delta_HU)

        network.print_heats()
        network.print_demands()

        print("---------------------------------- Transshipment Normal ----------------------------------")
        (result, model) = solve_transshipment_model(network)
        display_matches_transshipment(network, model)
        #print("---------------------------------- Transshipment Greedy ----------------------------------")
        #solve_transshipment_model_greedy(network)
        print("------------------------------------ Transport Normal ------------------------------------")
        (results, model) = solve_transport_model(network)
        display_matches_transport(network, model)
        #print("------------------------------------ Transport Greedy ------------------------------------")
        #solve_transport_model_greedy(network)
