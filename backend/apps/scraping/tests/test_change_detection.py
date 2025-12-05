"""
Unit tests for change detection functionality
"""
from datetime import datetime, timedelta
from django.test import TestCase
from apps.scraping.services import ChangeDetectionService


class ChangeDetectionTest(TestCase):
    """Test cases for change detection logic"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = ChangeDetectionService()

    def test_detect_changes_first_scrape(self):
        """Test detecting changes on first scrape (no old state)"""
        old_state = {}
        new_state = {
            "status": "open",
            "deadline": "2024-12-31"
        }

        has_changes, changes = self.service.detect_changes(old_state, new_state)

        self.assertTrue(has_changes)
        self.assertEqual(len(changes), 2)
        self.assertEqual(changes["status"]["old"], None)
        self.assertEqual(changes["status"]["new"], "open")
        self.assertEqual(changes["deadline"]["old"], None)
        self.assertEqual(changes["deadline"]["new"], "2024-12-31")

    def test_detect_changes_no_changes(self):
        """Test detecting changes when state is unchanged"""
        old_state = {
            "status": "open",
            "deadline": "2024-12-31"
        }
        new_state = {
            "status": "open",
            "deadline": "2024-12-31"
        }

        has_changes, changes = self.service.detect_changes(old_state, new_state)

        self.assertFalse(has_changes)
        self.assertEqual(len(changes), 0)

    def test_detect_changes_single_field_changed(self):
        """Test detecting changes when one field changes"""
        old_state = {
            "status": "closed",
            "deadline": "2024-12-31"
        }
        new_state = {
            "status": "open",
            "deadline": "2024-12-31"
        }

        has_changes, changes = self.service.detect_changes(old_state, new_state)

        self.assertTrue(has_changes)
        self.assertEqual(len(changes), 1)
        self.assertIn("status", changes)
        self.assertEqual(changes["status"]["old"], "closed")
        self.assertEqual(changes["status"]["new"], "open")

    def test_detect_changes_multiple_fields_changed(self):
        """Test detecting changes when multiple fields change"""
        old_state = {
            "status": "closed",
            "deadline": "2024-12-31",
            "priority": "low"
        }
        new_state = {
            "status": "open",
            "deadline": "2025-01-15",
            "priority": "high"
        }

        has_changes, changes = self.service.detect_changes(old_state, new_state)

        self.assertTrue(has_changes)
        self.assertEqual(len(changes), 3)
        self.assertIn("status", changes)
        self.assertIn("deadline", changes)
        self.assertIn("priority", changes)

    def test_detect_changes_new_field_added(self):
        """Test detecting changes when new field is added"""
        old_state = {
            "status": "open"
        }
        new_state = {
            "status": "open",
            "deadline": "2024-12-31"
        }

        has_changes, changes = self.service.detect_changes(old_state, new_state)

        self.assertTrue(has_changes)
        self.assertEqual(len(changes), 1)
        self.assertIn("deadline", changes)
        self.assertEqual(changes["deadline"]["old"], None)
        self.assertEqual(changes["deadline"]["new"], "2024-12-31")

    def test_detect_changes_field_removed(self):
        """Test detecting changes when field is removed"""
        old_state = {
            "status": "open",
            "deadline": "2024-12-31"
        }
        new_state = {
            "status": "open"
        }

        has_changes, changes = self.service.detect_changes(old_state, new_state)

        self.assertTrue(has_changes)
        self.assertEqual(len(changes), 1)
        self.assertIn("deadline", changes)
        self.assertEqual(changes["deadline"]["old"], "2024-12-31")
        self.assertEqual(changes["deadline"]["new"], None)

    def test_should_alert_on_change_mode_with_changes(self):
        """Test alert decision in on_change mode with changes"""
        has_changes = True
        changes = {"status": {"old": "closed", "new": "open"}}
        alert_mode = "on_change"
        last_alert_state = None
        current_state = {"status": "open"}

        should_alert = self.service.should_alert(
            has_changes, changes, alert_mode, last_alert_state, current_state
        )

        self.assertTrue(should_alert)

    def test_should_alert_on_change_mode_without_changes(self):
        """Test alert decision in on_change mode without changes"""
        has_changes = False
        changes = {}
        alert_mode = "on_change"
        last_alert_state = None
        current_state = {"status": "open"}

        should_alert = self.service.should_alert(
            has_changes, changes, alert_mode, last_alert_state, current_state
        )

        self.assertFalse(should_alert)

    def test_should_alert_once_mode_first_time_truthy(self):
        """Test alert decision in once mode on first truthy value"""
        has_changes = True
        changes = {"status": {"old": None, "new": "open"}}
        alert_mode = "once"
        last_alert_state = None
        current_state = {"status": "open"}
        truthy_values = {"status": ["open", "available"]}

        should_alert = self.service.should_alert(
            has_changes, changes, alert_mode, last_alert_state,
            current_state, truthy_values
        )

        self.assertTrue(should_alert)

    def test_should_alert_once_mode_first_time_not_truthy(self):
        """Test alert decision in once mode on first non-truthy value"""
        has_changes = True
        changes = {"status": {"old": None, "new": "closed"}}
        alert_mode = "once"
        last_alert_state = None
        current_state = {"status": "closed"}
        truthy_values = {"status": ["open", "available"]}

        should_alert = self.service.should_alert(
            has_changes, changes, alert_mode, last_alert_state,
            current_state, truthy_values
        )

        self.assertFalse(should_alert)

    def test_should_alert_once_mode_becomes_truthy(self):
        """Test alert decision in once mode when value becomes truthy"""
        has_changes = True
        changes = {"status": {"old": "closed", "new": "open"}}
        alert_mode = "once"
        last_alert_state = {"status": "closed"}
        current_state = {"status": "open"}
        truthy_values = {"status": ["open", "available"]}

        should_alert = self.service.should_alert(
            has_changes, changes, alert_mode, last_alert_state,
            current_state, truthy_values
        )

        self.assertTrue(should_alert)

    def test_should_alert_once_mode_already_truthy(self):
        """Test alert decision in once mode when already truthy"""
        has_changes = True
        changes = {"deadline": {"old": "2024-12-31", "new": "2025-01-15"}}
        alert_mode = "once"
        last_alert_state = {"status": "open", "deadline": "2024-12-31"}
        current_state = {"status": "open", "deadline": "2025-01-15"}
        truthy_values = {"status": ["open", "available"]}

        should_alert = self.service.should_alert(
            has_changes, changes, alert_mode, last_alert_state,
            current_state, truthy_values
        )

        # Status was already truthy, so no alert
        self.assertFalse(should_alert)

    def test_should_alert_once_mode_becomes_non_truthy(self):
        """Test alert decision in once mode when value becomes non-truthy"""
        has_changes = True
        changes = {"status": {"old": "open", "new": "closed"}}
        alert_mode = "once"
        last_alert_state = {"status": "open"}
        current_state = {"status": "closed"}
        truthy_values = {"status": ["open", "available"]}

        should_alert = self.service.should_alert(
            has_changes, changes, alert_mode, last_alert_state,
            current_state, truthy_values
        )

        # Becoming non-truthy doesn't trigger alert in once mode
        self.assertFalse(should_alert)

    def test_is_truthy_case_insensitive(self):
        """Test truthy check is case-insensitive"""
        truthy_list = ["open", "available"]

        self.assertTrue(self.service._is_truthy("OPEN", truthy_list))
        self.assertTrue(self.service._is_truthy("Open", truthy_list))
        self.assertTrue(self.service._is_truthy("open", truthy_list))
        self.assertTrue(self.service._is_truthy("  AVAILABLE  ", truthy_list))

    def test_is_truthy_with_none(self):
        """Test truthy check with None value"""
        truthy_list = ["open", "available"]

        self.assertFalse(self.service._is_truthy(None, truthy_list))

    def test_is_truthy_with_non_string(self):
        """Test truthy check with non-string values"""
        truthy_list = ["1", "true"]

        self.assertTrue(self.service._is_truthy(1, truthy_list))
        self.assertTrue(self.service._is_truthy(True, ["true"]))

    def test_is_rate_limited_no_previous_alert(self):
        """Test rate limiting with no previous alert"""
        last_alert_time = None
        current_time = datetime.now()

        is_limited = self.service.is_rate_limited(last_alert_time, current_time)

        self.assertFalse(is_limited)

    def test_is_rate_limited_within_limit(self):
        """Test rate limiting within time limit"""
        current_time = datetime.now()
        last_alert_time = current_time - timedelta(minutes=30)

        is_limited = self.service.is_rate_limited(last_alert_time, current_time)

        self.assertTrue(is_limited)

    def test_is_rate_limited_outside_limit(self):
        """Test rate limiting outside time limit"""
        current_time = datetime.now()
        last_alert_time = current_time - timedelta(minutes=90)

        is_limited = self.service.is_rate_limited(last_alert_time, current_time)

        self.assertFalse(is_limited)

    def test_is_rate_limited_exactly_at_limit(self):
        """Test rate limiting exactly at time limit"""
        current_time = datetime.now()
        last_alert_time = current_time - timedelta(minutes=60)

        is_limited = self.service.is_rate_limited(last_alert_time, current_time)

        # At exactly the limit, should not be limited
        self.assertFalse(is_limited)

    def test_get_change_summary_no_changes(self):
        """Test change summary with no changes"""
        changes = {}

        summary = self.service.get_change_summary(changes)

        self.assertEqual(summary, "No changes detected")

    def test_get_change_summary_single_change(self):
        """Test change summary with single change"""
        changes = {
            "status": {"old": "closed", "new": "open"}
        }

        summary = self.service.get_change_summary(changes)

        self.assertEqual(summary, "status: closed → open")

    def test_get_change_summary_multiple_changes(self):
        """Test change summary with multiple changes"""
        changes = {
            "status": {"old": "closed", "new": "open"},
            "deadline": {"old": "2024-12-31", "new": "2025-01-15"},
            "priority": {"old": "low", "new": "high"}
        }

        summary = self.service.get_change_summary(changes)

        self.assertIn("status: closed → open", summary)
        self.assertIn("deadline: 2024-12-31 → 2025-01-15", summary)
        self.assertIn("priority: low → high", summary)

    def test_get_change_summary_many_changes(self):
        """Test change summary with many changes (should truncate)"""
        changes = {
            f"field{i}": {"old": f"old{i}", "new": f"new{i}"}
            for i in range(5)
        }

        summary = self.service.get_change_summary(changes)

        # Should show first 3 and indicate more
        self.assertIn("...", summary)
        self.assertIn("2 more changes", summary)

    def test_should_update_alert_state_once_mode_alert_sent(self):
        """Test alert state update decision in once mode when alert sent"""
        alert_mode = "once"
        alert_sent = True

        should_update = self.service.should_update_alert_state(alert_mode, alert_sent)

        self.assertTrue(should_update)

    def test_should_update_alert_state_once_mode_no_alert(self):
        """Test alert state update decision in once mode when no alert"""
        alert_mode = "once"
        alert_sent = False

        should_update = self.service.should_update_alert_state(alert_mode, alert_sent)

        self.assertFalse(should_update)

    def test_should_update_alert_state_on_change_mode(self):
        """Test alert state update decision in on_change mode"""
        alert_mode = "on_change"
        alert_sent = True

        should_update = self.service.should_update_alert_state(alert_mode, alert_sent)

        # on_change mode doesn't track alert state
        self.assertFalse(should_update)

    def test_has_truthy_values_with_truthy(self):
        """Test checking if state has truthy values"""
        state = {"status": "open", "deadline": "2024-12-31"}
        truthy_values = {"status": ["open", "available"]}

        has_truthy = self.service._has_truthy_values(state, truthy_values)

        self.assertTrue(has_truthy)

    def test_has_truthy_values_without_truthy(self):
        """Test checking if state has truthy values when none are truthy"""
        state = {"status": "closed", "deadline": "2024-12-31"}
        truthy_values = {"status": ["open", "available"]}

        has_truthy = self.service._has_truthy_values(state, truthy_values)

        self.assertFalse(has_truthy)

    def test_has_truthy_values_empty_truthy_config(self):
        """Test checking if state has truthy values with empty config"""
        state = {"status": "open"}
        truthy_values = {}

        has_truthy = self.service._has_truthy_values(state, truthy_values)

        self.assertFalse(has_truthy)
