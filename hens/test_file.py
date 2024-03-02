# This file tests the implementation of the classes
from hens import *
import os


def display_matches_transshipment(network, model):
    print('------- Matching Streams ------')
    for h in network.H:
        for c in network.C:
            if model.y[h, c].value != 0:
                print(f'{h.name} with {c.name}', end="")
                total_h = 0.0
                for t in network.T:
                    if model.q[h, c, t].value > 0.0:
                        # print(f'  {t} - {model.q[h, c, t].value:.2f}')
                        total_h += model.q[h, c, t].value
                        pass
                print(f' - q = {total_h:.2f}')


def display_matches_transport(network, model):
    print('------- Matching Streams ------')
    for h in network.H:
        for c in network.C:
            if model.y[h, c].value != 0:
                print(f'{h.name} with {c.name}', end="")
                total_h = 0.0
                for s in network.T:
                    for t in network.T:
                        if model.q[h, s, c, t].value > 0.0:
                            # print(f'  {t} - {model.q[h, c, t].value:.2f}')
                            total_h += model.q[h, s, c, t].value
                            pass
                print(f' - q = {total_h:.2f}')


if __name__ == '__main__':
    problems = ["4sp1", "6sp-cf1", "6sp-gg1", "6sp1", "7sp-cm1", "7sp-s1", "7sp-torw1", "7sp1", "7sp2",
                "8sp-fs1", "8sp1", "9sp-al1", "9sp-has1", "10sp-la1", "10sp-ol1", "10sp1", "12sp1", "14sp1", "15sp-tkm",
                "20sp1", "22sp-ph", "22sp1", "23sp1", "28sp-as1", "37sp-yfyv", "balanced5", "balance8", "balance10",
                "balance12", "balance15", "unbalanced5", "unbalanced10", "unbalanced15", "unbalanced17", "unbalanced20"]

    filename = 'test.csv'
    min_up_test: MinUtilityProblem = MinUtilityProblem.generate_from_csv(os.path.join(os.getcwd(), filename))
    min_up_test.plot_composite_diagram()
    exit(0)

#    sigma_HU, delta_HU = solve_min_utility_instance(min_up_test, debug=False)
#    problem_network: Network = Network(min_up_test, sigma_HU, delta_HU)
#    _, result_model = solve_transshipment_model(problem_network)
#   display_matches_transshipment(problem_network, result_model)
#    _, result_model = solve_transshipment_model_greedy(problem_network)
#    display_matches_transshipment(problem_network, result_model)
#    _, result_model = solve_transport_model(problem_network)
#    display_matches_transport(problem_network, result_model)
#    _, result_model = solve_transport_model_greedy(problem_network)
#    display_matches_transport(problem_network, result_model)

    for problem in problems:
        print("################################### {} #############################################".format(problem))
        min_up: MinUtilityProblem = MinUtilityProblem.generate_from_data(problem)
        (sigma_HU, delta_HU) = solve_min_utility_instance(min_up, debug=False)
        problem_network = Network(min_up, sigma_HU, delta_HU)
        print("---------------------------------- Transshipment Normal ----------------------------------")
        _, result_model = solve_transshipment_model(problem_network)
        display_matches_transshipment(problem_network, result_model)
        print("---------------------------------- Transshipment Greedy ----------------------------------")
        solve_transshipment_model_greedy(problem_network)
        print("------------------------------------ Transport Normal ------------------------------------")
        _, result_model = solve_transport_model(problem_network)
        display_matches_transport(problem_network, result_model)
        print("------------------------------------ Transport Greedy ------------------------------------")
        _, result_model = solve_transport_model_greedy(problem_network)
