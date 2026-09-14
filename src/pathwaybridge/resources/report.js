"use strict";
const search = document.getElementById("search");
const modality = document.getElementById("modality");
const statusFilter = document.getElementById("status");
const rows = Array.from(document.querySelectorAll("#ledger tr"));
function update() {
  const query = search.value.toLocaleLowerCase();
  let visible = 0;
  rows.forEach(row => {
    const keep = (!modality.value || row.dataset.modality === modality.value) &&
      (!statusFilter.value || row.dataset.status === statusFilter.value) &&
      row.textContent.toLocaleLowerCase().includes(query);
    row.hidden = !keep;
    if (keep) visible++;
  });
  document.getElementById("count").textContent = `${visible} / ${rows.length} records`;
  document.getElementById("empty").hidden = visible > 0;
}
[search, modality, statusFilter].forEach(el => el.addEventListener("input", update));
document.getElementById("reset").addEventListener("click", () => {
  search.value = modality.value = statusFilter.value = "";
  update();
});
function revealTarget() {
  const id = decodeURIComponent(window.location.hash.slice(1));
  const target = document.getElementById(id);
  if (!target) return;
  if (target.tagName === "DETAILS") target.open = true;
  if (target.tagName === "TR") {
    search.value = modality.value = statusFilter.value = "";
    update();
  }
  target.scrollIntoView({block: ["MAIN", "SECTION"].includes(target.tagName) ? "start" : "center"});
}
window.addEventListener("hashchange", revealTarget);
revealTarget();
