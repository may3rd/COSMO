"""Created on the 25 Feb 2024
@author: Maetee Lorprajuksir
@author contact: may3rd@gmail.com


API for controlling the Aspen Python Interface automatically

"""

import os
import win32com.client as win32
import numpy as np
import time
from .constants import UnitConversionType


class Simulation():
    """
    """

    HyApp = win32.gencache.EnsureDispatch("HYSYS.Application")
    HyCase = None

    def __init__(self, Filename: str, WorkingPath:str = None, Visibility:bool = True):
        print("The current Directory is : ")
        print(os.getcwd())

        if WorkingPath != None:
            os.chdir(WorkingPath)
            print("The new Directory where you shuold have your simulation file is : ")
            print(os.getcwd())
        else:
            WorkingPath = os.getcwd()
        
        self.HyCase = self.HyApp.SimualtionCases.Open(os.path.join(WorkingPath, Filename))
        print("The Aspen HYSYS in active now.")
        self.HyCase.Visible = Visibility
        print(' --- PLEASE! Be aware of the unit handling of this interface--- ')
        print(' --- Python SI Unit Set only --- ')
        print(' ')
        print(' --- It is ALWAYS a good practice to check consistency in units ')
        print('     between your Aspen HYSYS file and the Python interface. --- ')
        print(' ')
        print('**************************************************************** ')
        print(' Python SI unit set: ')
        print('   Temperature:      °C')
        print('   Pressure:         kPa')
        print('   Molar flowrate:   kgmole/s')
        print('   Energy flowrate:  kJ/s')
        print('**************************************************************** ')
        print(' ')
        print(' Aspen HYSYS-Python Interface has been established succesfully!')
        print(' ')

    def __init__(self):
        self.HyCase = self.HyApp.ActiveDocument
        print(' --- PLEASE! Be aware of the unit handling of this interface--- ')
        print(' --- Python SI Unit Set only --- ')
        print(' ')
        print(' --- It is ALWAYS a good practice to check consistency in units ')
        print('     between your Aspen HYSYS file and the Python interface. --- ')
        print(' ')
        print('**************************************************************** ')
        print(' Python SI unit set: ')
        print('   Temperature:      °C')
        print('   Pressure:         kPa')
        print('   Molar flowrate:   kgmole/s')
        print('   Energy flowrate:  kJ/s')
        print('**************************************************************** ')
        print(' ')
        print(' Aspen HYSYS-Python Interface has been established succesfully!')
        print(' ')

    def CloseCase(self):
        activeCase = self.HyApp.ActiveDocument
        activeCase.Close(False)
    
    @property
    def Solver(self):
        return self.HyCase.Solver
    
    @property
    def Operations(self):
        return self.HyCase.Flowsheet.Operations
    
    @property
    def Streams(self):
        return self.HyCase.Flowsheet.Streams
    

    def Stream_SetTemperature(self, Stream, value:float, unit:str = 'C') -> bool:
        if unit not in self.HyApp.UnitConversionSetManager.GetUnitConversionSet(UnitConversionType.uctTemperature).Names:
            print('Wrong unit')
            return False
        
        if not self.Stream(Stream).Temperature.CanModify:
            print(f"Temperature of {Stream} cannot be modified.")
            return False
        
        # Turn off the solving mode
        self.Solver.CanSolve = False

        # Set stream temperature
        self.Stream(Stream).Temperature.SetValue(value, unit)

        # Turn on the solving made
        self.Solver.CanSolve = True

        # wait for solver to run
        while self.Solver.IsSolving == True:
            time.sleep(0.001)

        return True

    def Stream_SetPressure(self, Stream, value:float, unit:str = 'kPa') -> bool:
        if unit not in self.HyApp.UnitConversionSetManager.GetUnitConversionSet(UnitConversionType.uctPressure).Names:
            print('Wrong unit')
            return False
        
        if not self.Stream(Stream).Pressure.CanModify:
            print(f"Pressure of {Stream} cannot be modified.")
            return False
        
        # Turn off the solving mode
        self.Solver.CanSolve = False

        # Set stream temperature
        self.Stream(Stream).Pressure.SetValue(value, unit)

        # Turn on the solving made
        self.Solver.CanSolve = True

        # wait for solver to run
        while self.Solver.IsSolving == True:
            time.sleep(0.001)

        return True

    def Stream_SetMolarFlow(self, Stream, value:float, unit:str = 'kgmole/h') -> bool:
        if unit not in self.HyApp.UnitConversionSetManager.GetUnitConversionSet(UnitConversionType.uctMolarFlow).Names:
            print('Wrong unit')
            return False
        
        if not self.Stream(Stream).MolarFlow.CanModify:
            print(f"Molar flow of {Stream} cannot be modified.")
            return False
        
        # Turn off the solving mode
        self.Solver.CanSolve = False

        # Set stream temperature
        self.Stream(Stream).MolarFlow.SetValue(value, unit)

        # Turn on the solving made
        self.Solver.CanSolve = True

        # wait for solver to run
        while self.Solver.IsSolving == True:
            time.sleep(0.001)

        return True

    def Stream_SetMassFlow(self, Stream, value:float, unit:str = 'kgmole/h') -> bool:
        if unit not in self.HyApp.UnitConversionSetManager.GetUnitConversionSet(UnitConversionType.uctMassFlow).Names:
            print('Wrong unit')
            return False
        
        if not self.Stream(Stream).MassFlow.CanModify:
            print(f"Mass flow of {Stream} cannot be modified.")
            return False
        
        # Turn off the solving mode
        self.Solver.CanSolve = False

        # Set stream temperature
        self.Stream(Stream).MassFlow.SetValue(value, unit)

        # Turn on the solving made
        self.Solver.CanSolve = True

        # wait for solver to run
        while self.Solver.IsSolving == True:
            time.sleep(0.001)

        return True
    