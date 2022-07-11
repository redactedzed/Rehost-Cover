# Rehost Cover Script
# author: hypermodified
# A python script to that will rehost a list of cover urls from random image hosts to ptpimg

# Import dependencies
import datetime  # Timestamps
import os  # OS-specific file paths
import sys  # References to STDOUT/STDERR
from csv import DictReader  # For parsing the input CSV file
from enum import Enum, IntEnum, unique, auto  # Enumeration types
from io import BytesIO, TextIOWrapper  # handle downloaded images as in-memory files, log file handles
from random import randint  # Imports functionality that lets you generate a random number
from time import sleep  # Imports functionality that lets you pause your script for a set period of time
from urllib.parse import urlparse  # URL parsing

import requests  # Imports the ability to make web or api requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from ratelimit import limits, sleep_and_retry

import config  # imports the config file where you set your API key, directories, etc

# Before running this script install the dependencies
# pip install ptpimg_uploader
# pip install pyperclip

SCRIPT_NAME = "Rehost Cover Script"

USER_AGENT = "Rehost-Cover-Script/0.5"

# Imports site and API information from config file
SITE_AJAX_PAGE = config.c_site_ajax_page  # imports gazelle ajax page
COLLAGE_AJAX_PAGE = config.c_site_collage_ajax_page  # imports missing cover art collage ajax page
R_API_KEY = config.c_r_api_key  # imports your RED api key
P_API_KEY = config.c_p_api_key  # imports your ptpIMG api key

HTTP_TIMEOUT = 20

LOW_QUALITY_HOSTS = {
    "img.photobucket.com",
    "upload.wikimedia.org",
}

BAD_HOSTS = {
    "images.junostatic.com",
    "115.imagebam.com",
    "www.pixhoster.info",
    "img4.hostingpics.net",
    "funkyimg.com",
    "www.freeimage.us",
    "imageshwcdn.junodownload.com",
    "shrani.si",
    "imghst.co",
    "i.xomf.com",
    "i.imgsafe.org",
    "images.coveralia.com",
    "www.mele.com",
    "www.israbox.co",
    "whatimg.com",
    "www.newzikstreet.com",
    "assets.audiomack.com",
    "upload.ouliu.net",
    "mp3fast.org"
}

TRICKY_HOSTS: dict[str, str] = {
    "i.imgur.com": "https://i.imgur.com/removed.png",
    "imgur.com": "https://i.imgur.com/removed.png",
    "tinyimg.io": "https://tinyimg.io/notfound",
}


@unique
class Facility(Enum):
    COLLAGE = auto()
    RED_API = auto()
    PTPIMG_API = auto()
    COVER = auto()


@unique
class Severity(IntEnum):
    EMERGENCY = 0
    ALERT = 1
    CRITICAL = 2
    ERROR = 3
    WARNING = 4
    NOTICE = 5
    INFO = 6
    DEBUG = 7


class Logger:
    log_directory: str
    counters: dict[Facility, list[int]]

    logfile: TextIOWrapper

    def __init__(self):
        self.log_directory = config.c_log_directory  # imports the directory path to where you want to write your logs

        self.counters = {}
        for facility in Facility:
            self.counters[facility] = [0] * len(Severity)

        try:
            self.logfile = open(os.path.join(self.log_directory, "log.txt"), "a", encoding="utf-8")
        except FileNotFoundError:
            print("--Error: Cannot open log.txt", sys.stderr)
            exit(-1)

    def log(self, facility: Facility, severity: Severity, message: str):
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

        self.counters[facility][severity.value] += 1

        stream = sys.stdout if severity >= Severity.WARNING else sys.stderr  # Severity values are inverted
        logstr = f"{ts} {facility.name:>10} {severity.name:>7} {message}"
        print(logstr, file=stream, flush=True)
        self.logfile.write(logstr + "\n")


class RehostCover:
    # Establishes the counters for completed covers and errors
    count_rehosted: int
    count_total: int

    red_session: requests.Session
    ptpimg_session: requests.Session
    host_session: requests.Session

    reader: DictReader

    def __init__(self):
        self.count_rehosted = 0
        self.count_total = 0

        self.logger = Logger()

        retry = Retry(total=3, backoff_factor=0.2, respect_retry_after_header=False)
        adapter = HTTPAdapter(max_retries=retry)

        self.red_session = requests.Session()
        self.red_session.headers.update(
            {
                "Authorization": R_API_KEY,
                "User-Agent": USER_AGENT,
            }
        )
        self.red_session.mount("http://", adapter)
        self.red_session.mount("https://", adapter)

        self.ptpimg_session = requests.Session()
        self.ptpimg_session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "referer": "https://ptpimg.me/index.php",
            }
        )
        self.ptpimg_session.mount("http://", adapter)
        self.ptpimg_session.mount("https://", adapter)

        self.host_session = requests.Session()
        self.host_session.headers.update(
            {
                "User-Agent": USER_AGENT,
            }
        )
        self.host_session.mount("http://", adapter)
        self.host_session.mount("https://", adapter)

        # assemble list path
        list_path = os.path.join(config.c_list_directory, "list.txt")

        # open the txt file
        try:
            self.reader = DictReader(open(list_path, encoding="utf-8"), dialect="unix")
        except FileNotFoundError:
            print("--Error: The list.txt file is missing.")
            exit(-1)

    # A function that writes a summary of what the script did at the end of the process
    def summary_text(self):
        print("")
        print(f"This script rehosted {self.count_rehosted} album covers out of {self.count_total} covers.")
        print("")

        errors = False

        for fac in Facility:
            for sev in Severity:
                if sev == Severity.DEBUG:
                    continue
                if not self.logger.counters[fac][sev.value]:
                    continue
                if sev <= Severity.ERROR:  # Less than means error or worse -- values are inverted.
                    errors = True

                print(f"{fac.name:>10} {sev.name:>7}: {self.logger.counters[fac][sev.value]}")

        # level = "Warning" if self.RED_replace_error else "Info"
        # print(f"--{level}: There were {self.RED_replace_error} cover urls that failed being added to RED.")
        #
        # level = "Warning" if self.RED_api_error else "Info"
        # print(f"--{level}: There were {self.RED_api_error} covers skipped due to errors with the RED api.")
        #
        # level = "Warning" if self.ptpimg_api_error else "Info"
        # print(
        #     f"--{level}: There were {self.ptpimg_api_error} covers skipped due to the covers no longer being on the internet or errors with the ptpimg api."
        # )
        #
        # level = "Warning" if self.cover_missing_error else "Info"
        # print(
        #     f"--{level}: There were {self.cover_missing_error} covers skipped due to the covers no longer being on the internet or being a 404 image."
        # )
        #
        # level = "Warning" if self.collage_message else "Info"
        # print(
        #     f"--{level}: There were {self.collage_message} albums added to a collage due to missing or bad cover art."
        # )
        #
        # level = "Warning" if self.collage_error else "Info"
        # print(
        #     f"--{level}: There were {self.collage_error} albums that had missing or bad cover art but adding them a collage failed."
        # )

        print()
        if errors:
            print("Check the logs to see which torrents and covers had errors and what they were.")
        else:
            print("There were no errors.")

    @sleep_and_retry
    @limits(calls=5, period=10)
    def red_session_ratelimited(self) -> requests.Session:
        return self.red_session

    # A function to add albums that have broken cover art to the -Torrents with broken cover art links- collage
    def post_to_collage(self, torrent_id, collage_type):
        # assign collage ID, name and URL
        if collage_type == "broken":
            collage_id = "31445"  # Torrents with broken cover art links
            collage_url = f"https://redacted.ch/collages.php?id={collage_id}"
        elif collage_type == "lowquality":
            collage_id = "31735"  # Torrents with poor quality cover art images
            collage_url = f"https://redacted.ch/collages.php?id={collage_id}"
        else:
            raise ValueError(f"{collage_type} not defined.")

        # create the ajax page and data
        ajax_page = f"{COLLAGE_AJAX_PAGE}{collage_id}"
        data = {"groupids": torrent_id}
        # post to collage
        r = self.red_session_ratelimited().post(ajax_page, data=data, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        # report status
        status = r.json()

        if status["response"]["groupsadded"]:
            self.logger.log(
                Facility.COLLAGE,
                Severity.INFO,
                f"Torrent {torrent_id} had broken cover art. Successfully added to {collage_url}",
            )
        elif status["response"]["groupsduplicated"]:
            self.logger.log(
                Facility.COLLAGE,
                Severity.NOTICE,
                f"Torrent {torrent_id} had broken cover art. It was already in {collage_url}",
            )
        else:
            self.logger.log(
                Facility.COLLAGE,
                Severity.WARNING,
                f"Torrent {torrent_id} had broken cover art. Adding to {collage_url} failed.",
            )

    # A function that replaces the existing cover art on RED with the newly hosted one
    def post_to_RED(self, torrent_id, new_cover_url, original_cover_url):
        cover_url = original_cover_url

        # create the ajax page and data
        ajax_page = f"{SITE_AJAX_PAGE}{torrent_id}"
        edit_message = "Automatically rehosted cover to PTPimg"
        data = {"summary": edit_message, "image": new_cover_url}

        # replace the cover art link on RED and leave edit summary
        try:
            r: requests.Response = self.red_session_ratelimited().post(ajax_page, data=data, timeout=HTTP_TIMEOUT)
            # r.raise_for_status()

            # Were we redirected because the TG no longer exists?
            if r.status_code == 401 and r.url.startswith("https://redacted.ch/log.php?search="):
                self.logger.log(
                    Facility.RED_API,
                    Severity.NOTICE,
                    "Replacing cover art URL on RED failed. Torrent group has been deleted.",
                )
                return False

            status = r.json()

            if status["status"] == "success":
                self.logger.log(Facility.RED_API, Severity.INFO, "Replacing cover art URL on RED succeeded.")
                return True
            elif status["error"] == "No changes detected.":
                self.logger.log(
                    Facility.RED_API,
                    Severity.NOTICE,
                    "Replacing cover art URL on RED failed. It has already been replaced.",
                )
            elif status["error"] == "No Torrent Group Found":
                self.logger.log(
                    Facility.RED_API,
                    Severity.NOTICE,
                    "Replacing cover art URL on RED failed. Torrent group has been deleted.",
                )
            else:
                self.logger.log(
                    Facility.RED_API,
                    Severity.WARNING,
                    f"Replacing cover art URL on RED failed. Status: {status['status']}: {status['status']['error']}",
                )
        except Exception as err:
            self.logger.log(Facility.RED_API, Severity.ERROR, f"Replacing cover art URL on RED failed. {err}")
        return False

    # A function that rehosts the cover to ptpimg
    def rehost_cover(self, torrent_id, cover_url, resp):
        try:
            # Based on https://github.com/theirix/ptpimg-uploader/blob/6f702090806e7e98dbf041789b9e9de1122f84fa/ptpimg_uploader.py#L87

            open_file = BytesIO(resp.content)

            files = {"file-upload[]": ("justfilename", open_file, resp.headers.get("content-type"))}

            resp = self.ptpimg_session.post(
                "https://ptpimg.me/upload.php", data={"api_key": P_API_KEY}, files=files, timeout=HTTP_TIMEOUT
            )
            resp.raise_for_status()

            new_cover_url = [f'https://ptpimg.me/{r["code"]}.{r["ext"]}' for r in resp.json()]

            if new_cover_url:
                new_cover_url = new_cover_url[0].strip()
                self.logger.log(Facility.PTPIMG_API, Severity.INFO, f"The cover has been rehosted at {new_cover_url}")
                return new_cover_url
            else:
                self.logger.log(Facility.PTPIMG_API, Severity.ERROR, f"Failed to rehost cover art to ptpimg.")

        except Exception as err:  # TODO: Improve exception handler
            self.logger.log(Facility.PTPIMG_API, Severity.ERROR, f"Failed to rehost the cover art to ptpimg. {err}")

        return

    # A function to introduce a random delay into the loop to reduce the chance of being blocked for web scraping.
    def loop_delay(self):
        if self.count_rehosted >= 1:
            delay = randint(1, 3)  # Generate a random number of seconds within this range
            self.logger.log(Facility.COVER, Severity.DEBUG, f"Sleeping {delay}s")
            sleep(delay)  # Delay the script randomly to reduce anti-web scraping blocks

    def get_cover_image(self, cover_url):
        try:
            r = self.host_session.get(cover_url, timeout=HTTP_TIMEOUT)  # Here is where im getting the error
            r.raise_for_status()
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.SSLError,
            requests.exceptions.ConnectionError,
            requests.exceptions.TooManyRedirects,
        ) as err:
            self.logger.log(Facility.COVER, Severity.WARNING, f"Failed to get image. 404-like exception.")
            return

        mime_type = r.headers.get("content-type")
        if not mime_type or mime_type.split("/")[0] != "image":
            self.logger.log(Facility.COVER, Severity.WARNING, "Failed to get image. Invalid content-type.")
            return

        return r

    # A function that check if text file exists, loads it, loops through the lines, get id and url
    def loop_rehost(self):

        for line in self.reader:
            print("\n", flush=True)

            torrent_id: int = int(line["ID"])
            cover_url: str = line["WikiImage"].strip()

            self.count_total += 1  # variable will increment every loop iteration
            self.logger.log(
                Facility.COVER,
                Severity.DEBUG,
                f"TG url: https://redacted.ch/torrents.php?id={torrent_id} Cover art URL: {cover_url}",
            )

            host = str(urlparse(cover_url).hostname)

            # Is the host known to give us a crappy image?
            if host in LOW_QUALITY_HOSTS:
                self.logger.log(Facility.COVER, Severity.NOTICE, f"Skipping due to known low-quality host.")
                self.post_to_collage(torrent_id, "lowquality")
                continue

            # Is the host known to be dead?
            if host in BAD_HOSTS:
                self.logger.log(Facility.COVER, Severity.NOTICE, f"Skipping due to known dead host.")
                self.post_to_collage(torrent_id, "broken")
                continue

            # try to get the image
            r = self.get_cover_image(cover_url)

            if not r:
                self.post_to_collage(torrent_id, "broken")
                continue

            # did we get redirected?
            if r.history:
                final_url = r.url
                self.logger.log(Facility.COVER, Severity.DEBUG, f"Followed redirects to {final_url}")

                # Is the host returning a bogus image instead of a 404?
                if TRICKY_HOSTS.get(host) == final_url:
                    self.logger.log(Facility.COVER, Severity.WARNING, "Host redirected us to a known bogus 404 image.")
                    self.post_to_collage(torrent_id, "broken")
                    continue

            # We got a good image! Let's rehost it
            new_cover_url = self.rehost_cover(torrent_id, cover_url, r)
            if not new_cover_url:
                continue

            # Rehosted successfully, tell RED about it
            if not self.post_to_RED(torrent_id, new_cover_url, cover_url):
                continue

            self.count_rehosted += 1

            # introduce a delay after the first cover is rehosted
            # self.loop_delay()


# The main function that controls the flow of the script
def main():
    rehost = RehostCover()
    try:
        # intro text
        print()
        print("You spin me right 'round, baby, right 'round...")

        # Run the function to loop through the list.txt file and rehost the cover art
        rehost.loop_rehost()
    except KeyboardInterrupt:
        print("Exiting due to KeyboardInterrupt...")
    finally:
        # Summary text
        print()
        print("Like a record, baby, right 'round, 'round, 'round...")
        # run summary text function to provide error messages
        rehost.summary_text()
        print()


if __name__ == "__main__":
    main()
