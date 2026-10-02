fr0 = _report("start")
# ... _report(tag): tb.towel_frame() and one print of size, extents, fold_ratio, centre, yaw
size_x0, size_y0 = fr0["size_x"], fr0["size_y"]

# ---- fold 1: far edge onto near edge, two hands ----
r1 = tb.fold_edge("far")
across = r1.get("carry_vec")
fr1 = r1["after"] if r1["after"] is not None else _report("after fold1")

if fr1 is not None and fr1["size_x"] > 0.72 * size_x0 and tb.get_step_count() < 260:
  # first fold did not take: one retry from the near side
  r1b = tb.fold_edge("near")
  if r1b.get("carry_vec") is not None and r1b["ok"]:
    across = r1b["carry_vec"]
  fr1 = r1b["after"] if r1b["after"] is not None else fr1

# ---- fold 2: across the first crease, one hand on the piece's own side ----
side2 = "left" if fr1["centre"][1] >= 0.0 else "right"
r2 = tb.fold_edge(side2, across=across)
fr2 = r2["after"] if r2["after"] is not None else _report("after fold2")

if fr2 is not None and fr2["size_y"] > 0.70 * size_y0 and tb.get_step_count() < 420:
  other = "right" if side2 == "left" else "left"
  r2b = tb.fold_edge(other, across=across)

_report("final")
