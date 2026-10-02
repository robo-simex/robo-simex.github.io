def towel_frame(self, det=None, camera_name="top_cam") -> dict | None:
  if det is None:
    det = self.find_towel(camera_name)
  if det is None:
    return None
  c = [np.asarray(p, dtype=float) for p in det["corners"]]
  centre = np.mean(np.stack(c), axis=0)
  edges = []
  for i in range(4):
    a, b = c[i], c[(i + 1) % 4]
    mid = 0.5 * (a + b)
    out = mid - centre
    out = out / (np.linalg.norm(out) or 1.0)
    along = b - a
    length = float(np.linalg.norm(along))
    along = along / (length or 1.0)
    edges.append({"corners": [tuple(map(float, a)), tuple(map(float, b))], "mid": tuple(map(float, mid)),
                  "out": tuple(map(float, out)), "along": tuple(map(float, along)), "length": length})
  frame: dict = {}
  used: set = set()
  for side, d in sorted(_SIDE_DIR.items(), key=lambda kv: kv[0]):
    best, best_dot = None, -2.0
    for i, e in enumerate(edges):
      if i in used:
        continue
      dot = e["out"][0] * d[0] + e["out"][1] * d[1]
      if dot > best_dot:
        best, best_dot = i, dot
    used.add(best)
    frame[side] = edges[best]
  size_x = float(np.linalg.norm(np.subtract(frame["far"]["mid"], frame["near"]["mid"])))
  size_y = float(np.linalg.norm(np.subtract(frame["left"]["mid"], frame["right"]["mid"])))
  ...
  area = max(size_x * size_y, 1e-6)
  frame.update({
    "yaw_deg": float(math.degrees(math.atan2(frame["far"]["out"][1], frame["far"]["out"][0]))),
    "centre": tuple(map(float, centre)),
    "size_x": size_x,
    "size_y": size_y,
    ...
    "layers": int(max(1, round(0.34 * 0.34 / area))),
    "fold_ratio": float(0.34 * 0.34 / area),
    ...
  })
  ...
  return frame
