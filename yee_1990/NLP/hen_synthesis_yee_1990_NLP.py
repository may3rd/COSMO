import pyomo.environ as pyo
import pandas as pd
import numpy as np

# --- Utility Functions ---
def smooth_max(x, epsilon=1e-4):
    """Smooth approximation of max(0, x) for NLP differentiability.
    
    Args:
        x: Input value (Pyomo expression or float).
        epsilon: Smoothing parameter (default 1e-4).
    
    Returns:
        Smoothed max(0, x).
    """
    return (x + pyo.sqrt(x**2 + epsilon**2)) / 2

def LMTD_ijk(model, i, j, k):
    """Calculate LMTD for process stream match (i,j) in stage k using Chen approximation.
    
    Args:
        model: Pyomo model with t (temperatures) and other parameters.
        i: Hot stream index.
        j: Cold stream index.
        k: Stage index.
    
    Returns:
        LMTD value (K).
    """
    dt1 = smooth_max(model.t[i, k].value - model.t[j, k].value)
    dt2 = smooth_max(model.t[i, k + 1].value - model.t[j, k + 1].value)
    return (dt1 * dt2 * ((dt1 + dt2) / 2)) ** (1/3) + 1e-6  # Avoid division by zero

def LMTD_cu_i(model, i):
    """Calculate LMTD for cold utility with hot stream i.
    
    Args:
        model: Pyomo model with t, TOUT_CU, TIN_CU, TOUT.
        i: Hot stream index.
    
    Returns:
        LMTD value (K).
    """
    dt1 = smooth_max(model.t[i, model.NOK + 1].value - model.TOUT_CU)
    dt2 = smooth_max(model.TOUT[i] - model.TIN_CU)
    return (dt1 * dt2 * ((dt1 + dt2) / 2)) ** (1/3) + 1e-6

def LMTD_hu_j(model, j):
    """Calculate LMTD for hot utility with cold stream j.
    
    Args:
        model: Pyomo model with t, TIN_HU, TOUT_HU, TOUT.
        j: Cold stream index.
    
    Returns:
        LMTD value (K).
    """
    dt1 = smooth_max(model.TIN_HU - model.t[j, 1].value)
    dt2 = smooth_max(model.TOUT_HU - model.TOUT[j])
    return (dt1 * dt2 * ((dt1 + dt2) / 2)) ** (1/3) + 1e-6

# --- Data Import ---
def read_data(streams_file, utilities_file, constraints_file=None):
    """Read input data from CSV files.
    
    Args:
        streams_file (str): Path to streams CSV.
        utilities_file (str): Path to utilities CSV.
        constraints_file (str, optional): Path to constraints CSV.
    
    Returns:
        tuple: Streams DataFrame, Utilities DataFrame, Constraints DataFrame or None.
    """
    streams = pd.read_csv(streams_file)
    utilities = pd.read_csv(utilities_file)
    constraints = pd.read_csv(constraints_file) if constraints_file else None
    return streams, utilities, constraints

# --- Model Construction ---
def build_model(streams, utilities, constraints=None, CF=0, C=1, B=1, epsilon=1e-4):
    """Build the Pyomo NLP model based on Yee & Grossmann (1990) Part I.
    
    Args:
        streams (pd.DataFrame): Streams data.
        utilities (pd.DataFrame): Utilities data.
        constraints (pd.DataFrame, optional): Constraints data.
        CF (float): Fixed charge ($/unit), default 0 for Part I.
        C (float): Area cost coefficient ($/m² yr).
        B (float): Area cost exponent.
        epsilon (float): Small value for smoothing max operator.
    
    Returns:
        pyo.ConcreteModel: The NLP model.
    """
    model = pyo.ConcreteModel()

    # Sets
    HP = streams[streams['Type'] == 'HP']['Name'].tolist()
    model.HP = pyo.Set(initialize=HP, doc="Hot Process Streams")
    CP = streams[streams['Type'] == 'CP']['Name'].tolist()
    model.CP = pyo.Set(initialize=CP, doc="Cold Process Streams")
    NOK = max(len(HP), len(CP))  # Number of stages
    model.NOK = NOK
    ST = range(1, NOK + 1)
    model.ST = pyo.Set(initialize=ST, doc="Stages")
    temp_locations = range(1, NOK + 2)
    model.temp_locations = pyo.Set(initialize=temp_locations, doc="Temperature Locations")

    # Parameters
    TIN = {row['Name']: row['TIN'] for _, row in streams.iterrows()}
    TOUT = {row['Name']: row['TOUT'] for _, row in streams.iterrows()}
    F = {row['Name']: row['F_cp'] for _, row in streams.iterrows()}
    U = {row['Name']: row['U'] for _, row in streams.iterrows()}
    
    model.F = pyo.Param(model.HP | model.CP, initialize=F, doc="Heat capacity flow rates (kW/K)")
    model.U = pyo.Param(model.HP | model.CP, initialize=U, doc="Overall heat transfer coefficients (kW/m² K)")
    model.TIN = pyo.Param(model.HP | model.CP, initialize=TIN, doc="Inlet temperatures (K)")
    model.TOUT = pyo.Param(model.HP | model.CP, initialize=TOUT, doc="Outlet temperatures (K)")
    
    HU = utilities[utilities['Type'] == 'HU'].iloc[0]
    CU = utilities[utilities['Type'] == 'CU'].iloc[0]
    TIN_HU, TOUT_HU = HU['TIN'], HU['TOUT']
    TIN_CU, TOUT_CU = CU['TIN'], CU['TOUT']
    CHU, CCU = HU['CostPerUnit'], CU['CostPerUnit']
    
    model.HU = pyo.Set(initialize=[HU['Name']], doc="Hot Utility")
    model.CU = pyo.Set(initialize=[CU['Name']], doc="Cold Utility")
    model.TIN_HU = pyo.Param(initialize=TIN_HU, doc="Hot utility inlet temperature (K)")
    model.TOUT_HU = pyo.Param(initialize=TOUT_HU, doc="Hot utility outlet temperature (K)")
    model.TIN_CU = pyo.Param(initialize=TIN_CU, doc="Cold utility inlet temperature (K)")
    model.TOUT_CU = pyo.Param(initialize=TOUT_CU, doc="Cold utility outlet temperature (K)")
    model.CHU = pyo.Param(initialize=CHU, doc="Hot utility cost per unit ($/kW)")
    model.CCU = pyo.Param(initialize=CCU, doc="Cold utility cost per unit ($/kW)")

    # Variables
    model.q = pyo.Var(HP, CP, ST, domain=pyo.NonNegativeReals, doc="Heat exchanged (kW)")
    model.qcu = pyo.Var(HP, domain=pyo.NonNegativeReals, doc="Cold utility heat (kW)")
    model.qhu = pyo.Var(CP, domain=pyo.NonNegativeReals, doc="Hot utility heat (kW)")
    model.t = pyo.Var(HP + CP, temp_locations, domain=pyo.NonNegativeReals, doc="Temperature (K)")

    # Constraints
    # Overall Heat Balances (Eq. 1)
    def overall_balance_hot(model, i):
        return (TIN[i] - TOUT[i]) * F[i] == sum(model.q[i,j,k] for j in CP for k in ST) + model.qcu[i]
    model.overall_balance_hot = pyo.Constraint(HP, rule=overall_balance_hot)

    def overall_balance_cold(model, j):
        return (TOUT[j] - TIN[j]) * F[j] == sum(model.q[i,j,k] for i in HP for k in ST) + model.qhu[j]
    model.overall_balance_cold = pyo.Constraint(CP, rule=overall_balance_cold)

    # Stagewise Heat Balances (Eq. 2)
    def stage_balance_hot(model, i, k):
        return (model.t[i,k] - model.t[i,k+1]) * F[i] == sum(model.q[i,j,k] for j in CP)
    model.stage_balance_hot = pyo.Constraint(HP, ST, rule=stage_balance_hot)

    def stage_balance_cold(model, j, k):
        return (model.t[j,k] - model.t[j,k+1]) * F[j] == sum(model.q[i,j,k] for i in HP)
    model.stage_balance_cold = pyo.Constraint(CP, ST, rule=stage_balance_cold)

    # Inlet Temperature Assignments (Eq. 3)
    model.temp_assign_hot = pyo.Constraint(HP, rule=lambda model, i: model.t[i,1] == TIN[i])
    model.temp_assign_cold = pyo.Constraint(CP, rule=lambda model, j: model.t[j,NOK+1] == TIN[j])

    # Temperature Feasibility (Eq. 4)
    def temp_feas_hot(model, i, k):
        return model.t[i,k] >= model.t[i,k+1]
    model.temp_feas_hot = pyo.Constraint(HP, ST, rule=temp_feas_hot)

    def temp_feas_cold(model, j, k):
        return model.t[j,k] >= model.t[j,k+1]
    model.temp_feas_cold = pyo.Constraint(CP, ST, rule=temp_feas_cold)

    model.temp_out_hot = pyo.Constraint(HP, rule=lambda model, i: model.t[i,NOK+1] >= TOUT[i])
    model.temp_out_cold = pyo.Constraint(CP, rule=lambda model, j: model.t[j,1] <= TOUT[j])

    # Utility Loads (Eq. 5)
    model.util_cold = pyo.Constraint(HP, rule=lambda model, i: (model.t[i,NOK+1] - TOUT[i]) * F[i] == model.qcu[i])
    model.util_hot = pyo.Constraint(CP, rule=lambda model, j: (TOUT[j] - model.t[j,1]) * F[j] == model.qhu[j])

    # Objective Function with Smooth LMTD (Eq. 13a)
    def smooth_max(x):
        return (x + pyo.sqrt(x**2 + epsilon**2)) / 2

    def LMTD_ijk(model, i, j, k):
        dt1 = smooth_max(model.t[i,k] - model.t[j,k])
        dt2 = smooth_max(model.t[i,k+1] - model.t[j,k+1])
        return (dt1 * dt2 * ((dt1 + dt2) / 2))**(1/3) + 1e-6

    def area_ijk(model, i, j, k):
        U_ij = min(U[i], U[j])  # Simplified U_ij assumption
        return model.q[i,j,k] / (U_ij * LMTD_ijk(model, i,j,k))

    def LMTD_cu_i(model, i):
        dt1 = smooth_max(model.t[i,NOK+1] - TOUT_CU)
        dt2 = smooth_max(TOUT[i] - TIN_CU)
        return (dt1 * dt2 * ((dt1 + dt2) / 2))**(1/3) + 1e-6

    def area_cu_i(model, i):
        return model.qcu[i] / (U[i] * LMTD_cu_i(model, i))

    def LMTD_hu_j(model, j):
        dt1 = smooth_max(TIN_HU - model.t[j,1])
        dt2 = smooth_max(TOUT_HU - TOUT[j])
        return (dt1 * dt2 * ((dt1 + dt2) / 2))**(1/3) + 1e-6

    def area_hu_j(model, j):
        return model.qhu[j] / (U[j] * LMTD_hu_j(model, j))

    def total_cost(model):
        utility_cost = CCU * sum(model.qcu[i] for i in HP) + CHU * sum(model.qhu[j] for j in CP)
        area_cost = sum(C * area_ijk(model, i,j,k)*B for i in HP for j in CP for k in ST) + \
                    sum(C * area_cu_i(model, i)*B for i in HP) + \
                    sum(C * area_hu_j(model, j)*B for j in CP)
        return utility_cost + area_cost
    model.obj = pyo.Objective(rule=total_cost, sense=pyo.minimize)

    return model

# --- Solver Interface ---
def solve_model(model):
    """Solve the NLP model using IPOPT.
    
    Args:
        model (pyo.ConcreteModel): The Pyomo model.
    
    Returns:
        dict: Solver results.
    """
    solver = pyo.SolverFactory('ipopt')
    results = solver.solve(model, tee=True)
    return results

# --- Results Export ---
def export_reports(model, output_path):
    """Export optimization results to CSV.
    
    Args:
        model (pyo.ConcreteModel): Solved Pyomo model.
        output_path (str): Path to output CSV.
    """
        
    data = []
    for i in model.HP:
        for j in model.CP:
            for k in model.ST:
                q_val = model.q[i, j, k].value or 0  # Handle None values
                if q_val > 1e-6:
                    U_ij = min(model.U[i], model.U[j])
                    lmtd = LMTD_ijk(model, i, j, k)
                    area = q_val / (U_ij * (lmtd + 1e-6))
                    data.append([i, j, k, q_val, area, model.t[i, k].value or 0, model.t[j, k].value or 0])
        qcu_val = model.qcu[i].value or 0
        if qcu_val > 1e-6:
            lmtd_cu = LMTD_cu_i(model, i)
            area_cu = qcu_val / (model.U[i] * (lmtd_cu + 1e-6))
            data.append([i, 'CU', '-', qcu_val, area_cu, model.t[i, model.NOK + 1].value or 0, model.TOUT_CU.value])
    for j in model.CP:
        qhu_val = model.qhu[j].value or 0
        if qhu_val > 1e-6:
            lmtd_hu = LMTD_hu_j(model, j)
            area_hu = qhu_val / (model.U[j] * (lmtd_hu + 1e-6))
            data.append(['HU', j, '-', qhu_val, area_hu, model.TIN_HU.value, model.t[j, 1].value or 0])

    df = pd.DataFrame(data, columns=['HotStream', 'ColdStream', 'Stage', 'HeatLoad', 'Area', 'TempHot', 'TempCold'])
    df.to_csv(output_path, index=False)

# --- Main Script ---
if __name__ == "__main__":
    streams, utilities, constraints = read_data('yee_1990/NLP/streams.csv', 'yee_1990/NLP/utilities.csv')
    model = build_model(streams, utilities, constraints, CF=0, C=200, B=0.6)  # Example costs
    results = solve_model(model)
    export_reports(model, 'yee_1990/NLP/results.csv')
    print("Optimization complete. Results saved to 'results.csv'.")