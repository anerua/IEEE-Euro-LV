#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 19 08:10:06 2021

@author: martins
"""


import pandas as pd


class Data_Generator:

    def __init__(self) -> None:
        
        data = pd.DataFrame(columns=['Day', 'time', 'Disco', 'Backup', 'PV(kW)', 'Battery_state', 'Battery_percent', 'Total_load_demand', 'Price_multiplier'])

    
    def add_entry(self):
        self.data