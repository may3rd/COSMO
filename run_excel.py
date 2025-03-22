# Run the case study from the excel file
from hens import *
import os
import pandas as pd
import argparse  # Import the argparse library

if __name__ == '__main__':
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Run heat exchange network synthesis from an Excel file.")
    parser.add_argument("excel_file", nargs='?', default="cases.xlsx", help="The path to the Excel file containing the case study data. Defaults to 'cases.xlsx' if not provided.")
    args = parser.parse_args()
    excel_file = args.excel_file  # Get the excel file from argument
    
    models = ["M1", "M2", "M3", "M4", "M5", "M6"]
    cost = "cost"
    alpha_w = 25.0
    
    # Error check: Ensure the Excel file exists
    if not os.path.exists(excel_file):
        print(f"Error: Excel file '{excel_file}' not found.")
        exit()  # Stop execution if the file doesn't exist

    print(f"Reading from Excel file: {excel_file}")
    xls = pd.ExcelFile(excel_file)

    # Print the list of sheet names
    print("Sheet names in the Excel file:")
    for sheet_name in xls.sheet_names:
        print(f"- {sheet_name}")

    print(f"Reading from Excel file: {excel_file}")
    xls = pd.ExcelFile(excel_file)

    for sheet_name in xls.sheet_names:
        print(f"================================= Sheet: {sheet_name} =================================")
        min_up_test: MinUtilityProblem = MinUtilityProblem.generate_from_excel_sheet(xls, sheet_name)
        min_up_test.print_minimum_demanded_utility()
        
        # Save composite and grand composite plots
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", f"{sheet_name}_composite.png")
        min_up_test.plot_composite_diagram(save=True, filename=filename)
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", f"{sheet_name}_grand_composite.png")
        min_up_test.plot_grand_composite_curve(save=True, filename=filename)
        
        print("- Solving Min Utility Problem -")
        sigma_HU, delta_HU, pinch_interval = solve_min_utility(min_up_test, debug=False)

        for model_selected in models:
            print("================================= Model: ", model_selected, " =================================")
            print("------- Matches without Pinch -------")
            no_pinch_network: Network = Network(min_up_test, sigma_HU, delta_HU)
            hexs = solve_transshipment_model(no_pinch_network, log_file=False, model_selected=model_selected, cost_selected=cost, alpha_w=alpha_w)
            print_matches_transshipment(hexs)

            if pinch_interval > 0:
                #print("------- Above Pinch -------")
                above_pinch_network: Network = Network(min_up_test, sigma_HU, delta_HU, pinch_interval, below_pinch=False)
                ab_hexs = solve_transshipment_model(above_pinch_network, log_file=False, model_selected=model_selected, cost_selected=cost, alpha_w=alpha_w)

                #print("------- Below Pinch -------")
                below_pinch_network: Network = Network(min_up_test, sigma_HU, delta_HU, pinch_interval, below_pinch=True)
                bl_hexs = solve_transshipment_model(below_pinch_network, log_file=False, model_selected=model_selected, cost_selected=cost, alpha_w=alpha_w)

                print("------- Match with Pinch -------")
                print_matches_transshipment(ab_hexs + bl_hexs)

    print("================================= Done =================================")