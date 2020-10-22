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
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from threading import Thread
from bs4 import BeautifulSoup

def open_dauphinpropertyinfo(driver):
    """ open dauphinprofertyinfo site.
    """
    lastname = ['greenview','cnh']
    table_data = {}
    for name in lastname:
        table_data[name]=get_table_expand(driver,name)
    with open('result_table_expand.json', 'w') as outfile:
        json.dump(table_data, outfile)


def get_table_expand(driver,lastname):
    api_url = 'http://www.dauphinpropertyinfo.org'
    wait = WebDriverWait(driver, 0.5)
    driver.get(api_url)

    try:
        driver.execute_script("document.getElementById('search-parcel').click()")
        # radio_button = driver.find_element_by_xpath('//input[@id="search-parcel"]')
        # ActionChains(driver).move_to_element(radio_button).click().perform()
        driver.implicitly_wait(3)
        print('Radio button Clicked')
    except NoSuchElementException:
        print("Error radio button.")
    
    try:
        driver.execute_script("document.getElementById('last_name').value='{}'".format(lastname))
        # lastname_textfield = driver.find_element_by_xpath('//input[@name="last_name"]')
        # ActionChains(driver).move_to_element(lastname_textfield).click().send_keys(lastname).perform()
        driver.implicitly_wait(2)
    except NoSuchElementException:
        print('Error inserting last name')

    try:
        driver.execute_script("document.getElementById('search').click()")
        # search_button = driver.find_element_by_xpath('//input[@id="search"]')
        # ActionChains(driver).move_to_element(search_button).click().perform()
        driver.implicitly_wait(2)
        print('Search Button Clicked')
    except NoSuchElementException:
        print("Error search button.")
    try:
        key_list = get_parcel_number_list(lastname)
        table_data = {}
        for i in range(0,len(key_list)):
            if i > 0:
                driver.execute_script("document.getElementsByClassName('all ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only')[0].click()")
                time.sleep(5)
            query = "document.querySelectorAll('#parcelGrid tbody tr')[" + str(i+1) + "].click()"
            driver.execute_script(query)
            time.sleep(5)
            table_data[key_list[i]] = get_tables(key_list[i])
    except Exception as e:
        print('Exception Error issue: \n{}'.format(e))
    return table_data


def get_tables(key_url):
    time.sleep(2)
    table_list = driver.find_elements_by_xpath('//table[contains(@class,"datagrid")]')
    time.sleep(1)
    table_data = {}
    request_url = 'http://www.dauphinpropertyinfo.org/view/RE/'
    index = 0
    for tl in table_list:
        index += 1
        if index == 1:
            table_response = requests.get(request_url + key_url + '/2019')
            table_data_list = get_fixed_table(table_response)
        elif index < 3:
            continue
        else:
            table_data_list = get_table_detail(tl)
        table_data[get_table_title(tl)]=table_data_list
    return table_data

def get_fixed_table(table_html):
    parsed_html = BeautifulSoup(table_html.content,"html.parser")
    table_content = {}
    table = parsed_html.find('table',attrs={'class':'datagrid'})
    for col in table.find_all('td'):
        col_title = col_content = ""
        if col.find('b'):
            if col.find('b') == "Property ID":
                continue
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
                # col_title = 'Tax year'
                # content_list = []
                # for i in col.find_all('option'):
                #     content_list.append(i.text)
                # col_content = content_list
        table_content[col_title]=col_content
    return table_content

def get_table_title(table):
    title = table.find_elements_by_xpath('.//th')
    return title[0].text


def get_table_detail(table):
    rows = table.find_elements_by_xpath('.//tr')
    if len(rows) > 3:
        table_data = get_2more_table(table)
    else:
        table_data = get_2rows_table(table)
    return table_data


def get_2more_table(table):
    more_table_data = get_2rows_table(table)
    index = 0
    item_content = {}
    for row in table.find_elements_by_xpath('.//tr'):
        index = index + 1
        if index < 4:
            continue
        elif index > 4:
            if row.find_elements_by_xpath('.//td[@colspan="10"]'):
                more_table_data[item_title.text]=item_content       
                item_content = {}
        if row.find_elements_by_xpath('.//td[@colspan="10"]'):
            item_title = row.find_element_by_xpath('.//td/strong')
        else:
            col_list = []
            for col in row.find_elements_by_xpath('.//td'):
                    col_list.append(col.text)
            item_content[col_list[0]]=col_list[1]
            if col_list[2] != '':
                item_content[col_list[2]]=col_list[3]
    more_table_data[item_title.text]=item_content
    return more_table_data


def get_2rows_table(table):
    row_cnt = index = 0
    item_list = []
    for row in table.find_elements_by_xpath('.//tr'):
        index += 1
        if index > 3:
            break
        for td_cell in row.find_elements_by_xpath('.//td'):
            row_cnt = row_cnt + 1
            item_list.append(td_cell.text)
    table_data = {}
    row_cnt /= 2
    row_cnt = int(row_cnt)
    index = 0
    for index in range(row_cnt):
        table_data[item_list[index]] = item_list[index + row_cnt]
    return table_data
    

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
    parser = argparse.ArgumentParser(description='Module that extracts slates list and projection data.')
    # parser.add_argument('-s', '--lastname', metavar='S', type=str,
    #     help='Determines the lastname to extract data from.')
    args = vars(parser.parse_args())
    
    driver = get_geckodriver()
    driver.set_window_position(0, 0)
    driver.set_window_size(1920, 1080)
    
    
    try:
        open_dauphinpropertyinfo(driver)
    except Exception as e:
        print('Stopped due to: \n{}'.format(e))
    finally:
        driver.close()
    
