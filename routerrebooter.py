#!/usr/bin/env python3
"""
Usage:
    routerrebooter check
    routerrebooter reset
    routerrebooter forward (enable|disable)
"""
import requests
from stat import *
import os
from docopt import docopt
from termcolor import colored
from bs4 import BeautifulSoup
from os.path import expanduser

target = "192.168.0.1"
proxies = {}  # Useful for debugging to flip back and forth and read traffic
# proxies = {'http': 'http://localhost:9191', 'https': 'http://localhost:9191'}

home = expanduser("~")
password = ""  # TODO: research a console based secret store
file = open(home + "/.dirty-router", "r")
line = file.readlines()
password = line[0]


def login():
    resp1 = requests.get("http://" + target, proxies=proxies)
    url = "http://" + target + "/goform/home_loggedout"
    payload = {"loginUsername": "admin", "loginPassword": password}
    resp2 = requests.post(url, cookies=resp1.cookies, data=payload, proxies=proxies)
    return resp1.cookies


def reset(validcookies):
    resp3 = requests.get("http://" + target + "/restore_reboot.asp", cookies=validcookies, proxies=proxies)
    soup = BeautifulSoup(resp3.content, "html.parser")
    csrftoken = soup.find("input", {"name": "csrf_token"})["value"]
    payload = {"resetbt": "1", "csrf_token": csrftoken}
    resp4 = requests.post(
        "http://" + target + "/goform/restore_reboot", cookies=validcookies, data=payload, proxies=proxies
    )


def forwardingToken(validcookies):
    resp3 = requests.get("http://" + target + "/port_forwarding.asp", cookies=validcookies, proxies=proxies)
    soup = BeautifulSoup(resp3.content, "html.parser")
    csrftoken = soup.find("input", {"name": "csrf_token"})["value"]
    return csrftoken


def disableForwarding(validcookies):
    token = forwardingToken(validcookies)
    payload = {"csrf_token": token, "forwarding": "Disabled"}
    resp4 = requests.post(
        "http://" + target + "/goform/port_forwarding", cookies=validcookies, data=payload, proxies=proxies
    )


def enableForwarding(validcookies):
    token = forwardingToken(validcookies)
    payload = {"csrf_token": token, "forwarding": "Enabled"}
    resp4 = requests.post(
        "http://" + target + "/goform/port_forwarding", cookies=validcookies, data=payload, proxies=proxies
    )


if __name__ == "__main__":
    args = docopt(__doc__, version="0.1")

    if oct(os.stat(".dirty-router").st_mode & 0o777) != "0o600":
        print("[{}] Fix file permissions on .dirty-router file to 600.".format(colored(u"\u2717", "red")))
        exit()

    if args["check"]:
        try:
            login()
            print("[{}] Verification of login was successful.".format(colored(u"\u2713", "green")))
        except Exception as err:
            print("[{}] Login to the router failed.".format(colored(u"\u2717", "red")))
    elif args["reset"]:
        try:
            reset(login())
            print("[{}] Router reset.".format(colored(u"\u2713", "green")))
        except Exception as err:
            print("[{}] Resetting the router failed.".format(colored(u"\u2717", "red")))
    elif args["disable"]:
        try:
            disableForwarding(login())
            print("[{}] Port forwarding disabled.".format(colored(u"\u2713", "green")))
        except Exception as err:
            print("[{}] Disabling forwarding failed.".format(colored(u"\u2717", "red")))
    elif args["enable"]:
        try:
            enableForwarding(login())
            print("[{}] Port forwarding enabled.".format(colored(u"\u2713", "green")))
        except Exception as err:
            print("[{}] Enabling forwarding failed.".format(colored(u"\u2717", "red")))
    else:
        print(docopt(__doc__))
