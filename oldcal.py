#!/usr/bin/env python3
"""
Old Calendar - A compact version of the traditional Unix calendar command

Usage:
    oldcal.py [-A <days>] [<files_or_directories>...]
    oldcal.py --help

Options:
    -A <days>    Look ahead this many days (default: 0 - today only)
    --help       Show this help message

Arguments:
    files_or_directories    Calendar files or directories to read
                           (default: ~/.remind directory)

Description:
    Reads calendar files in traditional BSD calendar format and displays
    events for today and/or upcoming days.
    
    Supports both formats:
    - BSD calendar format: MM/DD<TAB>Description
    - Remind format: REM DD Mon MSG Description
    
Examples:
    oldcal.py                    # Show today's events from ~/.remind
    oldcal.py -A 7              # Show events for next 7 days
    oldcal.py calendar/         # Read calendar files from directory
    oldcal.py -A 3 calendar.birthdays calendar.holidays
"""

from docopt import docopt
from pathlib import Path
from typing import List, Tuple, Optional, Set
import datetime
import sys
import re


class OldCal(object):
    """Traditional Unix calendar command implementation"""
    
    def __init__(self, look_ahead_days: int = 0):
        self.look_ahead_days = look_ahead_days
        self.target_dates = self._generate_target_dates()
    
    def _generate_target_dates(self) -> Set[Tuple[int, int]]:
        """Generate set of (month, day) tuples for target date range"""
        today = datetime.date.today()
        dates = set()
        
        for i in range(self.look_ahead_days + 1):
            target_date = today + datetime.timedelta(days=i)
            dates.add((target_date.month, target_date.day))
        
        return dates
    
    def parse_bsd_calendar_line(self, line: str) -> Optional[Tuple[int, int, str]]:
        """Parse BSD calendar format: MM/DD<TAB>Description"""
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('LANG='):
            return None
        
        # Match MM/DD format followed by whitespace and description
        match = re.match(r'^(\d{1,2})/(\d{1,2})\s+(.+)$', line)
        if not match:
            return None
        
        month, day, description = match.groups()
        return int(month), int(day), description.strip()
    
    def parse_remind_line(self, line: str) -> Optional[Tuple[int, int, str]]:
        """Parse Remind format: REM DD Mon MSG Description"""
        line = line.strip()
        if not line or line.startswith('#'):
            return None
        
        # Match REM DD Mon MSG format
        match = re.match(r'^REM\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+MSG\s+(.+)$', line)
        if not match:
            return None
        
        day_str, month_str, description = match.groups()
        
        # Convert month name to number
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        month = month_map.get(month_str)
        if month is None:
            return None
        
        return month, int(day_str), description.strip()
    
    def parse_calendar_file(self, file_path: Path) -> List[Tuple[int, int, str, str]]:
        """Parse calendar file and return matching events as (month, day, description, filename)"""
        if not file_path.is_file():
            return []
        
        events = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # Try BSD format first
                    result = self.parse_bsd_calendar_line(line)
                    if result is None:
                        # Try Remind format
                        result = self.parse_remind_line(line)
                    
                    if result is not None:
                        month, day, description = result
                        # Check if this date is in our target range
                        if (month, day) in self.target_dates:
                            events.append((month, day, description, file_path.name))
                            
        except (UnicodeDecodeError, FileNotFoundError) as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
        
        return events
    
    def find_calendar_files(self, paths: List[str]) -> List[Path]:
        """Find all calendar files from given paths"""
        files = []
        
        if not paths:
            # Default to ~/.remind directory
            default_dir = Path.home() / '.remind'
            if default_dir.is_dir():
                paths = [str(default_dir)]
            else:
                print(f"Default directory {default_dir} not found", file=sys.stderr)
                return []
        
        for path_str in paths:
            path = Path(path_str)
            if path.is_file():
                files.append(path)
            elif path.is_dir():
                # Add all files in directory that look like calendar files
                for file_path in path.iterdir():
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        files.append(file_path)
            else:
                print(f"Path not found: {path_str}", file=sys.stderr)
        
        return files
    
    def format_event_output(self, events: List[Tuple[int, int, str, str]]) -> None:
        """Format and display events"""
        if not events:
            return
        
        today = datetime.date.today()
        
        # Convert events to include actual dates for proper sorting
        dated_events = []
        for month, day, description, filename in events:
            try:
                event_date = datetime.date(today.year, month, day)
                # If the event already passed this year, consider next year
                if event_date < today:
                    event_date = datetime.date(today.year + 1, month, day)
                dated_events.append((event_date, description))
            except ValueError:
                # Handle leap year edge case (Feb 29)
                continue
        
        # Sort by actual date
        dated_events.sort(key=lambda x: x[0])
        
        # Display sorted events
        for event_date, description in dated_events:
            print(f"{event_date.month:02d}/{event_date.day:02d}: {description}")


if __name__ == "__main__":
    args = docopt(__doc__, version="oldcal 1.0")
    
    # Parse look-ahead days
    look_ahead = 0
    if args["-A"]:
        try:
            look_ahead = int(args["-A"])
            if look_ahead < 0:
                print("Error: Look-ahead days must be non-negative", file=sys.stderr)
                sys.exit(1)
        except ValueError:
            print("Error: Look-ahead days must be a valid integer", file=sys.stderr)
            sys.exit(1)
    
    # Get file/directory arguments
    paths = args["<files_or_directories>"] or []
    
    # Create oldcal instance and process
    oldcal = OldCal(look_ahead)
    calendar_files = oldcal.find_calendar_files(paths)
    
    if not calendar_files:
        print("No calendar files found", file=sys.stderr)
        sys.exit(1)
    
    # Collect all events from all files
    all_events = []
    for file_path in calendar_files:
        events = oldcal.parse_calendar_file(file_path)
        all_events.extend(events)
    
    # Display events
    oldcal.format_event_output(all_events)
