// Reviewer page. The key lives only in this tab (sessionStorage) and is sent as a header.
const $ = (s) => document.querySelector(s);
const ss = { get: (k) => { try { return sessionStorage.getItem(k) || ""; } catch { return ""; } },
             set: (k, v) => { try { sessionStorage.setItem(k, v); } catch { /* private mode */ } } };
let status = "open";
$("#key").value = ss.get("rv_key");

function toast(msg) { const el = $("#toast"); el.textContent = msg; el.hidden = false; setTimeout(() => (el.hidden = true), 3000); }
const when = (iso) => iso ? new Date(iso).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" }) : "";
const inr = (n) => "₹" + Number(n || 0).toLocaleString("en-IN");

async function call(path, opts = {}) {
  const res = await fetch(path, { ...opts, headers: { "Content-Type": "application/json", "x-review-key": $("#key").value.trim() } });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(res.status === 401 ? "Wrong review key." : res.status === 404 && !body.challenge_id ? (body.error || "Reviewing is switched off on this server.") : body.error || "Something went wrong.");
  return body;
}

function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
function box(title, rows) {
  const b = el("div", "box"); b.append(el("h3", null, title));
  const dl = el("dl");
  rows.filter(([, v]) => v !== null && v !== undefined && v !== "").forEach(([k, v]) => { dl.append(el("dt", null, k), el("dd", null, String(v))); });
  b.append(dl); return b;
}

async function load() {
  const list = $("#list"); list.replaceChildren();
  if (!$("#key").value.trim()) { list.append(el("p", "empty", "Enter the review key to see the queue.")); return; }
  let data;
  try { data = await call(`/review/disputes?status=${status}`); } catch (e) { list.append(el("p", "empty", e.message)); return; }
  if (!data.disputes.length) { list.append(el("p", "empty", status === "open" ? "No open disputes." : "No closed disputes yet.")); return; }
  data.disputes.forEach((d) => list.append(card(d)));
}

function card(d) {
  const c = el("article", "card glass");
  const top = el("div", "card-top");
  top.append(el("span", "num", d.identifier_value));
  const label = { under_review: d.hours_left != null ? `Open, ${d.hours_left} h left` : "Open", upheld: "Upheld", rejected: "Rejected",
    overruled: "Overruled by new victims", lapsed: "Lapsed, not decided in time" }[d.status] || d.status;
  top.append(el("span", `state ${d.status}`, label));
  c.append(top);

  const bulk = Math.max(d.same_contact_disputes || 0, d.same_network_disputes || 0);
  if (bulk > 2) c.append(el("div", "flag", `Bulk pattern: this contact or network has disputed ${bulk} different numbers. Real owners rarely dispute more than one or two.`));
  const e = d.evidence;
  if (e.money_lost_inr > 0) c.append(el("div", "flag", `${e.reports_with_loss} reports say money was taken, ${inr(e.money_lost_inr)} in total.`));

  const cols = el("div", "cols");
  cols.append(box("What the owner says", [["Name", d.claimant_name], ["Email", d.contact_email], ["Proof", d.proof_note || "None given"],
    ["Opened", when(d.opened)], ["Closes", d.status === "under_review" ? when(d.closes) : ""], ["Decided", when(d.decided)]]));
  cols.append(box("What people reported", [["People", e.people], ["Reports", e.reports], ["Described it", e.described],
    ["Scam type", e.scam_type], ["First / last", `${when(e.first_seen)} to ${when(e.last_seen)}`], ["Areas", (e.areas || []).join(", ")],
    ["Looks like a pile-on", e.pile_on && e.pile_on.length ? "Yes" : "No"], ["Shown now as", e.verdict_now]]));
  c.append(cols);

  const acts = el("div", "acts");
  const canUphold = d.status !== "upheld", canReject = d.status === "under_review";
  if (canUphold) acts.append(button("ok", "Uphold: set these reports aside", d, "upheld"));
  if (canReject) acts.append(button("no", "Reject: keep the warning", d, "rejected"));
  if (acts.childElementCount) c.append(acts);
  return c;
}
function button(cls, text, d, decision) {
  const b = el("button", `pill ${cls}`, text); b.type = "button";
  b.addEventListener("click", async () => {
    b.disabled = true;
    try { await call(`/review/disputes/${d.challenge_id}`, { method: "POST", body: JSON.stringify({ decision }) }); toast(decision === "upheld" ? "Upheld. The number starts fresh." : "Rejected. The warning stays."); load(); }
    catch (e) { toast(e.message); b.disabled = false; }
  });
  return b;
}

$("#keyForm").addEventListener("submit", (e) => { e.preventDefault(); ss.set("rv_key", $("#key").value.trim()); load(); });
document.querySelectorAll(".tabs button").forEach((b) => b.addEventListener("click", () => {
  status = b.dataset.status;
  document.querySelectorAll(".tabs button").forEach((x) => x.setAttribute("aria-checked", String(x === b)));
  load();
}));
load();
