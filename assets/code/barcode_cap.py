ARM = "left"
NEEDED = 2
MAX_PASSES = 8

stowed = 0
# ... source_xy(): the measured source-tote centre from tb.find_source_tote()
# ... new_reads(before): entries of tb.scanned_objects() that are not in `before`

for _pass in range(MAX_PASSES):
    if stowed >= NEEDED:
        break
    objs = tb.find_objects()
    if not objs:
        tb.view_source_tote(ARM)
        tb.wait(5)
        objs = tb.find_objects()
    if not objs:
        break
    obj = objs[0]

    tb.set_gripper(ARM, True, hold_steps=4)
    g = tb.grasp_object(ARM, obj)
    if g["reason"] == "attempt_cap":
        break
    if not g["ok"]:
        # ... two failed grasps in a row end the run; otherwise re-look from the view pose
        continue

    before = set(tb.scanned_objects())
    tb.present_to_scanner(ARM)
    if not new_reads(before):
        r = tb.regrasp_rotated(ARM)
        # ... a refused regrasp means the object is back in the source tote: re-perceive
        tb.present_to_scanner(ARM)

    if not new_reads(before):
        # Still unread and still held: never stow it. Put it back in the source
        # tote so the next pass re-perceives it in whatever pose it settles.
        tb.place_in_tote(ARM, tote_xy=source_xy(), require_scan=False)
        continue

    p = tb.place_in_tote(ARM, scanned_before=before)
    if p["ok"]:
        stowed += 1
