#!/usr/bin/env python3
"""
Usage:
    daycounter.py countdown [-h] <eventdate> <event>...
    daycounter.py countup [-h] <eventdate> <event>...

Options:
    -h, --human-readable    Display time in human readable format (years, months, days)
"""

from docopt import docopt
import datetime


def days_to_human_readable(days):
    """Convert days to human readable format (years, months, days)"""
    if days < 0:
        return f"{abs(days)} days"
    
    years = days // 365
    remaining_days = days % 365
    months = remaining_days // 30
    days_left = remaining_days % 30
    
    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    if days_left > 0:
        parts.append(f"{days_left} day{'s' if days_left != 1 else ''}")
    
    if not parts:
        return "0 days"
    elif len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    else:
        return f"{parts[0]}, {parts[1]}, and {parts[2]}"

if __name__ == "__main__":
    args = docopt(__doc__, version="0.1")

    if args["countdown"]:
        eventdate = datetime.datetime.strptime(args["<eventdate>"], "%Y-%m-%d").date()
        today = datetime.date.today()
        days_diff = (eventdate - today).days
        
        if args["--human-readable"]:
            time_str = days_to_human_readable(days_diff)
            print(f"It is {time_str} until {' '.join(args['<event>'])}.")
        else:
            print(f"It is {days_diff} days until {' '.join(args['<event>'])}.")
            
    elif args["countup"]:
        eventdate = datetime.datetime.strptime(args["<eventdate>"], "%Y-%m-%d").date()
        today = datetime.date.today()
        days_diff = (today - eventdate).days
        
        if args["--human-readable"]:
            time_str = days_to_human_readable(days_diff)
            print(f"It has been {time_str} since {' '.join(args['<event>'])}.")
        else:
            print(f"It has been {days_diff} days since {' '.join(args['<event>'])}.")
    else:
        print(docopt(__doc__))
