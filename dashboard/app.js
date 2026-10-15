/* ParaFOMO Panel — istemci. Veri: GET /api/state; yazma: board.py uçları (X-Dash başlığı şart). */
(() => {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const TR = "tr-TR";
  const TARGET_WEEK = 7000; // 1000 ziyaretçi/gün hedefi → 7 günlük kayan pencere
  let S = null;             // son durum
  const openRows = new Set(JSON.parse(store("open") || "[]"));

  function store(k, v) {
    try {
      if (v === undefined) return localStorage.getItem("pf-dash-" + k);
      localStorage.setItem("pf-dash-" + k, v);
    } catch (e) { return null; }
  }

  // ---------- yardımcılar ----------
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const num = (n) => (n == null || n === "" ? "—" : Number(n).toLocaleString(TR));
  const money = (n) => (n == null ? "—" : "$" + Number(n).toLocaleString(TR, { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
  const dshort = (iso) => new Date(iso.length === 10 ? iso + "T12:00:00Z" : iso).toLocaleDateString(TR, { day: "numeric", month: "short" });
  const tTR = (iso) => new Date(iso).toLocaleTimeString(TR, { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Istanbul" });
  function ago(iso) {
    if (!iso) return "—";
    const m = (Date.now() - new Date(iso).getTime()) / 60000;
    if (m < 1) return "az önce";
    if (m < 60) return Math.round(m) + " dk önce";
    if (m < 48 * 60) return Math.round(m / 60) + " sa önce";
    return Math.round(m / 1440) + " gün önce";
  }
  const ICON = {
    check: '<svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    x: '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>',
    clock: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 7.5V12l3 2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    up: '<svg viewBox="0 0 24 24"><path d="M12 19V6m-6 6 6-6 6 6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    warn: '<svg viewBox="0 0 24 24"><path d="M12 4 2.8 20h18.4L12 4z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M12 10v4.5M12 17.2v.1" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>',
    chev: '<svg class="chev" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  };
  const STATUS_ICON = { OK: ICON.check, success: ICON.check, UYARI: ICON.warn, budget: ICON.warn, HATA: ICON.x, "GECİKTİ": ICON.clock };
  const stPill = (s, label) => `<span class="st ${esc(s)}">${STATUS_ICON[s] || ""}${esc(label || s)}</span>`;

  // ---------- küçük markdown (ajanın rapor/plan biçimi: başlık, liste, tablo, kalın, kod, link) ----------
  function inline(s) {
    let t = esc(s);
    const codes = [];
    t = t.replace(/`([^`]+)`/g, (_, c) => { codes.push(c); return "\u0000" + (codes.length - 1) + "\u0000"; });
    t = t.replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    t = t.replace(/(^|[\s(])(https?:\/\/[^\s<)]+[^\s<).,;:])/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');
    t = t.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    t = t.replace(/~~(.+?)~~/g, "<s>$1</s>");
    t = t.replace(/(^|[\s(])_([^_]+?)_(?=[\s).,;:]|$)/g, "$1<em>$2</em>");
    return t.replace(/\u0000(\d+)\u0000/g, (_, i) => "<code>" + codes[i] + "</code>");
  }
  function md(src) {
    const lines = String(src || "").replace(/\r/g, "").split("\n");
    let html = "", i = 0;
    const isTable = (l) => /^\s*\|.*\|\s*$/.test(l);
    while (i < lines.length) {
      const l = lines[i];
      if (!l.trim()) { i++; continue; }
      let m;
      if ((m = l.match(/^(#{1,4})\s+(.*)/))) { html += `<h${m[1].length}>${inline(m[2])}</h${m[1].length}>`; i++; continue; }
      if (isTable(l) && i + 1 < lines.length && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1])) {
        const row = (r) => r.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
        html += "<table><thead><tr>" + row(l).map((c) => `<th>${inline(c)}</th>`).join("") + "</tr></thead><tbody>";
        i += 2;
        while (i < lines.length && isTable(lines[i])) { html += "<tr>" + row(lines[i]).map((c) => `<td>${inline(c)}</td>`).join("") + "</tr>"; i++; }
        html += "</tbody></table>"; continue;
      }
      if (/^\s*([-*]|\d+\.)\s+/.test(l)) {
        // iç içe listeler: girinti derinliğine göre
        // önce öğeleri topla (devam satırları dahil) → sonra satır aşan **kalın** da doğru işlenir
        const items = [];
        while (i < lines.length && (/^\s*([-*]|\d+\.)\s+/.test(lines[i]) || (/^\s{2,}\S/.test(lines[i]) && items.length))) {
          const mm = lines[i].match(/^(\s*)([-*]|\d+\.)\s+(.*)$/);
          if (mm) items.push({ depth: Math.floor(mm[1].replace(/\t/g, "  ").length / 2), tag: /\d/.test(mm[2]) ? "ol" : "ul", text: mm[3] });
          else items[items.length - 1].text += " " + lines[i].trim();
          i++;
        }
        const stack = [];
        for (const it of items) {
          while (stack.length > it.depth + 1) html += `</li></${stack.pop()}>`;
          if (stack.length === it.depth + 1) html += "</li>";
          while (stack.length < it.depth + 1) { html += `<${it.tag}>`; stack.push(it.tag); }
          html += "<li>" + inline(it.text.replace(/^\[( |x|X|-)\]\s+/, (_, c) => (c === " " ? "☐ " : c === "-" ? "⊘ " : "☑ ")));
        }
        while (stack.length) html += `</li></${stack.pop()}>`;
        continue;
      }
      let para = [];
      while (i < lines.length && lines[i].trim() && !/^(#{1,4})\s/.test(lines[i]) && !/^\s*([-*]|\d+\.)\s+/.test(lines[i]) && !isTable(lines[i])) { para.push(lines[i].trim()); i++; }
      html += `<p>${inline(para.join(" "))}</p>`;
    }
    return html;
  }

  // ---------- ağ ----------
  async function api(path, opt = {}) {
    const r = await fetch(path, {
      ...opt,
      headers: { "Content-Type": "application/json", "X-Dash": "1", ...(opt.headers || {}) },
      body: opt.body ? JSON.stringify(opt.body) : undefined,
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.detail || r.statusText);
    return j;
  }
  function toast(msg, err) {
    const t = $("#toast");
    t.textContent = msg; t.className = "toast on" + (err ? " err" : "");
    clearTimeout(toast._t); toast._t = setTimeout(() => (t.className = "toast"), 2400);
  }

  async function load(quiet) {
    const b = $("#refresh");
    b.classList.add("spin");
    try {
      S = await api("/api/state");
      renderAll();
    } catch (e) {
      if (!quiet) toast("Yüklenemedi: " + e.message, true);
    } finally {
      b.classList.remove("spin");
    }
  }

  // ---------- üst bant ----------
  function renderPulse() {
    const c = S.counts, k = S.kpi[S.kpi.length - 1] || {};
    const probs = problems();
    const st = S.agent.status || {};
    const pills = [
      { tab: "gorevler", cls: c.user_todo ? "hot" : "ok", html: `Senden <b>${c.user_todo}</b> iş` },
      { tab: "gorevler", cls: "", html: `Kuyruk <b>${c.agent_open}</b> açık` },
      { tab: "metrik", cls: "", html: `Ziyaretçi 7g <b>${num(k.real_7d)}</b>` },
      { tab: "uretim", cls: probs.length ? "bad" : "ok", html: probs.length ? `<b>${probs.length}</b> üretim sorunu` : "Üretim sorunsuz" },
      { tab: "ajan", cls: st.outcome === "success" ? "ok" : "bad", html: `Ajan ${ago(st.ended || st.started)}` },
    ];
    $("#pulse").innerHTML = pills.map((p) => `<button class="pill ${p.cls}" data-go="${p.tab}"><span class="dot"></span>${p.html}</button>`).join("");
    $("#b-gorevler").textContent = c.user_todo + c.inbox_new || "";
    const bu = $("#b-uretim");
    bu.textContent = probs.length || ""; bu.className = "badge bad";
    $("#stamp").textContent = "Güncellendi " + tTR(S.now) + " · " + new Date(S.now).toLocaleDateString(TR, { weekday: "long", day: "numeric", month: "long", timeZone: "Europe/Istanbul" });
  }
  function problems() {
    const h = S.health, p = [];
    for (const r of [...h.pipelines, h.agent]) if (r.status === "GECİKTİ" || r.status === "HATA") p.push(r.name);
    if (h.llm.state !== "ok") p.push("Claude");
    if (h.site !== 200) p.push("site"); if (h.api !== 200) p.push("api");
    if (h.disk_pct >= 88) p.push("disk");
    return p.concat(h.stale || []);
  }

  // ---------- GÖREVLER ----------
  function renderGorevler() {
    const B = S.board, wk = B.week;
    const open = wk.tasks.filter((t) => t.state === "open");
    const groups = {};
    for (const t of open) (groups[t.section] = groups[t.section] || []).push(t);

    const userCards = B.user_tasks.length ? B.user_tasks.map(userTask).join("") :
      `<div class="empty">Şu an senden beklenen iş yok.</div>`;

    const queue = Object.entries(groups).map(([sec, ts]) =>
      `<div class="qgroup">${esc(sec.replace(/\s*\(.*\)\s*$/, ""))} · ${ts.length}</div>` + ts.map(qRow).join("")).join("") ||
      `<div class="empty">Kuyruk boş — haftalık koşu yeni plan yazacak.</div>`;

    const done = wk.tasks.filter((t) => t.state !== "open");
    const doneHtml = done.map((t) => `<li>${t.state === "done" ? `<span class="tick">${ICON.check}</span>` : `<span class="tick x">${ICON.x}</span>`}
        <div><b>${esc(t.id)}</b> ${esc(t.title)}<span class="res">${inline(t.result || (t.state === "dropped" ? "iptal / park" : ""))}</span></div></li>`)
      .concat(wk.log_done.map((l) => `<li><span class="tick">${ICON.check}</span><div>${inline(l)}</div></li>`))
      .concat(B.user_closed.map((u) => `<li><span class="tick">${ICON.check}</span><div>${esc(u.title)} <span class="res">Senin işin · ${u.status === "verified" ? "ajan doğruladı" : "yapıldı"}${u.agent_note ? " — " + inline(u.agent_note) : ""}</span></div></li>`))
      .join("");

    const inbox = B.inbox.map((i) => `<div class="inbox-item">
        <div class="row"><span class="small muted">${esc(i.id)} · ${dshort(i.created)}</span>
          <span style="display:flex;gap:6px;align-items:center"><span class="chip ${esc(i.status)}">${esc(S.inbox_states[i.status] || i.status)}</span>
          ${i.status === "new" ? `<button class="btn ghost" data-unsend="${esc(i.id)}">Geri çek</button>` : ""}</span></div>
        <div>${esc(i.text)}</div>${i.agent_note ? `<div class="callout"><b>Ajan:</b> ${inline(i.agent_note)}</div>` : ""}</div>`).join("");

    const log = B.log.slice(0, 12).map((l) => `<li><span class="muted">${dshort(l.ts)} ${tTR(l.ts)}</span><span class="who">${l.who === "ajan" ? "Ajan" : "Sen"}</span><span>${esc(l.what)}</span></li>`).join("");

    $("#v-gorevler").innerHTML = `<div class="grid2 split">
      <div class="col">
        <div class="sec o1"><div class="sec-h"><h2>Senden beklenenler</h2><span class="meta">${B.user_tasks.length} iş</span></div>
          <p class="lead">"Yaptım" dediğinde ajan bir sonraki gece sunucuda doğrular; eksik varsa buraya yazar.</p>
          <div class="card">${userCards}</div>
          ${B.user_notes ? `<details class="small muted" style="margin:8px 4px 0"><summary>Kalıcı notlar (${B.user_notes.split("\n").filter((x) => x.trim()).length} satır)</summary><div class="md" style="margin-top:6px">${md(B.user_notes)}</div></details>` : ""}
        </div>
        <div class="sec o3"><div class="sec-h"><h2>Ajanın kuyruğu</h2><span class="meta">${esc(wk.title.replace("Hafta planı — ", ""))}</span></div>
          <p class="lead">Ajan her gece en üstteki açık görevi alır. <b>Onayla</b> öne alır, <b>Reddet</b> iptal eder; karar vermezsen sırası gelince yapılır. Not alanı ajana talimattır.</p>
          <div class="card">${queue}</div>
        </div>
        <div class="sec o4"><div class="sec-h"><h2>Bu hafta biten</h2><span class="meta">${done.length + wk.log_done.length + B.user_closed.length}</span></div>
          <div class="card"><ul class="done-list">${doneHtml || '<li><span></span><span class="muted">Henüz yok</span></li>'}</ul></div>
        </div>
      </div>
      <div class="col">
        <div class="sec o2"><div class="sec-h"><h2>Ajana görev ver</h2></div>
          <div class="card"><div class="compose">
            <textarea class="note" id="inbox-text" placeholder="Ör. “Emekli bayram ikramiyesi sayfasını Kasım'dan önce açalım” — ajan sonraki koşuda değerlendirip kuyruğa ekler." maxlength="2000"></textarea>
            <div class="actions" style="justify-content:space-between"><span class="small muted">Gece 06:00 TSİ koşusunda okunur.</span><button class="btn" id="inbox-send">Gönder</button></div>
          </div>${inbox}</div>
        </div>
        <div class="sec o5"><div class="sec-h"><h2>Son hareketler</h2></div>
          <div class="card">${log ? `<ul class="log">${log}</ul>` : '<div class="empty">Henüz hareket yok.</div>'}</div>
        </div>
      </div>
    </div>`;
  }

  function userTask(u) {
    const sts = [["todo", "Yapılacak", ""], ["done", "Yaptım", "ok"], ["later", "Sonraya", "info"]];
    return `<div class="utask s-${esc(u.status)}" data-user="${esc(u.slug)}">
      <div class="utask-title"><span class="no">${u.no}.</span>${inline(u.title)}</div>
      ${u.body ? `<div class="md small clamp ${openRows.has("u:" + u.slug) ? "full" : ""}">${md(u.body)}</div>
        <button class="more" data-more="u:${esc(u.slug)}">${openRows.has("u:" + u.slug) ? "Kısalt" : "Tamamını göster"}</button>` : ""}
      ${u.agent_note ? `<div class="callout ${u.status === "todo" ? "bad" : ""}"><b>Ajan:</b> ${inline(u.agent_note)}</div>` : ""}
      ${u.status === "done" ? `<div class="callout"><b>Bekliyor:</b> ajan bir sonraki koşuda doğrulayacak.</div>` : ""}
      <div class="actions"><div class="seg" role="group" aria-label="Durum">${sts.map(([k, l, c]) =>
        `<button class="${c}" data-ustatus="${k}" aria-pressed="${u.status === k}">${k === "done" ? ICON.check : ""}${l}</button>`).join("")}</div></div>
      <div class="note-wrap"><textarea class="note" rows="1" data-unote placeholder="Ajana not (isteğe bağlı)">${esc(u.note)}</textarea><span class="saved">kaydedildi</span></div>
    </div>`;
  }

  function qRow(t) {
    const isOpen = openRows.has(t.key);
    const decLbl = { pending: "Karar yok", approved: "Onaylı", rejected: "Reddedildi" }[t.decision];
    const decIco = { pending: "", approved: ICON.check, rejected: ICON.x }[t.decision];
    return `<div class="qrow ${t.decision} ${isOpen ? "open" : ""}" data-key="${esc(t.key)}">
      <div class="qhead" data-toggle>
        <span class="qid">${esc(t.id)}</span>
        <div class="qtitle">${inline(t.title)}${t.decision === "approved" ? '<span class="qnext">ÖNE ALINDI</span>' : ""}
          ${t.tag ? `<span class="qtag">${esc(t.tag)}</span>` : ""}
          ${t.agent_status ? `<span class="astat">Ajan: ${inline(t.agent_status)}</span>` : ""}</div>
        <span style="display:flex;align-items:center;gap:6px">${t.decision !== "pending" || t.note ? `<span class="dec ${t.decision}">${decIco}${decLbl}${t.note ? " · not" : ""}</span>` : ""}${ICON.chev}</span>
      </div>
      ${isOpen ? `<div class="qbody">
        <div class="md">${md(t.body.replace(/^→.*?(?= — \*\*)/, ""))}</div>
        <div class="actions"><div class="seg" role="group" aria-label="Karar">
          <button class="ok" data-dec="approved" aria-pressed="${t.decision === "approved"}">${ICON.check}Onayla · öne al</button>
          <button data-dec="pending" aria-pressed="${t.decision === "pending"}">Karar yok</button>
          <button class="bad" data-dec="rejected" aria-pressed="${t.decision === "rejected"}">${ICON.x}Reddet</button>
        </div></div>
        <div class="note-wrap"><textarea class="note" rows="2" data-qnote placeholder="Ajana talimat — ör. “bunu yaparken X'i de ekle” (ajan uyar)">${esc(t.note)}</textarea><span class="saved">kaydedildi</span></div>
        ${t.agent_status ? `<div class="small muted" style="margin-top:8px">Ajan durumu ${ago(t.agent_status_ts)} yazıldı.</div>` : ""}
      </div>` : ""}
    </div>`;
  }

  // ---------- METRİKLER ----------
  function kpiAt(daysBack) {
    const rows = S.kpi; if (!rows.length) return null;
    const last = new Date(rows[rows.length - 1].date + "T00:00:00Z");
    const want = new Date(last.getTime() - daysBack * 86400000).toISOString().slice(0, 10);
    return rows.find((r) => r.date === want) || null;
  }
  function delta(key) {
    const a = S.kpi[S.kpi.length - 1], b = kpiAt(7);
    if (!a || !b || a[key] == null || b[key] == null) return '<span class="delta flat">7g önce veri yok</span>';
    const d = a[key] - b[key];
    if (!d) return '<span class="delta flat">7 güne göre değişmedi</span>';
    return `<span class="delta ${d > 0 ? "up" : "down"}">${d > 0 ? "▲" : "▼"} ${num(Math.abs(d))} <span class="muted" style="font-weight:400">/ 7 gün</span></span>`;
  }

  function renderMetrik() {
    const k = S.kpi[S.kpi.length - 1] || {};
    const pct = Math.min(100, ((k.real_7d || 0) / TARGET_WEEK) * 100);
    const tiles = [
      ["organic_search_7d", "Organik arama ziyaretçisi · 7g"], ["gsc_clicks_7d", "Google tıklaması · 7g"],
      ["gsc_impr_7d", "Google gösterimi · 7g"], ["ai_assistant_28d", "AI asistan ziyaretçisi · 28g"],
      ["yt_subs", "YouTube abone"], ["yt_views", "YouTube toplam izlenme"],
    ];
    const bets = S.bets.map((b) => {
      const left = b.review ? Math.round((new Date(b.review + "T00:00:00Z") - Date.now()) / 86400000) : null;
      const due = left == null ? "" : left < 0 ? `<span class="due over">değerlendirme ${-left} gün gecikti</span>` :
        `<span class="due ${left <= 7 ? "soon" : ""}">${left} gün kaldı · ${dshort(b.review)}</span>`;
      return `<div class="bet"><div class="bet-h"><span class="bet-t">${esc(b.title)}</span>${due}</div>
        <div class="bet-id">${esc(b.id)} · ${esc(b.lever || "")}</div>
        <dl><dt>Metrik</dt><dd>${inline(b.metric)}</dd><dt>Başlangıç</dt><dd>${inline(String(b.baseline))}</dd><dt>Hedef</dt><dd>${inline(String(b.target))}</dd>
        ${(b.notes || []).length ? `<dt>Son not</dt><dd>${inline(b.notes[b.notes.length - 1])}</dd>` : ""}</dl></div>`;
    }).join("") || '<div class="empty">Aktif bahis yok.</div>';
    const closed = S.bets_closed.map((b) => `<li><span class="tick ${b.status === "won" ? "" : "x"}">${b.status === "won" ? ICON.check : ICON.x}</span><div>${esc(b.title)} <span class="res">${esc(b.status)} · ${inline(b.result || "")}</span></div></li>`).join("");

    $("#v-metrik").innerHTML = `
      <div class="sec"><div class="card hero">
        <div class="hero-top"><div><div class="hero-lbl">Gerçek ziyaretçi, son 7 gün (Direct hariç)</div>
          <div class="hero-num">${num(k.real_7d)}<small>/ ${num(TARGET_WEEK)} hedef</small></div></div>${delta("real_7d")}</div>
        <div class="track" role="img" aria-label="Hedefin yüzde ${pct.toFixed(1)}'i"><i style="width:${pct}%"></i></div>
        <div class="hero-foot"><span>Hedefin %${pct.toLocaleString(TR, { maximumFractionDigits: 1 })}'i</span><span>28 günde ${num(k.real_28d)} · ${k.date ? dshort(k.date) : ""}</span></div>
      </div></div>
      <div class="sec"><div class="tiles">${tiles.map(([key, lbl]) => `<div class="card tile"><div class="tile-lbl">${lbl}</div><div class="tile-num">${num(k[key])}</div>${delta(key)}</div>`).join("")}</div></div>
      <div class="sec"><div class="sec-h"><h2>Trend</h2><span class="meta">${S.kpi.length} gün · kayan pencereler</span></div>
        <div class="charts">
          ${chartCard("real_7d", "Gerçek ziyaretçi", "7 günlük kayan toplam")}
          ${chartCard("gsc_clicks_7d", "Google tıklaması", "7 günlük kayan toplam")}
          ${chartCard("yt_subs", "YouTube abone", "toplam")}
        </div>
        <button class="btn ghost tbl-toggle" id="kpi-tbl-btn">Tablo olarak gör</button>
        <div class="card" id="kpi-tbl" hidden style="margin-top:10px"><div class="scroll">${kpiTable()}</div></div>
      </div>
      <div class="grid2">
        <div class="sec"><div class="sec-h"><h2>Aktif bahisler</h2><span class="meta">${S.bets.length} / 3</span></div><div class="card">${bets}</div>
          ${closed ? `<div class="card" style="margin-top:10px"><ul class="done-list">${closed}</ul></div>` : ""}</div>
        <div class="sec"><div class="sec-h"><h2>Haftanın durumu</h2><span class="meta">ajanın teşhisi</span></div>
          <div class="card pad"><div class="md">${md(S.board.week.status_md)}</div></div></div>
      </div>`;
    drawCharts();
  }
  function kpiTable() {
    const cols = [["date", "Tarih"], ["real_7d", "Ziyaretçi 7g"], ["organic_search_7d", "Organik 7g"], ["gsc_clicks_7d", "GSC tık 7g"], ["gsc_impr_7d", "GSC gös. 7g"], ["yt_subs", "YT abone"], ["yt_views", "YT izlenme"]];
    return `<table class="data"><thead><tr>${cols.map(([, l], i) => `<th class="${i ? "n" : ""}">${l}</th>`).join("")}</tr></thead><tbody>${
      S.kpi.slice().reverse().map((r) => `<tr>${cols.map(([c], i) => `<td class="${i ? "n" : ""}">${i ? num(r[c]) : dshort(r[c])}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  }
  const chartCard = (key, title, sub) => `<div class="card chart" data-chart="${key}"><h3>${title}</h3><div class="sub">${sub}</div><svg role="img" aria-label="${title} trendi"></svg><div class="tip"></div></div>`;

  function nice(max) {
    if (max <= 0) return 1;
    const p = Math.pow(10, Math.floor(Math.log10(max)));
    for (const m of [1, 2, 2.5, 5, 10]) if (m * p >= max) return m * p;
    return 10 * p;
  }
  function drawCharts() {
    document.querySelectorAll("[data-chart]").forEach((card) => {
      const key = card.dataset.chart;
      const pts = S.kpi.filter((r) => r[key] != null).map((r) => ({ d: r.date, v: +r[key] }));
      const svg = $("svg", card), tip = $(".tip", card);
      const W = svg.clientWidth || 300, H = 150, L = 34, R = 34, T = 10, Bm = 22;
      if (pts.length < 2) { svg.innerHTML = `<text x="${W / 2}" y="${H / 2}" text-anchor="middle" class="axis" fill="currentColor">Yeterli veri yok</text>`; return; }
      const max = nice(Math.max(...pts.map((p) => p.v)) * 1.08);
      const x = (i) => L + (i * (W - L - R)) / (pts.length - 1);
      const y = (v) => T + (1 - v / max) * (H - T - Bm);
      const ticks = [0, max / 2, max];
      const path = pts.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.v).toFixed(1)}`).join("");
      const last = pts[pts.length - 1];
      svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
      svg.innerHTML = `
        <g class="grid">${ticks.map((t) => `<line x1="${L}" x2="${W - R}" y1="${y(t)}" y2="${y(t)}"/>`).join("")}</g>
        <g class="axis">${ticks.map((t) => `<text x="${L - 6}" y="${y(t) + 4}" text-anchor="end">${num(t)}</text>`).join("")}
          <text x="${L}" y="${H - 4}">${dshort(pts[0].d)}</text><text x="${W - R}" y="${H - 4}" text-anchor="end">${dshort(last.d)}</text></g>
        <path class="area" d="${path}L${x(pts.length - 1)},${y(0)}L${x(0)},${y(0)}Z"/>
        <path class="ln" d="${path}"/>
        <circle class="end" cx="${x(pts.length - 1)}" cy="${y(last.v)}" r="4.5"/>
        <text class="endlbl" x="${x(pts.length - 1) + 7}" y="${y(last.v) + 4}">${num(last.v)}</text>
        <line class="xh" y1="${T}" y2="${H - Bm}" visibility="hidden"/><circle class="hdot" r="5" visibility="hidden"/>
        <rect x="${L}" y="0" width="${W - L - R}" height="${H}" fill="transparent" data-hit/>`;
      const xh = $(".xh", svg), hd = $(".hdot", svg), hit = $("[data-hit]", svg);
      const move = (ev) => {
        const r = svg.getBoundingClientRect();
        const px = ((ev.clientX - r.left) / r.width) * W;
        const i = Math.max(0, Math.min(pts.length - 1, Math.round(((px - L) / (W - L - R)) * (pts.length - 1))));
        const p = pts[i];
        xh.setAttribute("x1", x(i)); xh.setAttribute("x2", x(i)); xh.setAttribute("visibility", "visible");
        hd.setAttribute("cx", x(i)); hd.setAttribute("cy", y(p.v)); hd.setAttribute("visibility", "visible");
        tip.innerHTML = `${dshort(p.d)} · <b>${num(p.v)}</b>`;
        const cr = card.getBoundingClientRect();
        tip.style.left = r.left - cr.left + Math.max(50, Math.min(r.width - 50, (x(i) / W) * r.width)) + "px";
        tip.style.top = r.top - cr.top + (y(p.v) / H) * r.height - 10 + "px";
        tip.style.opacity = 1;
      };
      hit.addEventListener("pointermove", move);
      hit.addEventListener("pointerdown", move);
      hit.addEventListener("pointerleave", () => { xh.setAttribute("visibility", "hidden"); hd.setAttribute("visibility", "hidden"); tip.style.opacity = 0; });
    });
  }

  // ---------- AJAN ----------
  function renderAjan() {
    const A = S.agent, st = A.status || {};
    const fresh = A.report && st.started && new Date(A.report_ts) >= new Date(st.started);
    const week = A.runs.filter((r) => Date.now() - new Date(r.started) < 7 * 86400000);
    const cost7 = week.reduce((s, r) => s + (+r.cost || 0), 0);
    const rows = A.runs.map((r) => `<tr><td>${dshort(r.started)} ${tTR(r.started)}</td><td>${r.mode === "weekly" ? "Haftalık" : "Günlük"}</td>
      <td>${stPill(r.outcome, { success: "Başarılı", budget: "Bütçe", auth: "Giriş yok" }[r.outcome] || r.outcome)}</td>
      <td class="n">${num(r.minutes)} dk</td><td class="n">${num(r.turns)}</td><td class="n">${money(r.cost)}</td>
      <td class="small">${esc((r.message || "").replace(/[#*_`]/g, "").slice(0, 120))}…</td></tr>`).join("");
    $("#v-ajan").innerHTML = `
      <div class="sec"><div class="sec-h"><h2>Son koşu raporu</h2><span class="meta">${fresh ? "bu koşuda yazıldı" : "rapor bu koşudan eski"}</span></div>
        <div class="card">
          <div class="run-top">
            <div class="kv"><div class="k">Koşu</div><div class="v">${st.mode === "weekly" ? "Haftalık plan" : "Günlük"}</div></div>
            <div class="kv"><div class="k">Sonuç</div><div class="v">${stPill(st.outcome || "?", { success: "Başarılı" }[st.outcome])}</div></div>
            <div class="kv"><div class="k">Bitti</div><div class="v">${st.ended ? dshort(st.ended) + " " + tTR(st.ended) : "—"}</div></div>
            <div class="kv"><div class="k">Süre · tur</div><div class="v">${num(st.minutes)} dk · ${num(st.turns)}</div></div>
            <div class="kv"><div class="k">Maliyet (API-eşd.) · 7g</div><div class="v">${money(st.cost)} · ${money(cost7)}</div></div>
          </div>
          <div class="report md">${fresh ? md(A.report) : md(st.message || "Rapor yok.")}</div>
          ${(st.denied || []).length ? `<details class="denied"><summary>İzin listesi dışında kalan ${st.denied.length} komut</summary>${st.denied.map((d) => `<code>${esc(d)}</code>`).join("")}</details>` : ""}
        </div></div>
      <div class="sec"><div class="sec-h"><h2>Koşu geçmişi</h2><span class="meta">son ${A.runs.length} · 7 günde ${week.length} koşu</span></div>
        <div class="card"><div class="scroll"><table class="data"><thead><tr><th>Başladı (TSİ)</th><th>Mod</th><th>Sonuç</th><th class="n">Süre</th><th class="n">Tur</th><th class="n">Maliyet</th><th>Özet</th></tr></thead><tbody>${rows}</tbody></table></div></div></div>`;
  }

  // ---------- ÜRETİM ----------
  function renderUretim() {
    const h = S.health;
    const LBL = { OK: "Çalışıyor", UYARI: "Uyarı", "GECİKTİ": "Gecikti", HATA: "Hata", "BİLİNMİYOR": "Bilinmiyor" };
    const pipes = [...h.pipelines, h.agent].map((r) => `<div class="pipe"><span class="pipe-n">${esc(r.name)}</span>${stPill(r.status, LBL[r.status])}
      <span class="pipe-m">Son başarı ${esc(r.age)} · ${esc(r.note)}</span>${r.error && r.status !== "OK" ? `<span class="pipe-e">${esc(r.error.slice(0, 200))}</span>` : ""}</div>`).join("");
    const g = h.git;
    const sys = [
      ["Claude (LLM)", h.llm.state === "ok" ? stPill("OK", "Hazır") : stPill("HATA", h.llm.state + (h.llm.until ? " → " + tTR(h.llm.until) : ""))],
      ["Canlı site", h.site === 200 ? stPill("OK", "200") : stPill("HATA", String(h.site))],
      ["Portföy API", h.api === 200 ? stPill("OK", "200") : stPill("HATA", String(h.api))],
      ["Disk", `${h.disk_pct >= 88 ? stPill("UYARI", "%" + h.disk_pct) : "%" + h.disk_pct + " dolu"} <span class="muted small">· ${h.disk_free_gb} GB boş</span>`],
      ["Git", `${esc(g.branch)}${g.rebasing ? " · " + stPill("HATA", "yarım rebase") : ""} <span class="muted small">· ${g.dirty ? g.dirty + " kirli" : "temiz"}${g.ahead ? " · " + g.ahead + " push bekliyor" : ""}</span>`],
      ["Veri tazeliği", (h.stale || []).length ? stPill("HATA", h.stale.length + " bayat") : stPill("OK", "Güncel")],
    ].map(([k, v]) => `<div><div class="k">${k}</div><div class="v">${v}</div></div>`).join("");
    const stale = (h.stale || []).map((s) => `<li>${inline(s)}</li>`).join("");

    const showBg = store("bg") === "1";
    const nowUtc = new Date(S.now).toISOString().slice(11, 16);
    const items = [];
    for (const r of S.schedule) {
      if (r.bg && !showBg) continue;
      const times = r.utc.length > 8 ? [r.utc[0]] : r.utc;
      for (const t of times) items.push({ t, label: r.label + (r.utc.length > 8 ? ` (gün boyu ${r.utc.length} kez)` : ""), bg: r.bg });
    }
    items.sort((a, b) => trMin(a.t) - trMin(b.t));
    let nowPlaced = false, li = "";
    for (const it of items) {
      const past = trMin(it.t) < trMin(nowUtc);
      if (!nowPlaced && !past) { li += `<li class="now-line"><span>ŞİMDİ ${tTR(S.now)}</span></li>`; nowPlaced = true; }
      li += `<li class="${past ? "past" : ""} ${it.bg ? "bg" : ""}"><span class="t">${utcToTr(it.t)}</span><span class="rail"></span><span>${esc(it.label)}</span></li>`;
    }
    if (!nowPlaced) li += `<li class="now-line"><span>ŞİMDİ ${tTR(S.now)}</span></li>`;

    $("#v-uretim").innerHTML = `<div class="grid2">
      <div>
        <div class="sec"><div class="sec-h"><h2>Hatlar</h2><span class="meta">loglardan · ${ago(h.ts)} <button class="btn ghost" id="hc-refresh" style="margin-left:6px">Şimdi kontrol et</button></span></div>
          <div class="card">${pipes}</div></div>
        <div class="sec"><div class="sec-h"><h2>Sistem</h2></div><div class="card"><div class="sys">${sys}</div>
          ${stale ? `<ul class="small" style="margin:0;padding:10px 16px 12px 32px;color:var(--bad)">${stale}</ul>` : ""}</div></div>
      </div>
      <div class="sec"><div class="sec-h"><h2>Bugün ne çıkıyor</h2>
          <label class="switch meta"><input type="checkbox" id="bg-toggle" ${showBg ? "checked" : ""}> arka plan işleri</label></div>
        <p class="lead">Saatler Türkiye saati; gerçek crontab'dan türetilir.</p>
        <div class="card"><ul class="sched">${li}</ul></div></div>
    </div>`;
  }
  // takvim TSİ gününe göre sıralanır (UTC 21:00+ = ertesi gün 00:00+ TSİ)
  const trMin = (t) => { const [h, m] = t.split(":").map(Number); return ((h + 3) % 24) * 60 + m; };
  const utcToTr = (t) => { const [h, m] = t.split(":").map(Number); return String((h + 3) % 24).padStart(2, "0") + ":" + String(m).padStart(2, "0"); };

  // ---------- çizim + olaylar ----------
  function renderAll() {
    const editing = document.activeElement && document.activeElement.matches("textarea");
    renderPulse();
    if (!editing) renderGorevler();
    renderMetrik(); renderAjan(); renderUretim();
  }

  function setTab(name) {
    document.querySelectorAll("#tabs button").forEach((b) => b.setAttribute("aria-selected", b.dataset.tab === name));
    document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== "v-" + name));
    if (location.hash !== "#" + name) history.replaceState(null, "", "#" + name);
    if (name === "metrik" && S) drawCharts();
    window.scrollTo({ top: 0 });
  }

  function patchLocal(fn) { fn(); renderPulse(); renderGorevler(); }

  async function saveNote(el, url, body) {
    try {
      await api(url, { method: "POST", body });
      const s = el.parentElement.querySelector(".saved");
      s.classList.add("on"); setTimeout(() => s.classList.remove("on"), 1500);
    } catch (e) { toast(e.message, true); }
  }

  document.addEventListener("click", async (ev) => {
    const t = ev.target.closest("button, [data-toggle]");
    if (!t) return;
    if (t.dataset.tab) return setTab(t.dataset.tab);
    if (t.dataset.go) return setTab(t.dataset.go);
    if (t.id === "refresh") return load();
    if (t.id === "theme") {
      const cur = document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      const nxt = cur === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = nxt; store("theme", nxt);
      return S && drawCharts();
    }
    if (t.id === "kpi-tbl-btn") { const tb = $("#kpi-tbl"); tb.hidden = !tb.hidden; t.textContent = tb.hidden ? "Tablo olarak gör" : "Tabloyu gizle"; return; }
    if (t.id === "hc-refresh") {
      t.disabled = true; t.textContent = "Kontrol ediliyor…";
      try { const r = await api("/api/health"); S.health = r.health; renderPulse(); renderUretim(); toast("Sağlık kontrolü güncellendi"); }
      catch (e) { toast(e.message, true); t.disabled = false; }
      return;
    }
    if (t.dataset.more) {
      const k = t.dataset.more;
      openRows.has(k) ? openRows.delete(k) : openRows.add(k);
      store("open", JSON.stringify([...openRows]));
      return renderGorevler();
    }
    if (t.dataset.toggle !== undefined) {
      const row = t.closest("[data-key]"), k = row.dataset.key;
      openRows.has(k) ? openRows.delete(k) : openRows.add(k);
      store("open", JSON.stringify([...openRows]));
      return renderGorevler();
    }
    if (t.dataset.dec) {
      const k = t.closest("[data-key]").dataset.key, dec = t.dataset.dec;
      const task = S.board.week.tasks.find((x) => x.key === k);
      const prev = task.decision;
      patchLocal(() => (task.decision = dec));
      try { await api("/api/agent/" + encodeURIComponent(k), { method: "POST", body: { decision: dec } }); toast(`${task.id}: ${S.decisions[dec]}`); }
      catch (e) { patchLocal(() => (task.decision = prev)); toast(e.message, true); }
      return;
    }
    if (t.dataset.ustatus) {
      const slug = t.closest("[data-user]").dataset.user, st = t.dataset.ustatus;
      const u = S.board.user_tasks.find((x) => x.slug === slug);
      const prev = u.status;
      patchLocal(() => { u.status = st; u.agent_note = ""; S.counts.user_todo = S.board.user_tasks.filter((x) => x.status === "todo").length; });
      try { await api("/api/user/" + encodeURIComponent(slug), { method: "POST", body: { status: st } }); toast(st === "done" ? "Harika — ajan doğrulayacak" : "Kaydedildi"); }
      catch (e) { patchLocal(() => (u.status = prev)); toast(e.message, true); }
      return;
    }
    if (t.id === "inbox-send") {
      const ta = $("#inbox-text"), text = ta.value.trim();
      if (!text) return ta.focus();
      t.disabled = true;
      try { await api("/api/inbox", { method: "POST", body: { text } }); ta.value = ""; toast("Ajana iletildi"); ta.blur(); await load(true); }
      catch (e) { toast(e.message, true); } finally { t.disabled = false; }
      return;
    }
    if (t.dataset.unsend) {
      try { await api("/api/inbox/" + t.dataset.unsend, { method: "DELETE" }); toast("Geri çekildi"); await load(true); }
      catch (e) { toast(e.message, true); }
    }
  });

  document.addEventListener("change", (ev) => {
    const el = ev.target;
    if (el.id === "bg-toggle") { store("bg", el.checked ? "1" : "0"); return renderUretim(); }
    if (el.matches("[data-qnote]")) {
      const k = el.closest("[data-key]").dataset.key;
      const task = S.board.week.tasks.find((x) => x.key === k);
      task.note = el.value;
      return saveNote(el, "/api/agent/" + encodeURIComponent(k), { note: el.value });
    }
    if (el.matches("[data-unote]")) {
      const slug = el.closest("[data-user]").dataset.user;
      S.board.user_tasks.find((x) => x.slug === slug).note = el.value;
      return saveNote(el, "/api/user/" + encodeURIComponent(slug), { note: el.value });
    }
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.target.id === "inbox-text" && ev.key === "Enter" && (ev.metaKey || ev.ctrlKey)) $("#inbox-send").click();
  });

  let rz; addEventListener("resize", () => { clearTimeout(rz); rz = setTimeout(() => S && drawCharts(), 150); });

  const th = store("theme"); if (th) document.documentElement.dataset.theme = th;
  setTab((location.hash || "#gorevler").slice(1).replace(/[^a-z]/g, "") || "gorevler");
  load();
  setInterval(() => { if (!document.hidden) load(true); }, 90000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) load(true); });
})();
