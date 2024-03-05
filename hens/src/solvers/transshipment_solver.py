# Minimization of Matches Solver via Transshipment Model
from pyomo.environ import ConcreteModel, Var, NonNegativeReals, RangeSet, Objective, Constraint, SolverFactory, Binary
from time import time
from hens import Network, Stream, log_mean_temperature_diff


def solve_transshipment_model(network: Network,
                              greedy: bool = False,
                              weighted: bool = False,
                              model4flag: bool = False,
                              model5flag: bool = False):
    if model5flag:
        model4flag = False
        weighted = False
        if model4flag:
            weighted = False

    # declaring model
    model_to_solve: ConcreteModel = ConcreteModel(name="MIN_MATCHES_TRANSSHIPMENT")

    # declaring model inputs
    hots = network.H  # hot streams including utilities
    colds = network.C  # cold streams including utilities
    intervals = network.T  # temperature intervals
    p_ij = network.P  # stream exchange permission
    p_ijk = network.Pk  # stream exchange in interval permission
    diff_t_min = network.diff_t_min
    sigma = network.sigmas  # heat supply per hot stream per interval
    delta = network.deltas  # heat demand per cold stream per interval
    if not greedy:
        u_ij = network.U  # Big-M parameter
    else:
        u_ij = network.U_greedy
    u_ijk = network.u_ijk
    u_ijkl = network.u_ijkl
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
        if weighted:
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
                        pass
                    else:
                        cost_objective += model.y_ij[h, c] * u_ij[h, c] / log_mean_temperature_diff(max(t_hot),
                                                                                                    min(t_hot),
                                                                                                    min(t_cold),
                                                                                                    max(t_cold))
            return cost_objective
        else:
            return sum(model.y_ij[h, c] for h in hots for c in colds)

    model_to_solve.obj = Objective(rule=matches_min_rule)

    # heat conservation
    def heat_conservation_rule(model, h, t):
        """
        constraint function: heat conservation of each temperature interval
        the total heat entering must equal to heat exiting temperature interval
        """
        interval_index = intervals.index(t) + 1  # the index of residual_k
        exiting_heat = sum(model.q_ijk[h, c, t] for c in colds) + model.residual_ik[h, interval_index]
        entering_heat = sigma[h, t] + model.residual_ik[h, interval_index - 1]
        return exiting_heat == entering_heat

    model_to_solve.heat_conservation_constraint = Constraint(hots, intervals, rule=heat_conservation_rule)

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

    # heat demand satisfaction
    def heat_demand_rule(model, c, t):
        """
        constraint function: heat demand of the cold stream
        """
        return sum(model.q_ijk[h, c, t] for h in hots) == delta[c, t]

    model_to_solve.demand_satisfaction_constraint = Constraint(colds, intervals, rule=heat_demand_rule)

    # big-M restriction
    def big_matrix_rule(model, h, c):
        """
        constraint function:
        """
        if model4flag:
            return Constraint.Skip
        else:
            return sum(model.q_ijk[h, c, t] for t in intervals) <= u_ij[h, c] * model.y_ij[h, c]

    model_to_solve.big_m_constraint = Constraint(hots, colds, rule=big_matrix_rule)

    def big_matrix_rules2(model, h, c, s):
        if model4flag:
            return model.q_ijk[h, c, s] <= u_ijk[h, c, s] * model.y_ij[h, c]
        else:
            return Constraint.Skip

    model_to_solve.big_m_constraint2 = Constraint(hots, colds, intervals, rule=big_matrix_rules2)

    def big_matrix_rules3(model, h, c, s, t):
        if model5flag:
            return model.q_ijkl[h, s, c, t] <= u_ijkl[h, s, c, t] * model.y_ij[h, c]
        else:
            return Constraint.Skip

    model_to_solve.big_m_constraint3 = Constraint(hots, colds, intervals, intervals, rule=big_matrix_rules3)

    # define hot to cold matching permission
    model_to_solve.stream_exchange_permission = Constraint(hots, colds, rule=lambda m, h, c: m.y_ij[h, c] <= p_ij[h, c])

    # solving model
    s_time = time()
    solver = SolverFactory("glpk")
    results = solver.solve(model_to_solve, logfile="solver.log", tee=True)
    sum_y = sum([model_to_solve.y_ij[h, c].value for h in hots for c in colds])
    print("HS: {}, CS: {}, TI: {}".format(len(hots), len(colds), len(intervals)))
    print("Objective: y = {}, in {} seconds".format(sum_y, round(time() - s_time, 6)))

    return results, model_to_solve


def print_matches_transshipment(network: Network, model: ConcreteModel) -> None:
    print('------- Matching Streams ------')
    for h in network.H:
        for c in network.C:
            if model.y_ij[h, c].value != 0:
                print(f'{h.name} with {c.name}', end="")
                total_h = 0.0
                for t in network.T:
                    if model.q_ijk[h, c, t].value > 0.0:
                        total_h += model.q_ijk[h, c, t].value
                        pass
                print(f' - q = {total_h:.2f}')


def print_exchanger_details_transshipment(network: Network, model: ConcreteModel) -> None:
    print('------- Exchanger Details Transshipment -------')
    hx_id: int = 1
    hxs: list = []
    diff_temp: float = network.diff_t_min
    for h in network.H:
        for c in network.C:
            if model.y_ij[h, c].value != 0:
                exchanger_id = f'E{hx_id}'
                # print(exchanger_id, h, c)
                hx_id += 1
                hx_q: float = 0.0
                t_k: list[float] = []
                for t in network.T:
                    if model.q_ijk[h, c, t].value > 0.0:
                        # print(f'{t} - q = {model.q_ijk[h, c, t].value}')
                        hx_q += model.q_ijk[h, c, t].value
                        t_k.append(t.t_min)
                        t_k.append(t.t_max)
                t_k = list(set(t_k))
                t_k.sort()
                hxs.append({'exchanger_id': exchanger_id, 'hot': h, 'cold': c, 't_k': t_k, 'q': hx_q})

    for hx in hxs:
        print(f'{hx['exchanger_id']} - q = {hx['q']}, HS={hx['hot'].name}, CS={hx['cold'].name}, T_ik={max(hx['t_k'])}-{min(hx['t_k'])}')
