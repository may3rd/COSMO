# Network Class
# This class abstacts the necessary items for a 
# Min Number of Matches Problem. It provides:
# 1. A set of hot streams (hot utilities included)
# 2. A set of cold streams (cold utilities included)
# 3. A set of temperature intevals 
# 4. A big-M parameter Ui,j that bounds the heat exchanged
#    between a hot stream i and a cold stream j
# 5. A dictionary with info of heat supply for each hot stream 
#    at each temperature interval
# 6. A dictionary with info of heat demand for each cold stream 
#    at each temperature interval
from .process_stream import Process_Stream
from .temperature_interval import Temperature_Interval
from .stream import Stream
from .utility import Utility
from .minimum_utility_problem import Min_Utility_Problem
from ..solvers.greedy_max_heat import greedy_heat
from typing import Any
import typing

class Network:


    def __init__(self, 
                 min_utility_instance: Min_Utility_Problem, 
                 utility_sigmas: typing.Dict[Stream, typing.Dict[Temperature_Interval, float]], 
                 utility_deltas: typing.Dict[Stream, typing.Dict[Temperature_Interval, float]]) -> None:
        self.H: list[Stream] = min_utility_instance.HS + min_utility_instance.HU
        self.C: list[Stream] = min_utility_instance.CS + min_utility_instance.CU
        self.T: list[Temperature_Interval] = min_utility_instance.intervals
        self.P = min_utility_instance.accepted_h_c
        self.sigmas: typing.Dict[Stream, typing.Dict[Temperature_Interval, float]] = min_utility_instance.sigmas
        self.deltas: typing.Dict[Stream, typing.Dict[Temperature_Interval, float]] = min_utility_instance.deltas
        self.heats: dict[Stream, float] = {}   # hi
        self.demands: dict[Stream, float] = {} # cj
        self.U: dict[(Any, Any), float] = {}
        self.U_greedy: dict[(Any, Any), float] = {}
        self.__update_sigmas(utility_sigmas)
        self.__update_deltas(utility_deltas)
        self.__init_heats()
        self.__init_demands()
        self.__init_U()
        self.__init_U_greedy()


    def __update_sigmas(self, new_sigmas: typing.Dict[Stream, typing.Dict[Temperature_Interval, float]]) -> None:
        for key in new_sigmas.keys():
            self.sigmas[key] = new_sigmas[key]

    
    def __update_deltas(self, new_deltas: typing.Dict[Stream, typing.Dict[Temperature_Interval, float]]) -> None:
        for key in new_deltas.keys():
            self.deltas[key] = new_deltas[key]


    def __init_heats(self) -> None:
        for hot_stream in self.H:
            stream_heat = 0
            for interval in self.T:
                stream_heat += self.sigmas[(hot_stream, interval)]
            self.heats[hot_stream] = stream_heat


    def __init_demands(self) -> None:
        for cold_stream in self.C:
            stream_demand = 0
            for interval in self.T:
                stream_demand += self.deltas[cold_stream, interval]
            self.demands[cold_stream] = stream_demand


    def __init_U(self) -> None:
        """
        Computes Uij as min{hi, cj}
        Where hi is the total heat supply of hot stream i
        and ci is the total heat demmand of cold stream j
        """
        for hot_stream in self.H:
            for cold_stream in self.C:
                self.U[(hot_stream, cold_stream)] = min(self.heats[hot_stream], self.demands[cold_stream])
                

    def __init_U_greedy(self) -> None:
        for hot_stream in self.H:
            for cold_stream in self.C:
                self.U_greedy[(hot_stream, cold_stream)] = greedy_heat(self.T, hot_stream, cold_stream, self.sigmas, self.deltas)[0]
                

    def __str__(self) -> str:
        return "H: {} \nC: {}".format(len(self.H), len(self.C))


    def __repr__(self) -> str:
        return self.__str__()


    def print_heats(self):
        for hot_stream in self.H:
            print(f'{hot_stream.name} - {self.heats[hot_stream]:.2f}')

    
    def print_demands(self):
        for cold_stream in self.C:
            print(f'{cold_stream.name} - {self.demands[cold_stream]:.2f}')