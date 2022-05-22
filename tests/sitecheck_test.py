import unittest
import sitecheck

# "Wecome to M Netscape" is a webpage that hasn't changed since 1994
TEST_URL = "http://home.mcom.com/home/welcome.html"
# ssdeep hash for the above page
TEST_HASH = "96:UP9U09bcRTZAmv7Izpnk4u18w0u63WMzA7Fnu89ZBnK:1CcRV5yuEWMGkaK"


class TestSitecheck(unittest.TestCase):
    def test_get_site_hash(self):
        try:
            sc = sitecheck.SiteCheck()
            status, ssdeep_hash = sc.fetch_page(TEST_URL)
            assert status == 200
            assert ssdeep_hash == TEST_HASH
        except Exception:
            self.fail("Exception thrown during test.")

    def test_check_site_hash(self):
        try:
            sc = sitecheck.SiteCheck()
            args = ["check", TEST_URL, TEST_HASH]
            status, compare = sc.check_page(TEST_URL, TEST_HASH)
            assert status == 200
            assert compare == 100
        except Exception:
            self.fail("Exception thrown during test.")
