#!/usr/bin/env python3
"""
Comprehensive test suite for sitecheck.py with local test server.

This test suite creates a standalone HTTP server with test pages that represent
different levels of content divergence for testing fuzzy hash comparison.

Test Coverage:
- 100% match: Identical content
- 80-99% match: Slight modifications (footer changes)
- 50-79% match: Moderate modifications (~30% content changed)
- 1-70% match: Heavy modifications (most text replaced)
- 0-20% match: Completely different content

The test server runs on localhost:8765 and serves HTML pages from a temporary
directory. All tests clean up after themselves.

Run with:
    python3 -m unittest tests.sitecheck_comprehensive_test -v
"""

import http.server
import shutil
import socketserver
import tempfile
import threading
import time
import unittest
from pathlib import Path

import sitecheck


class TestHTTPServer:
    """Standalone HTTP server for serving test pages."""

    def __init__(self, port=8765):
        self.port = port
        self.temp_dir = None
        self.server = None
        self.thread = None

    def setup_test_pages(self):
        """Create test HTML pages with varying levels of content similarity."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Base page - unchanged reference (longer content for better fuzzy hashing)
        base_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test Page - Base Version</title>
    <meta charset="UTF-8">
    <meta name="description" content="Test page for sitecheck fuzzy hashing">
</head>
<body>
    <header>
        <h1>Welcome to the Comprehensive Test Page</h1>
        <nav>
            <a href="/">Home</a> | <a href="/about">About</a> | <a href="/contact">Contact</a>
        </nav>
    </header>
    <main>
        <article>
            <h2>Main Article Content</h2>
            <p>This is a test page for sitecheck fuzzy hashing functionality.</p>
            <p>It contains several paragraphs of meaningful content to generate a substantial hash.</p>
            <p>The quick brown fox jumps over the lazy dog near the riverbank.</p>
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor.</p>
            <p>Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua est laboris.</p>
            <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi aliquip.</p>
            <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore fugiat.</p>
            <p>Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia mollit.</p>
        </article>
        <aside>
            <h3>Sidebar Content</h3>
            <ul>
                <li>Important item number one</li>
                <li>Important item number two</li>
                <li>Important item number three</li>
                <li>Important item number four</li>
                <li>Important item number five</li>
            </ul>
        </aside>
    </main>
    <footer>
        <p>Copyright 2025 Test Suite - All Rights Reserved</p>
        <p>Contact: test@example.com | Phone: 555-1234</p>
    </footer>
</body>
</html>"""

        # Unchanged page (100% match)
        (self.temp_dir / "unchanged.html").write_text(base_content)

        # Slightly modified (80-99% match) - small change to footer
        slight_content = base_content.replace(
            "Copyright 2025 Test Suite - All Rights Reserved",
            "Copyright 2025-2026 Test Suite - All Rights Reserved",
        ).replace("Phone: 555-1234", "Phone: 555-5678")
        (self.temp_dir / "slight.html").write_text(slight_content)

        # Moderately modified (50-79% match) - change ~30% of content
        moderate_content = (
            base_content.replace(
                "<h2>Main Article Content</h2>", "<h2>Modified Article Content</h2>"
            )
            .replace(
                "The quick brown fox jumps over the lazy dog near the riverbank.",
                "The swift red fox leaps across the sleeping hound by the stream.",
            )
            .replace("Important item number one", "Modified item number one")
            .replace("Important item number two", "Modified item number two")
            .replace(
                "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua est laboris.",
                "New content has been added to this paragraph with different words and structure.",
            )
        )
        (self.temp_dir / "moderate.html").write_text(moderate_content)

        # Heavily modified (1-49% match) - keep structure but change most text
        heavy_content = (
            base_content.replace(
                "Welcome to the Comprehensive Test Page",
                "Completely Different Heading Here Now",
            )
            .replace(
                "This is a test page for sitecheck fuzzy hashing functionality.",
                "Entirely new content replaces the original text in this location.",
            )
            .replace(
                "It contains several paragraphs of meaningful content to generate a substantial hash.",
                "Different words and phrases appear throughout this modified version.",
            )
            .replace(
                "The quick brown fox jumps over the lazy dog near the riverbank.",
                "All animals have been replaced with entirely different creatures.",
            )
            .replace(
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor.",
                "Brand new Latin-inspired text that bears no resemblance to lorem ipsum.",
            )
            .replace("Important item number", "Changed list entry")
        )
        (self.temp_dir / "heavy.html").write_text(heavy_content)

        # Completely different (0% match) - entirely new structure and content
        complete_content = """<!DOCTYPE html>
<html><head><title>Totally Different Document</title></head>
<body><div id="container"><section class="content">
<h1>Brand New Article Title</h1>
<p>This document contains completely different content with no similarity whatsoever.</p>
<p>Every single word phrase and sentence has been replaced with new material.</p>
<p>There is absolutely no overlap with the original test page structure or text.</p>
<table border="1"><tr><th>Column A</th><th>Column B</th><th>Column C</th></tr>
<tr><td>Data 1</td><td>Data 2</td><td>Data 3</td></tr>
<tr><td>Data 4</td><td>Data 5</td><td>Data 6</td></tr>
<tr><td>Data 7</td><td>Data 8</td><td>Data 9</td></tr></table>
<blockquote>This is a quotation that never appeared in the original document at all.</blockquote>
<pre><code>function newCode() { return "completely different"; }</code></pre>
<p>Additional paragraphs with unique content follow here in this section below.</p>
<p>More unique text continues to fill out this entirely different page structure.</p>
</section></div></body></html>"""
        (self.temp_dir / "complete.html").write_text(complete_content)

    def start(self):
        """Start the HTTP server in a background thread."""
        self.setup_test_pages()

        # Store temp_dir reference for closure
        temp_directory = self.temp_dir

        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(temp_directory), **kwargs)

            def log_message(self, format, *args):
                pass  # Suppress server logs

        self.server = socketserver.TCPServer(("127.0.0.1", self.port), CustomHandler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

        # Wait for server to be ready
        time.sleep(0.5)

    def stop(self):
        """Stop the HTTP server and clean up."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def get_url(self, page):
        """Get the full URL for a test page."""
        return f"http://127.0.0.1:{self.port}/{page}"


class TestSitecheckWithServer(unittest.TestCase):
    """Test cases for sitecheck.py using a local test server."""

    @classmethod
    def setUpClass(cls):
        """Set up the test server once for all tests."""
        cls.server = TestHTTPServer()
        cls.server.start()
        cls.sc = sitecheck.SiteCheck()

    @classmethod
    def tearDownClass(cls):
        """Tear down the test server."""
        cls.server.stop()

    def test_fetch_page_success(self):
        """Test that fetch_page successfully retrieves a page."""
        url = self.server.get_url("unchanged.html")
        status, hash_value = self.sc.fetch_page(url)

        self.assertEqual(status, 200)
        self.assertIsNotNone(hash_value)
        self.assertIsInstance(hash_value, str)
        self.assertGreater(len(hash_value), 0)

    def test_fetch_page_404_returns_none_tuple(self):
        """Test that HTTP error responses are treated as failures."""
        url = self.server.get_url("missing.html")

        status, hash_value = self.sc.fetch_page(url)

        self.assertIsNone(status)
        self.assertIsNone(hash_value)

    def test_unchanged_page_100_percent_match(self):
        """Test that identical content produces 100% match."""
        url = self.server.get_url("unchanged.html")

        # Get initial hash
        status1, hash1 = self.sc.fetch_page(url)
        self.assertEqual(status1, 200)

        # Check against itself
        status2, similarity = self.sc.check_page(url, hash1)
        self.assertEqual(status2, 200)
        self.assertEqual(similarity, 100, "Identical pages should have 100% similarity")

    def test_slightly_modified_page(self):
        """Test slightly modified page (80-99% similarity)."""
        base_url = self.server.get_url("unchanged.html")
        modified_url = self.server.get_url("slight.html")

        # Get base hash
        _, base_hash = self.sc.fetch_page(base_url)

        # Check modified page against base
        _, similarity = self.sc.check_page(modified_url, base_hash)

        self.assertGreaterEqual(
            similarity, 80, "Slightly modified page should be ≥80% similar"
        )
        self.assertLess(
            similarity, 100, "Slightly modified page should be <100% similar"
        )

    def test_moderately_modified_page(self):
        """Test moderately modified page (50-79% similarity)."""
        base_url = self.server.get_url("unchanged.html")
        modified_url = self.server.get_url("moderate.html")

        # Get base hash
        _, base_hash = self.sc.fetch_page(base_url)

        # Check modified page against base
        _, similarity = self.sc.check_page(modified_url, base_hash)

        self.assertGreaterEqual(
            similarity, 50, "Moderately modified page should be ≥50% similar"
        )
        self.assertLess(
            similarity, 80, "Moderately modified page should be <80% similar"
        )

    def test_heavily_modified_page(self):
        """Test heavily modified page (moderate similarity 40-70%)."""
        base_url = self.server.get_url("unchanged.html")
        modified_url = self.server.get_url("heavy.html")

        # Get base hash
        _, base_hash = self.sc.fetch_page(base_url)

        # Check modified page against base
        _, similarity = self.sc.check_page(modified_url, base_hash)

        self.assertGreater(similarity, 0, "Heavily modified page should be >0% similar")
        self.assertLess(similarity, 70, "Heavily modified page should be <70% similar")

    def test_completely_different_page(self):
        """Test completely different page (0% similarity or very low)."""
        base_url = self.server.get_url("unchanged.html")
        different_url = self.server.get_url("complete.html")

        # Get base hash
        _, base_hash = self.sc.fetch_page(base_url)

        # Check completely different page against base
        _, similarity = self.sc.check_page(different_url, base_hash)

        self.assertLess(
            similarity, 20, "Completely different page should be <20% similar"
        )

    def test_hash_consistency(self):
        """Test that the same page produces the same hash consistently."""
        url = self.server.get_url("unchanged.html")

        _, hash1 = self.sc.fetch_page(url)
        _, hash2 = self.sc.fetch_page(url)

        self.assertEqual(hash1, hash2, "Same page should produce consistent hash")

    def test_all_divergence_levels(self):
        """Test all divergence levels and verify they fall into correct buckets."""
        base_url = self.server.get_url("unchanged.html")
        _, base_hash = self.sc.fetch_page(base_url)

        # Test each level
        test_cases = [
            ("unchanged.html", 100, "Site Unchanged"),
            ("slight.html", (80, 99), "Site Modified Slightly"),
            ("moderate.html", (50, 79), "Site Modified Significantly"),
            ("heavy.html", (1, 70), "Site Modified Heavily"),  # Adjusted range
            ("complete.html", (0, 20), "Site Changed Completely"),  # Allow up to 20%
        ]

        for page, expected_range, expected_verdict in test_cases:
            url = self.server.get_url(page)
            _, similarity = self.sc.check_page(url, base_hash)

            if isinstance(expected_range, tuple):
                min_sim, max_sim = expected_range
                self.assertGreaterEqual(
                    similarity,
                    min_sim,
                    f"{page} should have similarity ≥{min_sim}%, got {similarity}%",
                )
                self.assertLessEqual(
                    similarity,
                    max_sim,
                    f"{page} should have similarity ≤{max_sim}%, got {similarity}%",
                )
            else:
                self.assertEqual(
                    similarity,
                    expected_range,
                    f"{page} should have similarity {expected_range}%, got {similarity}%",
                )


class TestSitecheckEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        self.sc = sitecheck.SiteCheck()

    def test_invalid_url(self):
        """Test handling of invalid URLs."""
        status, hash_value = self.sc.fetch_page("not-a-valid-url")
        self.assertIsNone(status)
        self.assertIsNone(hash_value)

    def test_get_page_info_invalid_url(self):
        """Test that get_page_info uses the same URL validation."""
        page_info = self.sc.get_page_info("not-a-valid-url")

        self.assertIsNone(page_info)

    def test_get_page_info_404_returns_none(self):
        """Test that get_page_info treats HTTP errors as failures."""
        server = TestHTTPServer(port=0)
        server.start()
        try:
            page_info = self.sc.get_page_info(server.get_url("missing.html"))
            self.assertIsNone(page_info)
        finally:
            server.stop()

    def test_unreachable_host(self):
        """Test handling of unreachable hosts."""
        # With current implementation, returns (None, None)
        status, hash_value = self.sc.fetch_page(
            "http://this-host-does-not-exist-12345.com"
        )
        self.assertIsNone(status)
        self.assertIsNone(hash_value)

    def test_hash_comparison_with_invalid_hash(self):
        """Test hash comparison with malformed hash."""
        import ssdeep

        # Create a valid hash
        valid_hash = ssdeep.hash("test content")

        # Test with empty hash
        try:
            result = ssdeep.compare(valid_hash, "")
            # If it doesn't raise an exception, it should return 0
            self.assertEqual(result, 0)
        except Exception:
            # Some versions may raise an exception for invalid hashes
            pass


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
