#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 27 07:29:05 2021

@author: martins
"""

import dss
from Data_Generator import Data_Generator
from Battery_Sizing import BatterySizing
from PV_Sizing import PVSizing


BASE = '/mnt/6840331B4032F004/Users/MARTINS/Documents/Texts/Acad/OAU/Part 5/Rain Semester/EEE502 - Final Year Project II/Work/IEEE Euro LV/Master_Control.dss'
CIRCUIT = 0  # OpenDSS Circuit
SOLUTION = 0
ACTIVE_ELEMENT = 0
TEXT = 0  # Text command
ENG = 0  # DSS COM Engine

NUMBER_OF_DAYS = 0  # Number of days of simulation. Set later
BACKUP_REQUEST = False
POWER_OUT_HOUR = 0  # Hour of day when grid supply goes off. Set later
POWER_ON_HOUR = 0  # Hour of day when grid supply comes back on. Set later

PV_PMPP = 0
total_loadshape = []
BATTERY_KW_RATED = 0
BATTERY_KWH_RATED = 0

def start():
    global TEXT, ENG, CIRCUIT, SOLUTION, ACTIVE_ELEMENT
    ENG = dss.DSS
    TEXT = ENG.Text
    TEXT.Command = 'Clear'
    CIRCUIT = ENG.ActiveCircuit        # Sets CIRCUIT to be the ActiveCircuit in DSS
    SOLUTION = CIRCUIT.Solution
    ACTIVE_ELEMENT = CIRCUIT.ActiveCktElement
    TEXT.Command = "compile '" + BASE + "'"
    ENG.AllowForms = False      # suppresses message forms from popping up during the execution of the user’s program
    
def solution_iteration(verbose=False):
    global PV_PMPP, total_loadshape
    
    total_loadshape = get_total_loadshape()
    TEXT.Command = f"New Loadshape.BatteryShape npts=1440 minterval=1 mult={total_loadshape}"
    TEXT.Command = f"New Storage.Battery phases=3 bus1=BackupBus kV=.416 kwrated={BATTERY_KW_RATED} kwhrated={BATTERY_KWH_RATED} pf=.95 daily=BatteryShape"
    
    TEXT.Command = "set mode = yearly"
    TEXT.Command = "set Year = 1"
    SOLUTION.Number = 1
    SOLUTION.StepSize = 60
    SOLUTION.dblHour = 0.0
    
    num_pts = 1440*NUMBER_OF_DAYS
    present_step = 0
    
    pv_name = "PVSystem.PV"
    CIRCUIT.SetActiveElement(pv_name)
    ACTIVE_ELEMENT.Properties('Pmpp').Val = PV_PMPP
    ACTIVE_ELEMENT.Properties('kVA').Val = PV_PMPP

    gen_data = Data_Generator(POWER_OUT_HOUR, POWER_ON_HOUR, NUMBER_OF_DAYS)
    
    while(present_step < num_pts):
        grid_response = grid_supply_control(present_step)
        pv_response = pv_control(present_step)
        
        # Solve the circuit and get output pv then pass as arg to battery_control
        SOLUTION.SolveSnap()
        
        CIRCUIT.SetActiveElement("PVSystem.PV")
        pv_power = abs(ACTIVE_ELEMENT.Powers[0]) * 3
        
        battery_response = battery_control(present_step, pv_power)
        
        present_load_demand = total_loadshape[present_step % 1440]
        
        price_mult, add_mult = price_multiplier(pv_response, pv_power, present_load_demand)
        
        SOLUTION.Solve()
        
        battery_name = "Storage.Battery"
        CIRCUIT.SetActiveElement(battery_name)
        ACTIVE_ELEMENT.Properties('DispMode').Val = "EXTERNAL"
        battery_stored = ACTIVE_ELEMENT.Properties('%stored').Val
        battery_kWh = ACTIVE_ELEMENT.Properties('kWhstored').Val
        battery_power = ACTIVE_ELEMENT.Properties('kW').Val
        
        day = ((present_step//60)//24) + 1
        hour = (present_step//60) % 24
        minute = present_step % 60

        entry = {
            'day': day,
            'hour': f"{hour:02d}",
            'minute': f"{minute:02d}",
            'disco': grid_response,
            'backup': pv_response,
            'pv': pv_power,
            'bat_state': battery_response,
            'bat_percent': battery_stored,
            'total_load_demand': present_load_demand,
            'price_mult': price_mult,
            'add_mult': add_mult
        }

        gen_data.add_entry(entry)
        
        if verbose:
            print("+------------------------------------------")
            print(f"| Day {day}, {hour:02d}:{minute:02d}")
            print("+------------------------------------------")
            print(f"| Grid supply: {grid_response}")
            print(f"| Backup supply: {pv_response}\n|")
            
            print(f"| PV output: {pv_power}\n|")
            
            print(f"| Battery state: {battery_response}")
            print(f"| Battery percent: {battery_stored} %")
            print(f"| Battery energy left: {battery_kWh} kWh")
            print(f"| Battery power: {battery_power} kW\n|")
            
            print(f"| Total load demand: {present_load_demand} kW")
            print(f"| Price multiplier: {price_mult}")
            print(f"| Additional charge multiplier: {add_mult}")
            print("+------------------------------------------")
            print(flush=True)
        
        present_step += 1
        
    gen_data.save_data()
    
    if verbose:
        print("Done!")
        print("===========================================")
        print()


def get_total_loadshape():
    loadshapes = CIRCUIT.LoadShapes
    loadshapes_dict = {}
    for i in range(1,56):
        shape_name = f"Shape_{i}"
        loadshapes.Name = shape_name
        loadshapes_dict[shape_name] = loadshapes.Pmult

    total_loadshape = []
    for i in range(1440):
        total = sum((loadshapes_dict[shape][i]) for shape in loadshapes_dict)
        total_loadshape.append(total)
    return total_loadshape.copy()
    
    
def battery_control(present_step, pv_power):
    CIRCUIT.SetActiveElement("Storage.Battery")
    
    present_load_demand = total_loadshape[present_step % 1440]
        
    if ((not BACKUP_REQUEST) and pv_power > 0) or (BACKUP_REQUEST and pv_power > (present_load_demand * 1.25)):
        ACTIVE_ELEMENT.Properties('DispMode').Val = "EXTERNAL"
        ACTIVE_ELEMENT.Properties('state').Val = 'CHARGING'
    elif BACKUP_REQUEST and (pv_power < present_load_demand):
        CIRCUIT.SetActiveElement("Storage.Battery")
        ACTIVE_ELEMENT.Properties('DispMode').Val = "EXTERNAL"
        ACTIVE_ELEMENT.Properties('kW').Val = present_load_demand
        ACTIVE_ELEMENT.Properties('state').Val = 'DISCHARGING'
    else:
        ACTIVE_ELEMENT.Properties('DispMode').Val = "EXTERNAL"
        ACTIVE_ELEMENT.Properties('state').Val = 'IDLING'
        
    return ACTIVE_ELEMENT.Properties('state').Val


def pv_control(present_step):
    
    if (present_step % 60) == 0:
        present_24hour = (present_step // 60) % 24
    
        if present_24hour == POWER_OUT_HOUR:
            TEXT.Command = "Close Line.BackupLine"
            return "BACKUP ONLINE"
        elif present_24hour == POWER_ON_HOUR:
            TEXT.Command = "Open Line.BackupLine"
            return "BACKUP OFFLINE"
    
    if BACKUP_REQUEST:
        return "BACKUP ONLINE"
    else:
        return "BACKUP OFFLINE"


def grid_supply_control(present_step):
    global BACKUP_REQUEST
    
    if (present_step % 60) == 0:
        present_24hour = (present_step // 60) % 24
    
        if present_24hour == POWER_OUT_HOUR:
            TEXT.Command = "Open VSource.Source"
            BACKUP_REQUEST = True
            return "POWER OUT"
        elif present_24hour == POWER_ON_HOUR:
            TEXT.Command = "Close VSource.Source"
            BACKUP_REQUEST = False
            return "POWER ON"
    
    if BACKUP_REQUEST:
        return "POWER OUT"
    else:
        return "POWER ON"
    
    
def price_multiplier(pv_response, pv_power, present_load_demand):
    
    price_mult = 0  # price multiplier
    add_mult = 0    # additional charge multiplier
    
    if pv_response == "BACKUP ONLINE":
        if pv_power >= present_load_demand:
            price_mult = pv_power / present_load_demand
        else:
            price_mult = BATTERY_KW_RATED / (BATTERY_KW_RATED - present_load_demand)
            add_mult = 1
    else:
        price_mult = 0 # represents that the price should be whatever disco charges
    
    return price_mult, add_mult



if __name__=='__main__':
    
    simulation_lengths = (1,) # 1 day, 1 week and 1 month simulation periods
    # periods = [(0,6), (6,12), (12,18), (18,0), (0,12), (12,0), (6,18), (18,6), (0,18), (18,12), (12,6), (6,0)]
    periods = [(0,6), (6,12), (12,18), (18,0), (0,12), (12,0), (6,18), (18,6)]
    # periods = [(6,18)]

    bs = BatterySizing(periods)
    bs.size_battery()
    battery_sizes = bs.get_battery_sizes()

    pvs = PVSizing(periods)
    pvs.size_PV()
    pv_sizes = pvs.get_PV_sizes()

    for simulation_length in simulation_lengths:
        print("===========================================")
        print(f"{simulation_length}-day simulations")
        print("===========================================")
        print()
        for period in periods:
            print(f"Running {period[0]} - {period[1]} ...", flush=True)
            NUMBER_OF_DAYS = simulation_length
            POWER_OUT_HOUR, POWER_ON_HOUR = period

            BATTERY_KW_RATED = battery_sizes[f"{POWER_OUT_HOUR}-{POWER_ON_HOUR}"]['kW']
            BATTERY_KWH_RATED = battery_sizes[f"{POWER_OUT_HOUR}-{POWER_ON_HOUR}"]['kWh']
            PV_PMPP = pv_sizes[f"{POWER_OUT_HOUR}-{POWER_ON_HOUR}"]

            start()
            solution_iteration(verbose=False)
            print("Done", flush=True)
        
        print("===========================================")
        print("===========================================")
        print(flush=True)
    
    print("Finally done at last!")

