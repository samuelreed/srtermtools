#!/usr/bin/env python3
"""Tests for daycounter.py."""

import datetime
import subprocess
import sys
import unittest
from pathlib import Path

import daycounter

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "daycounter.py"


class TestDaycounterFormatting(unittest.TestCase):
    def test_format_day_phrase_singular(self):
        self.assertEqual(daycounter.format_day_phrase(1), "1 day")

    def test_format_day_phrase_plural(self):
        self.assertEqual(daycounter.format_day_phrase(2), "2 days")
        self.assertEqual(daycounter.format_day_phrase(1000), "1,000 days")

    def test_days_to_human_readable_swaps_date_order(self):
        start_date = datetime.date(2026, 3, 20)
        end_date = datetime.date(2026, 3, 19)

        self.assertEqual(
            daycounter.days_to_human_readable(start_date, end_date),
            "1 day",
        )


class TestDaycounterCli(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_countdown_uses_singular_day(self):
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

        result = self.run_cli("countdown", tomorrow, "Tomorrow")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "It is 1 day until Tomorrow.")
        self.assertEqual(result.stderr.strip(), "")

    def test_countup_future_uses_singular_day(self):
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

        result = self.run_cli("countup", tomorrow, "Tomorrow")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "Tomorrow will be in 1 day.")
        self.assertEqual(result.stderr.strip(), "")

    def test_countup_past_uses_singular_day(self):
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

        result = self.run_cli("countup", yesterday, "Yesterday")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            result.stdout.strip(),
            "It has been 1 day since Yesterday.",
        )
        self.assertEqual(result.stderr.strip(), "")

    def test_invalid_usage_returns_non_zero_and_stderr(self):
        result = self.run_cli("invalid")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertIn("Usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
