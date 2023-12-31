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
pd.set_option('display.max_colwidth', None)

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

def process_cat_and_gen(df):
    df = df[(df['categories'].notnull()) & (df['genres'].notnull())]
    for i in ['categories', 'genres']:
        df[i] = df[i].apply(lambda x: ';'.join(y['description'] for y in literal_eval(x)))

    return df

def process_achiev_recom_and_desc(df):
    df.drop(['content_descriptors'], axis=1, inplace=True)
    df['achievements'] = df['achievements'].apply(lambda x: 0 if x is np.nan else literal_eval(x)['total'])
    df['recommendations'] = df['recommendations'].apply(lambda x: 0 if x is np.nan else literal_eval(x)['total'])

    return df

def export_data(df, filename):
    filepath = '/home/wroszu/Python_Projects/Connected-with-repo/Steam-Data-Analysis-FILES/2_files/' + filename + '.csv'
    df.to_csv(filepath, index=False)
    
    print("Exported {} to '{}'".format(filename, filepath))

def process_descriptions(df, export=False):
    if export:
        description_data = df[['steam_appid', 'detailed_description', 'about_the_game', 'short_description']]
        export_data(description_data, filename='description_data')
    df.drop(['detailed_description', 'about_the_game', 'short_description'], axis=1, inplace=True)

    return df

def process_media(df, export=False):
    if export:
        media_data = df[['steam_appid', 'header_image', 'screenshots', 'background', 'movies']]
        export_data(media_data, filename='media_data')
    df.drop(['header_image', 'screenshots', 'background', 'movies'], axis=1, inplace=True)

    return df

def process_info(df, export=False):
    if export:
        support_info_data = df[['steam_appid', 'website', 'support_info']].copy()
        support_info_data['support_info'] = support_info_data['support_info'].apply(lambda x: literal_eval(x))
        support_info_data['support_url'] = support_info_data['support_info'].apply(lambda x: x['url'])
        support_info_data['support_email'] = support_info_data['support_info'].apply(lambda x: x['email'])
        support_info_data.drop(['support_info'], axis=1, inplace=True)
        export_data(support_info_data, filename='support_data')
    df.drop(['support_info', 'website'], axis=1, inplace=True)

    return df

def process_requirements(df, export=False):
    if export:
        requirements_data = df[['steam_appid', 'pc_requirements', 'mac_requirements', 'linux_requirements']].copy()
        requirements_data['pc_requirements_clean'] = (requirements_data['pc_requirements']
                                                        .str.replace(r'\\[rtn]', '', regex=True)
                                                        .str.replace(r'<[pbr]{1,2}>', ' ', regex=True)
                                                        .str.replace(r'<[\/"=\w\s]+>', '', regex=True)
                                                      )
        requirements_data['pc_requirements_clean'] = requirements_data['pc_requirements_clean'].apply(lambda x: literal_eval(x))
        requirements_data.drop(['pc_requirements_clean'], axis=1, inplace=True)
        export_data(requirements_data, filename='requirements_data')
    df.drop(['pc_requirements', 'mac_requirements', 'linux_requirements'], axis=1, inplace=True)

    return df

def process_data_release(df):
    df['release_date'] = df['release_date'].apply(lambda x: 0 if x is np.nan else literal_eval(x)['date'])
    df['release_date'] = df['release_date'].apply(lambda x: x.replace(',', ''))
    df['release_date'] = pd.to_datetime(df['release_date'], format='%d %b %Y', errors='coerce')
    df = df[df['release_date'].notnull()]

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
    df = process_cat_and_gen(df)
    df = process_achiev_recom_and_desc(df)
    df = process_descriptions(df, export=True)
    df = process_media(df, export=True)
    df = process_info(df, export=True)
    df = process_requirements(df, export=True)
    df = process_data_release(df)

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
    
    # categories and genres cleaning
    #initial_processing['categories'].value_counts()
    #initial_processing['genres'].isnull().sum()
    #print_steam_links(initial_processing[initial_processing['genres'].isnull()].sample(5, random_state = 0))

    # achievements and content_descriptors cleaning
    #initial_processing['achievements'].isnull().sum()
    #initial_processing['content_descriptors'].isnull().sum()
    #initial_processing[['name', 'achievements', 'content_descriptors']].head(30)
    #literal_eval(initial_processing['achievements'][9])
    #initial_processing['content_descriptors'].value_counts()
    #initial_processing['achievements'].value_counts()

    initial_processing.head(2)

    # Exporting data which is not useful for now: Descriptions
    #initial_processing[['detailed_description', 'about_the_game', 'short_description']].isnull().sum()
    #initial_processing[initial_processing['detailed_description'].isnull()]
    #initial_processing[initial_processing['detailed_description'].str.len()<=20]
    pd.read_csv('/home/wroszu/Python_Projects/Connected-with-repo/Steam-Data-Analysis-FILES/2_files/description_data.csv').head()

    # Exporting data which is not useful for now: Media
    #for i in ['header_image', 'screenshots', 'background']:
    #    print(i+':', initial_processing[i].isnull().sum())
    pd.read_csv('/home/wroszu/Python_Projects/Connected-with-repo/Steam-Data-Analysis-FILES/2_files/media_data.csv').head()

    # Memory usage information
    raw_steam_data.info(verbose=False, memory_usage="deep")
    initial_processing.info(verbose=False, memory_usage="deep")

    # Exporting data which is not useful for now: Info
    #initial_processing[['name', 'website', 'support_info']][50:70]
    #initial_processing['support_info'].value_counts()
    pd.read_csv('/home/wroszu/Python_Projects/Connected-with-repo/Steam-Data-Analysis-FILES/2_files/support_data.csv').head()

    # Exporting data which is not useful for now: Requirements
    #initial_processing['pc_requirements'].iloc[[0,2000,15000]]
    #ppp = initial_processing[['steam_appid', 'pc_requirements']].copy()
    #ppp['clean_pcr'] = (ppp['pc_requirements']
    #                    .str.replace(r'\\[rtn]', '', regex=True)
    #                    .str.replace(r'<[pbr]{1,2}>', ' ', regex=True)
    #                    .str.replace(r'<[\/"=\w\s]+>', '', regex=True)
    #                    )
    #ppp['clean_pcr'] = ppp['clean_pcr'].apply(lambda x: literal_eval(x))
    #ppp.head()
    #print(ppp['clean_pcr'][1].values())

    initial_processing.head()
    pd.read_csv('/home/wroszu/Python_Projects/Connected-with-repo/Steam-Data-Analysis-FILES/2_files/requirements_data.csv').head()

    # Last tests to make sure file is ready to save!
    #initial_processing.isnull().sum()
    #initial_processing[initial_processing['release_date'] > '2020-02-02']
    initial_processing.to_csv('/home/wroszu/Python_Projects/Connected-with-repo/Steam-Data-Analysis-FILES/2_files/initial_processing.csv')

#%%    