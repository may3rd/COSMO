"""
Modified by Maetee L.
On: 2024
Contact: may3rd@gmail.com

Modification Notes:

Minimum_Utility_Problem
- add parameter for hot stream and cold stream heat exchange permit.
- add calculation and plotting for composite diagram and grand composite curve.
- add change_DTmin.
- add generate_from_csv and generate_from_file to be able to read heat exchange 
  permit.

Solvers
- add model in return result from transport and transshipment solvers.
"""

from .lib.classes.minimum_utility_problem import MinUtilityProblem
from .lib.classes.network import Network
from .lib.classes.processstream import ProcessStream
from .lib.classes.stream import Stream
from .lib.classes.temperatureinterval import TemperatureInterval
from .lib.classes.utility import Utility
from .lib.solvers.greedy_max_heat import greedy_heat, greedy_heat_2
from .lib.solvers.greedy_minmax_delta import greedy_min_delta
from .lib.solvers.min_utility_solver import solve_min_utility_instance
from .lib.solvers.transport_solver import solve_transport_model, solve_transport_model_greedy
from .lib.solvers.transshipment_solver import solve_transshipment_model, solve_transshipment_model_greedy

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


