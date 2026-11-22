"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""

# How long the blinker and the same-side detection must agree before the first chime.
CONFIRM_S = 0.2
# Minimum gap between chimes while the condition stays true, and after it returns.
COOLDOWN_S = 5.0


class BlindspotChime:
  """One chime when a turn signal is on and that side's blind spot is occupied.

  Hazards (both blinkers) are ignored. There is no engagement, speed, or auto
  lane change gate: the caller decides whether the car state is valid.
  """

  def __init__(self) -> None:
    self._condition_since: float | None = None
    self._next_allowed = 0.0

  def update(self, left_blinker: bool, right_blinker: bool, left_blindspot: bool, right_blindspot: bool,
             now: float, enabled: bool) -> bool:
    hazard = left_blinker and right_blinker
    occupied = (not hazard) and ((left_blinker and left_blindspot) or (right_blinker and right_blindspot))
    if not enabled or not occupied:
      self._condition_since = None
      return False

    if self._condition_since is None:
      self._condition_since = now
    # 1 µs of slack so a timestamp of exactly CONFIRM_S / COOLDOWN_S is ready.
    if (now - self._condition_since) + 1e-6 < CONFIRM_S or now + 1e-6 < self._next_allowed:
      return False

    self._next_allowed = now + COOLDOWN_S
    return True
