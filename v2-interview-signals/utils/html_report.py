"""Generate a scored periodic-table HTML report from signal results."""

from __future__ import annotations

import html
import json
from pathlib import Path


FAMILIES = {
    "Voice Delivery": "#18a56a",
    "Pace & Rhythm": "#1f7fd1",
    "Pauses & Silence": "#7b61d1",
    "Fluency": "#00a7b5",
    "Language Quality": "#f28c28",
    "Answer Structure": "#e14949",
    "Specificity": "#d9a900",
    "Reasoning": "#d94b86",
    "Conversation Behavior": "#159b8d",
    "Confidence Signals": "#4758c8",
    "Role Competency": "#8a633d",
    "Recording Quality": "#7c8894",
}


def _clean_result(result: dict) -> dict | None:
    if "error" in result:
        return None

    evidence = result.get("evidence") or []
    return {
        "code": str(result.get("code", "?")),
        "name": str(result.get("name", result.get("code", "?"))),
        "category": str(result.get("category", "Other")),
        "layer": str(result.get("layer", "?")),
        "source": str(result.get("source", "unknown")),
        "score": max(0, min(4, int(result.get("score", 0)))),
        "confidence": result.get("confidence", 0),
        "evidence": str(evidence[0]) if evidence else "",
        "evidence_list": [str(item) for item in evidence[:4]],
        "depends_on": [str(item) for item in result.get("depends_on", [])],
        "raw": result.get("raw", {}),
    }


def _prepare_payload(results: list[dict]) -> dict:
    signals = [r for r in (_clean_result(result) for result in results) if r]
    known = [r for r in signals if r["category"] in FAMILIES]
    unknown = [r for r in signals if r["category"] not in FAMILIES]
    families = dict(FAMILIES)
    if unknown:
        families["Other"] = "#7c8894"
    return {"families": families, "signals": known + unknown}


def generate_periodic_table_html(results: list[dict], output_path: Path, title: str = "Periodic Table of Interview Signals") -> None:
    """Write a self-contained scored periodic-table HTML file."""
    payload = json.dumps(_prepare_payload(results), ensure_ascii=False)
    safe_title = html.escape(title)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{safe_title} - Scored</title>
  <style>
    :root {{ --ink:#14202b; --muted:#607080; --paper:#f7f2e8; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; min-height:100vh; background:radial-gradient(circle at 12% 10%, rgba(255,196,0,.18), transparent 28%), radial-gradient(circle at 88% 18%, rgba(27,127,204,.16), transparent 30%), radial-gradient(circle at 72% 92%, rgba(226,73,120,.14), transparent 32%), var(--paper); color:var(--ink); font-family:Georgia,"Times New Roman",serif; padding:34px; }}
    .poster {{ width:1600px; min-height:1080px; margin:0 auto; padding:38px 42px 34px; background:rgba(255,253,247,.86); border:2px solid var(--ink); box-shadow:18px 18px 0 rgba(20,32,43,.12); position:relative; overflow:hidden; }}
    .poster::before {{ content:""; position:absolute; inset:0; pointer-events:none; background-image:linear-gradient(rgba(20,32,43,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(20,32,43,.035) 1px, transparent 1px); background-size:22px 22px; mix-blend-mode:multiply; }}
    header {{ position:relative; z-index:1; margin-bottom:26px; }}
    h1 {{ margin:0; max-width:980px; font-size:64px; line-height:.9; letter-spacing:-3px; }}
    .subtitle {{ margin:14px 0 0; max-width:900px; font:600 18px/1.35 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:var(--muted); }}
    .summary-bar {{ position:relative; z-index:1; display:flex; gap:24px; margin-bottom:24px; padding:16px 20px; background:white; border:1.5px solid rgba(20,32,43,.15); border-radius:4px; }}
    .summary-item {{ display:flex; flex-direction:column; align-items:center; gap:4px; }}
    .summary-item .label {{ font:700 10px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; text-transform:uppercase; color:var(--muted); letter-spacing:.5px; }}
    .summary-item .value {{ font:900 24px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:var(--ink); }}
    .summary-item .bar {{ width:80px; height:8px; background:rgba(20,32,43,.08); border-radius:4px; overflow:hidden; }}
    .summary-item .bar-fill {{ height:100%; background:var(--ink); border-radius:4px; }}
    .table {{ position:relative; z-index:1; display:grid; grid-template-columns:repeat(12,1fr); align-items:end; gap:12px; }}
    .group {{ display:grid; gap:8px; }}
    .group-title {{ height:56px; display:flex; align-items:center; justify-content:center; padding:8px 6px; border:1.5px solid rgba(20,32,43,.76); background:var(--c); color:white; box-shadow:5px 5px 0 rgba(20,32,43,.12); font:900 10px/1.05 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; text-transform:uppercase; letter-spacing:.4px; text-align:center; }}
    .group-avg {{ text-align:center; font:700 11px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:var(--muted); padding:2px 0; }}
    .tile {{ height:108px; padding:7px 7px 6px; border:1.5px solid rgba(20,32,43,.72); background:linear-gradient(180deg,#eceff1 0%,#dfe3e6 100%); box-shadow:5px 5px 0 rgba(20,32,43,.1); position:relative; overflow:hidden; display:flex; flex-direction:column; }}
    .tile-fill {{ position:absolute; bottom:0; left:0; right:0; height:0%; background:linear-gradient(to top,rgba(255,255,255,.06),rgba(255,255,255,.2)), color-mix(in srgb,var(--c) 78%,white); z-index:0; pointer-events:none; }}
    .tile-fill.s0 {{ height:0%; }} .tile-fill.s1 {{ height:25%; }} .tile-fill.s2 {{ height:50%; }} .tile-fill.s3 {{ height:75%; }} .tile-fill.s4 {{ height:100%; }}
    .tile > *:not(.tile-fill) {{ position:relative; z-index:2; }}
    .tile::after {{ content:""; position:absolute; inset:auto -18px -24px auto; width:64px; height:64px; border-radius:50%; background:rgba(20,32,43,.12); opacity:.45; z-index:1; }}
    .tile-header {{ display:flex; justify-content:space-between; align-items:flex-start; }}
    .layer {{ min-width:20px; height:18px; display:grid; place-items:center; border:1px solid rgba(20,32,43,.55); border-radius:999px; background:rgba(255,255,255,.74); font:900 9px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
    .score-badge {{ min-width:28px; height:18px; display:grid; place-items:center; border-radius:3px; font:900 10px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:white; }}
    .score-badge.s0 {{ background:#dc3545; }} .score-badge.s1 {{ background:#e67e22; }} .score-badge.s2 {{ background:#f1c40f; color:var(--ink); }} .score-badge.s3 {{ background:#27ae60; }} .score-badge.s4 {{ background:#2ecc71; }}
    .num {{ margin-top:2px; font:800 9px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:rgba(20,32,43,.5); }}
    .sym {{ margin-top:3px; font:900 20px/.95 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; letter-spacing:-1.2px; }}
    .name {{ margin-top:2px; font:800 10px/1.05 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
    .evidence {{ margin-top:auto; font:600 8px/1.1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:#455564; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    footer {{ position:relative; z-index:1; margin-top:24px; display:flex; justify-content:space-between; align-items:center; font:700 14px/1.3 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:var(--muted); border-top:2px solid rgba(20,32,43,.16); padding-top:16px; }}
    .legend {{ display:flex; gap:16px; align-items:center; flex-wrap:wrap; }} .legend b {{ color:var(--ink); }} .score-dot {{ width:12px; height:12px; border-radius:3px; display:inline-block; }}
  </style>
</head>
<body>
  <main class="poster">
    <header><h1>{safe_title}</h1><p class="subtitle">Scored results from audio + transcript analysis. Generated from the latest v2 signal run.</p></header>
    <div class="summary-bar" id="summary-bar"></div>
    <section class="table" id="table" aria-label="Periodic table of interview signals with scores"></section>
    <footer><span class="legend"><b>Layers:</b> M Metric D Derived J Judgment C Composite <b>Scores:</b><span class="score-dot" style="background:#dc3545"></span>0 <span class="score-dot" style="background:#e67e22"></span>1 <span class="score-dot" style="background:#f1c40f"></span>2 <span class="score-dot" style="background:#27ae60"></span>3 <span class="score-dot" style="background:#2ecc71"></span>4</span><span id="count"></span></footer>
  </main>
  <script>
    const data = {payload};
    const families = data.families;
    const signals = data.signals;
    const byCategory = signals.reduce((acc, s) => {{ (acc[s.category] ||= []).push(s); return acc; }}, {{}});
    const avg = (items) => items.length ? items.reduce((sum, s) => sum + s.score, 0) / items.length : 0;
    const esc = (value) => String(value ?? "").replace(/[&<>"]/g, (ch) => ({{ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }}[ch]));
    const fmt = (value, digits = 1) => value.toFixed(digits);
    const overall = avg(signals);
    document.getElementById("summary-bar").innerHTML = `
      <div class="summary-item"><span class="label">Overall</span><span class="value">${{fmt(overall, 2)}}/4</span><div class="bar"><div class="bar-fill" style="width:${{overall / 4 * 100}}%"></div></div></div>
      ${{Object.entries(families).map(([cat, color]) => {{ const value = avg(byCategory[cat] || []); return `<div class="summary-item"><span class="label">${{cat.split(' ')[0]}}</span><span class="value">${{fmt(value)}}</span><div class="bar"><div class="bar-fill" style="width:${{value / 4 * 100}}%;background:${{color}}"></div></div></div>`; }}).join('')}}`;
    const table = document.getElementById("table");
    let count = 0;
    Object.entries(families).forEach(([family, color]) => {{
      const group = document.createElement("div");
      group.className = "group";
      group.style.setProperty("--c", color);
      (byCategory[family] || []).forEach((s) => {{
        count += 1;
        const tile = document.createElement("article");
        tile.className = "tile";
        tile.style.setProperty("--c", color);
        tile.innerHTML = `<div class="tile-fill s${{s.score}}"></div><div class="tile-header"><div class="layer">${{esc(s.layer)}}</div><div class="score-badge s${{s.score}}">${{s.score}}</div></div><div class="num">${{String(count).padStart(2, "0")}}</div><div class="sym">${{esc(s.code)}}</div><div class="name">${{esc(s.name)}}</div><div class="evidence" title="${{esc(s.evidence)}}">${{esc(s.evidence)}}</div>`;
        group.appendChild(tile);
      }});
      const title = document.createElement("div");
      title.className = "group-title";
      title.textContent = family;
      group.appendChild(title);
      const avgEl = document.createElement("div");
      avgEl.className = "group-avg";
      avgEl.textContent = `avg ${{fmt(avg(byCategory[family] || []))}}`;
      group.appendChild(avgEl);
      table.appendChild(group);
    }});
    document.getElementById("count").textContent = `v2 Scored · ${{signals.length}} elements`;
  </script>
</body>
</html>
""",
        encoding="utf-8",
    )


def generate_slide_deck_html(results: list[dict], output_path: Path, title: str = "Interview Signal Report") -> None:
    """Write a self-contained presentation-style HTML report."""
    payload = json.dumps(_prepare_payload(results), ensure_ascii=False)
    safe_title = html.escape(title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{safe_title} - Slides</title>
  <style>
    :root {{ --ink:#111923; --muted:#667587; --paper:#f6f1e8; --card:#fffdf7; --line:rgba(17,25,35,.16); }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--paper); color:var(--ink); font-family:Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .deck {{ width:100%; min-height:100vh; padding:28px; display:grid; gap:28px; }}
    .slide {{ width:1600px; min-height:900px; margin:0 auto; padding:44px 48px; background:var(--card); border:2px solid var(--ink); box-shadow:14px 14px 0 rgba(17,25,35,.12); position:relative; overflow:hidden; page-break-after:always; }}
    .slide::before {{ content:""; position:absolute; inset:0; pointer-events:none; background-image:linear-gradient(rgba(17,25,35,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(17,25,35,.035) 1px, transparent 1px); background-size:24px 24px; }}
    .slide > * {{ position:relative; z-index:1; }}
    .kicker {{ font:900 13px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; text-transform:uppercase; letter-spacing:.14em; color:var(--muted); }}
    h1 {{ margin:12px 0 8px; max-width:1120px; font-size:74px; line-height:.92; letter-spacing:-.055em; }}
    h2 {{ margin:8px 0 4px; font-size:54px; line-height:.95; letter-spacing:-.045em; }}
    .sub {{ max-width:900px; margin:0; font:700 18px/1.45 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:var(--muted); }}
    .hero {{ display:grid; grid-template-columns:1fr 420px; gap:36px; align-items:end; margin-bottom:30px; }}
    .score-hero {{ padding:28px; border:2px solid var(--ink); background:#f1f5f6; }}
    .score-hero .label {{ font:900 12px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; text-transform:uppercase; color:var(--muted); letter-spacing:.1em; }}
    .score-hero .value {{ margin-top:8px; font:950 78px/.9 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
    .score-track {{ margin-top:18px; height:18px; background:rgba(17,25,35,.09); border-radius:99px; overflow:hidden; }}
    .score-fill {{ height:100%; background:var(--c,#111923); border-radius:99px; }}
    .sections-row {{ display:grid; grid-template-columns:repeat(12, 1fr); gap:10px; align-items:stretch; }}
    .section-table {{ min-height:390px; display:grid; grid-template-rows:auto 1fr auto; border:1.5px solid rgba(17,25,35,.68); background:#eef1f2; box-shadow:5px 5px 0 rgba(17,25,35,.10); overflow:hidden; }}
    .section-table header {{ padding:10px 8px; background:var(--c); color:white; text-align:center; font:950 10px/1.05 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; text-transform:uppercase; letter-spacing:.04em; }}
    .mini-elements {{ padding:8px; display:grid; gap:6px; align-content:end; }}
    .mini {{ min-height:44px; padding:5px 6px; border:1px solid rgba(17,25,35,.35); background:#e2e6e8; position:relative; overflow:hidden; }}
    .mini-fill {{ position:absolute; inset:auto 0 0 0; height:0%; background:color-mix(in srgb, var(--c) 76%, white); }}
    .s0 {{ height:0%; }} .s1 {{ height:25%; }} .s2 {{ height:50%; }} .s3 {{ height:75%; }} .s4 {{ height:100%; }}
    .mini span {{ position:relative; z-index:1; display:block; }}
    .mini .code {{ font:950 15px/.95 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
    .mini .name {{ margin-top:2px; font:800 8px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:#334150; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
    .section-avg {{ padding:8px; text-align:center; font:900 12px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:#334150; border-top:1px solid rgba(17,25,35,.16); }}
    .detail-grid {{ margin-top:28px; display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; }}
    .element-card {{ min-height:174px; padding:14px; border:1.5px solid rgba(17,25,35,.58); background:#edf0f1; position:relative; overflow:hidden; box-shadow:5px 5px 0 rgba(17,25,35,.08); }}
    .element-fill {{ position:absolute; inset:auto 0 0 0; background:color-mix(in srgb, var(--c) 76%, white); z-index:0; }}
    .element-card > *:not(.element-fill) {{ position:relative; z-index:1; }}
    .element-top {{ display:flex; justify-content:space-between; gap:10px; align-items:flex-start; }}
    .element-code {{ font:950 34px/.9 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; letter-spacing:-.08em; }}
    .pill-row {{ display:flex; gap:6px; align-items:center; }}
    .pill {{ padding:5px 7px; border:1px solid rgba(17,25,35,.35); border-radius:999px; background:rgba(255,255,255,.72); font:900 10px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
    .score-pill {{ min-width:30px; border-radius:4px; color:white; text-align:center; }}
    .score-pill.q0 {{ background:#dc3545; }} .score-pill.q1 {{ background:#e67e22; }} .score-pill.q2 {{ background:#f1c40f; color:var(--ink); }} .score-pill.q3 {{ background:#27ae60; }} .score-pill.q4 {{ background:#2ecc71; }}
    .element-name {{ margin-top:8px; font:950 19px/1.05 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
    .element-meta {{ margin-top:7px; display:flex; gap:8px; flex-wrap:wrap; font:800 10px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:#435365; }}
    .evidence {{ margin-top:12px; font:700 12px/1.35 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:#263545; }}
    .raw {{ margin-top:9px; font:650 10px/1.35 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:#526171; max-height:42px; overflow:hidden; }}
    .section-stats {{ margin-top:22px; display:grid; grid-template-columns:repeat(5, 1fr); gap:12px; }}
    .stat {{ padding:13px 14px; border:1px solid var(--line); background:white; }}
    .stat .label {{ font:900 10px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:var(--muted); text-transform:uppercase; }}
    .stat .value {{ margin-top:5px; font:950 26px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
    .nav-note {{ position:absolute; right:42px; bottom:24px; font:800 11px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; color:var(--muted); }}
    @media print {{ body {{ background:white; padding:0; }} .deck {{ padding:0; gap:0; }} .slide {{ box-shadow:none; margin:0; width:100vw; min-height:100vh; border:0; }} }}
  </style>
</head>
<body>
  <div class="deck" id="deck"></div>
  <script>
    const data = {payload};
    const families = data.families;
    const signals = data.signals;
    const byCategory = signals.reduce((acc, s) => {{ (acc[s.category] ||= []).push(s); return acc; }}, {{}});
    const avg = (items) => items.length ? items.reduce((sum, s) => sum + s.score, 0) / items.length : 0;
    const fmt = (value, digits = 1) => value.toFixed(digits);
    const esc = (value) => String(value ?? "").replace(/[&<>"]/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[ch]));
    const valueText = (value) => {{
      if (typeof value === "number") return fmt(value, 2);
      if (Array.isArray(value)) return value.slice(0, 4).map(item => typeof item === "object" ? JSON.stringify(item).slice(0, 28) : String(item)).join(",");
      if (value && typeof value === "object") return JSON.stringify(value).slice(0, 42);
      return String(value).slice(0, 42);
    }};
    const rawText = (raw) => {{
      if (!raw || typeof raw !== "object") return "";
      return Object.entries(raw).slice(0, 4).map(([k, v]) => `${{k}}=${{valueText(v)}}`).join(" · ");
    }};
    const deck = document.getElementById("deck");
    const overall = avg(signals);
    const overview = document.createElement("section");
    overview.className = "slide";
    overview.innerHTML = `<div class="hero"><div><div class="kicker">v2 scored overview</div><h1>{safe_title}</h1><p class="sub">Each vertical section is an individual mini-table. Cell fill height shows score, and fill color follows the signal family.</p></div><div class="score-hero"><div class="label">Overall score</div><div class="value">${{fmt(overall, 2)}}/4</div><div class="score-track"><div class="score-fill" style="width:${{overall/4*100}}%"></div></div></div></div><div class="sections-row" id="overview-row"></div><div class="nav-note">Overview · ${{signals.length}} scored elements</div>`;
    deck.appendChild(overview);
    const overviewRow = overview.querySelector("#overview-row");
    Object.entries(families).forEach(([family, color]) => {{
      const items = byCategory[family] || [];
      const block = document.createElement("article");
      block.className = "section-table";
      block.style.setProperty("--c", color);
      block.innerHTML = `<header>${{esc(family)}}</header><div class="mini-elements">${{items.map(s => `<div class="mini"><div class="mini-fill s${{s.score}}"></div><span class="code">${{esc(s.code)}} <small>${{s.score}}</small></span><span class="name">${{esc(s.name)}}</span></div>`).join("")}}</div><div class="section-avg">avg ${{fmt(avg(items))}}</div>`;
      overviewRow.appendChild(block);
    }});
    Object.entries(families).forEach(([family, color], index) => {{
      const items = byCategory[family] || [];
      if (!items.length) return;
      const sorted = [...items].sort((a, b) => a.score - b.score);
      const weak = sorted.slice(0, 2).map(s => `${{s.code}} ${{s.score}}`).join(", ");
      const strong = sorted.slice(-2).reverse().map(s => `${{s.code}} ${{s.score}}`).join(", ");
      const slide = document.createElement("section");
      slide.className = "slide";
      slide.style.setProperty("--c", color);
      slide.innerHTML = `<div class="kicker">section ${{String(index + 1).padStart(2, "0")}}</div><h2>${{esc(family)}}</h2><p class="sub">Detailed signal cards for this section. The colored overlay is the score fill; gray is unfilled capacity.</p><div class="section-stats"><div class="stat"><div class="label">Average</div><div class="value">${{fmt(avg(items))}}/4</div></div><div class="stat"><div class="label">Elements</div><div class="value">${{items.length}}</div></div><div class="stat"><div class="label">Lowest</div><div class="value">${{esc(weak)}}</div></div><div class="stat"><div class="label">Highest</div><div class="value">${{esc(strong)}}</div></div><div class="stat"><div class="label">Judgment Mix</div><div class="value">${{items.filter(s => s.layer.includes("J")).length}}</div></div></div><div class="detail-grid">${{items.map(s => `<article class="element-card"><div class="element-fill s${{s.score}}"></div><div class="element-top"><div class="element-code">${{esc(s.code)}}</div><div class="pill-row"><span class="pill">${{esc(s.layer)}}</span><span class="pill score-pill q${{s.score}}">${{s.score}}</span></div></div><div class="element-name">${{esc(s.name)}}</div><div class="element-meta"><span>source: ${{esc(s.source)}}</span><span>conf: ${{fmt(Number(s.confidence || 0), 2)}}</span>${{s.depends_on?.length ? `<span>deps: ${{esc(s.depends_on.join(", "))}}</span>` : ""}}</div><div class="evidence">${{esc((s.evidence_list && s.evidence_list[0]) || s.evidence || "No evidence")}}</div><div class="raw">${{esc(rawText(s.raw))}}</div></article>`).join("")}}</div><div class="nav-note">${{esc(family)}} · slide ${{index + 2}}</div>`;
      deck.appendChild(slide);
    }});
  </script>
</body>
</html>
""",
        encoding="utf-8",
    )
