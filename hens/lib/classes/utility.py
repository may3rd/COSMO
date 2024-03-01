# Utility Class
# A utility in the problems of interest is defined by:
# 1. An inlet temperature Tin
# 2. An outlet temperature Tout
# 3. A unitary cost per unit of heat
from .process_stream import Process_Stream

class Utility(Process_Stream):


    def __init__(self, name: str, Tin: float, Tout: float, cost: float) -> None:
        Process_Stream.__init__(self, name, Tin, Tout)
        self.cost: float = cost
