def find_objects(self, camera_name: str = "left_wrist_cam") -> list[dict]:
  if not self.has_depth(camera_name):
    ...
    return []
  pf = self.platform
  rgb = np.ascontiguousarray(np.asarray(pf.camera_image(camera_name)))
  ...
  depth = np.asarray(pf.depth_image(camera_name), dtype=np.float32)
  intr = pf.camera_intrinsics(camera_name)
  pose = self._camera_pose_opencv(camera_name)
  ...
  cavity = self._source_cavity_xy()
  floor_z = self._source_floor_z()
  finder = self._wrist_finder()
  sets, report = finder.object_point_sets(
    rgb,
    depth,
    intr,
    pose,
    ee,
    cavity_xy=cavity,
    floor_z=floor_z,
    ...
  )
  fits = [
    (self._fit_plan_shape(pts), pts, mid)
    for pts, mid in zip(sets, report["kept_mask_ids"], strict=True)
  ]
  fits = [f for f in fits if f[0] is not None]
  fits.sort(key=lambda f: (0 if f[0]["graspable"] else 1, f[0]["centre_xy"][0]))
  out: list[dict] = [f[0] for f in fits]
  ...
  self.last_perception = report
  ...
  return out
