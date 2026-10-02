  def fold_edge(self, side: str, arms="auto", grasp="corners", carry_z: float | None = None,
                settle_steps: int = 20, verify: bool = True, inboard: float | None = None,
                guard: bool = True, correct: bool = True, tighten: bool = False,
                sweep: float | None = None, across=None) -> dict:
    """Fold the towel in half by carrying edge ``side`` onto the opposite edge. Closed loop.

    ``across``: the previous fold's carry direction (x, y); when given the edge is chosen
    perpendicular to it, not by world name (see ``_pick_edges``). ``carry_vec`` is in the result.

    ``side`` in {"far", "near", "left", "right"} (world sides, see ``towel_frame``).
    ``arms``: "auto" is two hands on a far/near fold and ONE hand on a left/right fold,
    keyed on ``side`` (REAL-ROBOT EDIT 2026-09-21; the sim rule -- two hands on an edge
    running along y, one on an edge running along x -- sent both hands to the left edge
    once the towel was yawed past 30 deg), or an explicit list like ["left"] or
    ["left", "right"].
    ...
    Detects, plans grasp/place points ``CARRY_STOP_SHORT_M`` short of a full carry across
    (REAL-ROBOT EDIT: the real towel drags toward the hands on lift), vets clearance
    (falls back to one hand if two collide), parks the idle arm clear of the path,
    grasps, lifts, carries under the reach ceiling, lays, releases, settles, retreats,
    then re-detects. ...
    ... Returns ``{ok, folded, reason,
    before, after, grasp_pts, place_pts, arms, grasp_res, carry_res, shift,
    correction}`` -- ``folded`` means the extent along the fold axis shrank to <= 70%
    while the other extent kept >= 85%.
    """
    before = self.towel_frame()
    ...
    edge, opp = self._pick_edges(before, side, across)
    carry_vec = self._carry_vec(edge, opp)  # REAL-ROBOT EDIT: full extent minus CARRY_STOP_SHORT_M
    res["carry_vec"] = tuple(map(float, carry_vec))
    # REAL-ROBOT EDIT (2026-09-21): hands by the REQUESTED side, not the edge's direction.
    two_hand_ok = side in self.TWO_HAND_SIDES
    if arms == "auto":
      if two_hand_ok:
        use = ["left", "right"]
      elif abs(edge["out"][1]) > 0.5:
        use = [("left" if edge["out"][1] > 0 else "right")]  # own-side hand on a y-edge
      else:
        # REAL-ROBOT EDIT (2026-09-21): a one-hand far/near fold takes the arm on the grasp
        # point's side of y (grasp_points' choice), not a fixed one.
        use = None
    else:
      use = list(arms)
    ...
