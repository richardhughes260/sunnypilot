"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import unittest

from openpilot.sunnypilot.selfdrive.controls.lib.blindspot_chime import COOLDOWN_S, CONFIRM_S, BlindspotChime


class TestBlindspotChime(unittest.TestCase):
  def test_same_side_chimes_at_low_speed(self):
    # No engagement or auto lane change input. A crawl and a faster roll both chime.
    for _speed in (0.0, 4.5, 8.9):
      chime = BlindspotChime()
      self.assertFalse(chime.update(True, False, True, False, 0.0, True))
      self.assertTrue(chime.update(True, False, True, False, CONFIRM_S, True))

  def test_right_side(self):
    chime = BlindspotChime()
    self.assertFalse(chime.update(False, True, False, True, 0.0, True))
    self.assertTrue(chime.update(False, True, False, True, CONFIRM_S, True))

  def test_other_side_is_silent(self):
    chime = BlindspotChime()
    self.assertFalse(chime.update(True, False, False, True, 1.0, True))
    self.assertFalse(chime.update(False, True, True, False, 1.0, True))

  def test_hazards_are_ignored(self):
    chime = BlindspotChime()
    self.assertFalse(chime.update(True, True, True, True, 1.0, True))

  def test_disabled_is_silent(self):
    chime = BlindspotChime()
    self.assertFalse(chime.update(True, False, True, False, 1.0, False))

  def test_blinker_without_car_is_silent(self):
    chime = BlindspotChime()
    self.assertFalse(chime.update(True, False, False, False, 1.0, True))

  def test_cooldown_and_rearm(self):
    chime = BlindspotChime()
    self.assertFalse(chime.update(True, False, True, False, 0.0, True))
    self.assertTrue(chime.update(True, False, True, False, CONFIRM_S, True))
    self.assertFalse(chime.update(True, False, True, False, CONFIRM_S + 1.0, True))
    self.assertFalse(chime.update(True, False, True, False, CONFIRM_S + COOLDOWN_S - 0.05, True))
    self.assertTrue(chime.update(True, False, True, False, CONFIRM_S + COOLDOWN_S, True))

  def test_gap_restarts_confirmation(self):
    chime = BlindspotChime()
    self.assertFalse(chime.update(True, False, True, False, 0.0, True))
    self.assertFalse(chime.update(False, False, True, False, 0.1, True))
    restarted = 0.1
    self.assertFalse(chime.update(True, False, True, False, restarted, True))
    self.assertFalse(chime.update(True, False, True, False, restarted + CONFIRM_S - 0.05, True))
    self.assertTrue(chime.update(True, False, True, False, restarted + CONFIRM_S, True))

  def test_alert_does_not_outrank_safety_alerts(self):
    import importlib.util
    if importlib.util.find_spec("msgq") is None:
      self.skipTest("msgq is not importable")

    from openpilot.cereal import custom, log
    from openpilot.selfdrive.selfdrived.events import EVENTS
    from openpilot.sunnypilot.selfdrive.selfdrived.events import EVENTS_SP
    from openpilot.sunnypilot.selfdrive.selfdrived.events_base import ET, Priority

    from openpilot.selfdrive.ui.soundd import MAX_VOLUME, playback_volume

    EventName = log.OnroadEvent.EventName
    EventNameSP = custom.OnroadEventSP.EventName
    AudibleAlert = log.SelfdriveState.AudibleAlert
    AudibleAlertSP = custom.SelfdriveStateSP.AudibleAlert
    alert = EVENTS_SP[EventNameSP.blindspotChime][ET.PERMANENT]
    self.assertEqual(alert.priority, Priority.LOWEST)
    self.assertEqual(int(alert.audible_alert), int(AudibleAlertSP.blindspotChime))
    self.assertNotEqual(int(alert.audible_alert), int(AudibleAlert.prompt))
    self.assertEqual(int(alert.alert_size), int(log.SelfdriveState.AlertSize.none))
    # Full scale at a quiet device volume and at a loud one. Prompt stays scaled.
    self.assertEqual(playback_volume(alert.audible_alert, 0.05), MAX_VOLUME)
    self.assertEqual(playback_volume(alert.audible_alert, MAX_VOLUME), MAX_VOLUME)
    self.assertEqual(playback_volume(AudibleAlert.prompt, 0.05), 0.05)
    blocked = EVENTS[EventName.laneChangeBlocked][ET.WARNING]
    self.assertGreater(blocked.priority, alert.priority)
    self.assertEqual(int(blocked.audible_alert), int(AudibleAlert.prompt))
    self.assertEqual(playback_volume(blocked.audible_alert, 0.2), 0.2)
