""" Minimization of Matches Solver via Transshipment Model
Change by Maetee L : may3rd@gmail.com
By applying the model list in Chen, Grossmann, and Miller (2015).
Include model M-1 to M-5, selected by parameter model_selected
"""
from pyomo.environ import ConcreteModel, Var, NonNegativeReals, RangeSet, Objective, Constraint, SolverFactory, Binary, value
from time import time
from hens import Network, log_mean_temperature_diff


def solve_transshipment_model(network: Network, greedy: bool = False, model_selected: str = "M1", log: bool = False):
    """
    Solve the heat exchanger network synthesis using transshipment model listed in Yang (2015)

    :param network: the problem network
    :param greedy: weather using greedy U_ij or not
    :param model_selected: the model to be used to solve the network problem - ["M1" to "M5"]
    :param log: weather show logging and save to solver.log file

    :return:
    """
    # ensure that only one model is selected
    if model_selected is None:
        model_selected = "M1"

    network.model = model_selected
    print(f"The model to be used is {network.model}")
    # declaring model
    model_to_solve: ConcreteModel = ConcreteModel(name="MIN_MATCHES_TRANSSHIPMENT")

    # declaring model inputs
    intervals = network.T  # temperature intervals
    diff_t_min = network.diff_t_min
    hots = list(set([i for i in network.H for k in intervals if i.interval.passes_through_interval(k)]))  # hot streams including utilities
    colds = list(set(j for j in network.C for k in intervals if j.interval.shifted(diff_t_min).passes_through_interval(k)))  # cold streams including utilities
    sigma = network.sigmas  # heat supply per hot stream per interval
    delta = network.deltas  # heat demand per cold stream per interval
    p_ij = network.P  # stream exchange permission
    p_ijk = network.Pk  # stream exchange in interval permission
    if not greedy:
        u_ij = network.U  # Big-M parameter
    else:
        u_ij = network.U_greedy
    u_ijk = network.u_ijk
    u_ijkl = network.u_ijkl

    # determine n_h and n_c based on interval
    n_h = []
    n_c = []
    for interval in intervals:
        for hot in hots:
            if hot.interval.passes_through_interval(interval):
                if hot not in n_h:
                    n_h.append(hot)
        for cold in colds:
            if cold.interval.shifted(diff_t_min).passes_through_interval(interval):
                if cold not in n_c:
                    n_c.append(cold)

    # max demand and max supply for M-5
    max_demand: float = max(network.demands.values())
    max_supply: float = max(network.heats.values())

    # declaring model variables
    model_to_solve.q_ijk = Var(hots, colds, intervals, within=NonNegativeReals)
    model_to_solve.q_ijkl = Var(hots, intervals, colds, intervals, within=NonNegativeReals)
    model_to_solve.y_ij = Var(hots, colds, within=Binary)
    model_to_solve.residual_set = RangeSet(0, len(intervals))
    model_to_solve.residual_ik = Var(hots, model_to_solve.residual_set, within=NonNegativeReals)
    last_residual = len(intervals)

    # model objective
    def matches_min_rule(model):
        """
        objective function: minimize the number of matches between hot stream and cold stream, y_ij
        """
        if model_selected == "M2":
            # apply weight factor
            # w_ij = u_ij / LMTD
            cost_objective: float = 0
            t_hot: list[float] = []
            t_cold: list[float] = []
            for h in hots:
                for c in colds:
                    for t in intervals:
                        if p_ijk[(h, c, t)]:
                            t_hot.append(t.t_min)
                            t_hot.append(t.t_max)
                            t_cold.append(t.t_min - diff_t_min)
                            t_cold.append(t.t_max - diff_t_min)
                    if len(t_hot) == 0 or len(t_cold) == 0:
                        cost_objective += model.y_ij[h, c]
                    else:
                        cost_objective += model.y_ij[h, c] * u_ij[h, c] / log_mean_temperature_diff(max(t_hot), min(t_hot), min(t_cold), max(t_cold))
            return cost_objective
        else:
            return sum(model.y_ij[h, c] for h in hots for c in colds)
    model_to_solve.obj = Objective(rule=matches_min_rule)

    # zero residual constraint
    def zero_residual_rule(model, h, r):
        """
        constraint function: zero residual at top and bottom temperature interval
        """
        if (r == 0) or (r == last_residual):
            return model.residual_ik[h, r] == 0
        else:
            return Constraint.Skip
    model_to_solve.zero_residual_constraint = Constraint(hots, model_to_solve.residual_set, rule=zero_residual_rule)

    # heat conservation
    def heat_conservation_rule(model, h, t):
        """
        constraint function: heat conservation of each temperature interval
        the total heat entering must equal to heat exiting temperature interval
        """
        if model_selected == "M4":
            return Constraint.Skip
        else:
            interval_index = intervals.index(t) + 1  # the index of residual_k
            exiting_heat = sum(model.q_ijk[h, c, t] for c in colds) + model.residual_ik[h, interval_index]
            entering_heat = sigma[h, t] + model.residual_ik[h, interval_index - 1]
            return exiting_heat == entering_heat
    model_to_solve.heat_conservation_constraint = Constraint(hots, intervals, rule=heat_conservation_rule)

    # heat demand satisfaction
    def heat_demand_rule(model, j, k):
        """
        constraint function: heat demand of the cold stream
        """
        if model_selected == "M4":
            return delta[j, k] == sum(model.q_ijkl[i, l, j, k] for i in hots for l in intervals if intervals.index(l) <= intervals.index(k))
        else:
            return sum(model.q_ijk[h, j, k] for h in hots) == delta[j, k]
    model_to_solve.demand_satisfaction_constraint = Constraint(colds, intervals, rule=heat_demand_rule)

    def heat_supply_model4(model, i, k):
        if model_selected == "M4":
            return sigma[i, k] == sum(model.q_ijkl[i, k, j, l] for j in colds for l in intervals if intervals.index(l) >= intervals.index(k))
        else:
            return Constraint.Skip
    model_to_solve.big_m_constraint2 = Constraint(hots, intervals, rule=heat_supply_model4)

    # big-M restriction
    def big_matrix_rule(model, h, c):
        if model_selected in ["M3", "M4", "M5"]:
            return Constraint.Skip
        else:
            return sum(model.q_ijk[h, c, t] for t in intervals) <= u_ij[h, c] * model.y_ij[h, c]
    model_to_solve.big_m_constraint = Constraint(hots, colds, rule=big_matrix_rule)

    def big_matrix_rules1(model, h, c, s):
        if model_selected in ["M3", "M5"]:
            return model.q_ijk[h, c, s] <= u_ijk[h, c, s] * model.y_ij[h, c]
        else:
            return Constraint.Skip
    model_to_solve.big_m_constraint1 = Constraint(hots, colds, intervals, rule=big_matrix_rules1)

    def big_matrix_rules2(model, h, c, s, t):
        if model_selected == "M4":
            return model.q_ijkl[h, s, c, t] <= u_ijkl[h, s, c, t] * model.y_ij[h, c]
        else:
            return Constraint.Skip
    model_to_solve.big_m_constraint3 = Constraint(hots, colds, intervals, intervals, rule=big_matrix_rules2)

    def integer_cuts_h(model, i):
        if model_selected == "M5":
            return sum(model.y_ij[i, j] for j in colds) >= sum(sigma[i, k] for k in intervals) / max_demand
        else:
            return Constraint.Skip
    model_to_solve.integer_cuts_h = Constraint(hots, rule=integer_cuts_h)

    def integer_cuts_c(model, j):
        if model_selected == "M5":
            return sum(model.y_ij[i, j] for i in hots) >= sum(delta[j, k] for k in intervals) / max_supply
        else:
            return Constraint.Skip
    model_to_solve.integer_cuts_c = Constraint(colds, rule=integer_cuts_c)

    # def integer_cuts_y(model):
    #     if model_selected == "M5":
    #         return sum(model.y_ij[i, j] for i in hots for j in colds) <= len(n_h) + len(n_c) - 1
    #     else:
    #         return Constraint.Skip
    # model_to_solve.integer_cuts_y = Constraint(rule=integer_cuts_y)

    # define hot to cold matching permission
    model_to_solve.stream_exchange_permission = Constraint(hots, colds, rule=lambda m, h, c: m.y_ij[h, c] <= p_ij[h, c])

    # solving model
    s_time = time()
    solver: SolverFactory = SolverFactory("glpk")
    if log:
        results = solver.solve(model_to_solve, logfile="solver.log", tee=True)
    else:
        results = solver.solve(model_to_solve)
    sum_y = sum([value(model_to_solve.y_ij[h, c]) for h in hots for c in colds])
    print("HS: {}, CS: {}, TI: {}".format(len(hots), len(colds), len(intervals)))
    print("Objective: y = {}, in {} seconds".format(sum_y, round(time() - s_time, 6)))

    return results, model_to_solve


def print_matches_transshipment(network: Network, model: ConcreteModel) -> None:
    print('------- Matching Streams ------')
    for h in network.H:
        for c in network.C:
            try:
                if value(model.y_ij[h, c]) != 0:
                    if network.model == "M4":
                        print(f'{h.name} with {c.name} - q = {sum(value(model.q_ijkl[h, k, c, l]) for k in network.T for l in network.T):.2f}')
                    else:
                        print(f'{h.name} with {c.name} - q = {sum(value(model.q_ijk[h, c, t]) for t in network.T):.2f}')
            except KeyError:
                pass


def print_exchanger_details_transshipment(network: Network, model: ConcreteModel) -> None:
    print('------- Exchanger Details Transshipment -------')
    print(f"The solve model is {network.model}")
    hx_id: int = 1
    hxs: list = []
    diff_temp: float = network.diff_t_min
    for h in network.H:
        for c in network.C:
            try:
                if value(model.y_ij[h, c]) != 0:
                    exchanger_id = f'E{hx_id}'
                    hx_id += 1
                    hx_q: float = 0.0
                    t_h: list[float] = []
                    t_c: list[float] = []
                    for t in network.T:
                        if network.model == "M4":
                            q = sum(value(model.q_ijkl[h, t, c, k] for k in network.T))
                        else:
                            q = value(model.q_ijk[h, c, t])

                        if q > 0.0:
                            hx_q += q
                            if t.t_min not in t_h:
                                t_h.append(t.t_min)
                            if t.t_max not in t_h:
                                t_h.append(t.t_max)
                            t_h.sort(reverse=True)
                            hxs.append({'exchanger_id': exchanger_id, 'hot': h, 'cold': c, 't_h': t_h, 'q': hx_q})
            except KeyError:
                pass

    for hx in hxs:
        print(f'{hx['exchanger_id']} - q = {hx['q']}, HS={hx['hot'].name}, CS={hx['cold'].name}, T={hx['t_h']}')