#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 19 08:10:06 2021

@author: martins
"""


import pandas as pd


class Data_Generator:

    def __init__(self, length, start_time, end_time) -> None:
        
        self.length = length
        self.start_time = start_time
        self.end_time = end_time
        self.data = pd.DataFrame(columns=['Day', 'Time', 'Disco', 'Backup', 'PV(kW)', 'Battery_state', 'Battery_percent', 'Total_load_demand', 'Price_multiplier'])

    
    def add_entry(self, entry):
        
        self.data.append({
            'Day': entry['day'],
            'Time': entry['time'],
            'Disco': entry['disco'],
            'Backup': entry['backup'],
            'PV(kW)': entry['pv'],
            'Battery_state': entry['bat_state'],
            'Battery_percent': entry['bat_percent'],
            'Total_load_demand(kW)': entry['total_load_demand'],
            'Price_multiplier': entry['price_mult']
        }, ignore_index=True)

    
    def save_data(self):
        self.data.to_csv("test.csv")