# Rehost-Cover
### A python script to that will rehost a list of cover urls from random image hosts to ptpimg 

A gazelle site with a large contributor base will have cover art hosted all over the internet.  Much of this art disapears with time, as image hosts close, stores stop carrying albums, blogs shut down or other reasons.  It is ideal for a gazzelle site to have it's cover art on a dedicated image host.  This script can take a list produced from a database dump, loops through it, and re-hosts the art to a chosen image host. The list needs to be named list.txt and each line must contain a group ID and a cover-art url, seperated by a comma.

This script does a number of things to ensure the quality of what it is rehosting. This script will make sure the image host and image are there and logs it, if either is missing. It will also identify common 404 images and not rehost those.  Finally, it has a filter for problematic image hosts that watermark or force images to be really small. For all of these missing or broken images, it will log them, provide messaging for you, and it will post them to a collage on the gazelle site so they can be manually fixed.

In order to use this script you will need API keys to both the gazelle site and the preferred image host. It also has a dependency on the 
ptpimg-uploader script which can be found here: https://github.com/theirix/ptpimg-uploader

This script has been tested on Windows 10 and Ubuntu Linux.

## Install and set up
1. Clone this script where you want to run it.

2. Follow the instructions on the ptpimg-uploader script readme to install and set up that tool: https://github.com/theirix/ptpimg-uploader

to install it:

```
pip install ptpimg_uploader
```

note: you may also need to install pyclip to get it to work. you can find that here: https://pypi.org/project/pyclip/

to install it:

```
pip install pyclip
```

3. In the directory the script is in, make a copy of test-config.py and rename it config.py

4. Edit config.py to set up or specify two directories you will be using:
  -The directory where the list.txt file will be stored
  -A directory to store the log files the script creates

5. Edit config.py to add in your API keys:
  1. Your gazelle site API key
  2. Your image host API key

6. Then add your list.txt file to the folder you specified. Make sure it doesn't have any blank lines before or after the data.

7. Then run the script from the command line.  When it finishes it will output how many album covers it rehosted.

```
Rehost-Cover.py
```

It will also create logs of any albums it was unable to rehost album covers for and save to the logs folder with a short explanation of what went wrong. In some cases, connection or api issues, you might want to rerun those folders. In others, such as "the art is no longer on the internet", you will want to check in case the art is actually there and just at a weird URL. If it isn't on the site find a copy and consider adding it to the site. 
