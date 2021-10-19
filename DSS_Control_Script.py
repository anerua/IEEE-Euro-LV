#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 27 07:29:05 2021

@author: martins
"""

import dss
from Data_Generator import Data_Generator


BASE = '/mnt/6840331B4032F004/Users/MARTINS/Documents/Texts/Acad/OAU/Part 5/Rain Semester/EEE502 - Final Year Project II/Work/IEEE Euro LV/Master_Control.dss'
CIRCUIT = 0  # OpenDSS Circuit
SOLUTION = 0
ACTIVE_ELEMENT = 0
TEXT = 0  # Text command
ENG = 0  # DSS COM Engine

NUMBER_OF_DAYS = 1  # Number of days of simulation
BACKUP_REQUEST = False
BACKUP_DURATION = 6
POWER_OUT_HOUR = 0  # Hour of day when grid supply goes off
POWER_ON_HOUR = 6  # Hour of day when grid supply comes back on

PV_PMPP = 0
total_loadshape = []
BATTERY_KW_RATED = 70

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
    
def solution_iteration():
    global PV_PMPP, total_loadshape
    
    total_loadshape = get_total_loadshape()
    TEXT.Command = f"New Loadshape.BatteryShape npts=1440 minterval=1 mult={total_loadshape}"
    TEXT.Command = f"New Storage.Battery phases=3 bus1=BackupBus kV=.416 kwrated={BATTERY_KW_RATED} kwhrated=400 pf=.95 daily=BatteryShape"
    
    TEXT.Command = "set mode = yearly"
    TEXT.Command = "set Year = 1"
    SOLUTION.Number = 1
    SOLUTION.StepSize = 60
    SOLUTION.dblHour = 0.0
    
    num_pts = 1440*NUMBER_OF_DAYS
    present_step = 0
    
    pv_name = "PVSystem.PV"
    CIRCUIT.SetActiveElement(pv_name)
    PV_PMPP = int(ACTIVE_ELEMENT.Properties('Pmpp').Val)
    max_demand = 0
    min_demand = 400
    max_time = "00:00"
    min_time = "00:00"

    gen_data = Data_Generator(BACKUP_DURATION, POWER_OUT_HOUR, POWER_ON_HOUR)

    
    while(present_step < num_pts):
        grid_response = grid_supply_control(present_step)
        pv_response = pv_control(present_step)
        
        # Solve the circuit and get output pv then pass as arg to battery_control
        SOLUTION.SolveSnap()
        
        CIRCUIT.SetActiveElement("PVSystem.PV")
        pv_power = abs(ACTIVE_ELEMENT.Powers[0]) * 3
        
        battery_response = battery_control(present_step, pv_power)
        
        present_load_demand = total_loadshape[present_step % 1440] * 100
        
        price_mult = price_multiplier(pv_response, pv_power, present_load_demand)
        
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
        
        if max_demand < present_load_demand:
            max_demand = present_load_demand
            max_time = f"{hour:02d}:{minute:02d}"
        if min_demand > present_load_demand:
            min_demand = present_load_demand
            min_time = f"{hour:02d}:{minute:02d}"

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
            'price_mult': price_mult
        }

        gen_data.add_entry(entry)
        
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
        print("+------------------------------------------")
        print()
        
        present_step += 1
        
    gen_data.save_data()
    print("Done!")
    print()
    print(f"Maximum demand: {max_demand} kW at {max_time}")
    print(f"Minimum demand: {min_demand} kW at {min_time}")


def get_loadshapes():    
    loadshapes = CIRCUIT.LoadShapes
    loadshapes_dict = {}
    for i in range(1,56):
        shape_name = f"Shape_{i}"
        loadshapes.Name = shape_name
        loadshapes_dict[shape_name] = loadshapes.Pmult
    return loadshapes_dict


def get_total_loadshape():
    loadshapes_dict = get_loadshapes()
    total_loadshape = []
    for i in range(1440):
        total = sum((loadshapes_dict[shape][i] / 100) for shape in loadshapes_dict)
        total_loadshape.append(total)
    return total_loadshape.copy()
    
    
def battery_control(present_step, pv_power):
    CIRCUIT.SetActiveElement("Storage.Battery")
    
    present_load_demand = total_loadshape[present_step % 1440] * 100
        
    if ((not BACKUP_REQUEST) and pv_power > BATTERY_KW_RATED) or (BACKUP_REQUEST and pv_power > (BATTERY_KW_RATED + present_load_demand)):
        ACTIVE_ELEMENT.Properties('DispMode').Val = "EXTERNAL"
        ACTIVE_ELEMENT.Properties('state').Val = 'CHARGING'
    elif BACKUP_REQUEST and (pv_power < present_load_demand):
        ACTIVE_ELEMENT.Properties('DispMode').Val = "FOLLOW"
        CIRCUIT.SetActiveElement("Storage.Battery")
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
    
    total_demand_min = 3 # this is the minimum demand of the system at any time = demand of base load
    price_mult = 0
    
    if pv_response == "BACKUP ONLINE":
        if pv_power == present_load_demand:
            price_mult = 1
        elif pv_power > present_load_demand:
            price_mult = pv_power / present_load_demand
        else:
            alpha_min = total_demand_min / PV_PMPP
            beta = present_load_demand / BATTERY_KW_RATED
            price_mult = (1 / alpha_min) + beta
    else:
        price_mult = -1 # represents that the price should be whatever disco charges
    
    return price_mult

    
start()
solution_iteration()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    