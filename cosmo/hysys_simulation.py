"""Created on the 25 Feb 2024
@author: Maetee Lorprajuksir
@author contact: may3rd@gmail.com


API for controlling the Aspen Python Interface automatically

"""

import os
import win32com.client as win32
import numpy as np
import time
from pywintypes import com_error
from typing import Union
import cosmo.constants as constants
import cosmo.hysys_typelib as hytlb

OPERATION_CLASSIFICATION = ['All', 'Vessels', 'HeatTransfer', 'Rotating', 'Piping', 'SolidHandling', 'Reactor', 
                            'Column', 'ShortCutColumn', 'SubFlowsheet', 'Logical']

class Simulation():
    '''
    Skeleton class for HYSYS interface
    '''

    HyApp = win32.gencache.EnsureDispatch('HYSYS.Application')
    HyCase = None

    def __init__(self, Filename: str, WorkingPath:str = None, Visibility:bool = True):
        print('The current Directory is : ')
        print(os.getcwd())

        if WorkingPath != None:
            os.chdir(WorkingPath)
            print('The new Directory where you shuold have your simulation file is : ')
            print(os.getcwd())
        else:
            WorkingPath = os.getcwd()
        
        self.HyCase = self.HyApp.SimualtionCases.Open(os.path.join(WorkingPath, Filename))
        print('The Aspen HYSYS in active now.')
        self.HyCase.Visible = Visibility


    def __init__(self):
        self.HyCase = self.HyApp.ActiveDocument


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
    
    
    def ComponentList(self, name:Union[int, str] = 0):
        return self.HyCase.BasisManager.FluidPackages.Item(name).Components.Names
    
    
    def Components(self, name:Union[int, str] = 0):
        return self.HyCase.BasisManager.FluidPackages.Item(name).Components
    

########################################################################################################################

#   Utility functions   
    
########################################################################################################################
    
    def IsStreamValid(self, name:Union[int, str]) -> bool:
        """
        Check if stream called name is valid.

        Args:
            name: ethier int or string

        Returns:
            True or False
        """
        try:
            self.Streams.Item(name)
        except com_error as e:
            return False
        
        return True
    
    
    def IsOperationValid(self, name) -> bool:
        """
        Check if unit operation called name is valid.

        Args:
            name: ethier int or string

        Returns:
            True or False
        """
        try:
            self.Operations.Item(name)
        except com_error as e:
            return False
        
        return True
    
    
    def Normalize_values(self, data):
        """
        Normalizes a list of values

        Args:
            data: A list of floats to be normalized.

        Returns:
            A new list with the normalized values.
        """
        total_sum = sum(data)
        if total_sum == 0:
            # Handle the case where the sum of all elements is zero
            return [0.0] * len(data)
        return [x / total_sum for x in data]
    
    
    def OperationClass(self, name:Union[int, str]) -> str:
        return self.Operations(name).ClassificationName
    

    def ListAllStreams(self):
        if self.Streams.Count > 0:
            print(f'List of Streams in {self.HyCase.name} is:')
            for i in range(self.Streams.Count):
                stream = self.Streams(i)
                AttOps = []
                for j in range(stream.AttachedOpers.Count):
                    name = stream.AttachedOpers(j).name
                    if name != "":
                        AttOps.append(f'"{name}"')

                print(f'{i}: "{stream.name}" is connecting to: {', '.join(AttOps)}')
        else:
            print('No streams in current simulation case.')


    def ListAllOperations(self):
        if self.Operations.Count > 0:
            print(f'List of Unit Operations in {self.HyCase.name} is:')
            for i in range(self.Operations.Count):
                print(f'{i}: {self.Operations(i).name} with operation class of "{self.Operations(i).ClassificationName}"')
        else:
            print('No unit operation in current simualtion case.')
    

########################################################################################################################

#   Method for modify stream parameters    
    
########################################################################################################################

    def Stream_SetVapourFraction(self, name:Union[int, str], value:float) -> bool:
        return self.Stream_SetValue(name, self.Streams(name).VapourFration, 'Vapour Fraction', value)
    

    def Stream_SetTemperature(self, name:Union[int, str], value:float, unit:str = 'C') -> bool:
        if unit not in self.HyApp.UnitConversionSetManager.GetUnitConversionSet(hytlb.constants.uctTemperature).Names:
            print('Error: Wrong unit')
            return False
        
        return self.Stream_SetValue(name, self.Streams(name).Temperature, 'Temperature', value, unit)
    

    def Stream_SetPressure(self, name:Union[int, str], value:float, unit:str = 'kPa') -> bool:
        if unit not in self.HyApp.UnitConversionSetManager.GetUnitConversionSet(hytlb.constants.uctPressure).Names:
            print('Error: Wrong unit')
            return False
        
        return self.Stream_SetValue(name, self.Streams(name).Pressure, 'Pressure', value, unit)
    

    def Stream_SetMolarFlow(self, name:Union[int, str], value:float, unit:str = 'kgmole/h') -> bool:
        if unit not in self.HyApp.UnitConversionSetManager.GetUnitConversionSet(hytlb.constants.uctMolarFlow).Names:
            print('Error: Wrong unit')
            return False
        
        return self.Stream_SetValue(name, self.Streams(name).MolarFlow, 'Molar flow', value, unit)
    

    def Stream_SetMassFlow(self, name:Union[int, str], value:float, unit:str = 'kgmole/h') -> bool:
        if unit not in self.HyApp.UnitConversionSetManager.GetUnitConversionSet(hytlb.constants.uctMassFlow).Names:
            print('Error: Wrong unit')
            return False
        
        return self.Stream_SetValue(name, self.Streams(name).MassFlow, 'Mass flow', value, unit)
    
    
    def Stream_SetValue(self, name:Union[int, str], varibale:object, varName:str, value:float, unit:str = "") -> bool:
        if not self.IsStreamValid(name):
            print(f'Error: No stream {name}.')
            return False
        
        if not varibale.CanModify:
            print(f'Error: {varName} of {name} cannot be modified.')
            return False
        
        # Turn off the solving mode
        self.Solver.CanSolve = False

        # Set stream parameter
        varibale.SetValue(value, unit)

        # Turn on the solving made
        self.Solver.CanSolve = True

        # wait for solver to run
        while self.Solver.IsSolving == True:
            time.sleep(0.001)

        return True
    

########################################################################################################################

#   Method for modify unit operation parameters    
    
########################################################################################################################
    