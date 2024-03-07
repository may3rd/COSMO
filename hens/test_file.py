# This file tests the implementation of the classes
from hens import *
import os


if __name__ == '__main__':
    problems: list[str] = []
    problems += ["4sp1", "6sp-cf1", "6sp-gg1", "6sp1", "7sp-cm1", "7sp-s1", "7sp-torw1", "7sp1", "7sp2"]
#    problems += ["8sp-fs1", "8sp1", "9sp-al1", "9sp-has1", "10sp-la1", "10sp-ol1", "10sp1", "12sp1", "14sp1"]
#    problems += ["15sp-tkm", "20sp1", "22sp-ph", "22sp1", "23sp1", "28sp-as1", "37sp-yfyv"]
#    problems += ["balanced5"] #  , "balanced8"]
#    problems += ["balance10", "balance12", "balance15"]
#    problems += ["unbalanced5", "unbalanced8", "unbalanced10", "unbalanced15", "unbalanced17", "unbalanced20"]

    problems = ["14sp1"]
    filename = 'test.csv'
    model_selected = "M5"
    file_test = False

    if file_test:
        min_up_test: MinUtilityProblem = MinUtilityProblem.generate_from_csv(os.path.join(os.getcwd(), filename))
    else:
        min_up_test: MinUtilityProblem = MinUtilityProblem.generate_from_data(problems[0])
    # min_up_test.plot_composite_diagram()
    # min_up_test.plot_grand_composite_curve()
    sigma_HU, delta_HU, pinch_interval = solve_min_utility(min_up_test, debug=True)

    no_pinch_network: Network = Network(min_up_test, sigma_HU, delta_HU)
    _, no_pinch_model = solve_transshipment_model(no_pinch_network, log=False, model_selected=model_selected)
    print_matches_transshipment(no_pinch_network, no_pinch_model)

    if pinch_interval > 0:
        print("---- Above Pinch ----")
        above_pinch_network: Network = Network(min_up_test, sigma_HU, delta_HU, pinch_interval, below_pinch=False)
        _, above_pinch_model = solve_transshipment_model(above_pinch_network, log=False, model_selected=model_selected)
        # print_matches_transshipment(above_pinch_network, above_pinch_model)

        print("---- Below Pinch ----")
        below_pinch_network: Network = Network(min_up_test, sigma_HU, delta_HU, pinch_interval, below_pinch=True)
        _, below_pinch_model = solve_transshipment_model(below_pinch_network, log=False, model_selected=model_selected)
        # print_matches_transshipment(below_pinch_network, below_pinch_model)
        # print_exchanger_details_transshipment(below_pinch_network, below_pinch_model)

    # for problem in problems:
    #     print("################################### {} #############################################".format(problem))
    #     min_up: MinUtilityProblem = MinUtilityProblem.generate_from_data(problem)
    #     (sigma_HU, delta_HU) = solve_min_utility(min_up, debug=False)
    #     problem_network = Network(min_up, sigma_HU, delta_HU)
    #
    #     print("---------------------------------- Transshipment Normal ----------------------------------")
    #     print("- based -")
    #     _, result_model = solve_transshipment_model(network=problem_network, weighted=True)
    #     print_matches_transshipment(problem_network, result_model)
    #     print_exchanger_details_transshipment(network=problem_network, model=result_model)
    #
    #     print("- greedy -")
    #     _, result_model = solve_transshipment_model(network=problem_network, greedy=True)
    #     print_matches_transshipment(problem_network, result_model)
    #
    #     print("- weighted -")
    #     _, result_model = solve_transshipment_model(network=problem_network, weighted=True)
    #     print_matches_transshipment(problem_network, result_model)
    #
    #     print("- greedy and weighted -")
    #     _, result_model = solve_transshipment_model(network=problem_network, greedy=True, weighted=True)
    #     print_matches_transshipment(problem_network, result_model)
    #
    #     print("- model 4 -")
    #     _, result_model = solve_transshipment_model(network=problem_network, model4flag=True)
    #     print_matches_transshipment(problem_network, result_model)
    #
    #     print("- model 5 -")
    #     _, result_model = solve_transshipment_model(network=problem_network, model5flag=True)
    #     print_matches_transshipment(problem_network, result_model)
    #
    #     print("---------------------------------- Transshipment Greedy ----------------------------------")
    #     _, result_model = solve_transshipment_model(network=problem_network)
    #     print_matches_transshipment(problem_network, result_model)
    #     print("------------------------------------ Transport Normal ------------------------------------")
    #     _, result_model = solve_transport_model(network=problem_network, greedy=False)
    #     print_matches_transport(problem_network, result_model)
    #     print("------------------------------------ Transport Greedy ------------------------------------")
    #     _, result_model = solve_transport_model(network=problem_network, greedy=True)
