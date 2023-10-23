# -*- coding: utf-8 -*-
"""
Created on Wed Sep 20 19:24:05 2023

@author: WroszuKoks

This file is about to celaning data
"""

#%% standard library imports
from ast import literal_eval
import itertools
import time
import re

#%% third-party imports
import numpy as np
import pandas as pd

#%% customisations
pd.options.display.max_columns = 100

#%% functions definition
def drop_null_cols(df, thresh=0.5):
    cutoff_count = len(df) * thresh
    
    return df.dropna(thresh=cutoff_count, axis=1)

def process_name_type(df):
    df = df[df['type'].notnull()]
    df = df[df['name'].notnull()]
    df = df[df['name'] != 'none']
    
    df = df.drop('type', axis=1)
    
    return df

def process_age(df):
    cut_points = [-1, 0, 3, 7, 12, 16, 2000]
    label_values = [0, 3, 7, 12, 16, 18]
    
    df['required_age'].replace({'18+': '18'}, inplace=True)
    df['required_age'] = pd.to_numeric(df['required_age'])
    df['required_age'] = pd.cut(df['required_age'], bins=cut_points, labels=label_values)
    
    return df

def process_platforms(df):
    df['platforms'] = df['platforms'].apply(literal_eval)
    df['platforms'] = df['platforms'].apply(lambda i: ';'.join(x for x in i.keys() if i[x]))
    
    return df

def process(df):
    df = df.copy()
    df = df.drop_duplicates()
    df = drop_null_cols(df)
    df = process_name_type(df)
    df = process_age(df)
    df = process_platforms(df)
    
    return df

def print_steam_links(df):
    url_base = "https://store.steampowered.com/app/"
    
    for row in df.iterrows():
        appid = row['steam_appid']
        name = row['name']
        
        print(name + ':', url_base + str(appid))

#%% data cleaning
if __name__ == '__main__':
    
    # read in downloaded data
    raw_steam_data = pd.read_csv('C:/Users/wrosz/Desktop/Python/Spyder/Projekty/006_Steam_Database_for_APPs/2_files/steam_app_data.csv')
    
    # print out number of rows and columns
    print('Rows:', raw_steam_data.shape[0])
    print('Columns:', raw_steam_data.shape[1])

    # view first five rows
    raw_steam_data.head()
    
    # checking how many null's in raw file, deleting those with more than 50% null's in column
    #null_counts = raw_steam_data.isnull().sum()
    #treshold = raw_steam_data.shape[0] // 2
    #drop_rows = raw_steam_data.columns[null_counts > treshold] 
    #print('Columns to drop: {}'.format(list(drop_rows)))
    
    # rows to remove, if 'type' column is null
    #raw_steam_data['type'].value_counts(dropna=False)
    #print('Rows to remove: ', raw_steam_data[raw_steam_data['type'].isnull()].shape[0])
    
    # rows to remove with no name (either Nan or 'none')
    #raw_steam_data[(raw_steam_data['name'].isnull()) | (raw_steam_data['name'] == 'none')]
    
    # duplicated rows to be removed later
    #duplicate_rows = raw_steam_data[raw_steam_data.duplicated()]
    #print('Duplicate rows to remove: ', duplicate_rows.shape[0])    
    
    print(raw_steam_data.shape)
    initial_processing = process(raw_steam_data)
    print(initial_processing.shape)
    
    initial_processing['price_overview'].isnull().sum()
    initial_processing['is_free'].sum()
    
    
    d = initial_processing[initial_processing['price_overview'].isnull() & initial_processing['is_free'] == True]
    print_steam_links(d[:5])
