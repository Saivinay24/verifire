// Scam Map mobile web app. Plain ES module, no build step.
// Privacy: the app never sends GPS. "Near me" picks the nearest supported area on this device
// and sends only its pincode. The reporter id is a random anonymous token kept on this device.

const $ = (sel) => document.querySelector(sel);

// ---------------- Words (English / Hindi) ----------------
const T = {
  en: {
    brand: "Scam Map",
    hello: "Check before you trust.",
    hello_sub: "Paste a number, UPI ID or link. See if people near you reported it.",
    report_cta: "Report a scam", near_cta: "Near me",
    check_label: "Number, UPI ID or link", check_placeholder: "Paste a number, UPI ID or link",
    fineprint: "Anonymous. We save only the area, never who you are.",
    call1930: "Lost money? Call 1930", report_this: "Report this",
    dispute_link: "Is this your business? Ask for a review",
    step1: "How did they reach you?", step2: "What did they try?", step3: "Who was it?",
    step3_sub: "Their number, UPI ID or link. Not yours.",
    value_label: "Their number, UPI ID or link", value_placeholder: "Their number, UPI ID or link",
    when: "When?", where: "Your area", choose_area: "Choose area", use_location: "Near me",
    add_note: "Add what happened (optional)", note_placeholder: "In your own words. Don't write your name or number.",
    lost_money: "Money lost (optional)", send: "Send report",
    done_title: "Report sent", done_sub: "Thank you. It helps the next person spot this scam.",
    file_complaint: "File a complaint on cybercrime.gov.in", done: "Done", not_sure: "Not sure, skip",
    map_title: "Scams reported nearby", map_sub: "Last 7 days, grouped by area. Never anyone's exact location.",
    dispute_title: "Ask for a review",
    dispute_sub: "We mark the number as under review. It is never shown as a scam while we check.",
    d_name: "Business name", d_email: "Email for our reply", d_proof: "Proof, e.g. GST or shop licence number",
    d_send: "Send for review", d_done: "Sent. This number is now under review.",
    expired_title: "Licence expired. Contact your provider.",
    expired_sub: "Your data is safe. The app works again as soon as a new licence is added.", retry: "Try again",
    when_now: "Just now", when_today: "Today", when_yday: "Yesterday", when_week: "This week",
    kinds: { phone: "Phone", upi: "UPI ID", url: "Link", sender_id: "SMS sender" },
    v_KNOWN_SCAM: "Reported as a scam", v_SUSPICIOUS: "Be careful", v_NO_REPORTS: "No reports yet",
    v_VERIFIED_BUSINESS: "Verified",
    reported_by: (n) => `Reported by ${n} ${n === 1 ? "person" : "people"} near you`,
    no_reports_sub: "Nobody near you has reported this yet. Still never share an OTP or pay to receive money.",
    verified_sub: (o) => `Official number of ${o}.`,
    verified_advice: "Any caller can fake this number on your screen. If someone asks for money or an OTP, hang up and call back yourself.",
    under_review: "Under review: the owner asked us to check these reports.",
    f_reports: "Reports", f_people: "People", f_last: "Last reported", f_type: "Scam type", f_shown: "Shown as",
    invalid: "That doesn't look like a real number, UPI ID or link.",
    need_area: "Choose your area first.", need_value: "Add their number, UPI ID or link.",
    paste_hint: "Long-press the box and choose Paste.", offline: "No connection. Try again in a moment.",
    slow: "You've sent many reports. Try again later.",
    locating: "Finding your area...", loc_fail: "Couldn't get your location. Choose your area instead.",
    no_clusters: "No scams reported near here in the last 7 days.",
    spike: (a, n) => `Scam reports near ${a} jumped today: ${n} in 24 hours.`,
    newtype: (a, t) => `New scam near ${a}: ${t}.`,
    reports_n: (n) => `${n} ${n === 1 ? "report" : "reports"}`,
    ago_min: (n) => `${n} min ago`, ago_h: (n) => `${n} h ago`, ago_d: (n) => `${n} d ago`,
  },
  hi: {
    brand: "स्कैम मैप",
    hello: "भरोसा करने से पहले जांचें।",
    hello_sub: "नंबर, UPI ID या लिंक डालें। देखें कि आपके पास किसी ने इसकी रिपोर्ट की है या नहीं।",
    report_cta: "स्कैम की रिपोर्ट करें", near_cta: "मेरे पास",
    check_label: "नंबर, UPI ID या लिंक", check_placeholder: "नंबर, UPI ID या लिंक डालें",
    fineprint: "गुमनाम। हम सिर्फ इलाका रखते हैं, आपकी पहचान कभी नहीं।",
    call1930: "पैसे गए? 1930 पर कॉल करें", report_this: "इसकी रिपोर्ट करें",
    dispute_link: "क्या यह आपका बिज़नेस नंबर है? जांच के लिए कहें",
    step1: "उन्होंने आपसे कैसे संपर्क किया?", step2: "उन्होंने क्या करने की कोशिश की?", step3: "वह कौन था?",
    step3_sub: "उनका नंबर, UPI ID या लिंक। आपका नहीं।",
    value_label: "उनका नंबर, UPI ID या लिंक", value_placeholder: "उनका नंबर, UPI ID या लिंक",
    when: "कब?", where: "आपका इलाका", choose_area: "इलाका चुनें", use_location: "मेरे पास",
    add_note: "क्या हुआ, लिखें (ज़रूरी नहीं)", note_placeholder: "अपने शब्दों में। अपना नाम या नंबर न लिखें।",
    lost_money: "कितने पैसे गए (ज़रूरी नहीं)", send: "रिपोर्ट भेजें",
    done_title: "रिपोर्ट भेज दी गई", done_sub: "धन्यवाद। इससे अगले व्यक्ति को यह स्कैम पहचानने में मदद मिलेगी।",
    file_complaint: "cybercrime.gov.in पर शिकायत दर्ज करें", done: "ठीक है", not_sure: "पता नहीं, आगे बढ़ें",
    map_title: "आसपास रिपोर्ट किए गए स्कैम", map_sub: "पिछले 7 दिन, इलाके के हिसाब से। किसी की सटीक जगह कभी नहीं।",
    dispute_title: "जांच के लिए कहें",
    dispute_sub: "हम नंबर को जांच में रखेंगे। जांच के दौरान इसे स्कैम नहीं दिखाया जाएगा।",
    d_name: "बिज़नेस का नाम", d_email: "जवाब के लिए ईमेल", d_proof: "सबूत, जैसे GST या दुकान लाइसेंस नंबर",
    d_send: "जांच के लिए भेजें", d_done: "भेज दिया। यह नंबर अब जांच में है।",
    expired_title: "लाइसेंस समाप्त हो गया। अपने प्रदाता से संपर्क करें।",
    expired_sub: "आपका डेटा सुरक्षित है। नया लाइसेंस जुड़ते ही ऐप फिर से चलेगा।", retry: "फिर कोशिश करें",
    when_now: "अभी", when_today: "आज", when_yday: "कल", when_week: "इस हफ्ते",
    kinds: { phone: "फ़ोन", upi: "UPI ID", url: "लिंक", sender_id: "SMS भेजने वाला" },
    v_KNOWN_SCAM: "स्कैम के रूप में रिपोर्ट किया गया", v_SUSPICIOUS: "सावधान रहें", v_NO_REPORTS: "अभी कोई रिपोर्ट नहीं",
    v_VERIFIED_BUSINESS: "सत्यापित",
    reported_by: (n) => `आपके पास ${n} लोगों ने रिपोर्ट किया`,
    no_reports_sub: "अभी तक आपके पास किसी ने इसकी रिपोर्ट नहीं की। फिर भी OTP कभी न बताएं, पैसे पाने के लिए भुगतान न करें।",
    verified_sub: (o) => `${o} का आधिकारिक नंबर।`,
    verified_advice: "कोई भी कॉलर आपकी स्क्रीन पर यही नंबर दिखा सकता है। अगर कोई पैसे या OTP मांगे, फोन काटें और खुद वापस कॉल करें।",
    under_review: "जांच जारी: मालिक ने इन रिपोर्टों की जांच के लिए कहा है।",
    f_reports: "रिपोर्ट", f_people: "लोग", f_last: "आखिरी रिपोर्ट", f_type: "स्कैम का प्रकार", f_shown: "ऐसे दिखाया गया",
    invalid: "यह सही नंबर, UPI ID या लिंक नहीं लगता।",
    need_area: "पहले अपना इलाका चुनें।", need_value: "उनका नंबर, UPI ID या लिंक डालें।",
    paste_hint: "बॉक्स को दबाकर रखें और पेस्ट चुनें।", offline: "कनेक्शन नहीं है। थोड़ी देर में फिर कोशिश करें।",
    slow: "आपने बहुत सारी रिपोर्ट भेजी हैं। बाद में कोशिश करें।",
    locating: "आपका इलाका ढूंढ रहे हैं...", loc_fail: "आपकी जगह नहीं मिली। इलाका खुद चुनें।",
    no_clusters: "पिछले 7 दिनों में यहां आसपास कोई स्कैम रिपोर्ट नहीं हुआ।",
    spike: (a, n) => `${a} के पास आज स्कैम रिपोर्ट अचानक बढ़ीं: 24 घंटे में ${n}।`,
    newtype: (a, t) => `${a} के पास नया स्कैम: ${t}।`,
    reports_n: (n) => `${n} रिपोर्ट`,
    ago_min: (n) => `${n} मिनट पहले`, ago_h: (n) => `${n} घंटे पहले`, ago_d: (n) => `${n} दिन पहले`,
  },
};

const CHANNELS = [
  { id: "Phone call", icon: "i-phone", en: "Phone call", hi: "फ़ोन कॉल" },
  { id: "SMS or WhatsApp", icon: "i-chat", en: "SMS or WhatsApp", hi: "SMS या WhatsApp" },
  { id: "QR code", icon: "i-qr", en: "QR code", hi: "QR कोड" },
  { id: "Fake website", icon: "i-globe", en: "Fake website", hi: "नकली वेबसाइट" },
  { id: "UPI request", icon: "i-rupee", en: "UPI request", hi: "UPI रिक्वेस्ट" },
  { id: "Something else", icon: "i-dots", en: "Something else", hi: "कुछ और" },
];

const TYPES = [
  { id: "digital-arrest", icon: "i-police", en: "Fake police or arrest", hi: "नकली पुलिस या गिरफ्तारी",
    advice: { en: "Police never arrest anyone on a video call or ask for money to close a case. Hang up.",
              hi: "पुलिस कभी वीडियो कॉल पर गिरफ्तार नहीं करती, न केस बंद करने के पैसे मांगती है। फोन काटें।" } },
  { id: "fake-kyc-link", icon: "i-idcard", en: "KYC update link", hi: "KYC अपडेट लिंक",
    advice: { en: "Banks never send KYC links by SMS. Update KYC only in your bank's own app or branch.",
              hi: "बैंक SMS से KYC लिंक नहीं भेजते। KYC सिर्फ बैंक के ऐप या शाखा में करें।" } },
  { id: "upi-refund-qr", icon: "i-qr", en: "Scan QR for refund", hi: "रिफंड के लिए QR स्कैन",
    advice: { en: "Scanning a QR code or entering your UPI PIN only ever sends money. You never need it to receive.",
              hi: "QR स्कैन करने या UPI PIN डालने से पैसे सिर्फ जाते हैं। पैसे पाने के लिए इसकी ज़रूरत नहीं होती।" } },
  { id: "investment-group", icon: "i-trend", en: "Investment group", hi: "निवेश ग्रुप",
    advice: { en: "Guaranteed high returns in a WhatsApp group are a trap. Profits shown there are fake.",
              hi: "WhatsApp ग्रुप में पक्के बड़े मुनाफे का वादा जाल है। वहां दिखाया मुनाफा नकली है।" } },
  { id: "courier-customs", icon: "i-parcel", en: "Parcel or customs fine", hi: "पार्सल या कस्टम जुर्माना",
    advice: { en: "Customs doesn't call you to pay fines over UPI. Check with the courier company directly.",
              hi: "कस्टम UPI से जुर्माना भरने के लिए कॉल नहीं करता। सीधे कूरियर कंपनी से पूछें।" } },
  { id: "job-offer", icon: "i-briefcase", en: "Task job with deposit", hi: "जमा राशि वाली नौकरी",
    advice: { en: "A real job never asks you to pay a deposit to start working.",
              hi: "असली नौकरी में काम शुरू करने के लिए पैसे जमा नहीं करने पड़ते।" } },
  { id: "lottery-prize", icon: "i-gift", en: "Lottery or prize", hi: "लॉटरी या इनाम",
    advice: { en: "If you have to pay a fee to get a prize, there is no prize.",
              hi: "अगर इनाम पाने के लिए फीस देनी पड़े, तो कोई इनाम नहीं है।" } },
  { id: "loan-app-harassment", icon: "i-loan", en: "Loan app threats", hi: "लोन ऐप की धमकी",
    advice: { en: "Don't pay under threat. Report the app and keep screenshots of the messages.",
              hi: "धमकी में आकर पैसे न दें। ऐप की रिपोर्ट करें और मैसेज के स्क्रीनशॉट रखें।" } },
  { id: "electricity-disconnection", icon: "i-bolt", en: "Power cut tonight", hi: "आज रात बिजली कटेगी",
    advice: { en: "Power companies don't text personal numbers to call. Pay bills only in the official app.",
              hi: "बिजली कंपनी निजी नंबर पर कॉल करने को नहीं कहती। बिल सिर्फ आधिकारिक ऐप में भरें।" } },
  { id: "fake-customer-care", icon: "i-headset", en: "Fake customer care", hi: "नकली कस्टमर केयर",
    advice: { en: "Search results can show fake helplines. Use the number on the company's own website or app.",
              hi: "सर्च में नकली हेल्पलाइन दिख सकती है। कंपनी की वेबसाइट या ऐप वाला नंबर ही इस्तेमाल करें।" } },
  { id: "otp-call", icon: "i-otp", en: "Asked for OTP", hi: "OTP मांगा",
    advice: { en: "Never share an OTP or card PIN with anyone, even if they say they are from your bank.",
              hi: "OTP या कार्ड PIN किसी को न बताएं, चाहे वह खुद को बैंक का बताए।" } },
  { id: "sextortion", icon: "i-camera-off", en: "Video call blackmail", hi: "वीडियो कॉल ब्लैकमेल",
    advice: { en: "Don't pay. Block them, keep evidence and report at cybercrime.gov.in. You are not at fault.",
              hi: "पैसे न दें। ब्लॉक करें, सबूत रखें और cybercrime.gov.in पर रिपोर्ट करें। आपकी गलती नहीं है।" } },
  { id: "other", icon: "i-dots", en: "Something else", hi: "कुछ और",
    advice: { en: "When in doubt, don't pay and don't share codes. Call 1930 if money was taken.",
              hi: "शक हो तो पैसे न दें, कोड न बताएं। पैसे गए हों तो 1930 पर कॉल करें।" } },
];

const WHEN = [
  { key: "when_now", minutes: 0 }, { key: "when_today", minutes: 180 },
  { key: "when_yday", minutes: 1440 }, { key: "when_week", minutes: 4320 },
];

// ---------------- Small helpers ----------------
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode: fine */ } },
};
let lang = store.get("sc_lang") === "hi" ? "hi" : "en";
const t = (k, ...a) => { const v = T[lang][k] ?? T.en[k]; return typeof v === "function" ? v(...a) : v; };
const rand = (n) => Array.from(crypto.getRandomValues(new Uint8Array(n)), (b) => b.toString(16).padStart(2, "0")).join("");
const memoryId = "r_" + rand(8);
const reporterId = () => {
  let id = store.get("sc_rid");
  if (!id) { id = memoryId; store.set("sc_rid", id); }
  return id;
};

function isoLocal(d) {
  const off = -d.getTimezoneOffset();
  const sign = off >= 0 ? "+" : "-";
  const pad = (n) => String(Math.floor(Math.abs(n))).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:` +
    `${pad(d.getSeconds())}${sign}${pad(off / 60)}:${pad(off % 60)}`;
}

function detectKind(raw) {
  const v = raw.trim();
  if (!v) return null;
  if (/^upi:\/\//i.test(v) || /^[^\s@/]+@[a-z][a-z0-9.]*$/i.test(v)) return "upi";
  if (/^https?:\/\//i.test(v) || /^(www\.)?[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}(\/\S*)?$/i.test(v)) return "url";
  if (/^\+?[\d\s\-().]{3,18}$/.test(v)) return "phone";
  if (/^([a-z]{2}-)?[a-z]{6}(-[pstg])?$/i.test(v)) return "sender_id";
  return null;
}

let toastTimer;
function toast(msg) {
  const el = $("#toast");
  el.textContent = msg; el.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => (el.hidden = true), 3200);
}

function speak(text) {
  // Spoken labels help people who can't read the tiles. Only on taps, only in Hindi mode.
  if (lang !== "hi" || !("speechSynthesis" in window)) return;
  try { speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(text); u.lang = "hi-IN"; speechSynthesis.speak(u); } catch { /* ignore */ }
}

class LicenceExpired extends Error {}

async function api(path, opts = {}) {
  let res;
  try {
    res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  } catch {
    throw new Error(t("offline"));
  }
  const body = await res.json().catch(() => ({}));
  if (res.status === 403 && body.error === "LICENSE_EXPIRED") { showExpired(); throw new LicenceExpired(); }
  if (res.status === 429) throw new Error(t("slow"));
  if (!res.ok) { const e = new Error(body.error || "error"); e.status = res.status; throw e; }
  return body;
}

// ---------------- Language ----------------
function applyLang() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-t]").forEach((el) => { el.textContent = t(el.dataset.t); });
  document.querySelectorAll("[data-tp]").forEach((el) => { el.placeholder = t(el.dataset.tp); });
  document.title = t("brand");
  renderTiles(); renderWhen(); renderArea(); updateKind($("#checkInput"), $("#kindChip")); updateKind($("#reportValue"), $("#reportKind"));
  refreshAlerts();
}
$("#lang").addEventListener("click", () => { lang = lang === "en" ? "hi" : "en"; store.set("sc_lang", lang); applyLang(); });

// ---------------- Areas ----------------
let AREAS = [];
const areaByPin = (pin) => AREAS.find((a) => a.pincode === pin);
let area = store.get("sc_area");

async function loadAreas() {
  try { AREAS = (await api("/areas")).areas; } catch { AREAS = []; }
  renderArea(); refreshAlerts();
}
function setArea(pin) {
  area = pin; store.set("sc_area", pin);
  renderArea(); refreshAlerts();
}
function renderArea() {
  const a = areaByPin(area);
  $("#areaLabel").textContent = a ? a.locality : t("choose_area");
  $("#areaBtn").dataset.set = a ? "true" : "false";
  $("#mapAreaLabel").textContent = a ? `${a.locality}, ${a.city}` : t("choose_area");
}
function openAreaPicker() {
  const list = $("#areaList"); list.replaceChildren();
  const byCity = {};
  AREAS.forEach((a) => (byCity[a.city] ||= []).push(a));
  Object.entries(byCity).forEach(([city, items]) => {
    const h = document.createElement("h3"); h.textContent = city; list.append(h);
    items.forEach((a) => {
      const b = document.createElement("button"); b.type = "button";
      b.innerHTML = `<b></b><span></span>`;
      b.querySelector("b").textContent = a.locality; b.querySelector("span").textContent = a.pincode;
      b.addEventListener("click", () => { setArea(a.pincode); closeSheet("#areaSheet"); if (!$("#mapView").hidden) loadMap(); });
      list.append(b);
    });
  });
  openSheet("#areaSheet");
}
function locate() {
  if (!navigator.geolocation) { toast(t("loc_fail")); return; }
  toast(t("locating"));
  navigator.geolocation.getCurrentPosition((pos) => {
    // Nearest supported area, worked out here on the phone. Coordinates never leave the device.
    const { latitude: la, longitude: lo } = pos.coords;
    let best = null, bestD = Infinity;
    AREAS.forEach((a) => { const d = (a.lat - la) ** 2 + ((a.lng - lo) * Math.cos(la * Math.PI / 180)) ** 2; if (d < bestD) { bestD = d; best = a; } });
    if (best) { setArea(best.pincode); toast(`${best.locality}, ${best.city}`); }
  }, () => toast(t("loc_fail")), { enableHighAccuracy: false, timeout: 8000, maximumAge: 600000 });
}
$("#areaBtn").addEventListener("click", openAreaPicker);
$("#locateBtn").addEventListener("click", locate);
$("#mapArea").addEventListener("click", openAreaPicker);

// ---------------- Sheets ----------------
function openSheet(sel) { $("#scrim").hidden = false; $(sel).hidden = false; $(sel).querySelector("button, input, a")?.focus({ preventScroll: true }); }
function closeSheet(sel) { $(sel).hidden = true; if (!document.querySelector(".sheet:not([hidden])")) $("#scrim").hidden = true; }
$("#scrim").addEventListener("click", () => document.querySelectorAll(".sheet").forEach((s) => closeSheet("#" + s.id)));
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  const open = document.querySelector(".sheet:not([hidden])");
  if (open) closeSheet("#" + open.id); else if (!$("#reportFlow").hidden) closeFlow(); else if (!$("#mapView").hidden) closeMap();
});

// ---------------- Check ----------------
function updateKind(input, chip) {
  const k = detectKind(input.value);
  chip.hidden = !k; if (k) chip.textContent = T[lang].kinds[k];
  if (input === $("#checkInput")) $("#checkBtn").disabled = !k;
  return k;
}
$("#checkInput").addEventListener("input", () => updateKind($("#checkInput"), $("#kindChip")));

async function pasteInto(input, chip) {
  try {
    const text = await navigator.clipboard.readText();
    if (text) { input.value = text.trim().slice(0, 300); updateKind(input, chip); input.dispatchEvent(new Event("input")); }
  } catch { input.focus(); toast(t("paste_hint")); }
}
$("#pasteBtn").addEventListener("click", () => pasteInto($("#checkInput"), $("#kindChip")));

let lastChecked = null;
$("#checkForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const value = $("#checkInput").value.trim();
  const kind = detectKind(value);
  if (!kind) { toast(t("invalid")); return; }
  $("#checkBtn").disabled = true;
  try {
    const r = await api(`/lookup?type=${encodeURIComponent(kind)}&value=${encodeURIComponent(value)}`);
    lastChecked = { kind, value };
    showResult(r);
  } catch (err) {
    if (!(err instanceof LicenceExpired)) toast(err.status === 400 ? t("invalid") : err.message);
  } finally { $("#checkBtn").disabled = false; }
});

function ago(iso) {
  if (!iso) return "";
  const m = Math.max(1, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  return m < 60 ? t("ago_min", m) : m < 2880 ? t("ago_h", Math.round(m / 60)) : t("ago_d", Math.round(m / 1440));
}
const typeInfo = (id) => TYPES.find((x) => x.id === id) || TYPES[TYPES.length - 1];

function showResult(r) {
  const v = r.verdict;
  const card = $("#verdictCard"); card.dataset.v = v;
  const icon = { KNOWN_SCAM: "#i-shield-x", SUSPICIOUS: "#i-alert", NO_REPORTS: "#i-search", VERIFIED_BUSINESS: "#i-shield-check" }[v];
  $("#verdictIconUse").setAttribute("href", icon);
  $("#verdictTitle").textContent = v === "VERIFIED_BUSINESS" && r.verified_owner ? `${t("v_VERIFIED_BUSINESS")}` : t("v_" + v);

  let sub = "";
  if (v === "VERIFIED_BUSINESS") sub = t("verified_sub", r.verified_owner || "");
  else if (v === "NO_REPORTS") sub = t("no_reports_sub");
  else sub = t("reported_by", r.distinct_reporters);
  if (r.challenged) sub += " " + t("under_review");
  $("#verdictSummary").textContent = sub;

  const facts = $("#facts"); facts.replaceChildren();
  const add = (label, value, wide) => {
    if (value === null || value === undefined || value === "") return;
    const d = document.createElement("div"); if (wide) d.className = "wide";
    const dt = document.createElement("dt"); dt.textContent = label;
    const dd = document.createElement("dd"); dd.textContent = value;
    d.append(dt, dd); facts.append(d);
  };
  add(t("f_shown"), r.display_value, true);
  if (r.report_count > 0) {
    add(t("f_reports"), r.report_count);
    add(t("f_people"), r.distinct_reporters);
    add(t("f_last"), ago(r.last_seen));
    add(t("f_type"), typeInfo(r.scam_type)[lang]);
  }
  $("#advice").textContent = v === "VERIFIED_BUSINESS" ? t("verified_advice")
    : r.report_count > 0 ? typeInfo(r.scam_type).advice[lang] : "";
  $("#disputeLink").hidden = v === "VERIFIED_BUSINESS" || r.report_count === 0 || r.challenged;
  $("#reportThis").hidden = v === "VERIFIED_BUSINESS";
  openSheet("#resultSheet");
}
$("#reportThis").addEventListener("click", () => { closeSheet("#resultSheet"); openFlow(lastChecked?.value || ""); });

// ---------------- Report flow ----------------
const draft = { channel: null, type: null, when: 0 };
let step = 1;

function renderTiles() {
  const build = (host, items, key) => {
    host.replaceChildren();
    items.forEach((it) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "tile"; b.setAttribute("aria-pressed", String(draft[key] === it.id));
      b.innerHTML = `<span class="tile-icon"><svg aria-hidden="true"><use href="#${it.icon}"/></svg></span><span></span>`;
      b.lastChild.textContent = it[lang];
      b.addEventListener("click", () => {
        draft[key] = it.id; speak(it.hi);
        host.querySelectorAll(".tile").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
        setTimeout(() => go(step + 1), 140); // one tap is enough: move on
      });
      host.append(b);
    });
  };
  build($("#channelTiles"), CHANNELS, "channel");
  build($("#typeTiles"), TYPES.filter((x) => x.id !== "other"), "type");
}
function renderWhen() {
  const seg = $("#whenSeg"); seg.replaceChildren();
  WHEN.forEach((w, i) => {
    const b = document.createElement("button"); b.type = "button"; b.setAttribute("role", "radio");
    b.setAttribute("aria-checked", String(draft.when === i)); b.textContent = t(w.key);
    b.addEventListener("click", () => { draft.when = i; renderWhen(); });
    seg.append(b);
  });
}
function go(n) {
  step = n;
  document.querySelectorAll("#reportFlow .step").forEach((s) => s.classList.toggle("active", Number(s.dataset.step) === n));
  document.querySelectorAll("#reportFlow .steps i").forEach((d, i) => d.classList.toggle("on", i < Math.min(n, 3)));
  $(".steps").hidden = n === 4; $("#flowBack").style.visibility = n === 1 || n === 4 ? "hidden" : "visible";
  const titles = { 1: ["step1", ""], 2: ["step2", ""], 3: ["step3", "step3_sub"], 4: ["", ""] };
  $("#stepTitle").textContent = titles[n][0] ? t(titles[n][0]) : "";
  $("#stepSub").textContent = titles[n][1] ? t(titles[n][1]) : "";
  $("#stepTitle").hidden = n === 4; $("#stepSub").hidden = n === 4 || !titles[n][1];
  if (n === 3 && !$("#reportValue").value) $("#reportValue").focus({ preventScroll: true });
}
function openFlow(prefill) {
  Object.assign(draft, { channel: null, type: null, when: 0 });
  $("#reportForm").reset(); $("#valueError").hidden = true;
  $("#reportValue").value = prefill; updateKind($("#reportValue"), $("#reportKind"));
  renderTiles(); renderWhen(); renderArea();
  $("#reportFlow").hidden = false; go(1);
}
function closeFlow() { $("#reportFlow").hidden = true; }
$("#openReport").addEventListener("click", () => openFlow(detectKind($("#checkInput").value) ? $("#checkInput").value.trim() : ""));
$("#flowClose").addEventListener("click", closeFlow);
$("#skipType").addEventListener("click", () => { draft.type = "other"; go(3); });
$("#flowBack").addEventListener("click", () => go(Math.max(1, step - 1)));
$("#doneBtn").addEventListener("click", closeFlow);
$("#reportValue").addEventListener("input", () => { $("#valueError").hidden = true; updateKind($("#reportValue"), $("#reportKind")); });
$("#reportPaste").addEventListener("click", () => pasteInto($("#reportValue"), $("#reportKind")));

$("#reportForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const value = $("#reportValue").value.trim();
  const kind = detectKind(value);
  const err = (msg) => { $("#valueError").textContent = msg; $("#valueError").hidden = false; };
  if (!value) return err(t("need_value"));
  if (!kind) return err(t("invalid"));
  if (!areaByPin(area)) { toast(t("need_area")); openAreaPicker(); return; }
  const a = areaByPin(area);
  const now = new Date();
  const occurred = new Date(now.getTime() - WHEN[draft.when].minutes * 60000);
  const amount = parseInt(($("#lostAmount").value || "").replace(/\D/g, ""), 10);
  const payload = {
    report_id: "app_" + rand(10), occurred_at: isoLocal(occurred), reported_at: isoLocal(now),
    reporter_id: reporterId(), channel: draft.channel || "Something else", scam_type: draft.type || "other",
    identifier_type: kind, identifier_value: value, pincode: a.pincode, locality: a.locality, city: a.city,
    note: $("#reportNote").value.trim(), has_screenshot: false, amount_lost_inr: Number.isFinite(amount) ? amount : 0,
  };
  $("#sendReport").disabled = true;
  try {
    await api("/reports", { method: "POST", body: JSON.stringify(payload) });
    go(4); refreshAlerts();
  } catch (ex) {
    if (!(ex instanceof LicenceExpired)) ex.status === 400 ? err(t("invalid")) : toast(ex.message);
  } finally { $("#sendReport").disabled = false; }
});

// ---------------- Dispute ----------------
$("#disputeLink").addEventListener("click", () => { closeSheet("#resultSheet"); openSheet("#disputeSheet"); });
$("#disputeForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!lastChecked) return;
  try {
    await api("/challenges", { method: "POST", body: JSON.stringify({
      identifier_type: lastChecked.kind, identifier_value: lastChecked.value,
      claimant_name: $("#dName").value.trim(), contact_email: $("#dEmail").value.trim(), proof_note: $("#dProof").value.trim(),
    }) });
    closeSheet("#disputeSheet"); $("#disputeForm").reset(); toast(t("d_done"));
  } catch (ex) { if (!(ex instanceof LicenceExpired)) toast(ex.message); }
});

// ---------------- Alerts and map ----------------
async function refreshAlerts() {
  const a = areaByPin(area);
  const banner = $("#alertBanner");
  if (!a) { banner.hidden = true; return []; }
  try {
    const { alerts } = await api(`/alerts?pincode=${a.pincode}`);
    if (!alerts.length) { banner.hidden = true; return alerts; }
    $("#alertText").textContent = alertText(alerts[0], a);
    banner.hidden = false;
    return alerts;
  } catch { banner.hidden = true; return []; }
}
function alertText(al, a) {
  return al.type === "SPIKE" ? t("spike", a.locality, al.count) : t("newtype", a.locality, typeInfo(al.scam_type)[lang]);
}
$("#alertBanner").addEventListener("click", () => openMap());

let leaflet = null, map = null, layer = null;
function loadLeaflet() {
  if (leaflet) return leaflet;
  leaflet = new Promise((resolve, reject) => {
    const css = document.createElement("link"); css.rel = "stylesheet";
    css.href = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"; document.head.append(css);
    const s = document.createElement("script"); s.src = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js";
    s.onload = () => resolve(window.L); s.onerror = reject; document.head.append(s);
  });
  return leaflet;
}
async function openMap() {
  $("#mapView").hidden = false;
  if (!areaByPin(area)) { openAreaPicker(); return; }
  loadMap();
}
function closeMap() { $("#mapView").hidden = true; }
$("#openMap").addEventListener("click", openMap);
$("#mapBack").addEventListener("click", closeMap);

async function loadMap() {
  const a = areaByPin(area); if (!a) return;
  renderArea();
  let data, alerts;
  try {
    [data, alerts] = await Promise.all([api(`/map?pincode=${a.pincode}&days=7&radius_km=25`), api(`/alerts?pincode=${a.pincode}`)]);
  } catch (ex) { if (!(ex instanceof LicenceExpired)) toast(ex.message); return; }

  const al = $("#alertList"); al.replaceChildren();
  alerts.alerts.forEach((x) => {
    const r = document.createElement("div"); r.className = "row row-alert";
    r.innerHTML = `<span class="dot sev-CRIT"></span><span class="grow"><strong></strong></span>`;
    r.querySelector("strong").textContent = alertText(x, a); al.append(r);
  });

  const cl = $("#clusterList"); cl.replaceChildren();
  if (!data.clusters.length) { const p = document.createElement("p"); p.className = "empty"; p.textContent = t("no_clusters"); cl.append(p); }
  data.clusters.forEach((c) => {
    const r = document.createElement("div"); r.className = "row";
    r.innerHTML = `<span class="dot sev-${c.severity}"></span><span class="grow"><strong></strong><small></small></span><span class="count"></span>`;
    r.querySelector("strong").textContent = `${c.locality}, ${c.city}`;
    r.querySelector("small").textContent = typeInfo(c.top_scam_type)[lang];
    r.querySelector(".count").textContent = t("reports_n", c.count);
    cl.append(r);
  });

  try {
    const L = await loadLeaflet();
    // The view was hidden a frame ago: wait for layout, or Leaflet sizes its layers at 0x0.
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    if (!map) {
      map = L.map("map", { zoomControl: false, attributionControl: true });
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18, attribution: "© OpenStreetMap",
      }).addTo(map);
      map.setView([a.lat, a.lng], 12);
    }
    map.invalidateSize();
    layer?.remove(); layer = L.layerGroup().addTo(map);
    const color = { CRIT: "#D4423A", HIGH: "#C27C0E", MED: "#E3B341" };
    L.circleMarker([a.lat, a.lng], { radius: 7, color: "#2F5BEA", weight: 3, fillColor: "#fff", fillOpacity: 1 }).addTo(layer);
    const pts = [[a.lat, a.lng]];
    data.clusters.forEach((c) => {
      L.circleMarker([c.lat, c.lng], { radius: 10 + Math.min(18, c.count * 1.5), color: color[c.severity], weight: 1.5,
        fillColor: color[c.severity], fillOpacity: 0.28 }).bindTooltip(`${c.locality}: ${c.count}`).addTo(layer);
      pts.push([c.lat, c.lng]);
    });
    if (pts.length > 1) map.fitBounds(pts, { padding: [28, 28], maxZoom: 14 }); else map.setView([a.lat, a.lng], 13);
  } catch { /* map tiles are a bonus; the list above already has everything */ }
}

// ---------------- Licence ----------------
function showExpired() { $("#expired").hidden = false; }
async function checkLicence() {
  try {
    const r = await fetch("/license"); const b = await r.json();
    $("#expired").hidden = b.status === "valid";
  } catch { /* offline: leave as is */ }
}
$("#expiredRetry").addEventListener("click", async () => { await checkLicence(); if ($("#expired").hidden) { loadAreas(); } });
document.addEventListener("visibilitychange", () => { if (!document.hidden) checkLicence(); });

// ---------------- Start ----------------
applyLang();
checkLicence();
loadAreas();
