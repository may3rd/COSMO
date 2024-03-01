# Minimum Utility Problem Class
# It encapsulates all the necessary elements of a minimum utility cost problem
# This class is defined by:
# 1. A set of strems
# 3. A set of utilities
# 5. A minimum aproach heat
#
# -----------------------------------------------------------------
# Modified by Maetee L. in 2024
#
#from .process_stream import Process_Stream
from .temperature_interval import Temperature_Interval
from .stream import Stream
from .utility import Utility
import typing
from typing import Any
import matplotlib.pyplot as plt
import csv
import numpy as np

class Min_Utility_Problem:
    """
    Basic class to contain the pinch analysis problem, includes hot stream, cold
    stream, hot utility, cold utility, minimum temperature difference, heat supply
    by hot stream, heat demanded by cold stream, etc.
    """

    def __init__(self, streams: list[Stream], utilities: list[Stream], DTmin: float) -> None:
        self.HS: list[Stream] = []
        self.CS: list[Stream] = []
        self.HU: list[Stream] = []
        self.CU: list[Stream] = []
        self.temperatures: list[float] = []
        self.intervals: list[Temperature_Interval] = []
        self.sigmas: typing.Dict[(Any, Any), float] = {}
        self.deltas: typing.Dict[(Any, Any), float] = {}
        self.accepted_hu_sigmas: typing.Dict[(Any, Any), bool] = {}
        self.accepted_cu_deltas: typing.Dict[(Any, Any), bool] = {}
        self.DTmin: float = DTmin

        # ---------------------------------------------------------
        # appended by Maetee to display composite curve
        # ---------------------------------------------------------
        self.problem_table: dict[Temperature_Interval, float] = {}
        self.hot_composite_h: list[float] = []
        self.hot_composite_t: list[float] = []
        self.cold_composite_h: list[float] = []
        self.cold_composite_t: list[float] = []
        self.grand_composite_h: list[float] = []
        self.grand_composite_t: list[float] = []
        self.unfeasible_heat_cascade = []
        self.heat_cascade = []
        self.demanded_hot_utility: float = 0.0
        self.demanded_cold_utility: float = 0.0
        self.pinch_temperature: float = 0.0

        # heat exchanger match between hot stream h and cold stream c is permitted
        self.accepted_h_c: dict[(Stream, Stream), bool] = {}
        # ---------------------------------------------------------
        # Original methods
        # ---------------------------------------------------------
        self.__init_streams(streams)
        self.__init_utilities(utilities)
        self.__init_temperatures(streams, utilities)
        self.__init_heats()
        self.__init_accepted_u_intervals()
        # ---------------------------------------------------------
        # Maetee's customize methods
        # ---------------------------------------------------------
        self.__init_accepted_h_c()
        self.__init_heat_cascade()
        self.__init_composite_diagram()
        self.__init_grand_composite_curve()


    def __init_streams(self, streams: list[Stream]) -> None:
        """
        This method helps in the initialization of the streams.
        It receives a set of streams and initializes the hot 
        and cold streams lists.
        """
        for stream in streams:
            if stream.is_hot:
                self.HS.append(stream)
            else:
                self.CS.append(stream)


    def __init_utilities(self, utilities: list[Stream]) -> None:
        """
        This method helps in the initialization of the utilities.
        It receives a set of streams and initializes the hot and 
        cold streams lists.
        """
        for utility in utilities:
            if utility.is_hot:
                self.HU.append(utility)
            else:
                self.CU.append(utility)

    
    def __init_temperatures(self, streams: list[Stream], utilities: list[Stream]) -> None:
        """
        This method intialized a list of unique temperature
        values affected by DTmin.
        """
        process_streams: list[Stream] = streams + utilities
        for process_stream in process_streams:
            Tin = process_stream.Tin
            if not process_stream.is_hot:
                Tin += self.DTmin
            if Tin not in self.temperatures:
                self.temperatures.append(Tin)
            
        self.temperatures.sort(reverse = True)

        # creating intervals
        for i in range(len(self.temperatures) - 1):
            new_interval = Temperature_Interval(self.temperatures[i], self.temperatures[i + 1])
            self.intervals.append(new_interval)


    def __init_heats(self) -> None:
        for interval in self.intervals:
            total_h_interval: float = 0.0

            # initializing sigmas
            for hot_stream in self.HS:
                if hot_stream.interval.passes_through_interval(interval):
                    self.sigmas[(hot_stream, interval)] = Temperature_Interval.common_interval(interval, hot_stream.interval).DT * hot_stream.FCp
                else:
                    self.sigmas[(hot_stream, interval)] = 0

                total_h_interval += self.sigmas[(hot_stream, interval)]

            # initializing deltas. This one is tricky because intervals were constructed 
            # by adding DTmin to each CS interval, but CS intervals were nos modified    
            for cold_stream in self.CS:
                if cold_stream.interval.shifted(self.DTmin).passes_through_interval(interval):
                    self.deltas[(cold_stream, interval)] = Temperature_Interval.common_interval(interval, cold_stream.interval.shifted(self.DTmin)).DT * cold_stream.FCp
                else:
                    self.deltas[(cold_stream, interval)] = 0

                total_h_interval -= self.deltas[(cold_stream, interval)]

            # initialzing problem table
            self.problem_table[interval] = total_h_interval

    def __init_accepted_u_intervals(self) -> None:
        for interval in self.intervals:
            
            # accepted sigmas
            for hot_utility in self.HU:
                if hot_utility.interval.passes_through_interval(interval):
                    self.accepted_hu_sigmas[(hot_utility, interval)] = True
                else:
                    self.accepted_hu_sigmas[(hot_utility, interval)] = False

            # accepted deltas
            for cold_utility in self.CU:
                if cold_utility.interval.shifted(self.DTmin).passes_through_interval(interval):
                    self.accepted_cu_deltas[(cold_utility, interval)] = True
                else:
                    self.accepted_cu_deltas[(cold_utility, interval)] = False


    def __init_accepted_h_c(self):
        for hot_stream in self.HS + self.HU:
            for cold_stream in self.CS + self.CU:
                self.accepted_h_c[(hot_stream, cold_stream)] = 1

        # not transfer hot utility to cold utility
        for H in self.HU:
            for C in self.CU:
                self.accepted_h_c[(H, C)] = 0

    
    def __init_heat_cascade(self) -> None:

        exitH = 0.0
        lowest_exitH = 0.0

        i: int = 0
        pinch_interval: int = i

        for interval in self.intervals:
            row = {}
            row['deltaH'] = self.problem_table[interval]

            exitH += row['deltaH']
            row['exitH'] = exitH

            if exitH < lowest_exitH:
                lowest_exitH = exitH
                pinch_interval = i

            self.unfeasible_heat_cascade.append(row)
            i += 1
        
        self.demanded_hot_utility = -lowest_exitH
        exitH = self.demanded_hot_utility

        for interval in self.intervals:
            row = {}
            row['deltaH'] = self.problem_table[interval]

            exitH += row['deltaH']
            row['exitH'] = exitH

            self.heat_cascade.append(row)

        self.demanded_cold_utility = exitH
        self.pinch_temperature = self.intervals[pinch_interval].Tmin

        return


    def __init_composite_diagram(self) -> None:
        # need tempartures and enthalpies in ascending order
        tempuratures = self.temperatures[::-1]
        delta_h_hot = []
        delta_h_cold = []

        # find enthalpies change for hot and cold composite streams
        for interval in self.intervals[::-1]:
            totalH = 0.0
            for H in self.HS:
                totalH += self.sigmas[(H, interval)]

            delta_h_hot.append(totalH)

            totalH = 0.0
            for C in self.CS:
                totalH += self.deltas[(C, interval)]

            delta_h_cold.append(totalH)

        total_h_hot = 0.0
        self.hot_composite_h.append(total_h_hot)
        self.hot_composite_t.append(tempuratures[0])
        for i in range(1, len(tempuratures)):
            if delta_h_hot[i - 1] != 0:
                total_h_hot += delta_h_hot[i - 1]
                self.hot_composite_h.append(total_h_hot)
                self.hot_composite_t.append(tempuratures[i])

        total_h_cold = self.demanded_cold_utility
        self.cold_composite_h.append(total_h_cold)
        self.cold_composite_t.append(tempuratures[0])
        for i in range(1, len(tempuratures)):
            if delta_h_cold[i - 1] != 0:
                total_h_cold += delta_h_cold[i - 1]
                self.cold_composite_h.append(total_h_cold)
                self.cold_composite_t.append(tempuratures[i])

        return


    def __init_grand_composite_curve(self) -> None:
        self.grand_composite_h.append(self.demanded_hot_utility)
        self.grand_composite_t.append(self.temperatures[0])

        for i in range(1, len(self.temperatures)):
            self.grand_composite_h.append(self.heat_cascade[i - 1]['exitH'])
            self.grand_composite_t.append(self.temperatures[i])

        return
    

    def change_DTmin(self, DTmin: float) -> None:
        self.DTmin = DTmin
        
        # clear all related parameters
        self.temperatures: list[float] = []
        self.intervals: list[Temperature_Interval] = []
        self.sigmas: typing.Dict[(Any, Any), float] = {}
        self.deltas: typing.Dict[(Any, Any), float] = {}
        self.accepted_hu_sigmas: typing.Dict[(Any, Any), bool] = {}
        self.accepted_cu_deltas: typing.Dict[(Any, Any), bool] = {}
        self.problem_table: dict[Temperature_Interval, float] = {}
        self.hot_composite_h: list[float] = []
        self.hot_composite_t: list[float] = []
        self.cold_composite_h: list[float] = []
        self.cold_composite_t: list[float] = []
        self.grand_composite_h: list[float] = []
        self.grand_composite_t: list[float] = []
        self.unfeasible_heat_cascade = []
        self.heat_cascade = []
        self.demanded_hot_utility: float = 0.0
        self.demanded_cold_utility: float = 0.0
        self.pinch_temperature: float = 0.0

        self.__init_temperatures(self.HS + self.CS, self.HU + self.CU)
        self.__init_heats()
        self.__init_accepted_u_intervals()
        self.__init_heat_cascade()
        self.__init_composite_diagram()
        self.__init_grand_composite_curve()
    

    def plot_composite_diagram(self, save: bool = False, fname: str = 'composite.svg') -> None:
        fig = plt.figure()
        plt.plot(self.hot_composite_h, self.hot_composite_t, 'tab:red')
        plt.plot(self.cold_composite_h, self.cold_composite_t, 'tab:blue')

        plt.plot(self.hot_composite_h, self.hot_composite_t, 'ro')
        plt.plot(self.cold_composite_h, self.cold_composite_t, 'bo')

        # find left point of hot composite curve
        for i in range(len(self.hot_composite_h)):
            if self.hot_composite_h[i] >= self.cold_composite_h[0]:
                left_hot_h_index= i
                break

        # find right point of cold composite curve
        for i in range(len(self.cold_composite_h) - 1, -1, -1):
            if self.cold_composite_h[i] <= self.hot_composite_h[-1]:
                right_cold_h_index = i
                break

        # calculate temperature according it left and right points
        left_hot_h = []
        left_hot_t = []
        if left_hot_h_index == 0:
            left_hot_h.append(self.hot_composite_h[i])
            left_hot_t.append(self.hot_composite_t[i])
        else:
            for i in range(left_hot_h_index):
                left_hot_h.append(self.hot_composite_h[i])
                left_hot_t.append(self.hot_composite_t[i])
            
            i = left_hot_h_index
            m = (self.hot_composite_t[i] - self.hot_composite_t[i - 1]) / (self.hot_composite_h[i] - self.hot_composite_h[i - 1])
            left_hot_h.append(self.cold_composite_h[0])
            left_hot_t.append(self.hot_composite_t[i - 1] + (self.cold_composite_h[0] - self.hot_composite_h[i - 1]) * m)
        
        right_hot_h = []
        
        if left_hot_h_index == 0:
            right_cold_h = self.hot_composite_h
        else:
            right_hot_h.append(left_hot_h[-1])
            for r in self.hot_composite_h[left_hot_h_index:]:
                right_hot_h.append(r)

        right_cold_h = []
        right_cold_t = []
        if right_cold_h_index == len(self.cold_composite_h) - 1:
            right_cold_h.append(self.cold_composite_h[-1])
            right_cold_t.append(self.cold_composite_t[-1])
        else:
            for i in range(len(self.cold_composite_h) - 1, right_cold_h_index, -1):
                right_cold_h.append(self.cold_composite_h[i])
                right_cold_t.append(self.cold_composite_t[i])
            
            i = right_cold_h_index
            m = (self.cold_composite_t[i + 1] - self.cold_composite_t[i]) / (self.cold_composite_h[i + 1] - self.cold_composite_h[i])
            right_cold_h.append(self.hot_composite_h[-1])
            right_cold_t.append(self.cold_composite_t[i] + (self.hot_composite_h[-1] - self.cold_composite_h[i]) * m)

        right_cold_h.reverse()
        right_cold_t.reverse()

        left_cold_h = []
        for l in self.cold_composite_h[:right_cold_h_index]:
            left_cold_h.append(l)
        if right_cold_h_index < len(self.cold_composite_h) - 1:
            left_cold_h.append(right_cold_h[0])

        combined_h = sorted(list(set(right_hot_h) | set(left_cold_h)))
        hot_t = np.interp(combined_h, self.hot_composite_h, self.hot_composite_t)
        cold_t = np.interp(combined_h, self.cold_composite_h, self.cold_composite_t)

        plt.fill_between(combined_h, hot_t, cold_t, color = 'g', alpha = 0.3)
        plt.fill_between(left_hot_h, 0, left_hot_t, color = 'b', alpha = 0.5)
        plt.fill_between(right_cold_h, 0, right_cold_t, color = 'r', alpha = 0.5)

        #max_cold_h = max(self.cold_composite_h)
        #plt.fill_between([0, self.demanded_cold_utility], 0, self.temperatures[0], color = 'b', alpha = 0.5)
        #plt.fill_between([max_cold_h - self.demanded_hot_utility, max_cold_h], 0, self.temperatures[0], color = 'r', alpha = 0.5)

        try:
            pinch_index = self.cold_composite_t.index(self.pinch_temperature)
            pinch_h = self.cold_composite_h[pinch_index]
            plt.plot([pinch_h, pinch_h], [self.temperatures[0], self.temperatures[-1]], ':')
        except ValueError:
            pass

        plt.grid(True)
        plt.title('Temperature-Enthalpy Composite Diagram')
        plt.xlabel('Enthalpy H')
        plt.ylabel('Temperature')

        if save:
            print(f'Save composite diagram to {fname}')
            plt.savefig(fname)
        else:
            plt.show()

        return
    
    def plot_grand_composite_curve(self, save: bool = False, fname: str = 'grand_composite.png') -> None:
        fig = plt.figure()
        plt.plot(self.grand_composite_h, self.grand_composite_t, 'tab:blue')
        plt.plot(self.grand_composite_h, self.grand_composite_t, 'bo')

        plt.fill_between([0, self.grand_composite_h[0]], 0, self.temperatures[0], color='r', alpha = 0.5)
        plt.fill_between([0, self.grand_composite_h[-1]], 0, self.temperatures[-1], color = 'b', alpha = 0.5)

        plt.plot([0, self.grand_composite_h[-1]], [self.pinch_temperature, self.pinch_temperature], ':')

        plt.grid(True)
        plt.title('Grand Composite Curve')
        plt.xlabel('Net Enthalpy Change')
        plt.ylabel('Temperature')

        if save:
            print(f'Same grand composite curve to {fname}')
            plt.savefig(fname)
        else:
            plt.show()

        return


    def __str__(self) -> str:
        return "HS: {} \nCS: {}\nHU: {}\nCU: {}\nDTmin: {}".format(
            len(self.HS), len(self.CS), 
            len(self.HU), len(self.CU), 
            self.DTmin)

    
    def __repr__(self) -> str:
        return self.__str__()


    def print_temperature_interval(self) -> None:
        for T in self.intervals:
            print(f'{T}, {self.problem_table[T]:.2f}')


    def print_minimum_demanded_utility(self) -> None:
        print(f'Pinch temperature is {self.pinch_temperature:.2f}')
        print(f'Demanded Hot Utility is {self.demanded_hot_utility:.2f}')
        print(f'Demanded Cold Utility is {self.demanded_cold_utility:.2f}')


    def get_hot_stream(self, name: str) -> Stream:
        for h in self.HS:
            if h.name == name:
                return h
        return None
    
    
    def get_cold_stream(self, name: str) -> Stream:
        for c in self.CS:
            if c.name == name:
                return c
        return None

    
    @staticmethod
    def generate_from_data(data_id: str) -> Any:
        
        path = 'data/original_problems/' + data_id + '.dat'
        f = open(path, 'r')
        lines = f.readlines()
        f.close()
        
        elements = [line.split() for line in lines]
        DTmin = float(elements[3][1])
        elements = elements[4:]
        streams = [Stream(name = str(e[0]), Tin = float(e[1]), Tout = float(e[2]), FCp = float(e[3])) for e in elements if e[0][1]!='U']
        utilities = [Utility(name = str(e[0]), Tin = float(e[1]),Tout = float(e[2]), cost = float(e[3])) for e in elements if e[0][1]=='U']

        return Min_Utility_Problem(streams, utilities, DTmin)


    @staticmethod
    def generate_from_file(filename: str) -> Any:
        
        f = open(filename, 'r')
        lines = f.readlines()
        f.close()
        
        elements = [line.split() for line in lines]

        if len(elements[0]) == 2: # first line is number of stream and number of utility
            NS = int(elements[0][0])
            NU = int(elements[0][1])

            DTmin = float(elements[1][1])
            elements_streams = elements[2:NS + 2]
            elements_utilities = elements[NS + 2:NU + NS + 2]
            streams = [Stream(name = str(e[0]), Tin = float(e[1]), Tout = float(e[2]), FCp = float(e[3])) for e in elements_streams]
            utilities = [Utility(name = str(e[0]), Tin = float(e[1]),Tout = float(e[2]), cost = float(e[3])) for e in elements_utilities]
            
            minup = Min_Utility_Problem(streams, utilities, DTmin)

            if NS + NU + 1 < len(elements):
                elements_permit = elements[NS + NU + 2:]
                if len(elements_permit) > 0:
                    for e in elements_permit:
                        hot_stream = minup.get_hot_stream(e[0])
                        cold_stream = minup.get_cold_stream(e[1])
                        minup.accepted_h_c[(hot_stream, cold_stream)] = int(e[2])
        else:
            DTmin = float(elements[3][1])
            elements = elements[4:]
            streams = [Stream(name = str(e[0]), Tin = float(e[1]), Tout = float(e[2]), FCp = float(e[3])) for e in elements if e[0][1]!='U']
            utilities = [Utility(name = str(e[0]), Tin = float(e[1]),Tout = float(e[2]), cost = float(e[3])) for e in elements if e[0][1]=='U']
            minup = Min_Utility_Problem(streams, utilities, DTmin)

        return minup
    
    @staticmethod
    def generate_from_csv(filename: str) -> Any:

        elements = []
        # open the csv file in read mode
        with open(filename, 'r') as csvfile:
            # create a CSV reader object
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                trimmed_row = [element.strip() for element in row]
                elements.append(trimmed_row)

        if len(elements[0]) == 2: # first line is number of stream and number of utility
            NS = int(elements[0][0])
            NU = int(elements[0][1])

            DTmin = float(elements[1][1])
            elements_streams = elements[2:NS + 2]
            elements_utilities = elements[NS + 2:NU + NS + 2]
            streams = [Stream(name = str(e[0]), Tin = float(e[1]), Tout = float(e[2]), FCp = float(e[3])) for e in elements_streams]
            utilities = [Utility(name = str(e[0]), Tin = float(e[1]),Tout = float(e[2]), cost = float(e[3])) for e in elements_utilities]
            
            minup = Min_Utility_Problem(streams, utilities, DTmin)

            if NS + NU + 2 < len(elements):
                elements_permit = elements[NS + NU + 2:]
                if len(elements_permit) > 0:
                    for e in elements_permit:
                        hot_stream = minup.get_hot_stream(e[0])
                        cold_stream = minup.get_cold_stream(e[1])
                        minup.accepted_h_c[(hot_stream, cold_stream)] = int(e[2])
        return minup