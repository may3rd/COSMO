"""
Modified by Maetee L.
On: 2024
Contact: may3rd@gmail.com

Modification Notes:

Minimum_Utility_Problem
- add parameter for hot stream and cold stream heat exchange permit.
- add calculation and plotting for composite diagram and grand composite curve.
- add change_diff_t_min.
- add generate_from_csv and generate_from_file to be able to read heat exchange 
  permit.

Solvers
- add model in return result from transport and transshipment solvers.
"""

from .src.classes.minimum_utility_problem import MinUtilityProblem
from .src.classes.network import Network
from .src.classes.processstream import ProcessStream
from .src.classes.stream import Stream
from .src.classes.temperatureinterval import TemperatureInterval
from .src.classes.utility import Utility
from .src.solvers.greedy_max_heat import greedy_heat, greedy_heat_2
from .src.solvers.greedy_minmax_delta import greedy_min_delta
from .src.solvers.min_utility_solver import solve_min_utility_instance
from .src.solvers.transport_solver import solve_transport_model, solve_transport_model_greedy
from .src.solvers.transshipment_solver import solve_transshipment_model, solve_transshipment_model_greedy

__all__ = ['MinUtilityProblem',
           'Network',
           'ProcessStream',
           'Stream',
           'TemperatureInterval',
           'Utility',
           'greedy_heat', 'greedy_heat_2',
           'greedy_min_delta',
           'solve_min_utility_instance',
           'solve_transport_model', 'solve_transport_model_greedy',
           'solve_transshipment_model', 'solve_transshipment_model_greedy']
