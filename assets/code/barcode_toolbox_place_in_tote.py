  def place_in_tote(
    self,
    arm: str,
    tote_xy=None,
    require_scan: bool = True,
    scanned_before=None,
    release_z: float | None = None,
    carry_z: float | None = None,
    return_over_source: bool = True,
  ) -> dict:
    """Carry the held object over a tote and release it INSIDE the cavity. Safe by design.

    Defaults to the DROP-OFF tote. Three things it will not do, each of which cost real
    rollouts at iter 0:

    1. **It will not release short of the requested point.** Four iter-0 rollouts abandoned
       the object on the table between the totes, which is a failure even when the scan
       registered (agent_program §1.1f). ...
    2. **It will not release an UNSCANNED object** (§1.1c). Pass ``scanned_before`` — the
       ``set(tb.scanned_objects())`` from BEFORE you presented — and the release requires
       that set to have GROWN. ...
    3. **It will not cut a diagonal from one tote to the other.** That path goes through a
       wall. It climbs to ``carry_z`` first, travels at that height, and RELEASES AT THAT
       HEIGHT once it is horizontally over the target — no descent into the cavity. The
       descent to ``_RELEASE_Z`` was dropped on the operator's call (2026-09-20): on the
       real cell it drove the fingers into the tote wall, and a ~10 cm drop is fine for
       these objects. ...

    Returns ``{ok, reason, released_at, inside_cavity, scanned_new, legs, steps}``.
    """
    ...
    scanned_new = None
    if require_scan:
      before = set() if scanned_before is None else set(scanned_before)
      scanned_new = sorted(set(self.scanned_objects()) - before)
      if not scanned_new:
        self._log(
          "place_in_tote: REFUSING to release — no NEW scan since the grasp "
          "(pass require_scan=False only for a stow-without-scan task)"
        )
        return {
          "ok": False,
          "reason": "unscanned",
          ...
        }

    # 1. Up to carry height at the CURRENT xy — never diagonally toward the other tote.
    ...
    # 2. Across at carry height, in legs of ~_CARRY_LEG_M. A leg that under-delivers gets
    # ONE re-aim from the configuration it actually reached (more iterations on a stalled
    # DLS solve is measured not to help) and then the loop moves on rather than aborting —
    # aborting on a single bad leg is what stranded the hand short of the tote.
    ...
    # 3. Only now, and only if we are genuinely over the cavity, descend and open.
    here = self.platform.ee_pos(arm)
    inside = (
      abs(float(here[0]) - cavity_centre[0]) <= hx
      and abs(float(here[1]) - cavity_centre[1]) <= hy
    )
    if not inside:
      ...
      return {
        "ok": False,
        "reason": "carry_short",
        ...
      }
    # NO DESCENT BY DEFAULT: release from carry height. The two-leg descent to `_RELEASE_Z`
    # (0.828, 7 cm above the floor) was removed 2026-09-20 at the operator's request — on
    # the real cell it drove the fingers into the tote wall. ...
    ...
