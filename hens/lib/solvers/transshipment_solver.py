# Minimization of Matches Solver via Transshipment Model
from pyomo.environ import ConcreteModel, Var, NonNegativeReals, RangeSet, Objective, Constraint, SolverFactory, Binary
from time import time


def solve_transshipment_model(network):

    # declaring model
    model = ConcreteModel(name = "MIN_MATCHES_TRANSSHIPMENT")

    # declaring model inputs
    H = network.H               # hot streams including utilities
    C = network.C               # cold streams including utilities
    T = network.T               # temperature intervals
    P = network.P               # stream exchange premission
    sigma = network.sigmas      # heat supply per hot stream per interval
    delta = network.deltas      # heat demand per cold stream per interval
    U = network.U               # Big-M parameter

    # declaring model variables
    model.q = Var(H, C, T, within = NonNegativeReals)
    model.y = Var(H, C, within = Binary)
    model.rset = RangeSet(0, len(T))
    model.R = Var(H, model.rset, within = NonNegativeReals)
    last_R = len(T)

    # model objective
    def matches_min_rule(model):
        return sum(model.y[h, c] for h in H for c in C)
    model.obj = Objective(rule = matches_min_rule)

    # heat conservation
    def heat_conservation_rule(model, h, t):
        interval_index = T.index(t) + 1
        exiting_heat = sum(model.q[h, c, t] for c in C) + model.R[h, interval_index]
        entering_heat = sigma[h, t] + model.R[h, interval_index - 1]
        return exiting_heat == entering_heat
    model.heat_conservation_constraint = Constraint(H, T, rule = heat_conservation_rule)

    # zero residual constraint
    def zero_residual_rule(model, h, r):
        if (r == 0) or (r == last_R):
            return model.R[h, r] == 0
        else:
            return Constraint.Skip
    model.zero_residual_constraint = Constraint(H, model.rset, rule = zero_residual_rule)

    # heat demand satisfaction
    def heat_demand_rule(model, c, t):
        return sum(model.q[h, c, t] for h in H) == delta[c, t]
    model.demand_satisfaction_constraint = Constraint(C, T, rule = heat_demand_rule)

    # big-M restriction
    def big_M_rule(model, h, c):
        return sum(model.q[h, c, t] for t in T) <= U[h, c] * model.y[h, c]
    model.big_m_constraint = Constraint(H, C, rule = big_M_rule)

    # define hot to cold matching permission
    model.stream_exchange_permission = Constraint(H, C, rule = lambda m, h, c: m.y[h, c] <= P[h, c])

    # solving model
    s_time = time()
    solver = SolverFactory("glpk")
    results = solver.solve(model)
    y = [model.y[h, c].value for h in H for c in C]
    print("HS: {}, CS: {}, TI: {}".format(len(H), len(C), len(T)))
    print("Objective: y = {}, in {} seconds".format(sum(y), round(time() - s_time, 6)))

    return (results, model)


def solve_transshipment_model_greedy(network):

    # declaring model
    model = ConcreteModel(name = "MIN_MATCHES_TRANSSHIPMENT_GREEDY")

    # declaring model inputs
    H = network.H               # hot streams including utilities
    C = network.C               # cold streams including utilities
    T = network.T               # temperature intervals
    P = network.P               # stream exchange premission
    sigma = network.sigmas      # heat supply per hot stream per interval
    delta = network.deltas      # heat demand per cold stream per interval
    U = network.U_greedy        # Big-M parameter

    # declaring model variables
    model.q = Var(H, C, T, within = NonNegativeReals)
    model.y = Var(H, C, within = Binary)
    model.rset = RangeSet(0, len(T))
    model.R = Var(H, model.rset, within = NonNegativeReals)
    last_R = len(T)

    # model objective
    def matches_min_rule(model):
        return sum(model.y[h, c] for h in H for c in C)
    model.obj = Objective(rule = matches_min_rule)

    # heat conservation
    def heat_conservation_rule(model, h, t):
        interval_index = T.index(t) + 1
        exiting_heat = sum(model.q[h, c, t] for c in C) + model.R[h, interval_index]
        entering_heat = sigma[h, t] + model.R[h, interval_index - 1]
        return exiting_heat == entering_heat
    model.heat_conservation_constraint = Constraint(H, T, rule = heat_conservation_rule)

    # zero residual constraint
    def zero_residual_rule(model, h, r):
        if (r == 0) or (r == last_R):
            return model.R[h, r] == 0
        else:
            return Constraint.Skip
    model.zero_residual_constraint = Constraint(H, model.rset, rule = zero_residual_rule)

    # heat demand satisfaction
    def heat_demand_rule(model, c, t):
        return sum(model.q[h, c, t] for h in H) == delta[c, t]
    model.demand_satisfaction_constraint = Constraint(C, T, rule = heat_demand_rule)

    # big-M restriction
    def big_M_rule(model, h, c):
        return sum(model.q[h, c, t] for t in T) <= U[h, c] * model.y[h, c]
    model.big_m_constraint = Constraint(H, C, rule = big_M_rule)

    # define hot to cold matching permission
    model.stream_exchange_permission = Constraint(H, C, rule = lambda m, h, c: m.y[h, c] <= P[h, c])

    # solving model
    s_time = time()
    solver = SolverFactory("glpk")
    results = solver.solve(model)
    y = [model.y[h, c].value for h in H for c in C]
    print("HS: {}, CS: {}, TI: {}".format(len(H), len(C), len(T)))
    print("Objective: y = {}, in {} seconds".format(sum(y), round(time() - s_time, 6)))
    return (results, model)
