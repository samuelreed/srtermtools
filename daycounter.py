#!/usr/bin/env python3
"""
Day Counter - Calculate days between dates with human-readable output

Usage:
    daycounter.py countdown [-h] <eventdate> <event>...
    daycounter.py countup [-h] <eventdate> <event>...

Options:
    -h, --human-readable    Display time in human readable format (years, months, days)

Examples:
    daycounter.py countdown 2025-12-25 Christmas
    daycounter.py countup -h 2020-01-01 "New Year 2020"
    daycounter.py countdown -h 2026-06-15 "My Birthday"

Date format: YYYY-MM-DD (ISO format)
Human-readable format includes accurate years, months, and days calculation.
"""

from docopt import docopt
from dateutil.relativedelta import relativedelta
from typing import List, Optional
import datetime
import sys


def parse_date(date_string: str) -> datetime.date:
    """Parse date string and return date object with error handling
    
    Supports ISO format (YYYY-MM-DD) and validates reasonable date ranges.
    """
    try:
        parsed_date = datetime.datetime.strptime(date_string, "%Y-%m-%d").date()
        
        # Validate reasonable date range (not more than 100 years in past/future)
        today = datetime.date.today()
        max_date = today + datetime.timedelta(days=365 * 100)
        min_date = today - datetime.timedelta(days=365 * 100)
        
        if parsed_date > max_date:
            print(f"Warning: Date '{date_string}' is more than 100 years in the future.", file=sys.stderr)
        elif parsed_date < min_date:
            print(f"Warning: Date '{date_string}' is more than 100 years in the past.", file=sys.stderr)
            
        return parsed_date
    except ValueError as e:
        if "time data" in str(e):
            print(f"Error: Invalid date format '{date_string}'. Please use YYYY-MM-DD format (e.g., 2023-12-25).", file=sys.stderr)
        else:
            print(f"Error: Invalid date '{date_string}'. {str(e)}", file=sys.stderr)
        sys.exit(1)


def validate_event(event_list: List[str]) -> str:
    """Validate that event description is provided"""
    if not event_list or not any(event.strip() for event in event_list):
        print("Error: Event description cannot be empty.", file=sys.stderr)
        sys.exit(1)
    return ' '.join(event_list).strip()


def days_to_human_readable(start_date: datetime.date, end_date: datetime.date) -> str:
    """Convert date difference to human readable format using accurate date arithmetic"""
    if start_date > end_date:
        # Swap dates and remember it's negative
        start_date, end_date = end_date, start_date
        is_negative = True
    else:
        is_negative = False
    
    # Use relativedelta for accurate date arithmetic
    delta = relativedelta(end_date, start_date)
    
    parts = []
    if delta.years > 0:
        parts.append(f"{delta.years} year{'s' if delta.years != 1 else ''}")
    if delta.months > 0:
        parts.append(f"{delta.months} month{'s' if delta.months != 1 else ''}")
    if delta.days > 0:
        parts.append(f"{delta.days} day{'s' if delta.days != 1 else ''}")
    
    # If we have years or months, always show days for completeness
    if (delta.years > 0 or delta.months > 0) and delta.days == 0:
        parts.append("0 days")
    
    if not parts:
        return "0 days"
    elif len(parts) == 1:
        result = parts[0]
    elif len(parts) == 2:
        result = f"{parts[0]} and {parts[1]}"
    else:
        result = f"{parts[0]}, {parts[1]}, and {parts[2]}"
    
    return result


def format_days_count(days: int) -> str:
    """Format large day counts with comma separators"""
    return f"{days:,}"


def process_date_calculation(mode: str, eventdate: datetime.date, event_description: str, 
                           use_human_readable: bool) -> None:
    """Process date calculation for countdown or countup modes"""
    today = datetime.date.today()
    
    if mode == "countdown":
        days_diff = (eventdate - today).days
        
        if days_diff < 0:
            # Event is in the past
            abs_days = abs(days_diff)
            if use_human_readable:
                time_str = days_to_human_readable(eventdate, today)
                print(f"{event_description} was {time_str} ago.")
            else:
                print(f"{event_description} was {format_days_count(abs_days)} days ago.")
        else:
            # Event is in the future
            if use_human_readable:
                time_str = days_to_human_readable(today, eventdate)
                print(f"It is {time_str} until {event_description}.")
            else:
                print(f"It is {format_days_count(days_diff)} days until {event_description}.")
                
    elif mode == "countup":
        days_diff = (today - eventdate).days
        
        if days_diff < 0:
            # Event is in the future
            abs_days = abs(days_diff)
            if use_human_readable:
                time_str = days_to_human_readable(today, eventdate)
                print(f"{event_description} will be in {time_str}.")
            else:
                print(f"{event_description} will be in {format_days_count(abs_days)} days.")
        else:
            # Event is in the past
            if use_human_readable:
                time_str = days_to_human_readable(eventdate, today)
                print(f"It has been {time_str} since {event_description}.")
            else:
                print(f"It has been {format_days_count(days_diff)} days since {event_description}.")

if __name__ == "__main__":
    try:
        args = docopt(__doc__, version="0.1")
    except Exception as e:
        print(f"Error parsing command line arguments: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse and validate input
    eventdate = parse_date(args["<eventdate>"])
    event_description = validate_event(args["<event>"])
    use_human_readable = args["--human-readable"]
    
    # Process the appropriate mode
    if args["countdown"]:
        process_date_calculation("countdown", eventdate, event_description, use_human_readable)
    elif args["countup"]:
        process_date_calculation("countup", eventdate, event_description, use_human_readable)
    else:
        print(__doc__.strip())
