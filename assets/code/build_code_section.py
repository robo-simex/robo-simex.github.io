#!/usr/bin/env python3
"""Regenerate the per-task "View code" dialogs in index.html.

Toolbox pane: every toolbox method the CAP calls, in first-call order, as a stub
(signature, one-line summary from SUMMARIES, body length) read from toolbox_api.json,
which was extracted with `ast` from the deployed toolbox.py files (signatures only).  The primitive
the task hinges on is expanded with the comment-stripped body excerpt from its
*_toolbox_*.py snippet.  CAP pane: the CAP snippet with comments stripped.
Both are written into the CODE-PANEL:<task> marker blocks in ../../index.html.

    python3 assets/code/build_code_section.py
"""
from html import escape
from pathlib import Path
import json, re, textwrap

HERE = Path(__file__).resolve().parent
INDEX = HERE.parent.parent / "index.html"
API = json.loads((HERE / "toolbox_api.json").read_text())
IND = "  "           # the toolboxes use 2-space indentation
WIDTH = 92

TASKS = {
  "barcode": dict(
    title="Barcode scanning",
    instruction="Clear the tote. The source tote holds two different objects. Read both barcodes at the scanner and put both objects in the drop-off tote.",
    toolbox_src="toolbox.py", toolbox_total=6887, expand={"find_objects": ("barcode_toolbox_find_objects.py", 0), "grasp_object": ("barcode_toolbox_grasp_object.py", 0),
            "present_to_scanner": ("barcode_toolbox_present_to_scanner.py", 0), "regrasp_rotated": ("barcode_toolbox_regrasp_rotated.py", 0),
            "place_in_tote": ("barcode_toolbox_place_in_tote.py", 0)},
    toolbox_note="The ten primitives this CAP calls, in call order; the five that do the work are cut to their key lines. The grasp vets its poses before moving, the scan sweeps and tilts the payload until a read latches, and the stow refuses to release an unscanned object.",
    cap=("barcode_cap.py", 0, 79),
    cap_note="Find, grasp, present to the scanner; judge the read by the set of scanned codes growing; regrasp rotated on a miss; put an object that still will not read back in the source tote instead of stowing it.",
  ),
  "plate": dict(
    title="Plate to tote",
    instruction="Clean the station by moving all four plates (green front-left, blue front-right, red back-left, yellow back-right) into the tote.",
    toolbox_src="toolbox.py", toolbox_total=1834, expand={"perceive_plates": ("plate_toolbox_perceive_plates.py", 0), "deliver_plate": ("plate_toolbox_deliver_plate.py", 0)},
    toolbox_note="The three primitives this CAP calls. Perception re-detects once when an expected colour is missing; delivery grasps the rim, carries, releases and re-detects, and counts the plate only if none of its colour remains.",
    cap=("plate_cap.py", 0, 43),
    cap_note="One perception call, then one delivery per colour in a fixed order, reusing the detection list each delivery returns. A colour still on the table after its delivery gets a single retry at its new location.",
  ),
  "towel": dict(
    title="Towel folding",
    instruction="Fold the towel twice, into quarters: fold it in half, then fold the result in half again along the other axis. Keep it on the table.",
    toolbox_src="toolbox.py", toolbox_total=1639, expand={"towel_frame": ("towel_toolbox_towel_frame.py", 0), "fold_edge": ("towel_toolbox_fold_edge.py", 0)},
    toolbox_note="The three primitives this CAP calls. The frame labels the towel's edges by their outward normals, so it works on a yawed or folded towel; one fold is one closed-loop call that picks its edge relative to the previous crease.",
    cap=("towel_cap.py", 0, 50),
    cap_note="Two fold calls. The second passes the first fold's carry direction as across. Each fold gets one retry, gated on the measured towel size and the step budget.",
  ),
}

SUMMARIES = {
  "find_source_tote": "Pose of the source tote, perceived from the wrist camera's depth; None if it has not been seen yet.",
  "scanned_objects": "Names of the objects whose barcodes have been read so far in this rollout.",
  "view_source_tote": "Park the hand where the wrist camera looks into the source tote.",
  "find_objects": "Every object in the source tote, segmented and measured from the wrist camera. Shape-agnostic.",
  "wait": "Hold the current command for a number of env steps.",
  "set_gripper": "Open or close the gripper on the named arm.",
  "grasp_object": "Grasp one object from find_objects(); centre, jaw azimuth and grasp height all come from its measurement.",
  "present_to_scanner": "Hold the grasped object at the scanner and search its facing until a new read latches.",
  "regrasp_rotated": "Set the held object back down in the source tote, re-perceive it, and grasp it again at a new azimuth.",
  "place_in_tote": "Carry the held object over a tote and release it inside the cavity.",
  "perceive_plates": "Park both arms, then detect every plate on the table; re-detects once if an expected colour is missing.",
  "get_step_count": "Env steps elapsed in this rollout.",
  "deliver_plate": "Grasp a plate by its rim, carry it to the tote, release, then re-detect the table to confirm delivery.",
  "towel_frame": "The towel's four edges keyed by world side (far, near, left, right), plus its centre, size and fold ratio.",
  "fold_edge": "Fold the towel in half by carrying one edge onto the opposite edge. Closed loop.",
}

# ---------- text processing ----------
def strip_comments(src: str) -> str:
  out, in_doc = [], False
  for line in src.splitlines():
    s = line.strip()
    if in_doc:
      if '"""' in s: in_doc = False
      continue
    if s.startswith('"""'):
      if s.count('"""') == 1:
        in_doc = True
        line = line.rstrip() + ' ..."""'
      out.append(line); continue
    if s.startswith("#"):
      if s.startswith("# ..."):
        out.append(line[:len(line) - len(line.lstrip())] + "...")
      continue
    out.append(re.sub(r"\s{2,}# .*$", "", line))
  res = []
  for line in out:
    if line.strip() in ("...", "") and res and res[-1].strip() == line.strip(): continue
    res.append(line)
  return "\n".join(res).strip("\n")

def load_snippet(fname, drop):
  lines = (HERE / fname).read_text().splitlines()[drop:]
  return strip_comments(textwrap.dedent("\n".join(lines)))

def tidy_arg(a: str) -> str:
  a = a.replace("'", '"')
  if ":" in a and "=" in a: a = re.sub(r"(?<! )=(?! )", " = ", a, count=1)
  return a

def signature(m) -> str:
  args = [tidy_arg(a) for a in re.split(r", (?![^\[\]]*\])", m["args"])]
  args = [a for a in args if a != "self"]
  ret = f" -> {m['ret']}" if m["ret"] else ""
  one = f"def {m['name']}({', '.join(args)}){ret}:"
  if len(one) <= WIDTH: return one
  return f"def {m['name']}(\n" + "".join(f"{IND}{IND}{a},\n" for a in args) + f"){ret}:"

def summary(doc: str, name: str = "") -> str:
  if name in SUMMARIES:
    sent = SUMMARIES[name]                      # curated one-liner, used whole
  else:
    text = " ".join(doc.split())
    m = re.match(r"(.+?\.)(\s|$)", text)
    sent = m.group(1) if m else text
  lines = textwrap.wrap(sent, WIDTH - len(IND) - 3, break_on_hyphens=False)
  if len(lines) == 1: return f'{IND}"""{lines[0]}"""'
  return f'{IND}"""{lines[0]}\n' + "\n".join(f"{IND}{l}" for l in lines[1:]) + '"""'

def stub(m) -> str:
  return f"{signature(m)}\n{summary(m.get('doc', ''), m['name'])}\n{IND}...  # {m['body_lines']} lines"

def expanded(m, fname, drop) -> str:
  body = load_snippet(fname, drop).splitlines()
  # drop the snippet's own signature and docstring line; keep the body under our stub header
  depth, i = 0, 0
  while True:                                        # end of the (possibly multi-line) def header
    depth += body[i].count("(") - body[i].count(")")
    i += 1
    if depth == 0 and body[i - 1].rstrip().endswith(":"): break
  if body[i].strip().startswith('"""'):               # past the docstring summary line
    while '"""' not in body[i].strip()[3:]: i += 1
    i += 1
  return f"{signature(m)}\n{summary(m.get('doc', ''), m['name'])}\n" + "\n".join(body[i:])

def toolbox_text(key, t) -> str:
  parts = []
  for m in API[key]:
    if m["name"] in t["expand"]: parts.append(expanded(m, *t["expand"][m["name"]]))
    else: parts.append(stub(m))
  return "\n\n".join(parts)

# ---------- markup ----------
def pane(kind, name, code, meta, note):
  return f'''
      <div class="code-pane code-pane--{kind}">
        <div class="code-pane-head">
          <span class="code-kind">{"Toolbox" if kind == "toolbox" else "CAP script"}</span>
          <span class="code-name">{escape(name)}</span>
          <span class="code-meta">{escape(meta)}</span>
        </div>
        <pre><code class="language-python">{escape(code)}</code></pre>
        <p class="code-pane-note">{escape(note)}</p>
      </div>'''

def dialog(key, t):
  tb = toolbox_text(key, t)
  cap_file, cap_drop, cap_total = t["cap"]
  cap = load_snippet(cap_file, cap_drop)
  n = len(API[key])
  return f'''<!-- CODE-PANEL:{key}:BEGIN -->
    <dialog class="code-dialog" id="code-{key}" aria-labelledby="code-{key}-title">
      <div class="code-dialog-head">
        <div>
          <p class="eyebrow">Toolbox and program</p>
          <h3 id="code-{key}-title">{escape(t["title"])}</h3>
          <p class="code-instruction">&ldquo;{escape(t["instruction"])}&rdquo;</p>
        </div>
        <button type="button" class="code-dialog-close" aria-label="Close">&times;</button>
      </div>
      <div class="code-pair">{pane("toolbox", t["toolbox_src"], tb, f"{n} primitives called · {t['toolbox_total']} lines", t["toolbox_note"])}{pane("cap", "agent_script.py", cap, f"{len(cap.splitlines())} of {cap_total} lines", t["cap_note"])}
      </div>
    </dialog>
    <!-- CODE-PANEL:{key}:END -->'''

html = INDEX.read_text()
for key, t in TASKS.items():
  pat = re.compile(rf"<!-- CODE-PANEL:{key}:BEGIN -->.*?<!-- CODE-PANEL:{key}:END -->", re.S)
  assert pat.search(html), f"no CODE-PANEL:{key} markers in index.html"
  html = pat.sub(lambda m: dialog(key, t), html)
INDEX.write_text(html)
print("wrote", INDEX, "with", len(TASKS), "dialogs")
if __name__ == "__main__":
  import sys
  if "--print" in sys.argv:
    for key, t in TASKS.items(): print(f"\n##### {key} toolbox pane\n{toolbox_text(key, t)}")
