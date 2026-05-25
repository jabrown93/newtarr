"""Unit tests for pure helpers in src.primary.auth.

Covers:
  - _is_local_ip: loopback, link-local, RFC1918/ULA, IPv4-mapped IPv6,
    public addresses, and malformed input.
  - _resolve_client_ip: X-Forwarded-For is honored only when the direct
    peer is itself local (otherwise XFF is attacker-controlled).
  - Login rate limiter: window enforcement, success clears state, expiry.
"""
import time
import unittest
from unittest import mock

from src.primary import auth


class IsLocalIpTests(unittest.TestCase):
    def test_loopback_v4(self):
        self.assertTrue(auth._is_local_ip("127.0.0.1"))

    def test_loopback_v6(self):
        self.assertTrue(auth._is_local_ip("::1"))

    def test_rfc1918_10(self):
        self.assertTrue(auth._is_local_ip("10.0.0.5"))

    def test_rfc1918_192_168(self):
        self.assertTrue(auth._is_local_ip("192.168.1.10"))

    def test_rfc1918_172_16(self):
        # 172.16/12 — the range string-prefix matching used to miss.
        self.assertTrue(auth._is_local_ip("172.16.5.5"))
        self.assertTrue(auth._is_local_ip("172.31.255.254"))

    def test_outside_172_16_block_is_public(self):
        # 172.32.0.0 is outside the RFC1918 172.16/12 block.
        self.assertFalse(auth._is_local_ip("172.32.0.1"))

    def test_link_local(self):
        self.assertTrue(auth._is_local_ip("169.254.1.1"))

    def test_ipv6_ula(self):
        self.assertTrue(auth._is_local_ip("fd00::1"))

    def test_ipv4_mapped_ipv6_private(self):
        # ::ffff:192.168.1.5 should unwrap and be treated as local.
        self.assertTrue(auth._is_local_ip("::ffff:192.168.1.5"))

    def test_ipv4_mapped_ipv6_public(self):
        self.assertFalse(auth._is_local_ip("::ffff:8.8.8.8"))

    def test_public_v4(self):
        self.assertFalse(auth._is_local_ip("8.8.8.8"))

    def test_public_v6(self):
        self.assertFalse(auth._is_local_ip("2001:4860:4860::8888"))

    def test_empty(self):
        self.assertFalse(auth._is_local_ip(""))
        self.assertFalse(auth._is_local_ip(None))

    def test_garbage(self):
        self.assertFalse(auth._is_local_ip("not-an-ip"))
        self.assertFalse(auth._is_local_ip("999.999.999.999"))


class ResolveClientIpTests(unittest.TestCase):
    def test_no_remote_addr(self):
        self.assertIsNone(auth._resolve_client_ip(None, None))
        self.assertIsNone(auth._resolve_client_ip("", "1.2.3.4"))

    def test_no_xff_returns_peer(self):
        self.assertEqual(auth._resolve_client_ip("8.8.8.8", None), "8.8.8.8")

    def test_xff_honored_when_peer_local(self):
        # Trusted local proxy forwards the real client.
        self.assertEqual(
            auth._resolve_client_ip("10.0.0.1", "8.8.8.8, 10.0.0.1"),
            "8.8.8.8",
        )

    def test_xff_ignored_when_peer_public(self):
        # Public peer claiming to forward a local client must be ignored.
        self.assertEqual(
            auth._resolve_client_ip("8.8.8.8", "10.0.0.5"),
            "8.8.8.8",
        )

    def test_xff_leftmost_is_client(self):
        self.assertEqual(
            auth._resolve_client_ip("127.0.0.1", "1.1.1.1, 2.2.2.2, 127.0.0.1"),
            "1.1.1.1",
        )

    def test_empty_xff_falls_back_to_peer(self):
        self.assertEqual(auth._resolve_client_ip("127.0.0.1", ""), "127.0.0.1")
        self.assertEqual(auth._resolve_client_ip("127.0.0.1", "   "), "127.0.0.1")


class LoginRateLimitTests(unittest.TestCase):
    def setUp(self):
        # Isolate the global attempts dict per test.
        auth._login_attempts.clear()

    def tearDown(self):
        auth._login_attempts.clear()

    def test_under_limit_not_blocked(self):
        for _ in range(auth._LOGIN_MAX_ATTEMPTS - 1):
            auth.record_failed_login("1.2.3.4")
        self.assertFalse(auth.login_rate_limited("1.2.3.4"))

    def test_at_limit_is_blocked(self):
        for _ in range(auth._LOGIN_MAX_ATTEMPTS):
            auth.record_failed_login("1.2.3.4")
        self.assertTrue(auth.login_rate_limited("1.2.3.4"))

    def test_different_ips_are_independent(self):
        for _ in range(auth._LOGIN_MAX_ATTEMPTS):
            auth.record_failed_login("1.2.3.4")
        self.assertTrue(auth.login_rate_limited("1.2.3.4"))
        self.assertFalse(auth.login_rate_limited("5.6.7.8"))

    def test_success_clears_attempts(self):
        for _ in range(auth._LOGIN_MAX_ATTEMPTS):
            auth.record_failed_login("1.2.3.4")
        auth.clear_failed_logins("1.2.3.4")
        self.assertFalse(auth.login_rate_limited("1.2.3.4"))

    def test_window_expiry(self):
        # Backdate every attempt past the window.
        old = time.time() - auth._LOGIN_ATTEMPT_WINDOW - 10
        auth._login_attempts["1.2.3.4"] = [old] * auth._LOGIN_MAX_ATTEMPTS
        self.assertFalse(auth.login_rate_limited("1.2.3.4"))

    def test_none_ip_is_safe(self):
        # Defensive: callers might pass None if remote_addr is missing.
        self.assertFalse(auth.login_rate_limited(None))
        auth.record_failed_login(None)  # must not raise


if __name__ == "__main__":
    unittest.main()
