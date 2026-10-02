  def deliver_plate(self, plate_xy, arm: str | None = None, tote_xy=None) -> dict:
    """Grasp (inboard rim, then outboard) -> carry -> release -> park + LOOK,
    retrying once if the plate is shed mid-delivery (SG11, loss-aware).

    The delivery verdict comes from PERCEPTION *gated by the place outcome*: after
    the release both hands park and the table is re-detected; the plate counts as
    delivered when no plate of its colour (or, colour unknown, none within 15 cm of
    its start) remains on the table AND place_in_tote did not report a rise-stage
    loss. ... Returns {delivered, stage, arm, grasp, place,
    plates}; ``plates`` is the fresh detection list (hands parked), so callers need
    not re-perceive.
    """
    arm = self.arm_for_plate(plate_xy) if arm is None else arm
    ...
    g = self.grasp_plate_rim((px, py), arm)
    if not g["grasped"] and g["plan"] is not None:
      other = "outboard" if g["plan"]["side"] == "inboard" else "inboard"
      ...
      g2 = self.grasp_plate_rim((px, py), arm, side=other)
      if g2["plan"] is not None:
        g = g2
    ...
    if not g["grasped"]:
      self.set_gripper(arm, True, hold_steps=2)
      out["plates"] = self.perceive_plates()
      return out
    ...
    MAX_PLACE_TRIES = 2
    for _try in range(MAX_PLACE_TRIES):
      p = self.place_in_tote(
        arm,
        tote_xy=self._tote_cache,
        flip=g["plan"]["flip"],
        side_used=g["plan"]["side"],
      )
      rise_loss = p.get("stage") == "rise"
      ...
      if rise_loss:
        self.stow_arm(arm)
      plates = self.perceive_plates()
      out["plates"] = plates
      ...
      remaining = [d for d in same if d not in inside]
      # A rise-stage loss cannot be in the tote; never let perception call it delivered.
      out["delivered"] = (not remaining) and not rise_loss
      if out["delivered"]:
        out["stage"] = "released"
        break
      out["stage"] = "lost_in_rise" if rise_loss else "lost_in_carry"
      ...
      # Retry the re-perceived (now-closer) plate once, if it is visible to re-grasp.
      if remaining and _try + 1 < MAX_PLACE_TRIES:
        ...
        g = self.grasp_plate_rim((rx, ry), arm)
        ...
        continue
      break
    ...
    return out
