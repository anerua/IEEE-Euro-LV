#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 11:06:09 2021

@author: martins
"""

import dss


BASE = '/mnt/6840331B4032F004/Users/MARTINS/Documents/Texts/Acad/OAU/Part 5/Rain Semester/EEE502 - Final Year Project II/Work/IEEE Euro LV/Master.dss'
CIRCUIT = 0  # OpenDSS Circuit
TEXT = 0  # Text command
ENG = 0  # DSS COM Engine

def start():
    global TEXT, ENG, CIRCUIT
    ENG = dss.DSS
    TEXT = ENG.Text
    TEXT.Command = 'Clear'
    CIRCUIT = ENG.ActiveCircuit        # Sets CIRCUIT to be the ActiveCircuit in DSS
    TEXT.Command = "compile '" + BASE + "'"
    ENG.AllowForms = False      # suppresses message forms from popping up during the execution of the user’s program
    
    
def get_total_active_power():
    total_power = CIRCUIT.TotalPower
    print(total_power)

def get_load_energy():
    meter_element = CIRCUIT.Meters
    num_meters = 55
    kwhs = []
    
    meter_element.Name = 'gen_meter'
    kwhs.append(meter_element.RegisterValues[0])
    
    for i in range(1,num_meters + 1):
        meter_element.Name = 'load_meter' + str(i)
        kwhs.append(meter_element.RegisterValues[60])
    
    return kwhs

def energy_losses():
    meter_element = CIRCUIT.Meters
    meter_element.Name = 'gen_meter'
    
    return meter_element.RegisterValues[12]

start()
get_total_active_power()
kwhs = get_load_energy()

print("Total energy consumption: " + str(kwhs[0]) + " kWh")
for i in range(1, len(kwhs)):
    print("---------------------------------------")
    print("Energy consumption of Load " + str(i) + ": " + str(kwhs[i]) + " kWh")

print()
load_energy_sum = sum(kwhs[1:])

if (int(round(load_energy_sum + energy_losses())) == int(round(kwhs[0]))):
    print("Sum of load energy = total measured energy by generator meter")
    print("Sum of load energy = " + str(load_energy_sum + energy_losses()) + " kWh")
    print("Total measured energy by generator meter = " + str(kwhs[0]) + " kWh")
else:
    print("Sum of load energy = " + str(load_energy_sum) + " kWh")
    print("Total measured energy by generator meter = " + str(kwhs[0]) + " kWh")


























