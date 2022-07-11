# Rehost-Cover
### A python script to that will rehost a list of cover urls from random image hosts to ptpimg 

A Gazelle site with a large contributor base will have cover art hosted all over the internet.  Much of this art disappears with time, as image hosts close, stores stop carrying albums, blogs shut down or other reasons.  It is ideal for a gazelle site to have its cover art on a dedicated image host.  This script can take a list produced from a database dump, loops through it, and re-hosts the art to a chosen image host.

This script does a number of things to ensure the quality of what it is rehosting. This script will make sure the image host and image are there and logs it, if either is missing. It will also identify common 404 images and not rehost those.  Finally, it has a filter for problematic image hosts that watermark or force images to be tiny. For all of these missing or broken images, it will log them, provide messaging for you, and post them to a collage on the Gazelle site for manual handling.

This script has been tested on Windows 10, Ubuntu Linux 20.04.4 LTS and macOS 12 (Monterey).

## Requirements
- Python 3.10 (or higher)
- API key for the Gazelle site
- API key for your image host

There is intent to make this more generic someday, but for now the script makes some assumptions based around RED and ptpimg.

## Install and set up
1) Clone this script to wherever you want to run it from.
2) Install [Poetry](https://python-poetry.org/docs/#installation) to manage dependencies.
   1) Alternatively, manually install the dependencies in `pyproject.toml`
3) Run `poetry install --no-dev --remove-untracked` to set up a virtual Python environment, and install dependencies into it.
4) Copy/rename `config.py.example` to `config.py`
5) Edit config.py, to set the following values:
   - `LIST_PATH`
   - `LOG_PATH`
   - `RED_API_KEY`
   - `PTPIMG_API_KEY`

## Running
1) Copy your input CSV file to the path specified in `LIST_PATH`. This file will likely be provided by a Gazelle site developer.
2) `poetry run python3 Rehost-Cover.py` to start the script. When it finishes it will output how many album covers it rehosted.

The script will write log output to `LOG_PATH` for any art it was unable to rehost. In some cases, connection or API issues, you might want to retry the failed entries. In others, such as "the art is no longer on the internet", you will want to check in case the art is actually there and just at a weird URL. If it isn't on the site find a copy and consider adding it to the site. 

## Input file format
The input file is a CSV with the following format:
```
"ID","WikiImage"
123,"http://bad.host/image.jpg"
456,"http://whatimg.com/abcd.jpg"
```
