"""Unit tests for resolve_schedule_target in src.primary.scheduler_engine."""
import unittest

from src.primary.scheduler_engine import resolve_schedule_target


class ResolveScheduleTargetTests(unittest.TestCase):
    def test_global_maps_to_global(self):
        self.assertEqual(resolve_schedule_target("global"), "global")

    def test_bare_base_app_passes_through(self):
        for app in ("sonarr", "radarr", "lidarr", "readarr", "whisparr", "eros"):
            with self.subTest(app=app):
                self.assertEqual(resolve_schedule_target(app), app)

    def test_all_suffix_maps_to_base_app(self):
        self.assertEqual(resolve_schedule_target("sonarr-all"), "sonarr")
        self.assertEqual(resolve_schedule_target("radarr-all"), "radarr")
        self.assertEqual(resolve_schedule_target("lidarr-all"), "lidarr")
        self.assertEqual(resolve_schedule_target("readarr-all"), "readarr")

    def test_whisparr_versions_route_to_their_config_files(self):
        # v2 is the legacy "whisparr" config; v3 is the Eros config.
        self.assertEqual(resolve_schedule_target("whisparr-v2"), "whisparr")
        self.assertEqual(resolve_schedule_target("whisparr-v3"), "eros")

    def test_unsupported_values_return_none(self):
        for value in (
            None,
            "",
            123,
            [],
            {},
            "swaparr",  # not a scheduler target
            "general",  # not a scheduler target
            "sonarr-1",  # per-instance — not currently supported by the executor
            "whisparr-v4",
            "unknownapp-all",
        ):
            with self.subTest(value=value):
                self.assertIsNone(resolve_schedule_target(value))

    def test_traversal_payloads_return_none(self):
        for value in (
            "../user/credentials",
            "sonarr/../etc",
            "/etc/passwd",
            "..",
            "sonarr.json",
            "sonarr\x00",
        ):
            with self.subTest(value=value):
                self.assertIsNone(resolve_schedule_target(value))


if __name__ == "__main__":
    unittest.main()
