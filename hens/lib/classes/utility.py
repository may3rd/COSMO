# Utility Class
# A utility in the problems of interest is defined by:
# 1. An inlet temperature Tin
# 2. An outlet temperature Tout
# 3. A unitary cost per unit of heat
from .processstream import ProcessStream


class Utility(ProcessStream):

    def __init__(self, name: str, t_in: float, t_out: float, cost: float) -> None:
        ProcessStream.__init__(self, name, t_in, t_out)
        self.cost: float = cost
