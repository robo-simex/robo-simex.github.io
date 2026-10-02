def grasp_object(self, arm, obj, grasp_z=None, seat_advance=0.0, pre_slew=True, vet=True, narrow_jaws=False) -> dict:
  self._held_obj = dict(obj)
  if self._grasp_attempts >= int(self._MAX_GRASP_ATTEMPTS):
    ...
    return {
      "ok": False,
      "reason": "attempt_cap",
      ...
    }
  self._grasp_attempts += 1
  ...
  top_z = float(obj["top_z"])
  psi = float(obj["grasp_azimuth_rad"])
  x, y = (float(v) for v in obj["centre_xy"])
  psi = self._round_grasp_azimuth(obj, psi)
  gz = (
    float(grasp_z)
    if grasp_z is not None
    else max(
      self._GRASP_Z_MIN,
      min(self._GRASP_Z_MAX, 0.5 * (self._CAVITY_FLOOR_Z + top_z)),
    )
  )
  gz -= float(self._GRASP_Z_BIAS_M)
  quat = self.topdown_grasp_quat(psi)
  ...
  pre_z = top_z + self._HAND_BELOW_SITE_M + self._PRE_GRASP_CLEAR_M
  ...
  if vet:
    b = self.plan_pose((x, y, gz), arm, target_quat=quat)
    a = self.plan_pose((x, y, pre_z), arm, target_quat=quat)
    if a["pos_err_m"] > self._HOVER_PLAN_LEAN_M:
      ...
      for lean_deg in self._LEAN_DEGS:
        lq = self._lean_toward_robot(self.topdown_grasp_quat(psi_l), lean_deg)
        la = self.plan_pose((x, y, pre_z), arm, target_quat=lq)
        lb = self.plan_pose((x, y, gz), arm, target_quat=lq)
        if (
          max(la["pos_err_m"], lb["pos_err_m"]) <= self._VET_POS_TOL_M
          and la["pos_err_m"] < a["pos_err_m"]
        ):
          quat, a, b, lean_used, psi = lq, la, lb, lean_deg, psi_l
          ...
          break
    ...
    if b["pos_err_m"] > self._VET_POS_TOL_M:
      ...
      return {
        "ok": False,
        "reason": "unreachable",
        ...
      }
  ...
  r = self.grasp_topdown(
    arm,
    (x, y),
    psi,
    grasp_z=gz,
    ...
    pre_z=pre_z,
    pre_iters=strain_iters,
    approach_quat=None if lean_used == 0.0 else quat,
    object_geometry=obj,
  )
  if (not r["ok"]) and r["reason"] == "pre_grasp" and lean_used == 0.0:
    ...
    r = self.grasp_topdown(
      ...
      approach_quat=lq,
      object_geometry=obj,
    )
    ...
  ...
  return r
