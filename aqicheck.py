#!/usr/bin/env python3
"""
Usage:
    aqicheck.py [<zipcode>]
"""

from os.path import expanduser
from docopt import docopt
from termcolor import colored
import requests
import requests_cache

url = "https://samuelreed.info"
aqi_api = "http://www.airnowapi.org/aq/observation/zipCode/current/"

proxies = {}
# proxies = {'http': 'http://localhost:9191', 'https': 'http://localhost:9191'}


def aqicolor(value):
    if value >= 0 and value <= 50:
        return "green"
    elif value > 50 and value <= 100:
        return "yellow"
    elif value > 100 and value <= 150:
        return "orange"
    elif value > 150 and value <= 200:
        return "red"
    elif value > 200 and value <= 300:
        return "purple"
    elif value > 300:
        return "maroon"
    return "blue"  # Unavailable, TODO: What does AQI value report as if Unavailable? Not in doc.


if __name__ == "__main__":
    args = docopt(__doc__, version="0.1")

    home = expanduser("~")
    api_key = ""  # TODO: research a console based secret store
    file = open(home + "/.dirty-aqi-api-key", "r")
    line = file.readlines()
    api_key = line[0]

    zipcode = "94103"
    if args["<zipcode>"] is not None:
        zipcode = args["<zipcode>"]

    cachefile = home + "/.dirty-aqi-cache"
    requests_cache.install_cache(cachefile, expire_after=3600)

    payload = {"format": "application/json", "distance": "5", "zipCode": zipcode, "API_KEY": api_key}
    resp = requests.get(aqi_api, params=payload, proxies=proxies)
    # print(resp.from_cache)

    # print(resp.json())
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
            print(msg)
