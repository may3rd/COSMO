# Minimization of Utility Solver
from pyomo.environ import ConcreteModel, Var, NonNegativeReals, RangeSet, Objective, Constraint, SolverFactory
from hens import Utility, TemperatureInterval


def solve_min_utility(problem_instance, debug: bool = False) -> tuple[dict[tuple[Utility, TemperatureInterval], float], dict[tuple[Utility, TemperatureInterval], float]]:
    """
    Before solving the MILP transshipment model, this module is solved to provide the minimum utility consumption
    and the location of pinch points that partition the full network into subnetworks.

    :param problem_instance: Instance of the minimum utility problem
    :param debug: whether to print debug information

    :return: sigmas_hu, deltas_cu: used to update network problem before solve for MILP transshipment model
    """
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
    model_to_solve.sigma_hu = Var(hot_utilities, intervals, within=NonNegativeReals)
    model_to_solve.delta_cu = Var(cold_utilities, intervals, within=NonNegativeReals)
    model_to_solve.residual_set = RangeSet(0, len(intervals))
    model_to_solve.residual_ik = Var(model_to_solve.residual_set, within=NonNegativeReals)
    last_residual = len(intervals)

    # defining model cost computation
    def utility_cost_rule(model):
        hu_cost = sum(k_hu[hu] * model.sigma_hu[hu, ti] for hu in hot_utilities for ti in intervals)
        cu_cost = sum(k_cu[cu] * model.delta_cu[cu, ti] for cu in cold_utilities for ti in intervals)
        return model.cost == hu_cost + cu_cost
    model_to_solve.utility_cost_constraint = Constraint(rule=utility_cost_rule)

    # defining model objective
    def cost_min_rule(model):
        return model.cost
    model_to_solve.obj = Objective(rule=cost_min_rule)

    # heat balance restriction
    def heat_balance_rule(model, t_interval):
        interval_index = intervals.index(t_interval) + 1
        entering_energy = sum(sigmas[hs, t_interval] for hs in hot_streams) + sum(model.sigma_hu[hu, t_interval] for hu in hot_utilities) + model.residual_ik[interval_index - 1]
        exiting_energy = sum(deltas[cs, t_interval] for cs in cold_streams) + sum(model.delta_cu[cu, t_interval] for cu in cold_utilities) + model.residual_ik[interval_index]
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
    def forbidden_hu_intervals(model, hu, ti):
        if accepted_hu_sigmas[hu, ti]:
            return Constraint.Skip
        else:
            return model.sigma_hu[hu, ti] == 0
    model_to_solve.forbidden_hu_intervals_constraint = Constraint(hot_utilities, intervals, rule=forbidden_hu_intervals)

    # forbidden heat exchanges for cold utilities
    def forbidden_cu_intervals(model, cu, ti):
        if accepted_cu_deltas[cu, ti]:
            return Constraint.Skip
        else:
            return model.delta_cu[cu, ti] == 0
    model_to_solve.forbidden_cu_intervals_constraint = Constraint(cold_utilities, intervals, rule=forbidden_cu_intervals)

    # solving model
    solver = SolverFactory("glpk")
    solver.solve(model_to_solve)
    
    # generating sigmas dictionary for hot utilities
    sigma_hu: dict[tuple[Utility, TemperatureInterval], float] = {}
    for utility in hot_utilities:
        for interval in intervals:
            # ignore VS Code error: line works as intended
            sigma_hu[utility, interval] = model_to_solve.sigma_hu[utility, interval].value
    
    # generating deltas dictionary for cold utilities
    delta_cu: dict[tuple[Utility, TemperatureInterval], float] = {}
    for utility in cold_utilities:
        for interval in intervals:
            # ignore VS Code error: line works as intended
            delta_cu[utility, interval] = model_to_solve.delta_cu[utility, interval].value

    if debug:
        print('debug mode')
        print('hot utility')
        for utility in hot_utilities:
            for interval in intervals:
                print(sigma_hu[utility, interval])

        print('cold utility')
        for utility in cold_utilities:
            for interval in intervals:
                print(delta_cu[utility, interval])

    return sigma_hu, delta_cu
