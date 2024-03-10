# Minimization of Utility Solver
from pyomo.environ import ConcreteModel, Var, NonNegativeReals, RangeSet, Objective, Constraint, SolverFactory, value
from hens import MinUtilityProblem


def solve_min_utility(problem_instance: MinUtilityProblem, debug: bool = False):
    # declaring model
    model_to_solve: ConcreteModel = ConcreteModel(name="MIN_UTILITY")  # declaring concrete model

    # declaring model inputs
    hot_streams = problem_instance.hot_streams
    cold_streams = problem_instance.cold_streams
    hot_utilities = problem_instance.hot_utilities
    cold_utilities = problem_instance.cold_utilities
    intervals = problem_instance.intervals
    sigmas = problem_instance.sigmas
    deltas = problem_instance.deltas
    accepted_hu_sigmas = problem_instance.accepted_hu_sigmas
    accepted_cu_deltas = problem_instance.accepted_cu_deltas
    k_hu = {}
    for hot_utility in hot_utilities:
        k_hu[hot_utility] = hot_utility.cost
    k_cu = {}
    for cold_utility in cold_utilities:
        k_cu[cold_utility] = cold_utility.cost

    # declaring model variables
    model_to_solve.cost = Var(within=NonNegativeReals)
    model_to_solve.sigma_hu = Var(hot_utilities, cold_streams, intervals, within=NonNegativeReals)
    model_to_solve.delta_cu = Var(hot_streams, cold_utilities, intervals, within=NonNegativeReals)
    model_to_solve.residual_set = RangeSet(0, len(intervals))
    model_to_solve.residual_ik = Var(model_to_solve.residual_set, within=NonNegativeReals)
    last_residual = len(intervals)

    # defining model cost computation
    def utility_cost_rule(model):
        hu_cost = sum(k_hu[hu] * model.sigma_hu[hu, cs, ti] for hu in hot_utilities for cs in cold_streams for ti in intervals)
        cu_cost = sum(k_cu[cu] * model.delta_cu[hs, cu, ti] for hs in hot_streams for cu in cold_utilities for ti in intervals)
        return model.cost == hu_cost + cu_cost
    model_to_solve.utility_cost_constraint = Constraint(rule=utility_cost_rule)

    # defining model objective
    def cost_min_rule(model):
        return model.cost
    model_to_solve.obj = Objective(rule=cost_min_rule)

    # heat balance restriction
    def heat_balance_rule(model, t_interval):
        interval_index = intervals.index(t_interval) + 1
        entering_energy = sum(sigmas[hs, t_interval] for hs in hot_streams) + sum(model.sigma_hu[hu, cs, t_interval] for hu in hot_utilities for cs in cold_streams) + model.residual_ik[interval_index - 1]
        exiting_energy = sum(deltas[cs, t_interval] for cs in cold_streams) + sum(model.delta_cu[hs, cu, t_interval] for hs in hot_streams for cu in cold_utilities) + model.residual_ik[interval_index]
        return entering_energy == exiting_energy
    model_to_solve.heat_balance_constraint = Constraint(intervals, rule=heat_balance_rule)

    # residual heat entering the first temperature interval and the one exiting the last temperature interval
    # must be zero
    def r_zero_rule(model, r):
        if (r == 0) or (r == last_residual):
            return model.residual_ik[r] == 0
        else:
            return Constraint.Skip
    model_to_solve.r_zero_constraint = Constraint(model_to_solve.residual_set, rule=r_zero_rule)

    # forbidden heat exchanges for hot utilities
    def forbidden_hu_intervals(model, hu, cs, ti):
        if accepted_hu_sigmas[hu, ti]:
            return Constraint.Skip
        else:
            return model.sigma_hu[hu, cs, ti] == 0
    model_to_solve.forbidden_hu_intervals_constraint = Constraint(hot_utilities, cold_streams, intervals, rule=forbidden_hu_intervals)

    # forbidden heat exchanges for cold utilities
    def forbidden_cu_intervals(model, hs, cu, ti):
        if accepted_cu_deltas[cu, ti]:
            return Constraint.Skip
        else:
            return model.delta_cu[hs, cu, ti] == 0
    model_to_solve.forbidden_cu_intervals_constraint = Constraint(hot_streams, cold_utilities, intervals, rule=forbidden_cu_intervals)

    # solving model
    solver = SolverFactory("glpk")
    solver.solve(model_to_solve)
    
    # generating sigmas dictionary for hot utilities
    sigma_hu = {}
    for hot in hot_utilities:
        for k in intervals:
            # ignore VS Code error: line works as intended
            sigma_hu[hot, k] = sum(value(model_to_solve.sigma_hu[hot, cs, k]) for cs in cold_streams)
    
    # generating deltas dictionary for cold utilities
    delta_cu = {}
    for cold in cold_utilities:
        for k in intervals:
            # ignore VS Code error: line works as intended
            delta_cu[cold, k] = sum(value(model_to_solve.delta_cu[hs, cold, k]) for hs in hot_streams)

    # determine the pinch temperature interval
    residual_ik_value = {i: value(model_to_solve.residual_ik[i]) for i in model_to_solve.residual_ik}
    zero_indices = [
        i for i in residual_ik_value.keys() if residual_ik_value[i] < 1e-6
    ]
    pinch_interval = 0
    if zero_indices:
        for i in zero_indices:
            if not (i == 0 or i == len(intervals)):
                pinch_interval = i
                break
    pinch_hots_pass: bool = False
    pinch_colds_pass: bool = False
    for hot in problem_instance.hot_streams:
        pinch_hots_pass = intervals[pinch_interval].passes_through_interval(hot.interval)
        if pinch_hots_pass:
            break
    for cold in problem_instance.cold_streams:
        pinch_colds_pass = intervals[pinch_interval].passes_through_interval(cold.interval)
        if pinch_colds_pass:
            break
    if not (pinch_colds_pass and pinch_hots_pass):
        pinch_interval = 0

    if debug:
        print('--------------------- debug mode : begin ---------------------')
        print('hot utility')
        for hot in hot_utilities:
            for k in intervals:
                if sigma_hu[hot, k] > 0:
                    print(hot, k, sigma_hu[hot, k])

        print('cold utility')
        for cold in cold_utilities:
            for k in intervals:
                if delta_cu[cold, k] > 0:
                    print(cold, k, delta_cu[cold, k])

        if pinch_interval > 0:
            print('pinch interval')
            print(intervals[pinch_interval])
        else:
            print("No pinch")
        print('--------------------- debug mode : end ---------------------')

    return sigma_hu, delta_cu, pinch_interval
