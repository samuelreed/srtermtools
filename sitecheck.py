#!/usr/bin/env python3

"""
Usage:
    sitecheck.py hash <url>
    sitecheck.py check <url> <lasthash>
"""

import sys
from urllib.parse import urlparse

import requests
import ssdeep
from docopt import docopt
from termcolor import colored


class SiteCheck(object):
    def __init__(self, timeout=10, user_agent=None):
        """Initialize SiteCheck with configurable options"""
        self.timeout = timeout
        self.session = requests.Session()
        if user_agent:
            self.session.headers.update({"User-Agent": user_agent})
        else:
            self.session.headers.update(
                {
                    "User-Agent": (
                        "SiteCheck/0.1 " "(https://github.com/yourusername/sitecheck)"
                    )
                }
            )

    def validate_url(self, url: str) -> None:
        """Validate URL format before making a request."""
        parsed_url = urlparse(url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("Invalid URL format")

    def fetch_page(self, url: str):
        """Fetch a web page and return status code and ssdeep hash

        Args:
            url (str): The URL to fetch

        Returns:
            tuple: (status_code, hash) or (None, None) on error
        """
        try:
            self.validate_url(url)
            r = self.session.get(url, timeout=self.timeout)
            r.raise_for_status()
            status = r.status_code
            newhash = ssdeep.hash(r.text)
            return status, newhash

        except ValueError as e:
            print(f"Error: {e} for {url}", file=sys.stderr)
            return None, None
        except requests.exceptions.Timeout:
            print(f"Error: Timeout fetching {url}", file=sys.stderr)
            return None, None
        except requests.exceptions.HTTPError as e:
            response = e.response
            status = response.status_code if response is not None else "unknown"
            reason = response.reason if response is not None else str(e)
            print(
                f"Error: HTTP {status} fetching {url}: {reason}",
                file=sys.stderr,
            )
            return None, None
        except requests.exceptions.RequestException as e:
            print(f"Error: Request failed for {url}: {e}", file=sys.stderr)
            return None, None

    def check_page(self, url: str, oldhash: str):
        """Check if a web page has changed compared to a previous hash

        Args:
            url (str): The URL to check
            oldhash (str): The previous hash to compare against

        Returns:
            tuple: (status_code, comparison_score) or (None, None) on error
        """
        status, newhash = self.fetch_page(url)
        if status is None or newhash is None:
            return None, None

        try:
            compare = ssdeep.compare(newhash, oldhash)
            return status, compare
        except (TypeError, ValueError) as e:
            print(f"Error: Comparison failed for {url}: {e}", file=sys.stderr)
            return status, None

    def get_page_info(self, url: str):
        """Get detailed information about a web page

        Args:
            url (str): The URL to analyze

        Returns:
            dict: Page information including status, hash, and headers
        """
        try:
            self.validate_url(url)
            r = self.session.get(url, timeout=self.timeout)
            r.raise_for_status()
            return {
                "status": r.status_code,
                "hash": ssdeep.hash(r.text),
                "headers": dict(r.headers),
                "url": url,
                "response_time": r.elapsed.total_seconds(),
            }
        except ValueError as e:
            print(f"Error: {e} for {url}", file=sys.stderr)
            return None
        except requests.exceptions.RequestException as e:
            print(
                f"Error: Failed to get page info for {url}: {e}",
                file=sys.stderr,
            )
            return None


def print_status(status, url, color=None):
    """Print status with optional color formatting"""
    if color:
        print(f"[ {colored(status, color)} ] for {url}")
    else:
        print(f"[ {status} ] for {url}")


def print_comparison_result(status, url, verdict, color):
    """Print comparison results with color coding"""
    print(f"[ {colored(status, color)} ] for {url}: {colored(verdict, color)}")


def main():
    """Main function with improved error handling and user experience"""
    args = docopt(__doc__, version="0.1")

    URL = args["<url>"]

    if args["hash"]:
        try:
            sc = SiteCheck()
            status, newhash = sc.fetch_page(URL)
            if status is None:
                sys.exit(1)

            if status == 200:
                color = "green"
            else:
                color = "red"
            print(f"[ {colored(status, color)} ] for {URL}: {newhash}")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user", file=sys.stderr)
            sys.exit(1)
    elif args["check"]:
        if not args["<lasthash>"]:
            print("Error: No previous hash provided", file=sys.stderr)
            sys.exit(1)

        try:
            sc = SiteCheck()
            status, compare = sc.check_page(URL, args["<lasthash>"])
            if status is None or compare is None:
                sys.exit(1)

            verdict = "Verdict Never Set."
            color = "green"

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

            print_comparison_result(status, URL, verdict, color)

        except KeyboardInterrupt:
            print("\nOperation cancelled by user", file=sys.stderr)
            sys.exit(1)
    else:
        print((__doc__ or "").strip(), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
