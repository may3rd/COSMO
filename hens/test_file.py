# This file tests the implementation of the classes
from hens import *
import os


if __name__ == '__main__':
    problems = ["4sp1", "6sp-cf1", "6sp-gg1", "6sp1", "7sp-cm1", "7sp-s1", "7sp-torw1", "7sp1", "7sp2"]
    problems += ["8sp-fs1", "8sp1", "9sp-al1", "9sp-has1", "10sp-la1", "10sp-ol1", "10sp1", "12sp1", "14sp1"]
    problems += ["15sp-tkm", "20sp1", "22sp-ph", "22sp1", "23sp1", "28sp-as1", "37sp-yfyv"]
#    problems += ["balanced5", "balance8", "balance10", "balance12", "balance15"]
#    problems += ["unbalanced5", "unbalanced10", "unbalanced15", "unbalanced17", "unbalanced20"]

    filename = 'test.csv'
    min_up_test: MinUtilityProblem = MinUtilityProblem.generate_from_csv(os.path.join(os.getcwd(), filename))
    min_up_test.plot_composite_diagram()
    exit(0)

#    sigma_HU, delta_HU = solve_min_utility_instance(min_up_test, debug=False)
#    problem_network: Network = Network(min_up_test, sigma_HU, delta_HU)
#    _, result_model = solve_transshipment_model(problem_network)
#   print_matches_transshipment(problem_network, result_model)
#    _, result_model = solve_transshipment_model_greedy(problem_network)
#    print_matches_transshipment(problem_network, result_model)
#    _, result_model = solve_transport_model(problem_network)
#    print_matches_transport(problem_network, result_model)
#    _, result_model = solve_transport_model_greedy(problem_network)
#    print_matches_transport(problem_network, result_model)

    for problem in problems:
        print("################################### {} #############################################".format(problem))
        min_up: MinUtilityProblem = MinUtilityProblem.generate_from_data(problem)
        (sigma_HU, delta_HU) = solve_min_utility_instance(min_up, debug=False)
        problem_network = Network(min_up, sigma_HU, delta_HU)
        print("---------------------------------- Transshipment Normal ----------------------------------")
        _, result_model = solve_transshipment_model(problem_network)
        print_matches_transshipment(problem_network, result_model)
        print("---------------------------------- Transshipment Greedy ----------------------------------")
        solve_transshipment_model_greedy(problem_network)
        print("------------------------------------ Transport Normal ------------------------------------")
        _, result_model = solve_transport_model(problem_network)
        print_matches_transport(problem_network, result_model)
        print("------------------------------------ Transport Greedy ------------------------------------")
        _, result_model = solve_transport_model_greedy(problem_network)
