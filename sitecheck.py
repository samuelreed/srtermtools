#!/usr/bin/env python3
"""
Usage:
    sitecheck.py hash <url>
    sitecheck.py check <url> <lasthash>
"""

from docopt import docopt
import ssdeep
import requests
from termcolor import colored


def fetchpage(url):
    r = requests.get(url)
    status = r.status_code
    newhash = ssdeep.hash(r.text)
    return status, newhash


if __name__ == "__main__":
    args = docopt(__doc__, version="0.1")

    URL = args["<url>"]

    if args["hash"]:
        try:
            status, newhash = fetchpage(URL)
            if status == 200:
                color = "green"
            else:
                color = "red"
            print("[ {} ] for {}: {}".format(colored(status, color), URL, newhash))
        except requests.ConnectionError:
            print("[{}] Unreachable site: {}".format(colored(u"\u2717", "red"), URL))
    elif args["check"]:
        catcherror = 0
        try:
            status, newhash = fetchpage(URL)
            verdict = "Verdict Never Set."
            color = "green"
            compare = ssdeep.compare(newhash, args["<lasthash>"])
            if compare == 0:
                verdict = "Site Changed Completely."
                color = "magenta"
            elif compare == 100:
                verdict = "Site Unchanged."
                color = "green"
            elif compare < 100 and compare >= 80:
                verdict = "Site Modified Slightly."
                color = "yellow"
            elif compare < 80 and compare >= 50:
                verdict = "Site Modified Significantly."
                color = "red"
            elif compare < 50 and compare > 0:
                verdict = "Site Modified Heavily."
                color = "magenta"
            print(
                "[ {} ] for {}: {}".format(
                    colored(status, color), URL, colored(verdict, color)
                )
            )
        except requests.ConnectionError:
            print("[{}] Unreachable site: {}".format(colored(u"\u2717", "red"), URL))
    else:
        print(docopt(__doc__))
