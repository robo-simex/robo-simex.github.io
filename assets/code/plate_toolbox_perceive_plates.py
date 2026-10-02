def perceive_plates(self) -> list[dict]:
  self.park_arms()
  plates = self.find_table_plates()
  seen = {d["name"] for d in plates}
  expected = {n for n in self._expected_names if n not in seen}
  if expected:
    ...
    self.wait(6)
    again = self.find_table_plates()
    for d in again:
      if d["name"] in expected and d["name"] not in seen:
        plates.append(d)
        seen.add(d["name"])
    self._last_plates = list(plates)
  self._expected_names = set(seen)
  return plates
