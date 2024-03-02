# Temperature Interval Class
# Abstracts the idea of a temperature interval 
# going from T1 to T2

from typing import Any


class TemperatureInterval:

    def __init__(self) -> None:
        self.Tmax: float = 0
        self.Tmin: float = 0
        self.DT: float = 0

    def __init__(self, T1: float, T2: float) -> None:
        self.Tmax: float = max(T1, T2)
        self.Tmin: float = min(T1, T2)
        self.DT: float = self.Tmax - self.Tmin

    def __str__(self) -> str:
        return "[{}, {}]".format(self.Tmax, self.Tmin)

    def __repr__(self) -> str:
        return self.__str__()

    def passes_through_interval(self, other: Any) -> bool:
        """
        This method checks if self temperature 
        interval passes through other temperature
        interval. 
        Returns True if it does.
        """
        # self interval is to the left of other interval
        if self.Tmin >= other.Tmax:
            return False
        
        # self interval is to the right of other interval
        if self.Tmax <= other.Tmin:
            return False

        # otherwise it is contained
        return True

    def shifted(self, shift) -> Any:
        return TemperatureInterval(self.Tmax + shift, self.Tmin + shift)

    @staticmethod
    def common_interval(interval_1, interval_2) -> Any:

        assert interval_1.passes_through_interval(interval_2), "Intervals do not have common ground."

        t_max = min(interval_1.Tmax, interval_2.Tmax)
        t_min = max(interval_1.Tmin, interval_2.Tmin)

        return TemperatureInterval(t_max, t_min)
