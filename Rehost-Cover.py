# Rehost Cover Script
# author: hypermodified
# A python script to that will rehost a list of cover urls from random image hosts to ptpimg 

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
collage_ajax_page = config.c_site_collage_ajax_page # imports missing cover art collage ajax page
r_api_key = config.c_r_api_key # imports your RED api key 
p_api_key = config.c_p_api_key # imports your ptpIMG api key 
headers = {"Authorization": r_api_key} # sets the key value pair for accessing the RED api

# Establishes the counters for completed covers and errors
count = 0
RED_api_error = 0
ptpimg_api_error = 0
RED_replace_error = 0
cover_missing_error = 0
error_message = 0
list_error = 0

# A function to log events
def log_outcomes(torrent_id,cover_url,log_name,message):
    global log_directory
    script_name = "Rehost Cover Script"
    log_name = log_name + ".txt"
    today = datetime.datetime.now()
    log_path = os.path.join(log_directory, log_name)
    with open(log_path, 'a',encoding='utf-8') as log_name:
        log_name.write("--{:%b, %d %Y}".format(today)+ " at " +"{:%H:%M:%S}".format(today)+ " from the " + script_name + ".\n")
        log_name.write("The torrent group " + torrent_id + " " + message + ".\n")
        log_name.write("Torrent location: https://redacted.ch/torrents.php?id=" + torrent_id + "\n")
        log_name.write("Cover location: " + cover_url + "\n")
        log_name.write(" \n")  
        log_name.close()
        
def summary_text():
    global count
    global list_error
    global RED_replace_error
    global RED_api_error
    global ptpimg_api_error
    global error_message
    global cover_missing_error
    
    print("This script rehosted " + str(count) + " album covers.")  
    if  list_error ==0: 
        if RED_replace_error >= 1:
            print("--Warning: There were " + str(RED_replace_error) + " cover urls that failed being added to RED.")
            error_message +=1 # variable will increment if statement is true
        elif RED_replace_error == 0:    
            print("--Info: There were " + str(RED_replace_error) + " cover urls that failed being added to RED.") 
        if RED_api_error >= 1:
            print("--Warning: There were " + str(RED_api_error) + " covers skipped due to errors with the RED api. Please try again.")
            error_message +=1 # variable will increment if statement is true
        elif RED_api_error == 0:    
            print("--Info: There were " + str(RED_api_error) + " covers skipped due to errors with the RED api.")
        if ptpimg_api_error >= 1:
            print("--Warning: There were " + str(ptpimg_api_error) + " covers skipped due to the covers no longer being on the internet or errors with the ptpimg api. Please try again.")
            error_message +=1 # variable will increment if statement is true
        elif ptpimg_api_error == 0:    
            print("--Info: There were " + str(ptpimg_api_error) + " covers skipped due to the covers no longer being on the internet or errors with the ptpimg api.")
        if cover_missing_error >= 1:
            print("--Warning: There were " + str(cover_missing_error) + " covers skipped due to the covers no longer being on the internet or being 404 images.")
            error_message +=1 # variable will increment if statement is true
        elif cover_missing_error == 0:    
            print("--Info: There were " + str(cover_missing_error) + " covers skipped due to the covers no longer being on the internet or being 404 images.")
        if error_message >= 1:
            print("Check the logs to see which torrents and covers had errors and what they were.")
        else:
            print("There were no errors.")           
    else:
        print("The was an error loading or parsing the list of torrent ids and cover urls, please check it and try again.")

# A function to check if a website exists
def site_check(url):
    try:
        request = requests.get(url) #Here is where im getting the error
        if request.status_code == 200:
            return True
    except:
        return False
        
# A function to get the final url if a url is redirected
def final_destination(url):
    response = requests.get(url)
    if response.history:
        return response.url
    else:
        return url        

# A function that looks for images that have been replaced with 404 images
def check_404(url):
    #list of potentially problematic hosts
    host_list = {"i.imgur.com", "imgur.com", "tinyimg.io"}
    #parse url string looking for certain urls
    parsed_url = urlparse(url)
    #check parsed hostname against list
    if parsed_url.hostname in host_list:
        #if found run history
        final_url = final_destination(url)
        print("--The url was forwarded to " + final_url)
        #match final destination to known 404 image
        if parsed_url.hostname == "i.imgur.com" and final_url == "https://i.imgur.com/removed.png":
            return True
        elif parsed_url.hostname == "imgur.com" and final_url == "https://i.imgur.com/removed.png":
            return True
        elif parsed_url.hostname == "tinyimg.io" and final_url == "https://tinyimg.io/notfound":
            return True
        else:
            return False
    else:
        return False

# A function to add albums that have broken cover art to the -Torrents with broken cover art links- collage
def post_to_collage(add_id):
    global collage_ajax_page
    global headers
    # create the data 
    data = {'groupids': add_id}    
    # post to collage     
    r = requests.post(collage_ajax_page, data=data, headers=headers)  
    # report status
    status = r.json()
    if status['response']['groupsadded']:
        print("--Adding release to missing covers collage was a success.")      
    else:
        print("--Adding release to missing covers collage was a failure.")      
    
# A function that replaces the existing cover art on RED with the newly hosted one    
def post_to_RED(torrent_id,new_cover_url,original_cover_url):   
    global count 
    global headers    
    global site_ajax_page
    global RED_api_error
    global RED_replace_error
    cover_url = original_cover_url
    
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
            count +=1 # variable will increment every loop iteration
        elif status['error'] == "No changes detected.":  
            print("--Replacing the cover on RED was a " + str(status["status"]))
            print("--has already had it's cover replaced on RED.")
            print("--Logged cover being skipped due to already haveing been replaced.")
            log_name = "RED_api_error"
            log_message = "You have already replaced this cover on RED"
            log_outcomes(torrent_id,cover_url,log_name,log_message)
            RED_replace_error +=1 # variable will increment every loop iteration
        else:
            print("--THISReplacing the cover on RED was a " + str(status["status"]))
            print("--There was an issue connecting to or interacting with the RED API. If it is unstable, please try again later.")
            print("--Logged cover skipped due failed upload to RED.")
            log_name = "RED_api_error"
            log_message = "There may have been an issue connecting to the RED API. If it is unstable, please try again later"
            log_outcomes(torrent_id,cover_url,log_name,log_message)
            post_to_collage(torrent_id)
            RED_replace_error +=1 # variable will increment every loop iteration
    except:
        print("--There was an issue connecting to or interacting with the RED API. Please try again later.")
        print("--Logged cover skipped due to an issue connecting to the RED API.")
        log_name = "RED_api_error"
        log_message = "There may have been an issue connecting to the RED API. If it is unstable, please try again later"
        log_outcomes(torrent_id,cover_url,log_name,log_message)
        post_to_collage(torrent_id)
        RED_api_error +=1 # variable will increment every loop iteration
        return
        
# A function that rehosts the cover to ptpimg     
def rehost_cover(torrent_id,cover_url):
    global p_api_key
    global ptpimg_api_error

    #assemble the command for rehosting the cover
    the_command = "ptpimg_uploader -k  \"" + p_api_key + "\"" + " " + cover_url
    #print(the_command)
    original_cover_url = cover_url

    # using subprocess, rehost the cover to ptpIMG
    try:
        with Popen(the_command, stdout=PIPE, stderr=None, shell=True) as process:
            new_cover_url = process.communicate()[0].decode("utf-8")
            # test to see if ptpimg returned a url, if not there was an error
            if new_cover_url:
                new_cover_url = new_cover_url.strip()
                print("--The cover has been rehosted at " + new_cover_url)
                ptp_rehost_status = True
                return ptp_rehost_status,new_cover_url,original_cover_url 
            else:
                ptp_rehost_status = False
                print("--The cover was missing from the internet. Please replace the image manually. If the image is there, then the site resisted being scraped or there was an issue connecting to or interacting with PTPimg.")
                print("--Logged cover skipped due to it being no longer on the internet or there being an issue connecting to the ptpimg API.")
                log_name = "cover_missing"
                log_message = "albums cover is missing from the internet or the site is blocking scraping images. Please replace the image manually. If the image is there, it is possible that it was skipped due to an issue connecting to the ptpimg API. Please try again later"
                log_outcomes(torrent_id,cover_url,log_name,log_message)
                ptpimg_api_error +=1 # variable will increment every loop iteration
                post_to_collage(torrent_id)
                return ptp_rehost_status,cover_url,original_cover_url 
    except:    
        print("--There was an issue rehosting the cover art to ptpimg. Please try again later.")  
        print("--Logged cover skipped due to an issue connecting to the ptpimg API.")
        log_name = "ptpimg-api-error"
        log_message = "was skipped due to an issue connecting to the ptpimg API. Please try again later"
        log_outcomes(torrent_id,cover_url,log_name,log_message)
        ptpimg_api_error +=1 # variable will increment every loop iteration
        return            

# A function to introduce a random delay into the loop to reduce the chance of being blocked for web scraping.
def loop_delay():
    global count
    if count >=1:
        delay = randint(1,3)  # Generate a random number of seconds within this range
        print("The script is pausing for " + str(delay) + " seconds.")
        sleep(delay) # Delay the script randomly to reduce anti-web scraping blocks   

# A function to check a series of conditions on the cover url before it is attempted to be rehosted.
def url_condition_check(torrent_id,cover_url):
    global cover_missing_error
    
    #check to see if the site exists
    site_exists = site_check(cover_url)
    if site_exists == False:
        print('--Cover is no longer on the internet. The site that hosted it is gone.')
        print("--Logged missing cover, site no longer exists.")
        log_name = "cover_missing"
        log_message = "cover is no longer on the internet. The site that hosted it is gone"
        log_outcomes(torrent_id,cover_url,log_name,log_message)
        cover_missing_error +=1 # variable will increment every loop iteration
        post_to_collage(torrent_id)
        return False
    else:    
        #check to see if the cover is known 404 image
        url_checked = check_404(cover_url)
        if url_checked == True:
            print('--Cover is no longer on the internet. It was replaced with a 404 image.')
            print("--Logged missing cover, image is not on site.")
            log_name = "cover_missing"
            log_message = "cover is no longer on the internet. It was replaced with a 404 image"
            log_outcomes(torrent_id,cover_url,log_name,log_message)
            cover_missing_error +=1 # variable will increment every loop iteration
            # if it is a 404 image post it to the missing covers collage
            post_to_collage(torrent_id)
            return False
        else:
            return True

#A function that check if text file exists, loads it, loops through the lines, get id and url
def loop_rehost():
    global list_error
    #load the list of torrent ids and cover urls and cycle through them
    #check to see if there is an text file
    #file_exists = os.path.exists('list.txt')
    
    if os.path.exists('list.txt'):
        #open the txt file and get the torrent group ID and cover url
        '''try:'''
        with open('list.txt',encoding='utf-8') as f:
            for line in f:
                line_values = line.split(",")
                torrent_id = line_values[0]
                cover_url = line_values[1]
                cover_url = cover_url.strip()
                print("")
                print("Rehosting:")
                print("--The torrent ID is " + torrent_id)
                print("--The url for the cover art is " + cover_url)
                
                #check to see if the site is there and whether the image is a 404 image
                site_condition = url_condition_check(torrent_id,cover_url)
                if site_condition == True:
                    #run the rehost cover function passing it the torrent_id and cover_url
                    ptp_rehost_status,new_cover_url,original_cover_url = rehost_cover(torrent_id,cover_url)
                    # trigger function to post cover to RED
                    if ptp_rehost_status == True:
                        post_to_RED(torrent_id,new_cover_url,original_cover_url)
                        
                #introduce a delay after the first cover is rehosted
                loop_delay()        

        '''except:
            print("--There was an issue parsing the text file and the cover could not be rehosted.")  
            list_error +=1 # variable will increment every loop iteration
            return'''
    else:            
        print("--The list of ids and album covers is missing.")  
        list_error +=1 # variable will increment every loop iteration
        
# The main function that controls the flow of the script
def main():
    #intro text
    print("")
    print("You spin me right 'round, baby, right 'round...")

    # Run the function to loop through the list.txt file and rehost the cover art               
    loop_rehost()   

    # Summary text
    print("")
    print("Like a record, baby, right 'round, 'round, 'round...")
    # run summary text function to provide error messages
    summary_text()        
 
if __name__ == "__main__":
    main()
