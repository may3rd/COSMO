# Process Stream Class
# A process stream in the problems of interest is defined by:
# 1. An inlet temperature Tin
# 2. An outlet temperature Tout
from .temperature_interval import Temperature_Interval

class Process_Stream:

    # Static Variable
    hot_stream_id: int = 0
    cold_stream_id: int = 0


    def __init__(self, name: str, Tin: float, Tout: float) -> None:
        self.name: str = name
        self.Tin: float = Tin
        self.Tout: float = Tout
        self.is_hot: bool = Tin > Tout
        self.interval: Temperature_Interval = Temperature_Interval(Tin, Tout)
        self.__set_id()

    
    def __set_id(self) -> None:
        if self.is_hot:
            self.id: str = "H{}".format(Process_Stream.hot_stream_id)
            Process_Stream.hot_stream_id += 1
        else:
            self.id: str = "C{}".format(Process_Stream.cold_stream_id)
            Process_Stream.cold_stream_id += 1


    def __str__(self) -> str:
        return self.id

    
    def __repr__(self) -> str:
        return self.id
