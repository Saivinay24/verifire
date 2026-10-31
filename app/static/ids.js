// Identifier rules shared by the check box, the report form and the message reader.
// Everything here runs on the phone; a pasted message is never sent to the server.

// The same rules the server uses (app/domain/identifiers.py), so the arrow lights only for a value
// the server will accept: an Indian number, a UPI ID, a real link or a 6-letter SMS sender.
export function validPhone(raw) {
  let v = raw.replace(/[\s\-(). ]/g, "");
  if (v.startsWith("+")) { v = v.slice(1); if (!v.startsWith("91")) return false; }
  if (!/^\d+$/.test(v)) return false;
  if ((v.startsWith("1800") || v.startsWith("1860")) && v.length >= 8 && v.length <= 11) return true;
  if (v.startsWith("1") && v.length >= 3 && v.length <= 6) {
    const steps = new Set([...v].slice(1).map((d, i) => (Number(d) - Number(v[i]) + 10) % 10));
    const run = steps.size === 1 && (steps.has(1) || steps.has(9));
    return !(v.length >= 4 && (run || new Set(v).size < 2));  // 1930 yes; 1234, 1111 no
  }
  if (v.startsWith("0091") && v.length === 14) v = v.slice(4);
  else if (v.startsWith("91") && v.length === 12) v = v.slice(2);
  else if (v.startsWith("0") && v.length === 11) v = v.slice(1);
  return v.length === 10 && !"01".includes(v[0]) && new Set(v).size >= 3;
}
export function validUpi(raw) {
  let v = raw.trim();
  if (/^upi:\/\/pay\?/i.test(v)) {
    const pa = new URLSearchParams(v.split("?")[1] || "").get("pa"); v = pa || "";
  }
  v = v.replace(/\s+/g, "").toLowerCase();
  return /^[a-z0-9._-]{2,256}@[a-z][a-z0-9.]{1,63}$/.test(v);
}
export function validUrl(raw) {
  let v = raw.trim();
  if (!/^[a-z][a-z0-9+.-]*:\/\//i.test(v)) v = "https://" + v;
  try {
    const u = new URL(v);
    if (!["http:", "https:"].includes(u.protocol)) return false;
    const host = u.hostname.replace(/\.$/, "").replace(/^www\./, "");
    return /^(?=.{4,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/.test(host);
  } catch { return false; }
}
export function validSender(raw) {
  const v = raw.replace(/\s+/g, "").toUpperCase().replace(/^[A-Z]{2}-/, "").replace(/-[PSTG]$/, "");
  return /^[A-Z]{6}$/.test(v);
}
export function detectKind(raw) {
  const v = raw.trim();
  if (!v) return null;
  if (v.includes("@") || /^upi:\/\//i.test(v)) return validUpi(v) ? "upi" : null;
  if (/^[+\d\s\-(). ]+$/.test(v)) return validPhone(v) ? "phone" : null;
  if (/^([a-z]{2}-)?[a-z]{6}(-[pstg])?$/i.test(v)) return "sender_id";
  if (/^https?:\/\//i.test(v) || /\.[a-z]{2,}/i.test(v)) return validUrl(v) ? "url" : null;
  return null;
}


// ---------------- Reading a pasted message ----------------
// A message is anything long enough with spaces in it that is not itself one identifier.
export const looksLikeMessage = (raw) => raw.trim().length >= 20 && /\s/.test(raw.trim()) && !detectKind(raw);

// Bare domains in SMS are only picked up with a TLD common in scam messages, so "no.XX" or
// "Rs.500" never turn into links. A scheme or "www." makes any TLD count.
const TLDS = "in|com|net|org|co|info|xyz|top|online|site|link|app|me|io|ly|live|shop|store|club|cc|tk|ml|ga|cf|gq|buzz|icu|vip|page|tech|cloud|biz|us|uk|win|bid|loan|work|click|support|help|services|digital|today|cyou|sbs|bond";
const RX = {
  url: new RegExp(String.raw`(?<![@\w.])(?:https?:\/\/[^\s<>"']+|www\.[^\s<>"']+|(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+(?:${TLDS})\b(?:\/[^\s<>"']*)?)`, "gi"),
  upi: /(?<![\w.])[a-z0-9._-]{2,256}@[a-z][a-z0-9]{1,63}(?![\w.@])/gi,
  phone: /(?<![\w+])\+?\d[\d\s\-().]{6,18}\d(?!\w)/g,
  sender: /\b[A-Z]{2}-[A-Z]{6}(?:-[PSTG])?\b/g,
};
const trimEnd = (s) => s.replace(/[.,;:!?)\]}'"]+$/, "");
const key = (kind, v) => kind === "phone" ? v.replace(/\D/g, "").slice(-10)
  : kind === "url" ? v.toLowerCase().replace(/^https?:\/\//, "").replace(/^www\./, "").replace(/\/$/, "")
  : v.toLowerCase();

/** Every number, UPI ID, link and SMS sender in the text that the server would accept, in order. */
export function extractIds(text, max = 6) {
  const found = [];
  const seen = new Set();
  const push = (kind, value, at) => {
    const k = kind + ":" + key(kind, value);
    if (seen.has(k)) return;
    seen.add(k); found.push({ kind, value, at });
  };
  for (const m of text.matchAll(RX.upi)) if (validUpi(m[0])) push("upi", m[0], m.index);
  for (const m of text.matchAll(RX.url)) { const v = trimEnd(m[0]); if (validUrl(v)) push("url", v, m.index); }
  for (const m of text.matchAll(RX.phone)) {
    const v = m[0].trim(), digits = v.replace(/\D/g, "");
    // In a message, short digit runs are OTPs, amounts or dates; only full numbers count.
    if (digits.length >= 8 && validPhone(v)) push("phone", v, m.index);
  }
  for (const m of text.matchAll(RX.sender)) if (validSender(m[0])) push("sender_id", m[0], m.index);
  return found.sort((a, b) => a.at - b.at).slice(0, max);
}

// Warning signs: fixed patterns, not a model. Each one says what it found and where, so a person
// can see exactly which words raised it. English, Hinglish and Hindi.
export const FLAGS = [
  { id: "otp", rx: /\bo\.?t\.?p\b|one[\s-]?time[\s-]?pass\w*|verification code|\bcvv\b|\bupi pin\b|\bm?pin\b|ओटीपी|पिन/gi },
  { id: "arrest", rx: /\barrest\w*|\bwarrant\b|\bcbi\b|\bnarcotics?\b|\bcustoms\b|\bf\.?i\.?r\b|money laundering|digital arrest|\bcourt\b|\bpolice\b|गिरफ्तार\w*|पुलिस|वारंट/gi },
  { id: "urgent", rx: /\burgent\w*|\bimmediately\b|within \d+\s?(?:hours?|hrs?|minutes?|mins?)|\btoday itself\b|\blast (?:chance|date|warning)\b|\bexpir\w+|\bturant\b|\bjaldi\b|तुरंत|जल्दी|आज ही/gi },
  { id: "blocked", rx: /\bkyc\b|\bblock(?:ed)?\b|\bsuspend\w*|\bdeactivat\w*|\bdisconnect\w*|\bfrozen\b|\bfreeze\b|pan (?:card )?(?:update|link)\w*|\bbandh?\b|बंद|ब्लॉक/gi },
  { id: "prize", rx: /\bcongratulations?\b|\byou (?:have )?won\b|\bwinner\b|\blottery\b|\bprize\b|lucky draw|\bkbc\b|\bcashback\b|\breward points?\b|\bgift\b|इनाम|लॉटरी/gi },
  { id: "pay", rx: /pay (?:now|immediately|a fee|the fee|charges?)|processing fee|registration fee|\bsecurity deposit\b|\bsend money\b|\brefund\b|\badvance (?:fee|payment)\b|scan (?:the |this )?qr|पैसे भेज\w*|शुल्क/gi },
  { id: "remote", rx: /\banydesk\b|\bteamviewer\b|quick ?support|rust ?desk|\.apk\b|screen ?shar\w*|install (?:this|the) app/gi },
  { id: "secret", rx: /don'?t (?:tell|inform|share this with)|do not (?:tell|inform|disconnect)|keep (?:it|this) (?:secret|confidential)|stay on (?:the )?(?:call|line)|किसी को (?:मत|न) बता\w*/gi },
  { id: "job", rx: /part[\s-]?time|work from home|daily (?:income|earning|payout)|earn (?:rs\.?|₹)\s?[\d,]+|like (?:videos|youtube)|\btelegram task\b|\bprepaid task\b/gi },
];

/** Warning signs in the text: [{ id, hits: [{ at, len, text }] }], in the order of FLAGS. */
export function redFlags(text, hasLink = false) {
  const out = [];
  for (const f of FLAGS) {
    const hits = [...text.matchAll(f.rx)].map((m) => ({ at: m.index, len: m[0].length, text: m[0] }));
    if (hits.length) out.push({ id: f.id, hits });
  }
  if (hasLink) out.push({ id: "link", hits: [] });
  return out;
}
