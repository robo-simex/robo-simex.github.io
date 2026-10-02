def regrasp_rotated(self, arm, delta_rad=math.pi / 2.0, settle_steps=40) -> dict:
  ...
  src = self._tote_centre("source")
  put = None
  objs: list[dict] = []
  if (
    self._is_flat(self._held_obj)
    or (self._held_obj or {}).get("long_axis_rad") is not None
  ):
    put, objs = self._flip_until_down(arm, src, settle_steps=int(settle_steps))
    if put is not None and not put["ok"]:
      ...
      put = None
  if put is None:
    put = self.place_in_tote(
      arm, tote_xy=src, require_scan=False, return_over_source=False
    )
  out["put_down"] = put
  if not put["ok"]:
    out["reason"] = f"put_down_{put['reason']}"
    ...
    return out
  if not objs:
    self.platform.wait(int(settle_steps))
    ...
    ref = put.get("released_at") or self.platform.ee_pos(arm)
    objs = self._look_for_dropped(arm, (ref[0], ref[1]))
  out["found"] = len(objs)
  if not objs:
    out["reason"] = "not_found_after_put_down"
    ...
    return out
  ref = put.get("released_at") or self.platform.ee_pos(arm)
  obj = min(objs, key=lambda o: math.dist(o["centre_xy"], (ref[0], ref[1])))
  obj = dict(obj)
  if obj.get("long_axis_rad") is None:
    obj["grasp_azimuth_rad"] = (
      float(obj["grasp_azimuth_rad"]) + float(delta_rad)
    ) % math.pi
    ...
  ...
  self.set_gripper(arm, True, hold_steps=4)
  g = self.grasp_object(arm, obj)
  out["grasp"] = g
  out["ok"] = bool(g["ok"])
  out["reason"] = "held" if g["ok"] else f"grasp_{g['reason']}"
  ...
  return out
