# -*- coding: utf-8 -*-
"""
Created on Sat Sep 16 15:22:29 2023

@author: WroszuKoks

This file is about to download data from Steamspy API to .csv file. 
"""

#%% standard library imports
import csv
import datetime as dt
import json
import os
import statistics
import time

#%% third-party imports
import numpy as np
import pandas as pd
import requests

#%% customisations - ensure tables show all columns
pd.options.display.max_columns = 100

#%% functions definition
def get_request(url_a, parameters=None):
    try:
        response = requests.get(url=url_a, params=parameters)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as s:
        print('Error:', s)
        
        for i in range(5, 0, -1):
            print('\rWaiting... ({})'.format(i), end=" ")
            time.sleep(1)
        print('\rRetrying.' + ' '*10)
        
        # recusively try again
        return get_request(url_a,parameters)
    
    if response:
        return response.json()
    else:
        # response is none usually means too many requests. Wait and try again 
        print('\rNo response, waiting 5 sec...')
        time.sleep(5)
        print("Retrying.")
        return get_request(url_a, parameters)
    
def get_app_data(start, stop, parser, pause):
    app_data = []
    
    #iterate through each row of app_list, confined by start and stop
    for index, row in app_list[start:stop].iterrows():
        print("\nCurrent index: {}".format(index), end='\r')
        
        appid = row["appid"]
        name = row["name"]
        
        #retrive app data for a row, handled by supplied parser and append to list
        data = parser(appid, name)
        app_data.append(data)
        
        time.sleep(pause) #prevent overloading api with requests
        
    return app_data

def process_batches(parser, app_list, download_path, data_filename, index_filename, columns, begin=0, end=-1, batchsize=100, pause=1):
    print("Starting at index {}:\n".format(begin))
    
    #by default, process all apps in app_list
    if end == -1:
        end = len(app_list) + 1
        
    #generate array of batch begin and end points
    batches = np.arange(begin, end, batchsize)
    batches = np.append(batches, end)
    
    apps_written = 0
    batch_times = []
    
    for i in range(len(batches) - 1):
        start_time = time.time()
        
        start = batches[i]
        stop = batches [i + 1]
        
        app_data = get_app_data(start, stop, parser, pause)
        
        rel_path = os.path.join(download_path, data_filename)
        
        #writing app data to file
        with open(rel_path, 'a', newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            
            for j in range(3,0,-1):
                print("\rAbout to write data, don't stop script! ({})".format(j), end="")
                time.sleep(0.5)
                
            writer.writerows(app_data)
            print("\rExported lines {}-{} to {}.".format(start, stop-1, data_filename), end=" ")
            
        apps_written += len(app_data)
        
        idx_path = os.path.join(download_path, index_filename)
        
        #writing last index to file
        with open(idx_path, "w") as f:
            index = stop
            print(index, file=f)
            
        #logging time taken
        end_time = time.time()
        time_taken = end_time - start_time
        
        batch_times.append(time_taken)
        mean_time = statistics.mean(batch_times)
        
        est_remaining = (len(batches) - i - 2) * mean_time
        
        reamining_td = dt.timedelta(seconds=round(est_remaining))
        time_td = dt.timedelta(seconds=round(time_taken))
        mean_td = dt.timedelta(seconds=round(mean_time))
        
        print("Batch {} time: {} (avg: {}, reamining: {})".format(i, time_td, mean_td, reamining_td))
        
    print("\nProcessing batches complete. {} apps written".format(apps_written))
        
def reset_index(download_path, index_filename):
    rel_path = os.path.join(download_path, index_filename)
    
    with open(rel_path, "w") as f:
        print(0, file=f)
        
def get_index(download_path, index_filename):
    try:
        rel_path = os.path.join(download_path, index_filename)
        
        with open(rel_path, "r") as f:
            index = int(f.readline())
            
    except FileNotFoundError:
        index = 0
        print("File Not Found Error, index = {}".format(index))
    
    return index
    
def prepare_data_file(download_path, filename, index, columns, page_number):
    if index == 0 and page_number == 0:
        rel_path = os.path.join(download_path, filename)
        
        with open(rel_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            
def parse_steam_request(appid, name):
    url = "http://store.steampowered.com/api/appdetails/"
    parameters = {"appids": appid}
    
    json_data = get_request(url, parameters=parameters)
    json_app_data = json_data[str(appid)]
    
    if json_app_data["success"]:
        data = json_app_data["data"]
    else:
        data = {"name": name, "steam_appid": appid}
    
    return data

def get_page_number(download_path, data_filename):
    try:
        rel_path = os.path.join(download_path, data_filename)
    
        rows_count = pd.read_csv(rel_path).shape[0]
        page_number = rows_count//1000
        
    except FileNotFoundError:
        page_number = 0
        print("File Not Found Error, page = {}".format(page_number))
    
    return str(page_number)
    
#%% data downloading
if __name__ == '__main__':
    
    # set file parameters
    download_path = "C:/Users/wrosz/Desktop/Python/Spyder/Projekty/006_Steam_Database_for_APPs/1_files"
    steam_app_data = "steam_app_data.csv"
    steam_index = "steam_index.txt"
    
    # gathering page number so we can continue file writing
    page_number = get_page_number(download_path=download_path, data_filename=steam_app_data)
    
    url = 'https://steamspy.com/api.php?request=all&page='+page_number
    parameters = {"request": "all"}
    
    # request 'all' from steam spy and parse into dataframe
    json_data = get_request(url, parameters=parameters)
    steam_spy_all = pd.DataFrame.from_dict(json_data, orient='index') 
    
    # generate sorted app_list from steamspy data
    app_list = steam_spy_all[['appid', 'name']].sort_values('appid').reset_index(drop=True)
    
    # export disabled to keep consistency across download sessions
    app_list.to_csv('C:/Users/wrosz/Desktop/Python/Spyder/Projekty/006_Steam_Database_for_APPs/1_files/app_list.csv', index=False)
    
    # instead read from stored csv
    app_list = pd.read_csv('C:/Users/wrosz/Desktop/Python/Spyder/Projekty/006_Steam_Database_for_APPs/1_files/app_list.csv')
    
    steam_columns = [
    'type', 'name', 'steam_appid', 'required_age', 'is_free', 'controller_support',
    'dlc', 'detailed_description', 'about_the_game', 'short_description', 'fullgame',
    'supported_languages', 'header_image', 'website', 'pc_requirements', 'mac_requirements',
    'linux_requirements', 'legal_notice', 'drm_notice', 'ext_user_account_notice',
    'developers', 'publishers', 'demos', 'price_overview', 'packages', 'package_groups',
    'platforms', 'metacritic', 'reviews', 'categories', 'genres', 'screenshots',
    'movies', 'recommendations', 'achievements', 'release_date', 'support_info',
    'background', 'content_descriptors']
    
    # overwrites last index for demonstration (would usually store highest index so can continue across sessions)
    # reset_index(download_path, steam_index)
    
    # retrieve last index downloaded from file
    index = get_index(download_path, steam_index)
    if index%1000 == 1:
        index = 0

    # wipe or creae data file and write headers if index is 0 and page_number is 0
    prepare_data_file(download_path, steam_app_data, index, steam_columns, page_number)

    # set end and chunksize for demonstration - remove to run through entire app list
    process_batches(parser=parse_steam_request, app_list=app_list, download_path=download_path, data_filename=steam_app_data, index_filename=steam_index, columns=steam_columns, begin=index, batchsize=5)
    
    Data_downloaded = pd.read_csv('C:/Users/wrosz/Desktop/Python/Spyder/Projekty/006_Steam_Database_for_APPs/1_files/steam_app_data.csv').head(15)

