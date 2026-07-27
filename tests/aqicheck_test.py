import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import aqicheck


class TestAqiCheckConfiguration(unittest.TestCase):
    def test_missing_config_file_writes_stderr_and_exits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch("aqicheck.Path.home", return_value=home):
                with contextlib.redirect_stdout(stdout):
                    with contextlib.redirect_stderr(stderr):
                        with self.assertRaises(SystemExit) as exc:
                            aqicheck.load_configuration()

        self.assertEqual(exc.exception.code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("Configuration file", stderr.getvalue())

    def test_insecure_permissions_writes_stderr_and_exits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = home / ".aqi.ini"
            config_path.write_text(
                "[DEFAULT]\n"
                "api_key = test-key\n"
                "zipcode = 94105\n"
            )
            config_path.chmod(0o644)

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch("aqicheck.Path.home", return_value=home):
                with contextlib.redirect_stdout(stdout):
                    with contextlib.redirect_stderr(stderr):
                        with self.assertRaises(SystemExit) as exc:
                            aqicheck.load_configuration()

        self.assertEqual(exc.exception.code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("Fix file permissions", stderr.getvalue())

    def test_missing_key_writes_stderr_and_exits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_path = home / ".aqi.ini"
            config_path.write_text(
                "[DEFAULT]\n"
                "api_key = test-key\n"
            )
            config_path.chmod(0o600)

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch("aqicheck.Path.home", return_value=home):
                with contextlib.redirect_stdout(stdout):
                    with contextlib.redirect_stderr(stderr):
                        with self.assertRaises(SystemExit) as exc:
                            aqicheck.load_configuration()

        self.assertEqual(exc.exception.code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("Missing or empty 'zipcode'", stderr.getvalue())


class TestAqiCheckResponses(unittest.TestCase):
    def fake_response(self, status_code=200, reason="OK", payload=None):
        response = MagicMock()
        response.status_code = status_code
        response.reason = reason
        response.json.side_effect = (
            payload if isinstance(payload, Exception) else None
        )
        if not isinstance(payload, Exception):
            response.json.return_value = payload
        return response

    def test_fetch_aqi_data_non_200_writes_stderr_and_exits(self):
        response = self.fake_response(
            status_code=503,
            reason="Service Unavailable",
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("aqicheck.requests.get", return_value=response):
            with contextlib.redirect_stdout(stdout):
                with contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as exc:
                        aqicheck.fetch_aqi_data("test-key", "94105")

        self.assertEqual(exc.exception.code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("API request failed with status 503", stderr.getvalue())

    def test_fetch_aqi_data_bad_json_writes_stderr_and_exits(self):
        response = self.fake_response(payload=ValueError("bad json"))

        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("aqicheck.requests.get", return_value=response):
            with contextlib.redirect_stdout(stdout):
                with contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as exc:
                        aqicheck.fetch_aqi_data("test-key", "94105")

        self.assertEqual(exc.exception.code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("Invalid JSON response from API", stderr.getvalue())

    def test_process_aqi_data_silent_below_threshold(self):
        response_data = [
            {
                "ParameterName": "PM2.5",
                "AQI": 35,
                "Category": {"Number": 1, "Name": "Good"},
                "HourObserved": 11,
                "LocalTimeZone": "PST",
            }
        ]

        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with contextlib.redirect_stderr(stderr):
                aqicheck.process_aqi_data(response_data, "94105", 3)

        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_process_aqi_data_prints_summary_when_threshold_met(self):
        response_data = [
            {
                "ParameterName": "PM2.5",
                "AQI": 105,
                "Category": {
                    "Number": 3,
                    "Name": "Unhealthy for Sensitive Groups",
                },
                "HourObserved": 11,
                "LocalTimeZone": "PST",
            }
        ]

        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with contextlib.redirect_stderr(stderr):
                aqicheck.process_aqi_data(response_data, "94105", 0)

        self.assertIn("AirNow reports AQI for 94105 is", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_process_aqi_data_missing_pm25_writes_stderr_and_exits(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exc:
                    aqicheck.process_aqi_data([], "94105", 0)

        self.assertEqual(exc.exception.code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("No PM2.5 data available", stderr.getvalue())


class TestAqiCheckCli(unittest.TestCase):
    def test_main_docopt_error_writes_stderr_and_exits(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch(
            "aqicheck.docopt",
            side_effect=aqicheck.DocoptExit("Usage:"),
        ):
            with contextlib.redirect_stdout(stdout):
                with contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as exc:
                        aqicheck.main()

        self.assertEqual(exc.exception.code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("Usage:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
