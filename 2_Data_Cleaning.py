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

def process_price(df):
    df['price_overview'] = df['price_overview'].apply(lambda i: {'currency': 'PLN', 'initial': -1} if i is np.nan else literal_eval(i))
    df['currency'] = df['price_overview'].apply(lambda i: i['currency'])
    df['price'] = df['price_overview'].apply(lambda i: i['initial'])
    df.loc[df['is_free'], 'price'] = 0
    df.loc[df['currency']=='EUR', 'price'] *= 4.5
    df.loc[df['currency']=='USD', 'price'] *= 4.3
    df['currency'] = df['currency'].apply(lambda i: 'PLN' if i in ['EUR', 'USD'] else i)
    df.drop(df[df['currency']!='PLN'].index, inplace=True)
    df=df[df['price']!=-1]
    df.drop(['is_free', 'currency', 'price_overview', 'packages', 'package_groups'], axis=1, inplace=True)
    df['price'] /= 100

    return df

def process_language(df):
    df.dropna(subset=['supported_languages'], inplace=True)
    df['english'] = df['supported_languages'].apply(lambda x: 1 if 'english' in x.lower() else 0)
    df.drop(['supported_languages'], axis=1, inplace=True)

    return df

def process_dev_and_pub(df):
    df = df[(df['developers'].notnull()) & (df['publishers'] != "['']")].copy()
    df = df[~(df['developers'].str.contains(';')) & ~(df['publishers'].str.contains(';'))]
    df = df[(df['publishers'] != "['NA']") & (df['publishers'] != "['N/A']")]

    df['developer'] = df['developers'].apply(lambda x: ';'.join(literal_eval(x)))
    df['publisher'] = df['publishers'].apply(lambda x: ';'.join(literal_eval(x)))

    df.drop(['developers', 'publishers'], axis=1, inplace=True)

    return df

def process(df):
    df = df.copy()
    df = df.drop_duplicates()
    df = drop_null_cols(df)
    df = process_name_type(df)
    df = process_age(df)
    df = process_platforms(df)
    df = process_price(df)
    df = process_language(df)
    df = process_dev_and_pub(df)
    
    return df

def print_steam_links(df):
    url_base = "https://store.steampowered.com/app/"
    
    for index, row in df.iterrows():
        appid = row['steam_appid']
        name = row['name']
        
        print(name + ':', url_base + str(appid))

#%% data cleaning
if __name__ == '__main__':
    
    # read in downloaded data
    raw_steam_data = pd.read_csv('/home/wroszu/Python_Projects/Connected-with-repo/Steam-Data-Analysis-FILES/2_files/steam_app_data.csv')
    
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

    # after initial process we can check if 'age' and 'platforms' works well
    #initial_processing['required_age'].value_counts().sort_index()
    #initial_processing['platforms'].value_counts()
    
    # checking if 'is_free' and 'price = null' are always matching
    #initial_processing['price_overview'].isnull().sum()
    #initial_processing['is_free'].sum()
    #initial_processing_wrong_price = initial_processing[initial_processing['price_overview'].isnull() & initial_processing['is_free'] == False]
    #print_steam_links(initial_processing_wrong_price[:5])

    initial_processing[initial_processing['name'].str.contains('Counter-Strike')].head(10)

    print_steam_links(initial_processing[initial_processing['name'].str.contains('Counter-Strike')])

    # comparation between price and package_groups as we still missing information about '-1' price games
    #initial_processing[initial_processing['price']==-1].shape[0]
    #initial_processing[initial_processing['package_groups']=='[]'].shape[0]
    #missing_price_and_package = initial_processing[(initial_processing['price'] == -1) & (initial_processing['package_groups'] == "[]")]
    #missing_price_and_package.shape[0]
    #print_steam_links(missing_price_and_package[-10:-5])
    #missing_price_with_package = initial_processing[(initial_processing['price'] == -1) & (initial_processing['package_groups'] != "[]")]
    #missing_price_with_package.shape[0]
    #print_steam_links(missing_price_with_package[-10:-5])

    # checking if english language is available for game
    #initial_processing['supported_languages'].value_counts().head(30)
    #initial_processing["supported_languages"].isnull().sum()
    initial_processing[['name', 'english']].head(15)
    initial_processing['english'].value_counts()

    # developers and publishers column, searching for 'null' values and cleaning
    #initial_processing['developers'].isnull().sum()
    #initial_processing['publishers'].value_counts().head(10)
    #initial_processing[initial_processing['publishers']=="['']"].shape[0]
    #print_steam_links(initial_processing[initial_processing['developers'].isnull()][:5])
 
    initial_processing[['name', 'steam_appid', 'developer', 'publisher']].head(-10)

#%%    