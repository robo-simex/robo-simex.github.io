def present_to_scanner(self, arm, max_steps=60, dither_steps=12, sweep_steps=420, restore_wrist=True) -> bool:
  already_read = set(self.scanned_objects())
  ...
  quat_entry = self.platform.ee_quat(arm)
  tilted = False
  flat = self._is_flat(self._held_obj)
  ...
  def _beep() -> bool:
    return bool(set(self.scanned_objects()) - already_read)

  def _done(value: bool) -> bool:
    ...
    if restore_wrist and (value or tilted):
      if tilted:
        self.set_gripper(arm, False, hold_steps=2)
        self._tilt_wrist(arm, quat_entry)
      if value and abs(float(self.platform.joint_pos(arm)[5]) - j6_entry) > 0.02:
        self._ramp_joint(arm, 5, j6_entry, self._PRESENT_AZ_RAMP_STEPS)
      ...
    return value

  ox, oy, oz = self._READ_ORIGIN
  read_point = np.array([ox - self._PRESENT_AXIS_DEPTH, oy, oz])

  def _aim_payload(legs: int, iters: int) -> bool:
    for _ in range(legs):
      if _beep():
        return True
      pay = np.asarray(self._payload_point(arm), dtype=float)
      ee = np.asarray(self.platform.ee_pos(arm), dtype=float)
      goal = read_point + (ee - pay)
      err = float(np.linalg.norm(goal - ee))
      if err < self._PRESENT_AIM_TOL_M:
        return False
      ...
      self.move_ee_to(
        (float(leg[0]), float(leg[1]), float(leg[2])),
        arm,
        max_iters=iters,
        tol=self._PRESENT_AIM_TOL_M,
      )
    return _beep()

  if _aim_payload(6, max(30, int(max_steps))):
    ...
    return _done(True)
  ...
  def _azimuth_sweep(budget: int) -> bool:
    j6_0 = float(self.platform.joint_pos(arm)[5])
    ...
    for deg in self._PRESENT_AZ_STEPS_DEG:
      ...
      want = j6_0 + math.radians(deg)
      ...
      self._ramp_joint(arm, 5, want, self._PRESENT_AZ_RAMP_STEPS)
      self.platform.wait(3)
      ...
      if _beep():
        ...
        return True
    return False

  if flat:
    ...
  else:
    ...
    if _azimuth_sweep(int(sweep_steps) // 2):
      ...
      return _done(True)
    ...
  for tilt in self._PRESENT_TILT_DEG:
    rq = self._axis_angle_quat((0.0, 1.0, 0.0), math.radians(tilt))
    ...
    tilted = True
    ...
    t_out = self._tilt_wrist(arm, dq)
    ...
    if _beep():
      ...
      return _done(True)
    if t_out["ori_err_rad"] > 0.5:
      ...
      continue
    ...
    if _aim_payload(3, 60):
      ...
      return _done(True)
    ...
    if _azimuth_sweep(int(sweep_steps) // 3):
      ...
      return _done(True)
    ...
  ...
  return _done(_beep() or bool(already_read))
