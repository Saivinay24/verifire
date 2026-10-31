// VeriFire mobile web app. Plain ES module, no build step.
// Privacy: the app never sends GPS. "Near me" picks the nearest supported area on this device
// and sends only its pincode. The reporter id is a random anonymous token kept on this device.

const $ = (sel) => document.querySelector(sel);

// ---------------- Words (English / Hindi) ----------------
const T = {
  en: {
    brand: "VeriFire",
    hello: "Check before you trust.",
    hello_sub: "Paste a number, UPI ID or link. See if people near you reported it.",
    report_cta: "Report a scam", near_cta: "Scams near me", dock_label: "Got a scam call or message?",
    heat_title: "Scam reports, last 7 days", heat_few: "Few", heat_many: "Many",
    area_search: "Search by area name or pincode", type_search: "Search scam types", type_search_ph: "Try police, OTP, job, parcel",
    type_none: "Nothing matches. Tap \"Not sure, skip\" below and describe it in your own words.", area_none: (q) => `No area matches "${q}" yet. Try the pincode or a nearby area.`,
    check_label: "Number, UPI ID or link", check_placeholder: "Paste a number, UPI ID or link",
    fineprint: "Anonymous. We save only the area, never who you are.",
    call1930: "Lost money? Call 1930", report_this: "Report this",
    dispute_link: "Is this your number? Ask for a review",
    step1: "How did they reach you?", step2: "What did they try?", step3: "Who was it?",
    step3_sub: "Their number, UPI ID or link. Not yours.",
    value_label: "Their number, UPI ID or link", value_placeholder: "Their number, UPI ID or link",
    when: "When?", where: "Your area", choose_area: "Choose area", use_location: "Near me",
    add_note: "Add what happened (optional)", note_placeholder: "In your own words. Don't write your name or number.",
    lost_money: "Money lost (optional)", send: "Send report",
    done_title: "Thank you", done_sub: (a) => `Report sent. You just helped warn the next person in ${a} who checks this number.`,
    file_complaint: "File a complaint on cybercrime.gov.in", done: "Done", not_sure: "Not sure, skip",
    map_title: "Scams reported nearby", map_sub: "Last 7 days, grouped by area. Never anyone's exact location.",
    dispute_title: "Ask for a review",
    dispute_sub: "While we check, this number shows \"Be careful\" instead of \"Reported as a scam\". People still see how many reported it. A reviewer looks at your proof within 7 days and may email you. If they can't confirm it in time, or new people keep reporting the number, the warning comes back. Each number can ask once.",
    d_name: "Your name or business name", d_email: "Email for our reply", d_proof: "Proof, e.g. GST or shop licence number",
    d_send: "Send for review", d_done: "Sent. This number is now under review for up to 7 days.",
    d_locked: "This number was already reviewed recently, so it can't be disputed again for now.",
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
    under_review: (d) => `Under review until ${d}: someone says this is their number and asked us to check. Until then, don't pay or share codes.`,
    dsp_overruled: "Someone asked us to review this number, but new people kept reporting it, so the warning is back.",
    dsp_rejected: "A reviewer checked the owner's request and kept the warning.",
    dsp_lapsed: "A review was asked for but not confirmed in time, so the warning is back.",
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
    say_it: "Say it", listening: "Listening. Tap to stop", mic_hint: "Listening. Say one sentence in English or Hindi, then tap Say it again to add more. Don't say your name or number.",
    mic_denied: "Microphone is blocked. Allow it for this site in your browser settings, or use your keyboard's mic key.",
    mic_none: "No microphone found. Check your phone or computer allows the browser to use it.",
    mic_unavailable: "Voice typing isn't available in this browser. Use the mic key on your keyboard instead.",
    mic_silent: "Didn't catch anything. Tap Say it and speak.", mic_fail: "Couldn't hear that. Use the mic key on your keyboard instead.",
    prepare_complaint: "Prepare my complaint", c_title: "Your complaint, ready to send",
    c_sub: "Written from your report. Fill in the parts in [brackets]. It stays on your phone.",
    c_money: "Money taken? Call 1930 first. Banks can hold the money only if it is reported fast.",
    c_copy: "Copy", c_share: "Share", c_email: "Email to my bank", c_portal: "Open cybercrime.gov.in", c_copied: "Copied. Paste it into the complaint form.",
    complaint: (r) => ({
      subject: `Complaint about a suspected scam: ${r.type}, ${r.date}`,
      body: [
        "To the Cyber Crime Cell / my bank's customer care,", "",
        "I want to report a suspected scam and ask for help.", "",
        `Date and time: ${r.when} (about)`,
        `How they contacted me: ${r.channel}`,
        `What they tried: ${r.type}`,
        `Their ${r.kind}: ${r.value}`,
        `My area: ${r.area}`,
        `Money lost: ${r.amount ? "₹" + r.amount : "None"}`,
        `What happened: ${r.note || "[describe what happened, in your own words]"}`, "",
        ...(r.amount ? ["Payment details: [bank or UPI app], [transaction ID], [date and time of payment]",
          "Please hold or recover the amount above. I have called or will call 1930, the national cybercrime helpline.", ""] : []),
        "My details:", "Name: [your name]", "Phone: [your phone number]", "Email: [your email]", "", "Thank you.",
      ].join("\n"),
    }),
    stats_cta: "Stats", pull_more: "Show more", menu: "Menu", close: "Close",
    mine_title: "Is my number reported?", mine_sub: "See what people said about your number, and ask for a review if it's wrong.",
    mine_how: "Type your number, UPI ID or link. You'll see exactly what anyone else sees. If people reported it by mistake, you can ask for a review from there.",
    mine_placeholder: "Your number, UPI ID or link",
    pull_title: (c) => `${c}, last 7 days`,
    pull_sub: (counted, aside) => aside ? `${counted} reports counted. ${aside} repeats and fake reports set aside.` : `${counted} reports counted.`,
    pull_empty: (c) => `No reports counted in ${c} in the last 7 days.`,
    trending: "Trending scams", known_here: "Numbers reported as scams", by_area: "By area", recent: "Recent reports",
    pull_foot: "Built only from reports our trust engine counted. Times are rounded to the hour. A number stays hidden until 3 different people report it.",
    none_known: "None yet. A number shows here once 3 different people report it.", spike_badge: "Spike today",
    spike_near: (a) => `Scam reports near ${a} jumped today.`, people_n: (n) => `${n} ${n === 1 ? "person" : "people"}`,
    stats_title: "Live on VeriFire",
    stats_sub: "What people reported here, counted after our trust engine set repeats and fake reports aside.",
    days_n: (n) => `${n} days`, reports_in: (n) => `reports in ${n} days`,
    counted: "Counted", set_aside: "Set aside",
    hero_note: (aside) => `${aside} were set aside: the same person again, fake accounts on one connection, or a pile-on. They never shape trends or alerts.`,
    k_numbers: "Numbers reported", k_known: "Reported as scams", k_money: "Money people said they lost",
    k_week: "Counted this week", vs_last: (n) => `${n} the week before`,
    last14: "Last 14 days", by_type: "By scam type", by_channel: "How they reached people", by_city: "By city",
    other_types: "Everything else", no_data: "No reports in this period yet.",
    india_title: "Across India", india_lost: "lost to online financial scams in 2025, in 28.15 lakh complaints",
    india_invest: "of that money was lost to fake investment and trading schemes",
    india_saved: "saved in 32.80 lakh complaints because people reported fast to 1930 (to 30 June 2026)",
    india_source: "Figures presented by NIELIT Kohima at a PIB media workshop, 21 Aug 2026.", india_link: "Read the PIB release",
    stats_fine: "Everything above the \"Across India\" card is reports made on VeriFire, not national totals.",
  },
  hi: {
    brand: "VeriFire",
    hello: "भरोसा करने से पहले जांचें।",
    hello_sub: "नंबर, UPI ID या लिंक डालें। देखें कि आपके पास किसी ने इसकी रिपोर्ट की है या नहीं।",
    report_cta: "स्कैम की रिपोर्ट करें", near_cta: "मेरे पास के स्कैम", dock_label: "स्कैम कॉल या मैसेज आया?",
    heat_title: "स्कैम रिपोर्ट, पिछले 7 दिन", heat_few: "कम", heat_many: "ज़्यादा",
    area_search: "इलाके का नाम या पिनकोड खोजें", type_search: "स्कैम का प्रकार खोजें", type_search_ph: "जैसे पुलिस, OTP, नौकरी, पार्सल",
    type_none: "कुछ नहीं मिला। नीचे \"पता नहीं, आगे बढ़ें\" दबाएं और अपने शब्दों में बताएं।", area_none: (q) => `"${q}" से कोई इलाका नहीं मिला। पिनकोड या पास का इलाका आज़माएं।`,
    check_label: "नंबर, UPI ID या लिंक", check_placeholder: "नंबर, UPI ID या लिंक डालें",
    fineprint: "गुमनाम। हम सिर्फ इलाका रखते हैं, आपकी पहचान कभी नहीं।",
    call1930: "पैसे गए? 1930 पर कॉल करें", report_this: "इसकी रिपोर्ट करें",
    dispute_link: "क्या यह आपका नंबर है? जांच के लिए कहें",
    step1: "उन्होंने आपसे कैसे संपर्क किया?", step2: "उन्होंने क्या करने की कोशिश की?", step3: "वह कौन था?",
    step3_sub: "उनका नंबर, UPI ID या लिंक। आपका नहीं।",
    value_label: "उनका नंबर, UPI ID या लिंक", value_placeholder: "उनका नंबर, UPI ID या लिंक",
    when: "कब?", where: "आपका इलाका", choose_area: "इलाका चुनें", use_location: "मेरे पास",
    add_note: "क्या हुआ, लिखें (ज़रूरी नहीं)", note_placeholder: "अपने शब्दों में। अपना नाम या नंबर न लिखें।",
    lost_money: "कितने पैसे गए (ज़रूरी नहीं)", send: "रिपोर्ट भेजें",
    done_title: "धन्यवाद", done_sub: (a) => `रिपोर्ट भेज दी गई। ${a} में इस नंबर को जांचने वाले अगले व्यक्ति को आपने सावधान कर दिया।`,
    file_complaint: "cybercrime.gov.in पर शिकायत दर्ज करें", done: "ठीक है", not_sure: "पता नहीं, आगे बढ़ें",
    map_title: "आसपास रिपोर्ट किए गए स्कैम", map_sub: "पिछले 7 दिन, इलाके के हिसाब से। किसी की सटीक जगह कभी नहीं।",
    dispute_title: "जांच के लिए कहें",
    dispute_sub: "जांच के दौरान यह नंबर \"स्कैम\" की जगह \"सावधान रहें\" दिखेगा। लोग फिर भी देखेंगे कि कितनों ने रिपोर्ट की। समीक्षक 7 दिन में आपका सबूत देखेंगे और ईमेल कर सकते हैं। अगर समय पर पुष्टि न हो, या नए लोग रिपोर्ट करते रहें, तो चेतावनी वापस आ जाएगी। हर नंबर एक बार ही जांच मांग सकता है।",
    d_name: "आपका या बिज़नेस का नाम", d_email: "जवाब के लिए ईमेल", d_proof: "सबूत, जैसे GST या दुकान लाइसेंस नंबर",
    d_send: "जांच के लिए भेजें", d_done: "भेज दिया। यह नंबर अब 7 दिन तक जांच में है।",
    d_locked: "इस नंबर की हाल ही में जांच हो चुकी है, इसलिए अभी दोबारा नहीं मांगी जा सकती।",
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
    under_review: (d) => `${d} तक जांच जारी: किसी ने कहा है कि यह उनका नंबर है। तब तक पैसे न दें, कोड न बताएं।`,
    dsp_overruled: "किसी ने इस नंबर की जांच मांगी, पर नए लोग रिपोर्ट करते रहे, इसलिए चेतावनी वापस है।",
    dsp_rejected: "समीक्षक ने मालिक का अनुरोध देखा और चेतावनी बनाए रखी।",
    dsp_lapsed: "जांच मांगी गई थी पर समय पर पुष्टि नहीं हुई, इसलिए चेतावनी वापस है।",
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
    say_it: "बोलकर बताएं", listening: "सुन रहे हैं। रोकने के लिए दबाएं", mic_hint: "सुन रहे हैं। हिंदी या अंग्रेज़ी में एक वाक्य बोलें, और जोड़ने के लिए फिर से दबाएं। अपना नाम या नंबर न बोलें।",
    mic_denied: "माइक्रोफ़ोन बंद है। ब्राउज़र सेटिंग में इस साइट के लिए अनुमति दें, या कीबोर्ड का माइक बटन इस्तेमाल करें।",
    mic_none: "माइक्रोफ़ोन नहीं मिला। देखें कि फ़ोन या कंप्यूटर ब्राउज़र को माइक की अनुमति देता है।",
    mic_unavailable: "इस ब्राउज़र में बोलकर लिखना नहीं चलता। कीबोर्ड का माइक बटन इस्तेमाल करें।",
    mic_silent: "कुछ सुनाई नहीं दिया। बोलकर बताएं दबाएं और बोलें।", mic_fail: "सुनाई नहीं दिया। कीबोर्ड का माइक बटन इस्तेमाल करें।",
    prepare_complaint: "मेरी शिकायत तैयार करें", c_title: "आपकी शिकायत, भेजने के लिए तैयार",
    c_sub: "आपकी रिपोर्ट से लिखी गई है। [ब्रैकेट] वाली जगह भरें। यह आपके फ़ोन पर ही रहती है।",
    c_money: "पैसे गए? पहले 1930 पर कॉल करें। जल्दी बताने पर ही बैंक पैसे रोक सकता है।",
    c_copy: "कॉपी करें", c_share: "शेयर करें", c_email: "बैंक को ईमेल करें", c_portal: "cybercrime.gov.in खोलें", c_copied: "कॉपी हो गया। शिकायत फ़ॉर्म में पेस्ट करें।",
    complaint: (r) => ({
      subject: `संदिग्ध स्कैम की शिकायत: ${r.type}, ${r.date}`,
      body: [
        "सेवा में, साइबर क्राइम सेल / मेरे बैंक की ग्राहक सेवा,", "",
        "मैं एक संदिग्ध स्कैम की रिपोर्ट करना चाहता/चाहती हूं और मदद चाहता/चाहती हूं।", "",
        `तारीख और समय: ${r.when} (लगभग)`,
        `उन्होंने संपर्क कैसे किया: ${r.channel}`,
        `उन्होंने क्या करने की कोशिश की: ${r.type}`,
        `उनका ${r.kind}: ${r.value}`,
        `मेरा इलाका: ${r.area}`,
        `कितने पैसे गए: ${r.amount ? "₹" + r.amount : "कोई नहीं"}`,
        `क्या हुआ: ${r.note || "[अपने शब्दों में लिखें कि क्या हुआ]"}`, "",
        ...(r.amount ? ["भुगतान का विवरण: [बैंक या UPI ऐप], [ट्रांज़ैक्शन ID], [भुगतान की तारीख और समय]",
          "कृपया ऊपर की राशि रोकें या वापस दिलाएं। मैंने 1930 (राष्ट्रीय साइबर क्राइम हेल्पलाइन) पर कॉल किया है या करूंगा/करूंगी।", ""] : []),
        "मेरा विवरण:", "नाम: [आपका नाम]", "फ़ोन: [आपका फ़ोन नंबर]", "ईमेल: [आपका ईमेल]", "", "धन्यवाद।",
      ].join("\n"),
    }),
    stats_cta: "आंकड़े", pull_more: "और देखें", menu: "मेन्यू", close: "बंद करें",
    mine_title: "क्या मेरे नंबर की रिपोर्ट हुई है?", mine_sub: "देखें लोगों ने आपके नंबर के बारे में क्या कहा, और गलत हो तो जांच के लिए कहें।",
    mine_how: "अपना नंबर, UPI ID या लिंक लिखें। आपको वही दिखेगा जो बाकी सबको दिखता है। अगर गलती से रिपोर्ट हुई है, तो वहीं से जांच के लिए कह सकते हैं।",
    mine_placeholder: "आपका नंबर, UPI ID या लिंक",
    pull_title: (c) => `${c}, पिछले 7 दिन`,
    pull_sub: (counted, aside) => aside ? `${counted} रिपोर्ट गिनी गईं। ${aside} दोहराई या नकली रिपोर्ट अलग रखी गईं।` : `${counted} रिपोर्ट गिनी गईं।`,
    pull_empty: (c) => `पिछले 7 दिनों में ${c} में कोई रिपोर्ट नहीं गिनी गई।`,
    trending: "अभी चल रहे स्कैम", known_here: "स्कैम के रूप में रिपोर्ट किए गए नंबर", by_area: "इलाके के हिसाब से", recent: "हाल की रिपोर्ट",
    pull_foot: "सिर्फ वे रिपोर्ट जिन्हें हमारे ट्रस्ट इंजन ने गिना। समय घंटे तक गोल किया गया है। जब तक 3 अलग लोग रिपोर्ट न करें, नंबर छिपा रहता है।",
    none_known: "अभी कोई नहीं। 3 अलग लोगों के रिपोर्ट करने पर नंबर यहां दिखेगा।", spike_badge: "आज अचानक बढ़ीं",
    spike_near: (a) => `${a} के पास आज स्कैम रिपोर्ट अचानक बढ़ीं।`, people_n: (n) => `${n} लोग`,
    stats_title: "VeriFire पर अभी",
    stats_sub: "यहां लोगों ने क्या रिपोर्ट किया, ट्रस्ट इंजन के दोहराई और नकली रिपोर्ट अलग करने के बाद।",
    days_n: (n) => `${n} दिन`, reports_in: (n) => `रिपोर्ट, ${n} दिनों में`,
    counted: "गिनी गईं", set_aside: "अलग रखी गईं",
    hero_note: (aside) => `${aside} अलग रखी गईं: वही व्यक्ति दोबारा, एक कनेक्शन पर नकली अकाउंट, या मिलकर की गई रिपोर्ट। ये रुझान या अलर्ट पर असर नहीं डालतीं।`,
    k_numbers: "रिपोर्ट किए गए नंबर", k_known: "स्कैम के रूप में रिपोर्ट", k_money: "लोगों ने बताया, इतने पैसे गए",
    k_week: "इस हफ्ते गिनी गईं", vs_last: (n) => `पिछले हफ्ते ${n}`,
    last14: "पिछले 14 दिन", by_type: "स्कैम के प्रकार से", by_channel: "लोगों तक कैसे पहुंचे", by_city: "शहर के हिसाब से",
    other_types: "बाकी सब", no_data: "इस अवधि में अभी कोई रिपोर्ट नहीं।",
    india_title: "पूरे भारत में", india_lost: "2025 में ऑनलाइन वित्तीय स्कैम में गए, 28.15 लाख शिकायतों में",
    india_invest: "पैसा नकली निवेश और ट्रेडिंग स्कीम में गया",
    india_saved: "32.80 लाख शिकायतों में बचाए गए, क्योंकि लोगों ने जल्दी 1930 पर बताया (30 जून 2026 तक)",
    india_source: "PIB मीडिया वर्कशॉप में NIELIT कोहिमा द्वारा प्रस्तुत आंकड़े, 21 अगस्त 2026।", india_link: "PIB रिलीज़ पढ़ें",
    stats_fine: "\"पूरे भारत में\" कार्ड के ऊपर सब कुछ VeriFire पर की गई रिपोर्ट है, राष्ट्रीय आंकड़े नहीं।",
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

// Extra words people use for each scam, so the search finds a tile by what happened, not only its label.
const TYPE_WORDS = {
  "digital-arrest": "cbi ed customs officer arrest warrant court case video call narcotics drugs aadhaar misuse sim block trai पुलिस गिरफ्तारी सीबीआई",
  "fake-kyc-link": "kyc bank account blocked pan aadhaar update link sms suspended केवाईसी बैंक खाता",
  "upi-refund-qr": "qr scan refund pin upi gpay phonepe paytm receive money olx क्यूआर रिफंड",
  "investment-group": "stock trading crypto share market ipo telegram whatsapp group returns profit निवेश शेयर ट्रेडिंग",
  "courier-customs": "parcel courier fedex dhl customs package drugs delivery पार्सल कूरियर",
  "job-offer": "job task part time work from home youtube like review rating deposit telegram नौकरी काम",
  "lottery-prize": "lottery prize gift winner kbc lucky draw reward इनाम लॉटरी",
  "loan-app-harassment": "loan app instant loan threat morphed photos contacts recovery लोन धमकी",
  "electricity-disconnection": "electricity bill power cut light bescom meter बिजली बिल",
  "fake-customer-care": "customer care helpline refund support google search swiggy amazon flipkart bank कस्टमर केयर हेल्पलाइन",
  "otp-call": "otp code pin cvv card bank verification ओटीपी कोड",
  "sextortion": "video call nude blackmail girl record leak ब्लैकमेल वीडियो",
};

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

// The same rules the server uses (app/domain/identifiers.py), so the arrow lights only for a value
// the server will accept: an Indian number, a UPI ID, a real link or a 6-letter SMS sender.
function validPhone(raw) {
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
function validUpi(raw) {
  let v = raw.trim();
  if (/^upi:\/\/pay\?/i.test(v)) {
    const pa = new URLSearchParams(v.split("?")[1] || "").get("pa"); v = pa || "";
  }
  v = v.replace(/\s+/g, "").toLowerCase();
  return /^[a-z0-9._-]{2,256}@[a-z][a-z0-9.]{1,63}$/.test(v);
}
function validUrl(raw) {
  let v = raw.trim();
  if (!/^[a-z][a-z0-9+.-]*:\/\//i.test(v)) v = "https://" + v;
  try {
    const u = new URL(v);
    if (!["http:", "https:"].includes(u.protocol)) return false;
    const host = u.hostname.replace(/\.$/, "").replace(/^www\./, "");
    return /^(?=.{4,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/.test(host);
  } catch { return false; }
}
function validSender(raw) {
  const v = raw.replace(/\s+/g, "").toUpperCase().replace(/^[A-Z]{2}-/, "").replace(/-[PSTG]$/, "");
  return /^[A-Z]{6}$/.test(v);
}
function detectKind(raw) {
  const v = raw.trim();
  if (!v) return null;
  if (v.includes("@") || /^upi:\/\//i.test(v)) return validUpi(v) ? "upi" : null;
  if (/^[+\d\s\-(). ]+$/.test(v)) return validPhone(v) ? "phone" : null;
  if (/^([a-z]{2}-)?[a-z]{6}(-[pstg])?$/i.test(v)) return "sender_id";
  if (/^https?:\/\//i.test(v) || /\.[a-z]{2,}/i.test(v)) return validUrl(v) ? "url" : null;
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
  $("#areaSearch").value = ""; renderAreaList("");
  openSheet("#areaSheet");
}
// One box for both: digits match the pincode, letters match the area or city name.
function renderAreaList(q) {
  const list = $("#areaList"); list.replaceChildren();
  const query = q.trim().toLowerCase();
  const hits = AREAS.filter((a) => !query || (/^\d+$/.test(query) ? a.pincode.startsWith(query)
    : `${a.locality} ${a.city}`.toLowerCase().includes(query)));
  if (!hits.length) { emptyLine(list, t("area_none", q.trim())); return; }
  const byCity = {};
  hits.forEach((a) => (byCity[a.city] ||= []).push(a));
  Object.entries(byCity).forEach(([city, items]) => {
    const h = document.createElement("h3"); h.textContent = city; list.append(h);
    items.forEach((a) => {
      const b = document.createElement("button"); b.type = "button";
      b.innerHTML = `<b></b><span></span>`;
      b.querySelector("b").textContent = a.locality; b.querySelector("span").textContent = a.pincode;
      if (a.pincode === area) b.setAttribute("aria-current", "true");
      b.addEventListener("click", () => pickArea(a));
      list.append(b);
    });
  });
}
function pickArea(a) { setArea(a.pincode); closeSheet("#areaSheet"); if (!$("#mapView").hidden) loadMap(); }
$("#areaSearch").addEventListener("input", (e) => renderAreaList(e.target.value));
$("#areaSearch").addEventListener("keydown", (e) => {
  // Enter picks the only match, so a full pincode plus Enter is enough.
  if (e.key !== "Enter") return;
  e.preventDefault();
  const first = $("#areaList button"); if ($("#areaList").querySelectorAll("button").length === 1) first.click();
});
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
  if (!$("#drawer").hidden) { setDrawer(false); return; }
  const open = document.querySelector(".sheet:not([hidden])");
  if (open) closeSheet("#" + open.id); else if (!$("#reportFlow").hidden) closeFlow(); else if (!$("#mapView").hidden) closeMap();
  else if (!$("#statsView").hidden) closeStats();
});

// ---------------- Check ----------------
function updateKind(input, chip) {
  const k = detectKind(input.value);
  chip.hidden = !k; if (k) chip.textContent = T[lang].kinds[k];
  // The arrow lights up only once the value is a real number, UPI ID, link or sender.
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
  const dsp = r.dispute;
  if (r.challenged) {
    const until = dsp?.closes_at ? new Date(dsp.closes_at).toLocaleDateString(lang === "hi" ? "hi-IN" : "en-IN", { day: "numeric", month: "short" }) : "";
    sub += (/[.।]$/.test(sub) ? " " : ". ") + t("under_review", until);
  } else if (dsp && r.report_count > 0 && ["overruled", "rejected", "lapsed"].includes(dsp.status)) {
    sub += (/[.।]$/.test(sub) ? " " : ". ") + t("dsp_" + dsp.status);
  }
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
  // Each number can ask once: after a review that ended against the claim, the link goes away.
  const locked = ["overruled", "rejected", "lapsed"].includes(r.dispute?.status);
  $("#disputeLink").hidden = v === "VERIFIED_BUSINESS" || r.report_count === 0 || r.challenged || locked;
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
  filterTypes();
}
// Every word typed must appear in the tile's label (either language) or its extra words.
function filterTypes() {
  const words = $("#typeSearch").value.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const shown = TYPES.filter((x) => x.id !== "other");
  let n = 0;
  $("#typeTiles").querySelectorAll(".tile").forEach((b, i) => {
    const it = shown[i], hay = `${it.en} ${it.hi} ${TYPE_WORDS[it.id] || ""}`.toLowerCase();
    const ok = words.every((w) => hay.includes(w)); b.hidden = !ok; n += ok;
  });
  $("#typeNone").hidden = n > 0;
}
function setTypeSearch(open) {
  $("#typeSearchBox").hidden = !open; $("#typeSearchBtn").hidden = open;
  $("#typeSearchBtn").setAttribute("aria-expanded", String(open));
  if (!open) $("#typeSearch").value = "";
  filterTypes();
  if (open) $("#typeSearch").focus();
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
  step = n; $("#reportFlow").dataset.step = n;
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
  $("#typeSearch").value = ""; setTypeSearch(false);
  renderTiles(); renderWhen(); renderArea(); stopListening(); setNoteOpen(false);
  $("#reportFlow").hidden = false; go(1);
}
function closeFlow() { stopListening(); $("#reportFlow").hidden = true; }
$("#openReport").addEventListener("click", () => openFlow(detectKind($("#checkInput").value) ? $("#checkInput").value.trim() : ""));
$("#flowClose").addEventListener("click", closeFlow);
$("#typeSearchBtn").addEventListener("click", () => setTypeSearch(true));
$("#typeSearch").addEventListener("input", filterTypes);
$("#typeSearch").addEventListener("keydown", (e) => {
  if (e.key === "Escape") { e.stopPropagation(); setTypeSearch(false); }
  if (e.key === "Enter") { e.preventDefault(); const vis = [...$("#typeTiles").querySelectorAll(".tile:not([hidden])")]; if (vis.length === 1) vis[0].click(); }
});
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
  stopListening();
  $("#sendReport").disabled = true;
  try {
    await api("/reports", { method: "POST", body: JSON.stringify(payload) });
    lastReport = { ...payload, kind, occurred, area: a };
    $("#doneSub").textContent = t("done_sub", a.locality);
    try { navigator.vibrate?.(35); } catch { /* no haptics here */ }
    go(4); refreshAlerts();
  } catch (ex) {
    if (!(ex instanceof LicenceExpired)) ex.status === 400 ? err(t("invalid")) : toast(ex.message);
  } finally { $("#sendReport").disabled = false; }
});

// ---------------- Voice note ----------------
// The phone's own speech recognition fills the note box; the person can read and edit it before
// sending. We never receive audio. On Android Chrome the phone's speech service does the
// transcribing (Google's service in Chrome), so we never claim "nothing leaves the phone".
const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let rec = null;
$("#micBtn").hidden = !Recognition;
function setNoteOpen(open) {
  $("#noteBody").hidden = !open; $("#noteToggle").setAttribute("aria-expanded", String(open));
  if (open) $("#reportNote").focus({ preventScroll: true });
}
$("#noteToggle").addEventListener("click", () => setNoteOpen($("#noteBody").hidden));
function stopListening() { if (rec) { try { rec.stop(); } catch { /* already stopped */ } } }
function showListening(on) {
  const b = $("#micBtn"); b.setAttribute("aria-pressed", String(on));
  b.querySelector("span").textContent = t(on ? "listening" : "say_it"); $("#micHint").hidden = !on;
}
$("#micBtn").addEventListener("click", () => {
  if (rec) { stopListening(); return; }
  setNoteOpen(true);
  const box = $("#reportNote"), before = box.value.trim();
  rec = new Recognition();
  // One phrase per tap. Continuous mode on Android Chrome repeats earlier words in every result,
  // so the note filled with duplicates; tapping again adds the next phrase after the first.
  rec.lang = lang === "hi" ? "hi-IN" : "en-IN"; rec.interimResults = true; rec.continuous = false;
  rec.onresult = (e) => {
    const said = e.results[e.results.length - 1][0].transcript.trim();
    box.value = ((before ? before + " " : "") + said).slice(0, 600);
  };
  rec.onerror = (e) => {
    const msg = { "not-allowed": "mic_denied", "audio-capture": "mic_none", "service-not-allowed": "mic_unavailable",
      network: "mic_unavailable", "language-not-supported": "mic_unavailable", "no-speech": "mic_silent" }[e.error];
    if (e.error !== "aborted") toast(t(msg || "mic_fail"));
  };
  rec.onend = () => { rec = null; showListening(false); };
  try { rec.start(); showListening(true); } catch { rec = null; toast(t("mic_fail")); }
});

// ---------------- Prepare my complaint ----------------
// Drafted here from the report just sent, in the person's language. It never goes to our server:
// they copy it into cybercrime.gov.in, share it, or email it from their own mail app.
let lastReport = null;
function fmtValue(kind, v) {
  // What the person typed, shown the way a bank or police form expects an Indian mobile number.
  const m = kind === "phone" && /^(?:\+?91|0)?(\d{5})(\d{5})$/.exec(v.replace(/[\s-]/g, ""));
  return m ? `+91 ${m[1]} ${m[2]}` : v;
}
function complaintDraft() {
  const r = lastReport, loc = lang === "hi" ? "hi-IN" : "en-IN";
  const ch = CHANNELS.find((c) => c.id === r.channel);
  return t("complaint", {
    type: typeInfo(r.scam_type)[lang], channel: ch ? ch[lang] : r.channel, kind: T[lang].kinds[r.kind].replace(/^([A-Z])(?=[a-z])/, (c) => c.toLowerCase()),  // "phone", "link", "UPI ID"
    value: fmtValue(r.kind, r.identifier_value), note: r.note,
    amount: r.amount_lost_inr ? r.amount_lost_inr.toLocaleString("en-IN") : "",
    date: r.occurred.toLocaleDateString(loc, { day: "numeric", month: "short", year: "numeric" }),
    when: r.occurred.toLocaleString(loc, { dateStyle: "medium", timeStyle: "short" }),
    area: `${r.area.locality}, ${r.area.city} ${r.area.pincode}`,
  });
}
let draftSubject = "";
$("#openComplaint").addEventListener("click", () => {
  if (!lastReport) return;
  const d = complaintDraft(); draftSubject = d.subject;
  $("#complaintText").value = d.body;
  $("#cMoney").hidden = !lastReport.amount_lost_inr;
  $("#cShare").hidden = !navigator.share;
  openSheet("#complaintSheet");
});
$("#cCopy").addEventListener("click", async () => {
  const text = `${draftSubject}\n\n${$("#complaintText").value}`;
  try { await navigator.clipboard.writeText(text); }
  catch { $("#complaintText").select(); document.execCommand("copy"); }
  toast(t("c_copied"));
});
$("#cShare").addEventListener("click", async () => {
  try { await navigator.share({ title: draftSubject, text: `${draftSubject}\n\n${$("#complaintText").value}` }); }
  catch { /* the person closed the share sheet */ }
});
$("#cEmail").addEventListener("click", () => {
  // No address: they pick their bank's official address in their own mail app.
  location.href = `mailto:?subject=${encodeURIComponent(draftSubject)}&body=${encodeURIComponent($("#complaintText").value)}`;
});

// ---------------- Side menu ----------------
function setDrawer(open) {
  $("#drawer").hidden = !open; $("#drawerScrim").hidden = !open;
  $("#menuBtn").setAttribute("aria-expanded", String(open));
  if (open) $("#menuMine").focus({ preventScroll: true }); else $("#menuBtn").focus({ preventScroll: true });
}
const fromMenu = (fn) => () => { setDrawer(false); fn(); };
$("#menuBtn").addEventListener("click", () => setDrawer(true));
$("#drawerClose").addEventListener("click", () => setDrawer(false));
$("#drawerScrim").addEventListener("click", () => setDrawer(false));
$("#menuReport").addEventListener("click", fromMenu(() => openFlow("")));
$("#menuMap").addEventListener("click", fromMenu(openMap));
$("#menuStats").addEventListener("click", fromMenu(openStats));
$("#menuMine").addEventListener("click", fromMenu(() => {
  $("#mineForm").reset(); updateKind($("#mineInput"), $("#mineKind")); openSheet("#mineSheet");
}));
// The owner sees the same answer as anyone else; the review link is on that result.
$("#mineInput").addEventListener("input", () => { $("#mineBtn").disabled = !updateKind($("#mineInput"), $("#mineKind")); });
$("#mineForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const value = $("#mineInput").value.trim(), kind = detectKind(value);
  if (!kind) { toast(t("invalid")); return; }
  closeSheet("#mineSheet"); lookupValue(kind, value);
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
    lookupValue(lastChecked.kind, lastChecked.value); // show the number as it now looks to everyone
  } catch (ex) { if (!(ex instanceof LicenceExpired)) toast(ex.status === 409 ? t("d_locked") : ex.message); }
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
  $("#mapView").hidden = false; setPull("peek");
  if (!areaByPin(area)) { openAreaPicker(); return; }
  loadMap();
}
function closeMap() { $("#mapView").hidden = true; }
$("#openMap").addEventListener("click", openMap);
$("#mapBack").addEventListener("click", closeMap);

// The city sheet: peeks over the lower half of the map, pulls up to nearly full screen.
const pull = $("#pull");
function setPull(state) {
  pull.dataset.state = state; pull.style.height = "";
  $("#pullHandle").setAttribute("aria-expanded", String(state === "full"));
}
let drag = null;
$("#pullHead").addEventListener("pointerdown", (e) => {
  drag = { y: e.clientY, h: pull.getBoundingClientRect().height, moved: false, id: e.pointerId };
  $("#pullHead").setPointerCapture(e.pointerId);
});
$("#pullHead").addEventListener("pointermove", (e) => {
  if (!drag || e.pointerId !== drag.id) return;
  const dy = drag.y - e.clientY;
  if (!drag.moved && Math.abs(dy) < 6) return;
  drag.moved = true; pull.classList.add("dragging");
  pull.style.height = `${Math.max(140, Math.min(innerHeight * 0.92, drag.h + dy))}px`;
});
function endDrag() {
  if (!drag) return;
  const { moved, h } = drag; drag = null; pull.classList.remove("dragging");
  if (!moved) { setPull(pull.dataset.state === "full" ? "peek" : "full"); return; }
  const now = pull.getBoundingClientRect().height;
  setPull(now > h + 40 ? "full" : now < h - 40 ? "peek" : pull.dataset.state);
}
$("#pullHead").addEventListener("pointerup", endDrag);
$("#pullHead").addEventListener("pointercancel", endDrag);

function row(tag, html) { const r = document.createElement(tag); r.className = "row"; if (tag === "button") r.type = "button"; r.innerHTML = html; return r; }
function emptyLine(host, text) { const p = document.createElement("p"); p.className = "empty-sm"; p.textContent = text; host.append(p); }

function renderBars(host, items, label, limit = 6) {
  host.replaceChildren();
  if (!items.length) { emptyLine(host, t("no_data")); return; }
  const shown = items.slice(0, limit);
  const rest = items.slice(limit).reduce((s, x) => s + x.count, 0);
  if (rest) shown.push({ _other: true, count: rest });
  const max = Math.max(...shown.map((x) => x.count));
  shown.forEach((x) => {
    const b = document.createElement("div"); b.className = "bar";
    b.innerHTML = `<span class="lbl"></span><span class="val"></span><div class="track"><div class="fill"></div></div>`;
    b.querySelector(".lbl").textContent = x._other ? t("other_types") : label(x);
    b.querySelector(".val").textContent = x.count.toLocaleString("en-IN");
    b.querySelector(".fill").style.width = `${Math.max(2, (100 * x.count) / max)}%`;
    host.append(b);
  });
}

async function lookupValue(kind, value) {
  try { const r = await api(`/lookup?type=${encodeURIComponent(kind)}&value=${encodeURIComponent(value)}`); lastChecked = { kind, value }; showResult(r); }
  catch (ex) { if (!(ex instanceof LicenceExpired)) toast(ex.message); }
}

async function loadMap() {
  const a = areaByPin(area); if (!a) return;
  renderArea();
  let city, alerts;
  try {
    [city, alerts] = await Promise.all([api(`/city?pincode=${a.pincode}&days=7`), api(`/alerts?pincode=${a.pincode}`)]);
  } catch (ex) { if (!(ex instanceof LicenceExpired)) toast(ex.message); return; }
  renderPull(city, alerts.alerts, a);
  drawMap(city, a);
}

function renderPull(city, alerts, a) {
  $("#pullTitle").textContent = t("pull_title", city.city);
  $("#pullSub").textContent = city.counted ? t("pull_sub", city.counted, city.reports - city.counted) : t("pull_empty", city.city);

  const al = $("#alertList"); al.replaceChildren();
  const spikes = city.areas.filter((x) => x.spike && x.pincode !== a.pincode);
  [...alerts.map((x) => alertText(x, a)), ...spikes.map((x) => t("spike_near", x.locality))].forEach((text) => {
    const r = row("div", `<span class="pulse" aria-hidden="true"></span><span class="grow"><strong></strong></span>`);
    r.classList.add("row-alert"); r.querySelector("strong").textContent = text; al.append(r);
  });

  renderBars($("#typeBars"), city.scam_types, (x) => typeInfo(x.scam_type)[lang], 5);

  const kl = $("#knownList"); kl.replaceChildren();
  if (!city.known_scams.length) emptyLine(kl, t("none_known"));
  city.known_scams.forEach((k) => {
    const r = row("button", `<span class="dot sev-CRIT"></span><span class="grow"><strong></strong><small></small></span><svg class="chev" aria-hidden="true"><use href="#i-chevron"/></svg>`);
    r.querySelector("strong").textContent = fmtValue(k.identifier_type, k.display_value);
    r.querySelector("small").textContent = `${typeInfo(k.scam_type)[lang]} · ${t("people_n", k.people)} · ${k.localities.join(", ")}`;
    r.addEventListener("click", () => lookupValue(k.identifier_type, k.display_value));
    kl.append(r);
  });

  const ar = $("#areaRows"); ar.replaceChildren();
  if (!city.areas.length) emptyLine(ar, t("no_clusters"));
  city.areas.forEach((x) => {
    const r = row("button", `<span class="dot sev-${x.severity}"></span><span class="grow"><strong></strong><small></small></span>`);
    r.querySelector("strong").textContent = x.locality;
    r.querySelector("small").textContent = `${typeInfo(x.top_scam_type)[lang]} · ${t("reports_n", x.count)}`;
    if (x.spike) { const s = document.createElement("span"); s.className = "badge"; s.textContent = t("spike_badge"); r.append(s); }
    r.addEventListener("click", () => focusArea(x));
    ar.append(r);
  });

  const fd = $("#feed"); fd.replaceChildren();
  if (!city.recent.length) emptyLine(fd, t("no_data"));
  city.recent.forEach((f) => {
    const open = f.verdict === "KNOWN_SCAM";
    const ch = CHANNELS.find((c) => c.id === f.channel) || CHANNELS[CHANNELS.length - 1];
    const r = row(open ? "button" : "div", `<span class="ch-icon"><svg aria-hidden="true"><use href="#${ch.icon}"/></svg></span><span class="grow"><strong></strong><small></small></span>`);
    r.querySelector("strong").textContent = typeInfo(f.scam_type)[lang];
    r.querySelector("small").textContent = `${fmtValue(f.identifier_type, f.display_value)} · ${f.locality} · ${ago(f.occurred_at)}`;
    if (open) {
      r.insertAdjacentHTML("beforeend", `<svg class="chev" aria-hidden="true"><use href="#i-chevron"/></svg>`);
      r.addEventListener("click", () => lookupValue(f.identifier_type, f.display_value));
    }
    fd.append(r);
  });
}

const markers = {};
let heatRenderer = null;
// White to red, the same scale the legend shows. t in [0, 1].
const HEAT = [[255, 255, 255], [255, 241, 201], [255, 193, 94], [240, 112, 60], [201, 48, 44]];
function heatColor(t) {
  const x = Math.max(0, Math.min(1, t)) * (HEAT.length - 1), i = Math.min(HEAT.length - 2, Math.floor(x)), f = x - i;
  return HEAT[i].map((c, k) => Math.round(c + (HEAT[i + 1][k] - c) * f));
}
async function drawMap(city, a) {
  try {
    const L = await loadLeaflet();
    // The view was hidden a frame ago: wait for layout, or Leaflet sizes its layers at 0x0.
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    if (!map) {
      // Zoom stops at neighbourhood level (15): the map is about areas, never streets or houses.
      map = L.map("map", { zoomControl: false, attributionControl: true, minZoom: 9, maxZoom: 15 });
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 15, attribution: "© OpenStreetMap" }).addTo(map);
      map.setView([a.lat, a.lng], 12);
    }
    map.invalidateSize();
    layer?.remove(); layer = L.layerGroup().addTo(map);
    Object.keys(markers).forEach((k) => delete markers[k]);
    const pts = [[a.lat, a.lng]];
    const max = Math.max(1, ...city.areas.map((c) => c.count));
    // Each area is a soft patch measured in metres, so it covers the same ground at every zoom.
    // A few overlapping discs around the official area centre (placed by the pincode, so they never
    // move) give an irregular, part-of-town shape. Nothing points at one street or one person.
    heatRenderer?.remove(); const renderer = heatRenderer = L.svg({ padding: 0.5 });
    const grads = [];
    city.areas.forEach((c) => {
      const w = c.count / max, [r, g, b] = heatColor(0.3 + 0.7 * w), id = `hg-${c.pincode}`;
      grads.push(`<radialGradient id="${id}"><stop offset="0" stop-color="rgb(${r},${g},${b})" stop-opacity="0.72"/>` +
        `<stop offset="0.5" stop-color="rgb(${r},${g},${b})" stop-opacity="0.42"/><stop offset="1" stop-color="rgb(${r},${g},${b})" stop-opacity="0"/></radialGradient>`);
      let seed = Number(c.pincode) || 1;
      const rnd = () => ((seed = (seed * 9301 + 49297) % 233280) / 233280);
      const size = 650 + 450 * w;
      const blob = [[0, 0, size]];
      for (let k = 0; k < 3; k++) {
        const ang = (k / 3) * 2 * Math.PI + rnd() * 1.5, d = size * (0.35 + rnd() * 0.25);
        blob.push([d * Math.sin(ang), d * Math.cos(ang), size * (0.55 + rnd() * 0.25)]);
      }
      blob.forEach(([dy, dx, rad]) => {
        const lat = c.lat + dy / 111320, lng = c.lng + dx / (111320 * Math.cos(c.lat * Math.PI / 180));
        L.circle([lat, lng], { renderer, radius: rad, stroke: false, fillColor: `url(#${id})`, fillOpacity: 1, interactive: false }).addTo(layer);
      });
      // An invisible, tappable disc on top gives the name and count.
      markers[c.pincode] = L.circleMarker([c.lat, c.lng], { radius: 22, stroke: false, fillOpacity: 0, fillColor: "#000" })
        .bindTooltip(`${c.locality}: ${t("reports_n", c.count)}`, { direction: "top", offset: [0, -8] }).addTo(layer);
      if (c.spike) L.marker([c.lat, c.lng], { icon: L.divIcon({ className: "", html: '<div class="spike-pin"></div>', iconSize: [18, 18] }), interactive: false }).addTo(layer);
      pts.push([c.lat, c.lng]);
    });
    if (renderer._container) {
      const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
      defs.innerHTML = grads.join(""); renderer._container.prepend(defs);
    }
    L.circleMarker([a.lat, a.lng], { radius: 7, color: "#2F5BEA", weight: 3, fillColor: "#fff", fillOpacity: 1, pane: "markerPane" }).addTo(layer);
    // Keep every point above the sheet: pad the bottom by the sheet's height.
    const bottom = pull.getBoundingClientRect().height + 16;
    if (pts.length > 1) map.fitBounds(pts, { paddingTopLeft: [24, 80], paddingBottomRight: [24, bottom], maxZoom: 14 });
    else map.setView([a.lat, a.lng], 13);
  } catch { /* map tiles are a bonus; the sheet already has everything */ }
}
function focusArea(x) {
  setPull("peek");
  if (!map) return;
  const bottom = innerHeight * 0.46;
  map.flyToBounds([[x.lat, x.lng]], { paddingTopLeft: [24, 80], paddingBottomRight: [24, bottom], maxZoom: 14, duration: 0.6 });
  markers[x.pincode]?.openTooltip();
}

// ---------------- Live statistics ----------------
let statsDays = 30;
const RANGES = [7, 30, 90];
function openStats() { $("#statsView").hidden = false; $("#statsView").scrollTop = 0; loadStats(); }
function closeStats() { $("#statsView").hidden = true; }
$("#openStats").addEventListener("click", openStats);
$("#statsBack").addEventListener("click", closeStats);
function renderRange() {
  const seg = $("#statsRange"); seg.replaceChildren();
  RANGES.forEach((d) => {
    const b = document.createElement("button"); b.type = "button"; b.setAttribute("role", "radio");
    b.setAttribute("aria-checked", String(d === statsDays)); b.textContent = t("days_n", d);
    b.addEventListener("click", () => { statsDays = d; loadStats(); });
    seg.append(b);
  });
}
const inr = (n) => "₹" + Math.round(n).toLocaleString("en-IN");

async function loadStats() {
  renderRange();
  let s;
  try { s = await api(`/stats?days=${statsDays}`); } catch (ex) { if (!(ex instanceof LicenceExpired)) toast(ex.message); return; }

  const hero = $("#statsHero");
  hero.innerHTML = `<div class="big"></div><div class="split" aria-hidden="true"></div><div class="legend"></div><p></p>`;
  hero.querySelector(".big").innerHTML = `${s.reports.toLocaleString("en-IN")}<small></small>`;
  hero.querySelector("small").textContent = t("reports_in", statsDays);
  const split = hero.querySelector(".split");
  [[s.counted, "counted"], [s.set_aside, "aside"]].forEach(([n]) => {
    if (!n) return; const i = document.createElement("i"); i.style.flex = String(n); split.append(i);
  });
  if (s.counted && !s.set_aside) split.firstChild.style.borderRadius = "4px";
  if (!s.counted && s.set_aside) { split.firstChild.style.background = "#E3A43A"; split.firstChild.style.borderRadius = "4px"; }
  hero.querySelector(".legend").innerHTML =
    `<span><i class="sw-counted"></i><span></span> <b></b></span><span><i class="sw-aside"></i><span></span> <b></b></span>`;
  const lg = hero.querySelectorAll(".legend > span");
  lg[0].querySelector("span").textContent = t("counted"); lg[0].querySelector("b").textContent = s.counted.toLocaleString("en-IN");
  lg[1].querySelector("span").textContent = t("set_aside"); lg[1].querySelector("b").textContent = s.set_aside.toLocaleString("en-IN");
  hero.querySelector("p").textContent = s.reports ? t("hero_note", s.set_aside.toLocaleString("en-IN")) : t("no_data");

  const k = $("#kpis"); k.replaceChildren();
  [[s.numbers_reported.toLocaleString("en-IN"), t("k_numbers")], [s.known_scam_numbers.toLocaleString("en-IN"), t("k_known")],
   [inr(s.money_lost_inr), t("k_money")], [s.this_week.toLocaleString("en-IN"), `${t("k_week")} · ${t("vs_last", s.last_week)}`]]
    .forEach(([v, l]) => {
      const d = document.createElement("div"); d.className = "kpi"; d.innerHTML = "<b></b><span></span>";
      d.querySelector("b").textContent = v; d.querySelector("span").textContent = l; k.append(d);
    });

  renderDaily(s.daily);
  renderBars($("#statTypes"), s.by_scam_type, (x) => typeInfo(x.scam_type)[lang]);
  renderBars($("#statChannels"), s.by_channel, (x) => (CHANNELS.find((c) => c.id === x.channel) || CHANNELS[CHANNELS.length - 1])[lang]);
  renderBars($("#statCities"), s.by_city, (x) => x.city);
}

// Two stacked series per day (counted, set aside), one y-axis, a 2px gap between segments,
// 4px rounded tops, a legend, and a tap or hover tooltip with both numbers.
function renderDaily(days) {
  const host = $("#daily"); host.replaceChildren();
  $("#dailyLegend").innerHTML = `<span><i class="sw-counted"></i></span><span><i class="sw-aside"></i></span>`;
  const lg = $("#dailyLegend").children;
  lg[0].append(t("counted")); lg[1].append(t("set_aside"));
  const W = Math.max(280, host.clientWidth || 320), H = 150, left = 26, bottom = 20, top = 8;
  const max = Math.max(4, ...days.map((d) => d.reports));
  const step = Math.ceil(max / 4), yMax = step * 4;
  const y = (v) => top + (H - top - bottom) * (1 - v / yMax);
  const slot = (W - left) / days.length, bw = Math.min(24, slot * 0.62);
  const loc = lang === "hi" ? "hi-IN" : "en-IN";
  let svg = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${t("last14")}">`;
  for (let v = 0; v <= yMax; v += step) svg += `<line class="grid" x1="${left}" x2="${W}" y1="${y(v)}" y2="${y(v)}"/><text class="tick" x="${left - 6}" y="${y(v) + 4}" text-anchor="end">${v}</text>`;
  days.forEach((d, i) => {
    const x = left + slot * i + (slot - bw) / 2, aside = d.reports - d.counted;
    const yc = y(d.counted), ya = y(d.counted + aside) ;
    svg += `<g class="col" data-i="${i}">`;
    if (d.counted) svg += `<path fill="#2F5BEA" d="${barPath(x, yc, bw, y(0) - yc, !aside)}"/>`;
    if (aside) svg += `<path fill="#E3A43A" d="${barPath(x, ya, bw, Math.max(1, yc - ya - (d.counted ? 2 : 0)), true)}"/>`;
    svg += `<rect class="hit" x="${left + slot * i}" y="${top}" width="${slot}" height="${H - top}"/></g>`;
    if ((days.length - 1 - i) % 4 === 0) {
      const label = new Date(d.date + "T12:00:00").toLocaleDateString(loc, { day: "numeric", month: "short" });
      svg += `<text class="tick" x="${x + bw / 2}" y="${H - 4}" text-anchor="middle">${label}</text>`;
    }
  });
  host.innerHTML = svg + "</svg>";
  const tip = document.createElement("div"); tip.className = "tip"; tip.hidden = true; host.append(tip);
  const show = (g) => {
    host.querySelectorAll(".col.on").forEach((c) => c.classList.remove("on"));
    if (!g) { tip.hidden = true; return; }
    const d = days[Number(g.dataset.i)]; g.classList.add("on");
    tip.innerHTML = "<b></b><span></span><br><span></span>";
    tip.querySelector("b").textContent = new Date(d.date + "T12:00:00").toLocaleDateString(loc, { weekday: "short", day: "numeric", month: "short" });
    const sp = tip.querySelectorAll("span");
    sp[0].textContent = `${t("counted")}: ${d.counted}`; sp[1].textContent = `${t("set_aside")}: ${d.reports - d.counted}`;
    const box = g.querySelector(".hit").getBoundingClientRect(), hb = host.getBoundingClientRect();
    tip.style.left = `${Math.min(hb.width - 60, Math.max(60, box.left - hb.left + box.width / 2))}px`;
    tip.style.top = `${Math.max(0, y(d.reports) - 6) * (hb.width / W)}px`; tip.hidden = false;
  };
  host.querySelectorAll(".col").forEach((g) => {
    g.addEventListener("pointerenter", () => show(g));
    g.addEventListener("click", () => show(g));
  });
  host.addEventListener("pointerleave", () => show(null));
}
function barPath(x, y0, w, h, roundTop) {
  if (h <= 0) return "";
  const r = roundTop ? Math.min(4, w / 2, h) : 0;
  return `M${x},${y0 + h}V${y0 + r}Q${x},${y0} ${x + r},${y0}H${x + w - r}Q${x + w},${y0} ${x + w},${y0 + r}V${y0 + h}Z`;
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
