# pylint: disable=too-many-return-statements
#!/usr/bin/env python3

"""
Usage:
    aqicheck.py [<zipcode>] [--MOD|--USG|--UH|--VUH|--HAZ]
"""

from os.path import expanduser
from docopt import docopt
from termcolor import colored
import os
import sys
import requests
import requests_cache
import configparser

AQI_API = "http://www.airnowapi.org/aq/observation/zipCode/current/"

proxies = {}
# proxies = {'http': 'http://localhost:9191', 'https': 'http://localhost:9191'}


def aqicolor(value):
    """Return color for the AQI range."""
    if value >= 0 and value <= 50:
        return "green"
    elif value > 50 and value <= 100:
        return "yellow"
    elif value > 100 and value <= 150:
        return "yellow"
    elif value > 150 and value <= 200:
        return "red"
    elif value > 200 and value <= 300:
        return "magenta"
    elif value > 300:
        return "magenta"
    else:
        return "blue"


if __name__ == "__main__":
    args = docopt(__doc__, version="0.1")

    home = expanduser("~")
    # Basically using a file with a secret in the user's home directory;
    # Similar approach to SSH keys in the user home, except I want this to be
    # automated and not require a password to decrypt due to automation.
    # The only secret being secured here is really just an API key
    # to a weather API. It's hardly the crown jewels.
    if oct(os.stat(home + "/.aqi.ini").st_mode & 0o777) != "0o600":
        print(
            "[{}] Fix file permissions on .aqi.ini file to 600.".format(
                colored("\u2717", "red")
            )
        )
        sys.exit()

    cp = configparser.ConfigParser()
    cp.read(home + "/.aqi.ini")
    api_key = cp["DEFAULT"]["api_key"]

    zipcode = cp["DEFAULT"]["zipcode"]
    if args["<zipcode>"] is not None:
        zipcode = args["<zipcode>"]

    cachefile = home + "/.dirty-aqi-cache"
    requests_cache.install_cache(cachefile, expire_after=3600)

    payload = {
        "format": "application/json",
        "distance": "5",
        "zipCode": zipcode,
        "API_KEY": api_key,
    }

    try:
        resp = requests.get(AQI_API, params=payload, proxies=proxies)
        if resp.status_code != 200:
            print(
                "[{}] Did not get 200 code from API.".format(colored("\u2717", "red"))
            )
            sys.exit()

        for i in resp.json():
            if i["ParameterName"] == "PM2.5":
                aqic = aqicolor(i["AQI"])
                msg = (
                    "[ "
                    + colored(i["AQI"], aqic)
                    + " ] AirNow reports AQI for "
                    + zipcode
                    + " is "
                    + colored(i["Category"]["Name"], aqic)
                    + " as of "
                    + str(i["HourObserved"])
                    + ":00 "
                    + i["LocalTimeZone"]
                    + "."
                )

                aqi_threshold = 0
                if args["--MOD"]:
                    aqi_threshold = 2
                elif args["--USG"]:
                    aqi_threshold = 3
                elif args["--UH"]:
                    aqi_threshold = 4
                elif args["--VUH"]:
                    aqi_threshold = 5
                elif args["--HAZ"]:
                    aqi_threshold = 6

                if i["Category"]["Number"] >= aqi_threshold:
                    print(msg)

                if (
                    oct(os.stat(home + "/.dirty-aqi-cache.sqlite").st_mode & 0o777)
                    != "0o600"
                ):
                    os.chmod(cachefile + ".sqlite", 0o600)
    except requests.exceptions.RequestException as err:
        print(
            "[{}] RequestException thrown, common when disconnnected from the Internet.".format(
                colored("\u2717", "red")
            )
        )
        sys.exit()
