targets = ["green", "blue", "red", "yellow"]
FRONT = {"green", "blue"}
LEFT_SIDE = {"green", "red"}

plates = tb.perceive_plates()

delivered = {}
for name in targets:
    cand = [d for d in plates if d["name"] == name]
    if not cand:
        # Colour not seen: slot rule on the same side (front = smallest x, back = largest x).
        cand = [d for d in plates if (d["world_xy"][1] > 0) == (name in LEFT_SIDE)]
        cand.sort(key=lambda d: d["world_xy"][0], reverse=(name not in FRONT))
    if not cand:
        delivered[name] = False
        continue

    xy = cand[0]["world_xy"]
    res = tb.deliver_plate(xy)
    plates = res["plates"]

    still = [d for d in plates if d["name"] == name]
    if still and not res["delivered"]:
        # Same colour still on the table: retry once at its new location.
        xy2 = still[0]["world_xy"]
        res = tb.deliver_plate(xy2)
        plates = res["plates"]
    delivered[name] = bool(res["delivered"])

print("summary:", delivered, "remaining on table:",
      [d["name"] for d in plates], "steps:", tb.get_step_count())
