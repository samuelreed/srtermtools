#!/usr/bin/env python3
"""
Usage:
    daycounter.py countdown <eventdate> <event>...
    daycounter.py countup <eventdate> <event>...
"""

from docopt import docopt
import datetime

if __name__ == "__main__":
    args = docopt(__doc__, version="0.1")

    if args["countdown"]:
        eventdate = datetime.datetime.strptime(args["<eventdate>"], "%Y-%m-%d").date()
        today = datetime.date.today()
        print("It is {} days until {}.".format((eventdate - today).days, " ".join(args["<event>"])))
    elif args["countup"]:
        eventdate = datetime.datetime.strptime(args["<eventdate>"], "%Y-%m-%d").date()
        today = datetime.date.today()
        print("It has been {} days since {}.".format((today - eventdate).days, " ".join(args["<event>"])))
    else:
        print(docopt(__doc__))
