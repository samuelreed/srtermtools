import unittest

import sitecheck

# "Wecome to M Netscape" is a webpage that hasn't changed since 1994
TEST_URL = "http://home.mcom.com/home/welcome.html"
# ssdeep hash for the above page
TEST_HASH = "96:UP9U09bcRTZAmv7Izpnk4u18w0u63WMzA7Fnu89ZBnK:1CcRV5yuEWMGkaK"


class TestSitecheck(unittest.TestCase):
    def test_get_site_hash(self):
        sc = sitecheck.SiteCheck()
        status, ssdeep_hash = sc.fetch_page(TEST_URL)

        if status is None:
            self.skipTest("External test URL unavailable in current environment")

        self.assertEqual(status, 200)
        self.assertEqual(ssdeep_hash, TEST_HASH)

    def test_check_site_hash(self):
        sc = sitecheck.SiteCheck()
        status, compare = sc.check_page(TEST_URL, TEST_HASH)

        if status is None:
            self.skipTest("External test URL unavailable in current environment")

        self.assertEqual(status, 200)
        self.assertEqual(compare, 100)
