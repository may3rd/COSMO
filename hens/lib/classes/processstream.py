# Process Stream Class
# A process stream in the problems of interest is defined by:
# 1. An inlet temperature Tin
# 2. An outlet temperature Tout
from .temperatureinterval import TemperatureInterval


class ProcessStream:

    # Static Variable
    hot_stream_id: int = 0
    cold_stream_id: int = 0

    def __init__(self):
        self.name: str = "ProcessStream"
        self.Tin: float = 0.0
        self.Tout: float = 0.0
        self.is_hot: bool = False
        self.interval: TemperatureInterval = TemperatureInterval()
        pass

    def __init__(self, name: str, t_in: float, t_out: float) -> None:
        self.name: str = name
        self.Tin: float = t_in
        self.Tout: float = t_out
        self.is_hot: bool = t_in > t_out
        self.interval: TemperatureInterval = TemperatureInterval(t_in, t_out)
        self.__set_id()

    def __set_id(self) -> None:
        if self.is_hot:
            self.id: str = "H{}".format(ProcessStream.hot_stream_id)
            ProcessStream.hot_stream_id += 1
        else:
            self.id: str = "C{}".format(ProcessStream.cold_stream_id)
            ProcessStream.cold_stream_id += 1

    def __str__(self) -> str:
        return self.id

    def __repr__(self) -> str:
        return self.id
