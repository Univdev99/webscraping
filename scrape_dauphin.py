import argparse
import datetime
import time
import glob
import requests
import pickle
import os
import csv
import json
from collections import OrderedDict
from scraping_common import *
from bs4 import BeautifulSoup


def get_dauphinpropertyinfo():
    """ open dauphinprofertyinfo site and get table data.
    """
    lastname_list = ['greenview','cnh']
    request_url = 'http://www.dauphinpropertyinfo.org/view/RE/'
    json_table=[]
    for name in lastname_list:
        parcel_number_list = get_parcel_number_list(name)
        for number in parcel_number_list:
            table_response = requests.get(request_url + number + '/2019')
            table_data_item = get_fixed_table(name,table_response)
            json_table.append(table_data_item)
    with open('result.json', 'w') as outfile:
        json.dump(json_table, outfile)
    create_csv(json_table)

def create_csv(json_table):
    f = csv.writer(open("result.csv", "w+"))

    # Write CSV Header, If you dont need that, remove this line
    f.writerow(["Lastname", "Property ID", "Image", "Township", "Property Use", "Neighborhood", "Site Address", "Owner Name and Address", "Mailing Name and Address"])

    for x in json_table:
        f.writerow([x["Lastname"],
                    x["Property ID"],
                    x["Image"],
                    x["Township"],
                    x["Property Use"],
                    x["Neighborhood"],
                    x["Site Address"],
                    x["Owner Name and Address"],
                    x["Mailing Name and Address"]])
def get_fixed_table(name,table_html):
    parsed_html = BeautifulSoup(table_html.content,"html.parser")
    table_content = {}
    table_content['Lastname']=name
    table = parsed_html.find('table',attrs={'class':'datagrid'})
    for col in table.find_all('td'):
        col_title = col_content = ""
        if col.find('b'):
            col_title = col.find('b').text.strip()
            col_content = col.find('p').text.strip()
            # for c in col.find_all('p'):
            #     content_list.append(c.text)
        else:
            if col.find(string='Images'):
                col_title = 'Image'
                if col.find('a'):
                    col_list = col.find_all('img')
                    col_content_list = []
                    for c in col_list:
                        col_content_list.append(c.get('data-src'))
                    col_content = col_content_list
                
            else:
                continue
            # else:
            #     col_title = 'Tax year'
            #     for i in col.find_all('option'):
            #         content_list.append(i.text)
        table_content[col_title]=col_content
    
    return table_content

def get_parcel_number_list(name):
    search_url = 'http://www.dauphinpropertyinfo.org/search'
    form_data = {'search_method' : 'search-parcel','last_name' : name}
    header = {'Content-Type': 'application/x-www-form-urlencoded'}
    search_response = requests.post(search_url, data = form_data, headers = header)
    json_response = json.loads(search_response.text)
    json_list = json_response["results"]
    parcel_num_list = []
    for parcel_number in json_list:
        if isinstance(parcel_number, str) and "000-0000" in parcel_number :
            parcel_num_list.append(parcel_number)
    return parcel_num_list

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Module that extracts table data using request.')

    args = vars(parser.parse_args())
    
    try:
        get_dauphinpropertyinfo()
    except Exception as e:
        print('Stopped due to: \n{}'.format(e))
