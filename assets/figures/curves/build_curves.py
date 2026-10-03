#!/usr/bin/env python3
"""Regenerate the Stage 1 / Stage 2 curve panels shown above each family's sim rollouts.

Stage 1 (left): sub-goal success rate per optimize iteration on one autoresearch island, probe diamonds in
the tick row, alternate cycles shaded (the paper's Figure 1 / Stage 1 curve without renders and labels).
Stage 2 (right): success of the deployment rollout at each of the five adaptation trials, averaged over the
paper's seven held-out tasks x 5 seeds, SimEX against the Without Simulation baseline (the paper's Figure 5
look). Both are inline SVG so they pick up the page fonts and colours; the data lives in data/.

    python3 assets/figures/curves/build_curves.py

Writes the SIM-CURVES marker block in ../../../index.html (one <template> per family, cloned by the
sim-section script after the family heading).
"""
from html import escape
from pathlib import Path
import json, re

HERE = Path(__file__).resolve().parent
INDEX = HERE.parent.parent.parent / "index.html"
S1 = json.loads((HERE / "data/stage1_islands.json").read_text())
S2 = json.loads((HERE / "data/stage2_paper7.json").read_text())

FAMILIES = {
  "barcode": dict(name="barcode scanning", s1_source="the paper's barcode autoresearch island"),
  "plate": dict(name="plate to tote", s1_source="one island of the plate autoresearch run"),
  "towel": dict(name="towel folding", s1_source="one island of an early towel autoresearch run"),
}

# geometry (SVG user units; the two panels share one scale through the CSS grid columns 600fr / 330fr)
H = 250
W1, W2 = 600, 330
ML, MR, MT, MB = 46, 12, 30, 46   # left: "100%" ticks; top: legend row; bottom: ticks + axis label
CH = 6.9                          # approximate advance of one 11.5px monospace glyph, for legend layout


def pct(v):
  return f"{round(100 * v)}%"


def y_of(v, top=MT, bottom=H - MB):
  return bottom - v * (bottom - top)


def axes(w, xlabel):
  """y gridlines + tick labels, y axis label, x axis label."""
  top, bottom = MT, H - MB
  out = []
  for v, lab in ((0, "0"), (0.5, "50"), (1, "100%")):
    y = y_of(v)
    out.append(f'<line class="c-grid" x1="{ML}" y1="{y:.1f}" x2="{w - MR}" y2="{y:.1f}"/>')
    out.append(f'<text class="c-tick" x="{ML - 6}" y="{y:.1f}" text-anchor="end" dominant-baseline="middle">{lab}</text>')
  ym = (top + bottom) / 2
  out.append(f'<text class="c-axis" transform="translate(12 {ym:.1f}) rotate(-90)" text-anchor="middle" dominant-baseline="middle">success rate</text>')
  out.append(f'<text class="c-axis" x="{ML + (w - ML - MR) / 2:.1f}" y="{H - 8}" text-anchor="middle">{escape(xlabel)}</text>')
  return out


def legend(w, items):
  """items: list of (marker svg factory, label). Left-aligned on the plot, one row."""
  out, x = [], ML
  y = 13
  for mark, label in items:
    out.append(mark(x + 7, y))
    out.append(f'<text class="c-legend" x="{x + 18}" y="{y}" dominant-baseline="middle">{escape(label)}</text>')
    x += 18 + len(label) * CH + 22
  return out


def square(cls, x, y, s=7.5):
  return f'<rect class="{cls}" x="{x - s / 2:.1f}" y="{y - s / 2:.1f}" width="{s}" height="{s}"/>'


def diamond(cls, x, y, s=9):
  return f'<path class="{cls}" d="M{x:.1f} {y - s / 2:.1f} L{x + s / 2:.1f} {y:.1f} L{x:.1f} {y + s / 2:.1f} L{x - s / 2:.1f} {y:.1f} Z"/>'


def circle(cls, x, y, r=4):
  return f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>'


def stage1_svg(fam):
  d = S1[fam]
  cyc = d["cycles"]
  # slots: each cycle = probe slot + one slot per optimize iteration (as in the paper)
  n_slots = sum(1 + len(c["optimize_iters"]) for c in cyc)
  pw = (W1 - ML - MR) / n_slots
  xs = lambda k: ML + (k + 0.5) * pw
  top, bottom = MT, H - MB
  out = [f'<svg class="curve curve--s1" viewBox="0 0 {W1} {H}" role="img" '
         f'aria-label="Stage 1: sub-goal success rate over the optimize iterations of {escape(FAMILIES[fam]["s1_source"])}">']
  # alternate cycle bands
  slot = 0
  for k, c in enumerate(cyc):
    n = 1 + len(c["optimize_iters"])
    if k % 2 == 1:
      out.append(f'<rect class="c-band" x="{ML + slot * pw:.1f}" y="{top}" width="{n * pw:.1f}" height="{bottom - top}"/>')
    slot += n
  out += axes(W1, "optimize iteration")
  # curve per cycle, probe diamonds in the tick row, tick labels
  slot, opt_no, marks, ticks = 0, 0, [], []
  step = 1 if pw >= 20 else 2
  for k, c in enumerate(cyc):
    px = xs(slot)
    pr = "" if c["probe_success"] is None else f": {pct(c['probe_success'])} on fresh tasks"
    lab = (c.get("label") or "").strip()
    marks.append(f'{diamond("c-probe", px, bottom + 11)[:-2]}><title>probe {k + 1}{pr}' +
                 (f' · new sub-goal: {escape(lab)}' if lab else "") + '</title></path>')
    slot += 1
    pts = []
    for it, v in zip(c["optimize_iters"], c["subgoal_success"]):
      opt_no += 1
      x = xs(slot)
      if opt_no % step == 0 or step == 1:
        ticks.append(f'<text class="c-tick" x="{x:.1f}" y="{bottom + 11}" text-anchor="middle" dominant-baseline="middle">{opt_no}</text>')
      if v is not None:
        y = y_of(v)
        pts.append((x, y))
        marks.append(f'{square("c-mark-s1", x, y)[:-2]}><title>cycle {k + 1} · optimize iteration {opt_no} · {pct(v)} on the sub-goal tasks</title></rect>')
      slot += 1
    if len(pts) > 1:
      out.append('<polyline class="c-line-s1" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '"/>')
  out += ticks + marks
  out += legend(W1, [(lambda x, y: diamond("c-probe", x, y), "probe (new sub-goal)"),
                     (lambda x, y: square("c-mark-s1", x, y), "success rate on the sub-goal tasks")])
  out.append("</svg>")
  return "\n".join(out)


# Trial 1 is the deployment rollout of the same starting toolbox for both methods, so the baseline is drawn from
# SimEX's trial-1 value for these families (the raw per-method numbers stay in data/stage2_paper7.json).
SHARED_START = {"plate"}


def stage2_svg(fam):
  d = json.loads(json.dumps(S2[fam]))
  if fam in SHARED_START:
    d["nosim"]["rate"][0] = d["simex"]["rate"][0]
  n = d["simex"]["n"][0]
  K = 5
  pw = (W2 - ML - MR) / K
  xs = lambda k: ML + (k + 0.5) * pw
  bottom = H - MB
  out = [f'<svg class="curve curve--s2" viewBox="0 0 {W2} {H}" role="img" '
         f'aria-label="Stage 2: success of the deployment rollout at each of five adaptation trials, SimEX against Without Simulation, {n} runs">']
  out += axes(W2, "adaptation trial")
  for k in range(K):
    out.append(f'<text class="c-tick" x="{xs(k):.1f}" y="{bottom + 11}" text-anchor="middle" dominant-baseline="middle">{k + 1}</text>')
  series = [("nosim", "Without Simulation", "c-line-nosim", lambda x, y: circle("c-mark-nosim", x, y)),
            ("simex", "SimEX", "c-line-simex", lambda x, y: square("c-mark-simex", x, y))]
  marks = []
  for key, label, lcls, mark in series:            # baseline first so SimEX draws on top
    pts = [(xs(k), y_of(r / 100)) for k, r in enumerate(d[key]["rate"])]
    out.append(f'<polyline class="{lcls}" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '"/>')
    for k, ((x, y), r, nn) in enumerate(zip(pts, d[key]["rate"], d[key]["n"])):
      marks.append(f'{mark(x, y)[:-2]}><title>{label} · trial {k + 1} · {r}% of {nn} runs succeed</title></{"circle" if key == "nosim" else "rect"}>')
  out += marks
  out += legend(W2, [(series[1][3], "SimEX"), (series[0][3], "Without Simulation")])
  out.append("</svg>")
  return "\n".join(out)


def template(fam):
  return f'''<template id="sim-curves-{fam}">
<figure class="curve-pair">
  <div class="curve-panel curve-panel--s1">
    <p class="curve-title"><span class="curve-stage">Stage 1</span>Open-ended autoresearch in simulation</p>
{stage1_svg(fam)}
  </div>
  <div class="curve-panel curve-panel--s2">
    <p class="curve-title"><span class="curve-stage">Stage 2</span>Adaptation to the stand-in robot</p>
{stage2_svg(fam)}
  </div>
</figure>
</template>'''


def main():
  html = INDEX.read_text()
  block = "<!-- SIM-CURVES:BEGIN -->\n" + "\n".join(template(f) for f in FAMILIES) + "\n<!-- SIM-CURVES:END -->"
  pat = re.compile(r"<!-- SIM-CURVES:BEGIN -->.*?<!-- SIM-CURVES:END -->", re.S)
  assert pat.search(html), "no SIM-CURVES markers in index.html"
  html = pat.sub(lambda m: block, html)
  INDEX.write_text(html)
  print("wrote", INDEX, "with", len(FAMILIES), "curve pairs")


if __name__ == "__main__":
  main()
