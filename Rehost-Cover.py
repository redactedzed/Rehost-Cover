# Rehost Cover Script
# author: hypermodified

# Import dependencies
import os  # Imports functionality that let's you interact with your operating system
import requests # Imports the ability to make web or api requests
import datetime # Imports functionality that lets you make timestamps
import ptpimg_uploader # imports the tool which lets you upload to ptpimg
import config # imports the config file where you set your API key, directories, etc
import json # imports json
from random import randint # Imports functionality that lets you generate a random number
from time import sleep # Imports functionality that lets you pause your script for a set period of time
import subprocess  # Imports functionality that let's you run command line commands in a script
from subprocess import PIPE, Popen
from urllib.parse import urlparse

# Before running this script install the dependencies
# pip install ptpimg_uploader
# pip install pyperclip

# Import directories from config file 
list_directory = config.c_list_directory # imports the directory path to where your albums are
log_directory = config.c_log_directory # imports the directory path to where you want to write your logs

# Imports site and API information from config file
site_ajax_page = config.c_site_ajax_page # imports gazelle ajax page
r_api_key = config.c_r_api_key # imports your RED api key 
p_api_key = config.c_p_api_key # imports your ptpIMG api key 
headers = {"Authorization": r_api_key} # sets the key value pair for accessing the RED api

# Establishes the counters for completed covers and errors
count = 0
RED_api_error = 0
ptpimg_api_error = 0
RED_replace_error = 0
error_message = 0
list_error = 0

#intro text
print("")
print("You spin me right 'round, baby, right 'round...")

# A function to log events
def log_outcomes(t,c,p,m):
    global log_directory
    script_name = "Rehost Cover Script"
    today = datetime.datetime.now()
    log_name = p
    torrent_id = t
    cover_url = c
    message = m
    log_path = log_directory + os.sep + log_name + ".txt"
    with open(log_path, 'a',encoding='utf-8') as log_name:
        log_name.write("--{:%b, %d %Y}".format(today)+ " at " +"{:%H:%M:%S}".format(today)+ " from the " + script_name + ".\n")
        log_name.write("The torrent group " + torrent_id + " " + message + ".\n")
        log_name.write("Torrent location: https://redacted.ch/torrents.php?id=" + torrent_id + "\n")
        log_name.write("Cover location: " + cover_url + "\n")
        log_name.write(" \n")  
        log_name.close()

# A function that looks for images that have been replaced with 404 images
def check_404(u):
    print(u)
    #list of potentially problematic hosts
    host_list = {"i.imgur.com", "imgur.com", "tinyimg.io", "i.ibb.co"}
    #parse url string looking for certain urls
    parsed_url = urlparse(u)
    print(parsed_url.hostname)
    #check parsed hostname against list
    if parsed_url.hostname in host_list:
        print("bad")
    else:
        print("good")
#if found run history
    #if history = bad url then log
    #else continue
#else continue
        
# A function that rehosts the cover and adds the cover to the site        
def rehost_cover(t_id,cov):
    global count
    global p_api_key
    global headers
    global site_ajax_page
    global RED_api_error
    global ptpimg_api_error
    global RED_replace_error
    
    # get the variables from the loop
    torrent_id = t_id
    cover_url = cov

    #assemble the command for rehosting the cover
    the_command = "ptpimg_uploader -k  \"" + p_api_key + "\"" + " " + cover_url
    #print(the_command)

    # using subprocess, rehost the cover to ptpIMG
    try:
        with Popen(the_command, stdout=PIPE, stderr=None, shell=True) as process:
            new_cover_url = process.communicate()[0].decode("utf-8")
            # test to see if ptpimg returned a url, if not there was an error
            if new_cover_url != None: 
                new_cover_url = new_cover_url.strip()
                print("--The cover has been rehosted at " + new_cover_url)
                
                # create the ajax page and data
                ajax_page = site_ajax_page
                ajax_page = ajax_page + torrent_id   
                edit_message = "Automatically rehosted cover to PTPimg"    
                data = {'summary': edit_message,
                        'image': new_cover_url}

                # replace the cover art link on RED and leave edit summary
                try:
                    r = requests.post(ajax_page, data=data, headers=headers)
                    status = r.json()
                    if status['status'] == "success":
                        print("--Replacing the cover on RED was a " + str(status["status"]))
                        #print("--" + str(status["response"]))
                        count +=1 # variable will increment every loop iteration
                    else:
                        print("--Replacing the cover on RED was a " + str(status["status"]))
                        print("--" + str(status["response"]))
                        RED_replace_error +=1 # variable will increment every loop iteration
                except:
                    print("--The cover was missing from the internet. Please replace the image manually. If you it is there then there was an issue connecting to or interacting with the RED API. Please try again later.")
                    print("--Logged cover skipped due to it being no longer on the internet or there being an issue connecting to the RED API.")
                    log_name = "red-api-error"
                    log_message = "was missing from the internet. Please replace the image manually. If the image is there, there may have been an issue connecting to the RED API. Please try again later"
                    log_outcomes(torrent_id,cover_url,log_name,log_message)
                    RED_api_error +=1 # variable will increment every loop iteration
                    return
            else:
                print("There was a problem with uploading the image to PTPimg.")
    except:    
        print("--There was an issue rehosting the cover art to ptpimg. Please try again later.")  
        print("--Logged cover skipped due to an issue connecting to the ptpimg API..")
        log_name = "ptpimg-api-error"
        log_message = "was skipped due to an issue connecting to the ptpimg API. Please try again later"
        log_outcomes(torrent_id,cover_url,log_name,log_message)
        ptpimg_api_error +=1 # variable will increment every loop iteration
        return               

#A function that check if text file exists, loads it, loops through the lines, get id and url
def loop_rehost():
    global count
    global list_error
    #load the list of torrent ids and cover urls and cycle through them
    #check to see if there is an text file
    file_exists = os.path.exists('list.txt')
    
    if file_exists == True:
        #open the txt file and get the torrent group ID and cover url
        try:
            with open('list.txt',encoding='utf-8') as f:
                for line in f:
                    line_values = line.split(",")
                    torrent_id = line_values[0]
                    cover_url = line_values[2]
                    cover_url = cover_url.strip()
                    print("")
                    print("Rehosting:")
                    print("--The torrent ID is " + torrent_id)
                    print("--The url for the cover art is " + cover_url)
                    #check to see if the cover is known 404 image
                    check_404(cover_url)
                    #run the rehost cover function passing it the torrent_id and cover_url
                    rehost_cover(torrent_id,cover_url)
                    #introduce a delay after the first cover is rehosted
                    if count >=1:
                        delay = randint(1,5)  # Generate a random number of seconds
                        print("The script is pausing for " + str(delay) + " seconds.")
                        sleep(delay) # Delay the script randomly to reduce anti-web scraping blocks    
        except:
            print("--There was an issue parsing the text file and the cover could not be rehosted.")  
            list_error +=1 # variable will increment every loop iteration
            return
    else:            
        print("--The list of ids and album covers is missing.")  
        list_error +=1 # variable will increment every loop iteration
        
# Run the funtion to loop through the list.txt file and rehost the cover art               
loop_rehost()   

# Summary text
print("")
print("Like a record, baby, right 'round, 'round, 'round...")
print("This script rehosted " + str(count) + " album covers.")  
if  list_error ==0: 
    if RED_replace_error >= 1:
        print("--Warning: There were " + str(RED_replace_error) + " cover urls that failed being added to RED.")
        error_message +=1 # variable will increment if statement is true
    elif RED_replace_error == 0:    
        print("--Info: There were " + str(RED_replace_error) + " cover urls that failed being added to RED.") 
    if RED_api_error >= 1:
        print("--Warning: There were " + str(RED_api_error) + " covers skipped due to the covers no longer being on the internet or errors with the RED api. Please try again.")
        error_message +=1 # variable will increment if statement is true
    elif RED_api_error == 0:    
        print("--Info: There were " + str(RED_api_error) + " covers skipped due to the covers no longer being on the internet or errors with the RED api.")
    if ptpimg_api_error >= 1:
        print("--Warning: There were " + str(ptpimg_api_error) + " covers skipped due to errors with the ptpimg api. Please try again.")
        error_message +=1 # variable will increment if statement is true
    elif ptpimg_api_error == 0:    
        print("--Info: There were " + str(ptpimg_api_error) + " covers skipped due to errors with the ptpimg api.")
    if error_message >= 1:
        print("Check the logs to see which torrents and covers had errors and what they were.")
    else:
        print("There were no errors.")           
else:
    print("The was an error loading or parsing the list of torrent ids and cover urls, please check it and try again.")