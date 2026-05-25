"""Unit tests for the CSRF policy helpers (src.primary.utils.csrf)."""
import os
import unittest
from unittest import mock

from src.primary.utils import csrf


class NormalizeOriginTests(unittest.TestCase):
    def test_http_default_port(self):
        self.assertEqual(
            csrf.normalize_origin("http", "example.com"),
            ("http", "example.com", 80),
        )

    def test_https_default_port(self):
        self.assertEqual(
            csrf.normalize_origin("https", "example.com"),
            ("https", "example.com", 443),
        )

    def test_explicit_port(self):
        self.assertEqual(
            csrf.normalize_origin("http", "example.com:9705"),
            ("http", "example.com", 9705),
        )

    def test_case_normalized(self):
        self.assertEqual(
            csrf.normalize_origin("HTTPS", "Example.COM:8443"),
            ("https", "example.com", 8443),
        )

    def test_missing_inputs(self):
        self.assertIsNone(csrf.normalize_origin("https", None))
        self.assertIsNone(csrf.normalize_origin("https", ""))


class ParseTrustedOriginsTests(unittest.TestCase):
    def test_empty(self):
        origins, hosts = csrf.parse_trusted_origins("")
        self.assertEqual(origins, set())
        self.assertEqual(hosts, set())

    def test_none(self):
        origins, hosts = csrf.parse_trusted_origins(None)
        self.assertEqual(origins, set())
        self.assertEqual(hosts, set())

    def test_bare_hostname(self):
        origins, hosts = csrf.parse_trusted_origins("example.com")
        self.assertEqual(origins, set())
        self.assertEqual(hosts, {"example.com"})

    def test_full_origin(self):
        origins, hosts = csrf.parse_trusted_origins("https://example.com:8443")
        self.assertEqual(origins, {("https", "example.com", 8443)})
        self.assertEqual(hosts, set())

    def test_mixed(self):
        origins, hosts = csrf.parse_trusted_origins(
            "https://a.example.com, b.example.com ,, https://c:9000"
        )
        self.assertEqual(
            origins,
            {("https", "a.example.com", 443), ("https", "c", 9000)},
        )
        self.assertEqual(hosts, {"b.example.com"})


class RequestAllowedTests(unittest.TestCase):
    EXPECTED = ("http", "newtarr.local", 9705)

    def test_safe_methods_pass(self):
        for m in ("GET", "HEAD", "OPTIONS", "TRACE"):
            self.assertTrue(
                csrf.request_allowed(m, "https://evil.example", self.EXPECTED, set(), set()),
                f"{m} should be allowed",
            )

    def test_no_origin_allowed(self):
        # Non-browser client (curl, scripts) — not a CSRF vector.
        self.assertTrue(csrf.request_allowed("POST", None, self.EXPECTED, set(), set()))
        self.assertTrue(csrf.request_allowed("POST", "", self.EXPECTED, set(), set()))

    def test_matching_origin_allowed(self):
        self.assertTrue(
            csrf.request_allowed(
                "POST", "http://newtarr.local:9705/login", self.EXPECTED, set(), set()
            )
        )

    def test_different_port_blocked(self):
        # The codex finding: another app on the same host on port 8080 must
        # NOT be allowed when our service runs on port 9705.
        self.assertFalse(
            csrf.request_allowed(
                "POST", "http://newtarr.local:8080/", self.EXPECTED, set(), set()
            )
        )

    def test_different_scheme_blocked(self):
        self.assertFalse(
            csrf.request_allowed(
                "POST", "https://newtarr.local:9705/", self.EXPECTED, set(), set()
            )
        )

    def test_different_host_blocked(self):
        self.assertFalse(
            csrf.request_allowed(
                "POST", "http://evil.example:9705/", self.EXPECTED, set(), set()
            )
        )

    def test_trusted_full_origin_allowed(self):
        trusted = {("https", "proxy.example.com", 443)}
        self.assertTrue(
            csrf.request_allowed(
                "POST", "https://proxy.example.com/", self.EXPECTED, trusted, set()
            )
        )

    def test_trusted_full_origin_wrong_port_blocked(self):
        trusted = {("https", "proxy.example.com", 443)}
        self.assertFalse(
            csrf.request_allowed(
                "POST", "https://proxy.example.com:8443/", self.EXPECTED, trusted, set()
            )
        )

    def test_trusted_bare_hostname_allows_any_port(self):
        # Bare hostname in NEWTARR_TRUSTED_ORIGINS is an explicit operator
        # opt-in; matches host-only.
        hostnames = {"proxy.example.com"}
        self.assertTrue(
            csrf.request_allowed(
                "POST", "https://proxy.example.com:8443/", self.EXPECTED, set(), hostnames
            )
        )

    def test_malformed_origin_blocked(self):
        self.assertFalse(
            csrf.request_allowed("POST", "not-a-url", self.EXPECTED, set(), set())
        )


class TrustedOriginsFromEnvTests(unittest.TestCase):
    def setUp(self):
        csrf._reset_cache_for_tests()

    def tearDown(self):
        csrf._reset_cache_for_tests()

    def test_env_parsed_and_cached(self):
        with mock.patch.dict(os.environ, {"NEWTARR_TRUSTED_ORIGINS": "https://a.b:8443, x.y"}):
            origins, hosts = csrf.trusted_origins_from_env()
            self.assertEqual(origins, {("https", "a.b", 8443)})
            self.assertEqual(hosts, {"x.y"})
            # Second call returns the same cached object.
            self.assertIs(csrf.trusted_origins_from_env()[0], origins)

    def test_cache_survives_env_change(self):
        with mock.patch.dict(os.environ, {"NEWTARR_TRUSTED_ORIGINS": "a.b"}):
            first = csrf.trusted_origins_from_env()
        with mock.patch.dict(os.environ, {"NEWTARR_TRUSTED_ORIGINS": "c.d"}):
            # Env-var changes mid-process are intentionally ignored (cached).
            second = csrf.trusted_origins_from_env()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
