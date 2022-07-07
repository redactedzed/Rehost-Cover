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
headers = {"Authorization": r_api_key, "User-Agent": "Rehost-Cover-Script/0.5"} # sets the key value pairs for accessing the RED api


# Establishes the counters for completed covers and errors
count = 0
total_count = 0
RED_api_error = 0
ptpimg_api_error = 0
RED_replace_error = 0
cover_missing_error = 0
collage_message = 0
collage_error = 0
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
        
# A function that writes a summary of what the script did at the end of the process        
def summary_text():
    global count
    global total_count
    global list_error
    global RED_replace_error
    global RED_api_error
    global ptpimg_api_error
    global error_message
    global cover_missing_error
    global collage_message
    global collage_error
    
    print ("")
    print("This script rehosted " + str(count) + " album covers out of " + str(total_count) + " covers.")  
    print ("")
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
            print("--Warning: There were " + str(cover_missing_error) + " covers skipped due to the covers no longer being on the internet or being a 404 image.")
            error_message +=1 # variable will increment if statement is true
        elif cover_missing_error == 0:    
            print("--Info: There were " + str(cover_missing_error) + " covers skipped due to the covers no longer being on the internet or being a 404 image.")
        if collage_message >= 1:
            print("--Info: There were " + str(collage_message) + " albums added to a collage due to missing or bad cover art.")
            error_message +=1 # variable will increment if statement is true
        elif collage_message == 0:    
            print("--Info: There were " + str(collage_message) + " albums added to a collage due to missing or bad cover art.")
        if collage_error >= 1:
            print("--Warning: There were " + str(collage_error) + " albums that had missing or bad cover art but adding them a collage failed.")
            error_message +=1 # variable will increment if statement is true
        elif collage_error == 0:    
            print("--Info: There were " + str(collage_error) + " albums that had missing or bad cover art but adding them a collage failed.")
        if error_message >= 1:
            print("Check the logs to see which torrents and covers had errors and what they were.")
        else:
            print("There were no errors.")           
    else:
        print("The was an error loading or parsing the list of torrent ids and cover urls, please check it and try again.")

# A function to check if a website exists
def is_url_valid(cover_url):
    try:
        request = requests.get(cover_url) #Here is where im getting the error
        if request.status_code == 200:
            return True
    except:
        return False
        
# A function to get the final url if a cover url is redirected
def final_destination(cover_url):
    response = requests.get(cover_url)
    if response.history:
        return response.url
    else:
        return cover_url        

# A function that looks for images that have been replaced with 404 images
def check_404_image(cover_url):
    #list of potentially problematic hosts
    host_list = {"i.imgur.com", "imgur.com", "tinyimg.io"}
    #parse cover url string looking for certain urls
    parsed_url = urlparse(cover_url)
    #check parsed hostname against list
    if parsed_url.hostname in host_list:
        #if found run history
        final_url = final_destination(cover_url)
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

# A function that looks for images that have been hosted on sites with known issues
def check_bad_host(cover_url):
    #list of potentially problematic hosts
    host_list = {"img.photobucket.com", "upload.wikimedia.org"}
    #parse cover url string looking for certain urls
    parsed_url = urlparse(cover_url)
    #check parsed hostname against list
    if parsed_url.hostname in host_list:
        return True
    else:
        return False

# A function to add albums that have broken cover art to the -Torrents with broken cover art links- collage
def post_to_collage(torrent_id,cover_url,collage_type):
    global collage_ajax_page
    global headers
    global collage_message
    global collage_error
    
    #assign collage ID, name and URL
    if collage_type == "broken_missing_covers_collage":
        collage_id = "31445"
        collage_name = "\'Torrents with broken cover art links\'"
        collage_url = "https://redacted.ch/collages.php?id=" + collage_id
    elif collage_type == "bad_covers_collage":    
        collage_id = "31735"   
        collage_name = "\'Torrents with poor quality cover art images\'"   
        collage_url = "https://redacted.ch/collages.php?id=" + collage_id
    
    # create the ajax page and data
    ajax_page = collage_ajax_page + collage_id
    data = {'groupids': torrent_id}    
    # post to collage 
    r = requests.post(ajax_page, data=data, headers=headers)  
    # report status
    status = r.json()
    if status['response']['groupsadded']:
        print("--Adding release to the " + collage_name + " collage was a success.")   
        print("--Logged cover being added to " + collage_name + ".")
        log_name = "collage_added"
        log_message = "had bad or missing art and was added to the " + collage_name + " collage. \nCollage Location: " + collage_url + "\nTorrent info below"
        log_outcomes(torrent_id,cover_url,log_name,log_message)
        collage_message +=1 # variable will increment every loop iteration        
    elif status['response']['groupsduplicated']: 
        print("--Error: Adding release to " + collage_name + " collage was a failure, the album was already in the collage.")   
        print("--Logged cover failing to be added to " + collage_name + " due to it already being in the collage.")
        log_name = "collage_fail"
        log_message = "had bad or missing art and failed to be added to the " + collage_name + " due to it already being in the collage. \nCollage Location: " + collage_url + "\nTorrent info below"
        log_outcomes(torrent_id,cover_url,log_name,log_message)
        collage_error +=1 # variable will increment every loop iteration        
    else:
        print("--Error: Adding release to " + collage_name + " collage was a failure.")     
        print("--Logged cover failing to be added to " + collage_name + ".")
        log_name = "collage_fail"
        log_message = "had bad or missing art and failed to be added to the " + collage_name + ". \nCollage Location: " + collage_url + "\nTorrent info below"
        log_outcomes(torrent_id,cover_url,log_name,log_message) 
        collage_error +=1 # variable will increment every loop iteration       
    
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
            print("--Success: Replacing the cover on RED was a " + str(status["status"]))
            count +=1 # variable will increment every loop iteration
        elif status['error'] == "No changes detected.":  
            print("--Failure: Replacing the cover on RED was a " + str(status["status"]))
            print("--This album has already had it's cover replaced on RED.")
            print("--Logged cover being skipped due to already haveing been replaced.")
            log_name = "RED_api_error"
            log_message = "has already had it's cover replaced on RED."
            log_outcomes(torrent_id,cover_url,log_name,log_message)
            RED_replace_error +=1 # variable will increment every loop iteration
        else:
            print("--Failure: Replacing the cover on RED was a " + str(status["status"]))
            print("--There was an issue connecting to or interacting with the RED API. If it is unstable, please try again later.")
            print("--Logged cover skipped due failed upload to RED.")
            log_name = "RED_api_error"
            log_message = "There may have been an issue connecting to the RED API. If it is unstable, please try again later"
            log_outcomes(torrent_id,cover_url,log_name,log_message)
            # if it is a missing image, post it to the missing covers collage
            collage_type="broken_missing_covers_collage"
            post_to_collage(torrent_id,cover_url,collage_type)
            RED_replace_error +=1 # variable will increment every loop iteration
    except:
        print("--Failure: There was an issue connecting to or interacting with the RED API. Please try again later.")
        print("--Logged cover skipped due to an issue connecting to the RED API.")
        log_name = "RED_api_error"
        log_message = "There may have been an issue connecting to the RED API. If it is unstable, please try again later"
        log_outcomes(torrent_id,cover_url,log_name,log_message)
        # if it is a missing image, post it to the missing covers collage
        collage_type="broken_missing_covers_collage"
        post_to_collage(torrent_id,cover_url,collage_type)
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
                print("--Failure: The cover was missing from the internet. Please replace the image manually. If the image is there, then the site resisted being scraped or there was an issue connecting to or interacting with PTPimg.")
                print("--Logged cover skipped due to it being no longer on the internet or there being an issue connecting to the ptpimg API.")
                log_name = "cover_missing"
                log_message = "albums cover is missing from the internet or the site is blocking scraping images. Please replace the image manually. If the image is there, it is possible that it was skipped due to an issue connecting to the ptpimg API. Please try again later"
                log_outcomes(torrent_id,cover_url,log_name,log_message)
                ptpimg_api_error +=1 # variable will increment every loop iteration
                # if it is a missing image, post it to the missing covers collage
                collage_type="broken_missing_covers_collage"
                post_to_collage(torrent_id,cover_url,collage_type)
                return ptp_rehost_status,cover_url,original_cover_url 
    except:    
        print("--Failure: There was an issue rehosting the cover art to ptpimg. Please try again later.")  
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
    site_exists = is_url_valid(cover_url)
    if site_exists == False:
        print('--Failure: Cover is no longer on the internet. The site that hosted it is gone.')
        print("--Logged missing cover, site no longer exists.")
        log_name = "cover_missing"
        log_message = "cover is no longer on the internet. The site that hosted it is gone"
        log_outcomes(torrent_id,cover_url,log_name,log_message)
        cover_missing_error +=1 # variable will increment every loop iteration
        # if it is a missing image, post it to the missing covers collage
        collage_type="broken_missing_covers_collage"
        post_to_collage(torrent_id,cover_url,collage_type)
        return False
    else:    
        #check to see if the cover is known 404 image
        url_checked = check_404_image(cover_url)
        if url_checked == True:
            print('--Failure: Cover is no longer on the internet. It was replaced with a 404 image.')
            print("--Logged album skipped due to bad host.")
            log_name = "cover_missing"
            log_message = "cover is no longer on the internet. It was replaced with a 404 image"
            log_outcomes(torrent_id,cover_url,log_name,log_message)
            cover_missing_error +=1 # variable will increment every loop iteration
            # if it is a 404 image, post it to the missing covers collage
            collage_type="broken_missing_covers_collage"
            post_to_collage(torrent_id,cover_url,collage_type)
            return False
        else:  
            #check to see if the cover is hosted on sites with known issues
            host_checked = check_bad_host(cover_url)
            if host_checked == True:
                print('--Failure: Cover skipped due to it being on a site that has watermarked or tiny images.')
                print("--Logged cover as missing cover, image is watermarked or tiny.")
                log_name = "cover_missing"
                log_message = "cover was skipped due to it being hosted on a site that has watermarked or tiny images"
                log_outcomes(torrent_id,cover_url,log_name,log_message)
                cover_missing_error +=1 # variable will increment every loop iteration
                # if it is a bad cove host, post it to the bad covers collage
                collage_type="bad_covers_collage"
                post_to_collage(torrent_id,cover_url,collage_type)
                return False
            else:                        
                return True

#A function that check if text file exists, loads it, loops through the lines, get id and url
def loop_rehost():
    global list_error
    global list_directory
    global total_count
    
    #assemble list path
    list_path = os.path.join(list_directory, "list.txt")
    
    #load the list of torrent ids and cover urls and cycle through them
    #check to see if there is an text file
    if os.path.exists(list_path):
        #open the txt file and get the torrent group ID and cover url
        try:
            with open(list_path,encoding='utf-8') as f:
                for line in f:
                    line_values = line.split(",")
                    torrent_id = line_values[0]
                    cover_url = line_values[1]
                    cover_url = cover_url.strip()
                    print("")
                    print("Rehosting:")
                    total_count +=1 # variable will increment every loop iteration
                    print("--The group url is https://redacted.ch/torrents.php?id=" + torrent_id)
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

        except FileNotFoundError:
            print("--Error: The list.txt file is missing or named something else and the cover could not be rehosted. Please check it.")  
            list_error +=1 # variable will increment every loop iteration
            return
        except IndexError:
            print("--Error: There was an issue parsing the list.txt file and the cover could not be rehosted. It was likely due to a blank line existing either before or after the list of links. Please check it.")  
            list_error +=1 # variable will increment every loop iteration
            return
    else:            
        print("--The list of ids and album covers is missing.")  
        list_error +=1 # variable will increment every loop iteration
        
# The main function that controls the flow of the script
def main():
    try:
        #intro text
        print("")
        print("You spin me right 'round, baby, right 'round...")

        # Run the function to loop through the list.txt file and rehost the cover art               
        loop_rehost()   

    finally:
        # Summary text
        print("")
        print("Like a record, baby, right 'round, 'round, 'round...")
        # run summary text function to provide error messages
        summary_text()   
        print("")     
 
if __name__ == "__main__":
    main()
