# Stream Class
# A stream in the problems of interest is defined by:
# 1. An inlet temperature Tin
# 2. An outlet temperature Tout
# 3. A flow rate - heat capacity product FCp
from .processstream import ProcessStream


class Stream(ProcessStream):

    def __init__(self):
        ProcessStream.__init__(self)
        pass

    def __init__(self, name: str, t_in: float, t_out: float, f_cp: float) -> None:
        ProcessStream.__init__(self, name, t_in, t_out)
        self.FCp: float = f_cp
        self.heat: float = abs((t_out - t_in) * f_cp)
