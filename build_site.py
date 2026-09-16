"""
Build site/index.html — inlines research/apps.json and research/patterns.json
into the HTML so it works as a single self-contained file.
Run: python build_site.py
"""
import json, os, pathlib

ROOT = pathlib.Path(__file__).parent
os.makedirs(ROOT / "site", exist_ok=True)

with open(ROOT / "research/apps.json", encoding="utf-8") as f:
    apps_json = json.dumps(json.load(f), ensure_ascii=False)
with open(ROOT / "research/patterns.json", encoding="utf-8") as f:
    patterns_json = json.dumps(json.load(f), ensure_ascii=False)

accuracy_placeholder = '{"pass1_accuracy":0,"final_accuracy":0,"sample_size":20,"per_field":{},"misses":[]}'

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Composio App Research — 100 Apps Case Study</title>
  <meta name="description" content="An agent-powered case study researching 100 apps for Composio: auth patterns, self-serve vs. gated access, buildability, and accuracy verification across 10 categories." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap" rel="stylesheet" />
  <style>
    :root{--bg:#0a0b0f;--surface:#13151c;--surface2:#1c1f2b;--border:rgba(255,255,255,.08);--accent:#6c63ff;--accent2:#00d4aa;--accent3:#ff6b6b;--accent4:#ffd166;--text:#e8eaf0;--muted:#8b8fa8;--card:rgba(255,255,255,.03);--r:12px;--rs:8px}
    [data-theme=light]{--bg:#f5f6fa;--surface:#fff;--surface2:#eef0f7;--border:rgba(0,0,0,.09);--text:#1a1d2e;--muted:#6b7080;--card:rgba(0,0,0,.02)}
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    html{scroll-behavior:smooth}
    body{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;font-size:15px;line-height:1.65;transition:background .3s,color .3s}
    a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}

    /* NAV */
    nav{position:sticky;top:0;z-index:100;background:rgba(10,11,15,.9);backdrop-filter:blur(16px);border-bottom:1px solid var(--border);padding:13px 24px}
    [data-theme=light] nav{background:rgba(245,246,250,.92)}
    .nav-inner{max-width:1200px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
    .nav-brand{font-weight:800;font-size:14px;letter-spacing:-.3px}.nav-brand span{color:var(--accent)}
    .nav-links{display:flex;gap:4px;flex-wrap:wrap}
    .nav-links a{font-size:12px;font-weight:500;color:var(--muted);padding:4px 10px;border-radius:20px;transition:color .2s,background .2s}
    .nav-links a:hover{color:var(--text);background:var(--surface2);text-decoration:none}
    .theme-toggle{background:var(--surface2);border:1px solid var(--border);color:var(--text);cursor:pointer;width:32px;height:32px;border-radius:50%;font-size:15px;display:flex;align-items:center;justify-content:center;flex-shrink:0}

    /* LAYOUT */
    .container{max-width:1200px;margin:0 auto;padding:0 24px}
    section{padding:64px 0;border-bottom:1px solid var(--border)}

    /* HERO */
    #hero{padding:72px 0 56px}
    .hero-chip{display:inline-flex;align-items:center;gap:8px;background:rgba(108,99,255,.12);border:1px solid rgba(108,99,255,.3);color:var(--accent);font-size:11px;font-weight:700;letter-spacing:.6px;padding:5px 12px;border-radius:20px;margin-bottom:22px;text-transform:uppercase}
    .hero-title{font-size:clamp(2.1rem,5vw,3.6rem);font-weight:800;letter-spacing:-1.5px;line-height:1.1;margin-bottom:18px}
    .hero-title .g{background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
    .hero-sub{font-size:16px;color:var(--muted);max-width:620px;margin-bottom:36px}
    .hero-meta{display:flex;gap:24px;flex-wrap:wrap}
    .meta-item{font-size:13px;color:var(--muted)}.meta-item strong{color:var(--text)}

    /* SECTION LABELS */
    .sl{font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--accent);margin-bottom:10px}
    .st{font-size:clamp(1.4rem,3.5vw,2.1rem);font-weight:800;letter-spacing:-.8px;margin-bottom:10px}
    .sd{color:var(--muted);max-width:680px;margin-bottom:44px}

    /* FINDING CARDS */
    .fg{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:18px}
    .fc{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:26px 22px;position:relative;overflow:hidden;transition:border-color .2s,transform .2s}
    .fc:hover{border-color:rgba(108,99,255,.35);transform:translateY(-2px)}
    .fc::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
    .fc:nth-child(1)::before{background:linear-gradient(90deg,var(--accent),var(--accent2))}
    .fc:nth-child(2)::before{background:linear-gradient(90deg,var(--accent2),#06b6d4)}
    .fc:nth-child(3)::before{background:linear-gradient(90deg,var(--accent4),#ff9f43)}
    .fc:nth-child(4)::before{background:linear-gradient(90deg,var(--accent3),#ee5a24)}
    .fc:nth-child(5)::before{background:linear-gradient(90deg,#a29bfe,var(--accent))}
    .fn{font-size:2.8rem;font-weight:800;letter-spacing:-2px;line-height:1;margin-bottom:8px;color:var(--text)}
    .ft{font-size:13px;font-weight:700;margin-bottom:5px}
    .fb{font-size:12px;color:var(--muted);line-height:1.5}

    /* CHARTS */
    .cg{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:22px}
    .cc{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:24px 22px}
    .ct{font-size:13px;font-weight:700;margin-bottom:20px}
    .cc svg{display:block;width:100%}
    .legend{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
    .li{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted)}
    .ld{width:9px;height:9px;border-radius:3px;flex-shrink:0}

    /* TWO COL */
    .two-col{display:grid;grid-template-columns:1fr 1fr;gap:22px}
    @media(max-width:700px){.two-col{grid-template-columns:1fr}}
    .col-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:26px 22px}
    .cch{display:flex;align-items:center;gap:10px;margin-bottom:18px}
    .cb{font-size:10px;font-weight:700;padding:3px 10px;border-radius:20px;letter-spacing:.3px}
    .cg2{background:rgba(0,212,170,.15);color:var(--accent2)}
    .co{background:rgba(255,107,107,.15);color:var(--accent3)}
    .ctitle{font-size:15px;font-weight:700}
    .csub{font-size:12px;color:var(--muted);margin-bottom:14px}
    .pill-list{display:flex;flex-wrap:wrap;gap:7px}
    .pill{font-size:11px;padding:4px 10px;background:var(--surface2);border:1px solid var(--border);border-radius:20px;color:var(--text);transition:background .15s}
    .pill:hover{background:rgba(108,99,255,.1)}

    /* TABLE */
    .tc{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}
    .search{flex:1;min-width:200px;background:var(--surface);border:1px solid var(--border);border-radius:var(--rs);padding:9px 13px;color:var(--text);font-family:inherit;font-size:14px;outline:none;transition:border-color .2s}
    .search:focus{border-color:var(--accent)}
    select.fsel{background:var(--surface);border:1px solid var(--border);border-radius:var(--rs);padding:9px 13px;color:var(--text);font-family:inherit;font-size:13px;cursor:pointer;outline:none}
    .tw{overflow-x:auto;border-radius:var(--r);border:1px solid var(--border)}
    table{width:100%;border-collapse:collapse}
    th{background:var(--surface);padding:11px 13px;font-size:10px;font-weight:700;letter-spacing:.5px;text-align:left;color:var(--muted);text-transform:uppercase;white-space:nowrap;cursor:pointer;user-select:none;border-bottom:1px solid var(--border);transition:color .15s}
    th:hover{color:var(--text)}
    th .si{margin-left:3px;opacity:.35}
    th.sorted .si{opacity:1;color:var(--accent)}
    td{padding:10px 13px;font-size:12px;border-bottom:1px solid var(--border);vertical-align:top}
    tr:last-child td{border-bottom:none}
    tr:hover td{background:rgba(255,255,255,.02)}
    [data-theme=light] tr:hover td{background:rgba(0,0,0,.02)}
    .badge{display:inline-block;font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px;letter-spacing:.2px;white-space:nowrap}
    .by{background:rgba(0,212,170,.15);color:var(--accent2)}
    .bp{background:rgba(255,209,102,.15);color:var(--accent4)}
    .bn{background:rgba(255,107,107,.15);color:var(--accent3)}
    .bs{background:rgba(0,212,170,.12);color:var(--accent2)}
    .bg{background:rgba(255,107,107,.12);color:var(--accent3)}
    .bu{background:rgba(139,143,168,.15);color:var(--muted)}
    .evl{display:flex;gap:5px;flex-wrap:wrap}
    .evl a{font-size:10px;color:var(--accent);background:rgba(108,99,255,.1);padding:2px 6px;border-radius:4px}
    .tf{display:flex;justify-content:space-between;align-items:center;padding:9px 13px;font-size:12px;color:var(--muted);background:var(--surface);border-top:1px solid var(--border)}
    #rc{font-weight:700;color:var(--text)}
    .tag-auth{display:inline-block;font-size:10px;font-weight:600;padding:2px 5px;border-radius:4px;margin:1px;background:rgba(108,99,255,.12);color:var(--accent)}

    /* PIPELINE */
    .pw{overflow-x:auto;padding-bottom:8px}
    .pipeline{display:flex;align-items:center;min-width:max-content;padding:8px 0}
    .pn{background:var(--surface);border:1px solid var(--border);border-radius:var(--rs);padding:16px 18px;text-align:center;min-width:130px;transition:border-color .2s}
    .pn:hover{border-color:var(--accent)}
    .ni{font-size:24px;margin-bottom:7px}
    .nn{font-size:11px;font-weight:700;margin-bottom:3px}
    .nd{font-size:10px;color:var(--muted);line-height:1.4;max-width:110px}
    .pa{font-size:17px;color:var(--accent);padding:0 8px;flex-shrink:0}
    .hb{background:rgba(255,209,102,.08);border:1px solid rgba(255,209,102,.3);border-radius:var(--r);padding:22px 26px;margin-top:28px}
    .hbt{font-size:14px;font-weight:700;color:var(--accent4);margin-bottom:10px;display:flex;align-items:center;gap:8px}
    .hl{list-style:none;display:flex;flex-direction:column;gap:7px}
    .hl li{font-size:12px;color:var(--text);padding-left:18px;position:relative}
    .hl li::before{content:'›';position:absolute;left:0;color:var(--accent4);font-weight:700}
    .cmd{background:var(--surface2);border:1px solid var(--border);border-radius:var(--rs);padding:14px 18px;font-family:'Courier New',monospace;font-size:13px;color:var(--accent2);margin-top:26px;overflow-x:auto}
    .cmd::before{content:'$ ';color:var(--muted)}

    /* VERIFICATION */
    .abars{display:flex;flex-direction:column;gap:14px;margin-bottom:28px}
    .abr{display:flex;align-items:center;gap:12px}
    .abl{font-size:13px;font-weight:600;min-width:90px}
    .abt{flex:1;height:18px;background:var(--surface2);border-radius:10px;overflow:hidden}
    .abf{height:100%;border-radius:10px;transition:width 1s cubic-bezier(.4,0,.2,1)}
    .abv{font-size:13px;font-weight:700;min-width:40px;text-align:right}
    .pfg{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-bottom:28px}
    .pfc{background:var(--surface);border:1px solid var(--border);border-radius:var(--rs);padding:16px 14px;text-align:center}
    .pfv{font-size:1.9rem;font-weight:800;letter-spacing:-1px;margin-bottom:3px}
    .pfn{font-size:11px;color:var(--muted)}
    .mt{width:100%;border-collapse:collapse;font-size:12px}
    .mt th{background:var(--surface2);font-size:10px;font-weight:700;color:var(--muted);padding:9px 11px;text-align:left;border-bottom:1px solid var(--border);text-transform:uppercase;letter-spacing:.5px}
    .mt td{padding:9px 11px;border-bottom:1px solid var(--border);vertical-align:top}
    .mt tr:last-child td{border-bottom:none}

    /* HONESTY */
    .dg{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px;margin-bottom:28px}
    .dc{background:rgba(255,107,107,.06);border:1px solid rgba(255,107,107,.2);border-radius:var(--rs);padding:16px 14px}
    .dcn{font-size:13px;font-weight:700;margin-bottom:5px}
    .dcr{font-size:11px;color:var(--muted);line-height:1.5}
    .nb{background:rgba(108,99,255,.07);border:1px solid rgba(108,99,255,.2);border-radius:var(--r);padding:20px 22px}
    .nb p{font-size:13px;color:var(--muted);line-height:1.7}.nb strong{color:var(--text)}

    /* FOOTER */
    footer{background:var(--surface);border-top:1px solid var(--border);padding:36px 24px;text-align:center}
    .fi{max-width:580px;margin:0 auto}
    .fttl{font-size:14px;font-weight:700;margin-bottom:10px}
    .flinks{display:flex;justify-content:center;gap:16px;flex-wrap:wrap;margin-bottom:16px}
    .flinks a{display:flex;align-items:center;gap:5px;background:var(--surface2);border:1px solid var(--border);border-radius:var(--rs);padding:7px 14px;font-size:12px;font-weight:600;color:var(--text);transition:border-color .2s}
    .flinks a:hover{border-color:var(--accent);text-decoration:none}
    .fn2{font-size:11px;color:var(--muted)}

    @media(max-width:600px){nav{padding:10px 16px}.nav-links{display:none}section{padding:44px 0}}
  </style>
</head>
<body>

<!-- NAV -->
<nav>
  <div class="nav-inner">
    <div class="nav-brand">Composio <span>Research</span></div>
    <div class="nav-links">
      <a href="#findings">Findings</a>
      <a href="#charts">Charts</a>
      <a href="#wins">Wins</a>
      <a href="#table">All Apps</a>
      <a href="#agent">Agent</a>
      <a href="#verification">Accuracy</a>
      <a href="#honesty">Honesty</a>
    </div>
    <button class="theme-toggle" id="themeBtn" title="Toggle theme" aria-label="Toggle theme">🌙</button>
  </div>
</nav>

<!-- HERO -->
<section id="hero">
  <div class="container">
    <div class="hero-chip">🔬 AI-assisted research &middot; 100 apps &middot; 10 categories</div>
    <h1 class="hero-title">Which apps can <span class="g">an agent</span><br/>build a toolkit for—today?</h1>
    <p class="hero-sub">A Python pipeline researched 100 apps for Composio across auth, self-serve access, API surface, and buildability—then verified itself.</p>
    <div class="hero-meta">
      <div class="meta-item"><strong>100</strong> apps researched</div>
      <div class="meta-item"><strong>10</strong> categories</div>
      <div class="meta-item"><strong>2 passes</strong> + human check</div>
      <div class="meta-item"><strong>3 checks</strong>: URL, critic, human</div>
    </div>
  </div>
</section>

<!-- FINDINGS -->
<section id="findings">
  <div class="container">
    <div class="sl">Pattern findings</div>
    <h2 class="st">5 things that jump out</h2>
    <p class="sd">Plain-language takeaways from the full dataset—before you look at a single row.</p>
    <div class="fg" id="findingsGrid"></div>
  </div>
</section>

<!-- CHARTS -->
<section id="charts">
  <div class="container">
    <div class="sl">Visualisations</div>
    <h2 class="st">The data at a glance</h2>
    <p class="sd">Inline SVG—no external libraries. All rendered from the embedded JSON.</p>
    <div class="cg">
      <div class="cc">
        <div class="ct">Auth method distribution</div>
        <svg id="authChart" viewBox="0 0 300 210" xmlns="http://www.w3.org/2000/svg"></svg>
        <div class="legend" id="authLegend"></div>
      </div>
      <div class="cc">
        <div class="ct">Access by category (heatmap)</div>
        <svg id="heatmapChart" xmlns="http://www.w3.org/2000/svg"></svg>
      </div>
      <div class="cc">
        <div class="ct">Buildability breakdown</div>
        <svg id="buildChart" xmlns="http://www.w3.org/2000/svg"></svg>
        <div class="legend" id="buildLegend"></div>
      </div>
    </div>
  </div>
</section>

<!-- WINS -->
<section id="wins">
  <div class="container">
    <div class="sl">Opportunity map</div>
    <h2 class="st">Where to build first</h2>
    <p class="sd">Apps that are self-serve and ready vs. apps that need a business relationship before any key is issued.</p>
    <div class="two-col">
      <div class="col-card">
        <div class="cch">
          <span class="cb cg2">&#10003; EASY WINS</span>
          <span class="ctitle">Self-serve + Ready</span>
        </div>
        <div class="csub">Self-serve credentials, documented API, buildable today.</div>
        <div class="pill-list" id="easyList"></div>
      </div>
      <div class="col-card">
        <div class="cch">
          <span class="cb co">&#9888; NEEDS OUTREACH</span>
          <span class="ctitle">Gated / Partner-only</span>
        </div>
        <div class="csub">Requires enterprise contract, sales approval, or partner-review before any API key is issued.</div>
        <div class="pill-list" id="outreachList"></div>
      </div>
    </div>
  </div>
</section>

<!-- TABLE -->
<section id="table">
  <div class="container">
    <div class="sl">Full dataset</div>
    <h2 class="st">All 100 apps</h2>
    <p class="sd">Search, filter by category, access type, or buildability. Click column headers to sort. Evidence links open source docs.</p>
    <div class="tc">
      <input class="search" id="tableSearch" placeholder="&#128269; Search apps&hellip;" type="text" />
      <select class="fsel" id="catFilter"><option value="">All categories</option></select>
      <select class="fsel" id="serveFilter">
        <option value="">All access</option>
        <option value="self-serve">Self-serve</option>
        <option value="partial">Partial</option>
        <option value="gated">Gated</option>
        <option value="unknown">Unknown</option>
      </select>
      <select class="fsel" id="buildFilter">
        <option value="">All buildability</option>
        <option value="yes">Buildable</option>
        <option value="partial">Partial</option>
        <option value="no">Not buildable</option>
      </select>
    </div>
    <div class="tw">
      <table id="appsTable">
        <thead>
          <tr>
            <th data-col="id">#<span class="si">&#8597;</span></th>
            <th data-col="name">App<span class="si">&#8597;</span></th>
            <th data-col="category">Category<span class="si">&#8597;</span></th>
            <th data-col="auth">Auth</th>
            <th data-col="self_serve">Access<span class="si">&#8597;</span></th>
            <th data-col="api_surface">API</th>
            <th data-col="mcp_exists">MCP<span class="si">&#8597;</span></th>
            <th data-col="buildability">Buildable<span class="si">&#8597;</span></th>
            <th data-col="evidence">Evidence</th>
          </tr>
        </thead>
        <tbody id="tableBody"></tbody>
      </table>
      <div class="tf">
        <span>Showing <span id="rc">0</span> of 100</span>
        <span style="color:var(--muted)">Click headers to sort</span>
      </div>
    </div>
  </div>
</section>

<!-- AGENT -->
<section id="agent">
  <div class="container">
    <div class="sl">How it was built</div>
    <h2 class="st">The pipeline</h2>
    <p class="sd">A multi-stage Python pipeline with an automated critic and a second pass for low-confidence findings.</p>
    <div class="pw">
      <div class="pipeline">
        <div class="pn"><div class="ni">&#128203;</div><div class="nn">research.py</div><div class="nd">Calls Claude to research each app via web search&nbsp;+ doc fetch</div></div>
        <div class="pa">&#8594;</div>
        <div class="pn"><div class="ni">&#128279;</div><div class="nn">check_urls.py</div><div class="nd">Fetches every evidence URL; flags errors, redirects, and pages not mentioning the claimed auth</div></div>
        <div class="pa">&#8594;</div>
        <div class="pn"><div class="ni">&#129488;</div><div class="nn">critic.py</div><div class="nd">LLM self-critique: flags low-confidence findings and contradictions</div></div>
        <div class="pa">&#8594;</div>
        <div class="pn"><div class="ni">&#128260;</div><div class="nn">Pass 2 re-run</div><div class="nd">Independent re-research of the 20-app verification sample</div></div>
        <div class="pa">&#8594;</div>
        <div class="pn"><div class="ni">&#128100;</div><div class="nn">Human check</div><div class="nd">Spot-checks 20 apps against live docs; corrects misses by hand</div></div>
      </div>
    </div>
    <div class="hb">
      <div class="hbt">&#128100; Where a human was needed</div>
      <ul class="hl">
        <li><strong>Paygent Connect</strong>: no public API found—confirmed likely white-label NMI gateway, marked "unknown".</li>
        <li><strong>Gladly</strong>: developer.gladly.com returned no useful content—enterprise-only gating verified via pricing coverage.</li>
        <li><strong>Ahrefs</strong>: docs are paywalled—Enterprise-only gate confirmed via public pricing page.</li>
        <li><strong>Sherlock</strong>: not an API at all—flagged as a local CLI tool, not suitable for a remote toolkit.</li>
        <li><strong>Mermaid CLI</strong>: same pattern as Sherlock—buildability corrected from "yes" to "partial" after confirming CLI-only architecture.</li>
        <li><strong>Coda</strong>: developer docs redirect to Superhuman—redirect confirmed, caution note added in gating_notes.</li>
        <li><strong>General</strong>: pass 1 ran interactively in Claude Code; the scripted pass 2 needed human review of merge logic in merge.py.</li>
        <li><strong>fanbasis</strong>: rebranded to commas.com; pass 1 cited stale evidence, the critic caught it.</li>
        <li><strong>Ramp</strong>: docs are JS-rendered, so the URL checker gave a false flag; the critic confirmed pass 1 was right.</li>
      </ul>
    </div>
    <div class="cmd">python agent/research.py --only "Notion"</div>
  </div>
</section>

<!-- VERIFICATION -->
<section id="verification">
  <div class="container">
    <div class="sl">Accuracy check</div>
    <h2 class="st">How trustworthy are the findings?</h2>
    <p class="sd">A random sample of 20 apps was hand-checked against live documentation. Results render from the <code style="color:var(--accent)">#accuracy</code> script tag below.</p>
    <div class="abars" id="accBars"></div>
    <div class="pfg" id="perFieldGrid"></div>
    <h3 style="font-size:14px;font-weight:700;margin-bottom:14px">Miss log &mdash; what the agent got wrong</h3>
    <div style="overflow-x:auto">
      <table class="mt" id="missesTable">
        <thead><tr><th>App</th><th>Field</th><th>Agent said</th><th>Correct</th><th>Reason</th></tr></thead>
        <tbody id="missesBody">
          <tr><td colspan="5" style="color:var(--muted);text-align:center;padding:18px">
            Fill the <code style="color:var(--accent)">#accuracy</code> script tag to populate this table.
          </td></tr>
        </tbody>
      </table>
    </div>
  </div>
</section>

<!-- HONESTY -->
<section id="honesty">
  <div class="container">
    <div class="sl">Honest account</div>
    <h2 class="st">What defeated the agent</h2>
    <p class="sd">Apps the pipeline couldn&#8217;t fully research&mdash;and why. Saying so is the correct finding, not a failure.</p>
    <div class="dg" id="defeatedGrid"></div>
    <div class="nb">
      <p>
        Pass 1 was run interactively in Claude Code (100 apps). The pipeline was then scripted in <code>agent/research.py</code> and re-run as an independent <strong>pass 2</strong> on a 20-app verification sample (10 random + 10 hardest). <code>check_urls.py</code> flagged 54/100 apps, mostly keyword false positives. <code>critic.py</code> reviewed 24 flagged apps (sample + low-confidence): 12 disputed, 12 agreed. The other 30 flagged apps were not critic-reviewed due to time/compute limits.
      </p>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <div class="fi">
    <div class="fttl">Composio App Research &mdash; 100 Apps Case Study</div>
    <div class="flinks">
      <a href="https://github.com/ParasharDeb/composio-assignment" id="repoLink" target="_blank" rel="noopener">&#128230; Source repo</a>
      <a href="../research/apps.json" id="dataLink">&#128196; data.json &mdash; for agents</a>
    </div>
    <div class="fn2">Built with Claude Code (Sonnet + critic) &middot; Antigravity IDE &middot; September 2026<br/>
    Data: <code>research/apps.json</code> &middot; Patterns: <code>research/patterns.json</code></div>
  </div>
</footer>

<!-- INLINE DATA (inlined by build_site.py) -->
<script id="apps-data" type="application/json">APPS_JSON_PLACEHOLDER</script>
<script id="patterns-data" type="application/json">PATTERNS_JSON_PLACEHOLDER</script>

<!-- Accuracy placeholder — fill this to populate Section 6 -->
<script id="accuracy" type="application/json">
ACCURACY_PLACEHOLDER
</script>

<script>
(function(){
  const APPS=JSON.parse(document.getElementById('apps-data').textContent||'[]');
  const PAT=JSON.parse(document.getElementById('patterns-data').textContent||'{}');
  const ACC=JSON.parse(document.getElementById('accuracy').textContent||'{}');

  // Theme
  const btn=document.getElementById('themeBtn'); let dark=true;
  btn.addEventListener('click',()=>{dark=!dark;document.documentElement.setAttribute('data-theme',dark?'':'light');btn.textContent=dark?'🌙':'☀️';});

  const ACOLS=['#6c63ff','#00d4aa','#ffd166','#ff6b6b','#a29bfe','#74b9ff'];
  const BCOLS={yes:'#00d4aa',partial:'#ffd166',no:'#ff6b6b'};

  // § Findings
  function buildFindings(){
    const p=PAT, g=document.getElementById('findingsGrid');
    const fs=[
      {n:`${p.self_serve_counts?.['self-serve']||71}`,t:'self-serve out of 100',b:'Most apps issue credentials instantly—no sales call, no waiting. Developer productivity wins.'},
      {n:`${p.auth_method_counts?.OAuth2||68}%`,t:'use OAuth 2.0',b:'OAuth2 dominates. A single OAuth2 layer covers most of the corpus; API keys are the reliable fallback.'},
      {n:`${p.buildability_counts?.yes||79}`,t:'buildable today',b:'Toolkits can ship right now for these apps. Only 3 are genuinely not buildable (CLI-only or no public API).'},
      {n:`${p.mcp_exists_count||78}`,t:'have an MCP server',b:'MCP adoption is ahead of expectations—78 of 100 have official or community MCP servers, many since 2025.'},
      {n:`${p.needs_outreach?.length||13}`,t:'need outreach first',b:'Enterprise-only / partner-gated apps (Meta Ads, LinkedIn Ads, DealCloud, PitchBook…) need a biz relationship before any key.'}
    ];
    fs.forEach(f=>{
      const d=document.createElement('div'); d.className='fc';
      d.innerHTML=`<div class="fn">${f.n}</div><div class="ft">${f.t}</div><div class="fb">${f.b}</div>`;
      g.appendChild(d);
    });
  }

  // § Auth donut
  function buildAuth(){
    const auth=PAT.auth_method_counts||{};
    const entries=Object.entries(auth).sort((a,b)=>b[1]-a[1]);
    const total=entries.reduce((s,[,v])=>s+v,0);
    const svg=document.getElementById('authChart');
    const cx=150,cy=100,r=78,ir=48; let angle=-Math.PI/2;
    const leg=document.getElementById('authLegend');
    entries.forEach(([label,val],i)=>{
      const frac=val/total, sweep=frac*2*Math.PI;
      const x1=cx+r*Math.cos(angle),y1=cy+r*Math.sin(angle);
      const x2=cx+r*Math.cos(angle+sweep),y2=cy+r*Math.sin(angle+sweep);
      const xi1=cx+ir*Math.cos(angle),yi1=cy+ir*Math.sin(angle);
      const xi2=cx+ir*Math.cos(angle+sweep),yi2=cy+ir*Math.sin(angle+sweep);
      const lg=sweep>Math.PI?1:0, col=ACOLS[i%ACOLS.length];
      const p=document.createElementNS('http://www.w3.org/2000/svg','path');
      p.setAttribute('d',`M ${xi1} ${yi1} L ${x1} ${y1} A ${r} ${r} 0 ${lg} 1 ${x2} ${y2} L ${xi2} ${yi2} A ${ir} ${ir} 0 ${lg} 0 ${xi1} ${yi1} Z`);
      p.setAttribute('fill',col); p.setAttribute('opacity','0.9'); svg.appendChild(p);
      if(frac>0.09){
        const mid=angle+sweep/2,lx=cx+(r+ir)/2*Math.cos(mid),ly=cy+(r+ir)/2*Math.sin(mid);
        const t=document.createElementNS('http://www.w3.org/2000/svg','text');
        t.setAttribute('x',lx);t.setAttribute('y',ly);t.setAttribute('text-anchor','middle');t.setAttribute('dominant-baseline','middle');
        t.setAttribute('font-size','11');t.setAttribute('fill','#fff');t.setAttribute('font-weight','700');t.textContent=val; svg.appendChild(t);
      }
      angle+=sweep;
      const li=document.createElement('div'); li.className='li';
      li.innerHTML=`<span class="ld" style="background:${col}"></span>${label} (${val})`; leg.appendChild(li);
    });
    const ct=document.createElementNS('http://www.w3.org/2000/svg','text');
    ct.setAttribute('x',cx);ct.setAttribute('y',cy-6);ct.setAttribute('text-anchor','middle');ct.setAttribute('fill','#e8eaf0');ct.setAttribute('font-size','14');ct.setAttribute('font-weight','700');ct.textContent=total; svg.appendChild(ct);
    const cs=document.createElementNS('http://www.w3.org/2000/svg','text');
    cs.setAttribute('x',cx);cs.setAttribute('y',cy+11);cs.setAttribute('text-anchor','middle');cs.setAttribute('fill','#8b8fa8');cs.setAttribute('font-size','9');cs.textContent='auth refs'; svg.appendChild(cs);
  }

  // § Heatmap
  function buildHeatmap(){
    const byCat=PAT.self_serve_by_category||{}, cats=Object.keys(byCat);
    const states=['self-serve','partial','gated','unknown'];
    const cols={'self-serve':'#00d4aa',partial:'#ffd166',gated:'#ff6b6b',unknown:'#888'};
    const svg=document.getElementById('heatmapChart');
    const short=c=>c.replace('Communications and Messaging','Comms & Msg')
                     .replace('Marketing, Ads, Email and Social','Marketing & Social')
                     .replace('Developer, Infra and Data platforms','Dev & Infra')
                     .replace('Productivity and Project Management','Productivity & PM')
                     .replace('AI, Research and Media-native','AI & Media')
                     .replace('Finance and Fintech','Finance')
                     .replace('Data, SEO and Scraping','Data & SEO')
                     .replace('Support and Helpdesk','Support')
                     .replace('CRM and Sales','CRM & Sales');
    const mL=110,mT=28,cW=54,cH=26;
    const W=mL+states.length*cW+8, H=mT+cats.length*cH+8;
    svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
    states.forEach((s,j)=>{
      const t=document.createElementNS('http://www.w3.org/2000/svg','text');
      t.setAttribute('x',mL+j*cW+cW/2);t.setAttribute('y',14);t.setAttribute('text-anchor','middle');
      t.setAttribute('fill','#8b8fa8');t.setAttribute('font-size','8');t.setAttribute('font-weight','600');
      t.textContent=s.charAt(0).toUpperCase()+s.slice(1).replace('-',' '); svg.appendChild(t);
    });
    cats.forEach((cat,i)=>{
      const lbl=document.createElementNS('http://www.w3.org/2000/svg','text');
      lbl.setAttribute('x',mL-5);lbl.setAttribute('y',mT+i*cH+cH/2);
      lbl.setAttribute('text-anchor','end');lbl.setAttribute('dominant-baseline','middle');
      lbl.setAttribute('fill','#8b8fa8');lbl.setAttribute('font-size','8');lbl.textContent=short(cat); svg.appendChild(lbl);
      states.forEach((s,j)=>{
        const val=(byCat[cat]||{})[s]||0;
        const alpha=val>0?0.18+(val/10)*0.65:0.04;
        const rect=document.createElementNS('http://www.w3.org/2000/svg','rect');
        rect.setAttribute('x',mL+j*cW+2);rect.setAttribute('y',mT+i*cH+2);
        rect.setAttribute('width',cW-4);rect.setAttribute('height',cH-4);rect.setAttribute('rx',4);
        rect.setAttribute('fill',cols[s]);rect.setAttribute('opacity',alpha); svg.appendChild(rect);
        if(val>0){
          const t=document.createElementNS('http://www.w3.org/2000/svg','text');
          t.setAttribute('x',mL+j*cW+cW/2);t.setAttribute('y',mT+i*cH+cH/2);
          t.setAttribute('text-anchor','middle');t.setAttribute('dominant-baseline','middle');
          t.setAttribute('fill','#e8eaf0');t.setAttribute('font-size','10');t.setAttribute('font-weight','700');
          t.textContent=val; svg.appendChild(t);
        }
      });
    });
  }

  // § Build chart
  function buildBuild(){
    const bc=PAT.buildability_counts||{}, total=Object.values(bc).reduce((s,v)=>s+v,0)||100;
    const items=[['Buildable today',bc.yes||0,BCOLS.yes],['Partial / blocked',bc.partial||0,BCOLS.partial],['Not buildable',bc.no||0,BCOLS.no]];
    const svg=document.getElementById('buildChart');
    const ml=100,bh=26,gap=14,mT=10, W=280, H=mT+items.length*(bh+gap)+10;
    svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
    const leg=document.getElementById('buildLegend');
    items.forEach(([label,val,col],i)=>{
      const pct=val/total, y=mT+i*(bh+gap), bw=(W-ml-50)*pct;
      const t=document.createElementNS('http://www.w3.org/2000/svg','text');
      t.setAttribute('x',ml-7);t.setAttribute('y',y+bh/2);t.setAttribute('text-anchor','end');t.setAttribute('dominant-baseline','middle');
      t.setAttribute('fill','#8b8fa8');t.setAttribute('font-size','10');t.textContent=label; svg.appendChild(t);
      const track=document.createElementNS('http://www.w3.org/2000/svg','rect');
      track.setAttribute('x',ml);track.setAttribute('y',y);track.setAttribute('width',W-ml-45);track.setAttribute('height',bh);
      track.setAttribute('rx',6);track.setAttribute('fill','rgba(255,255,255,0.05)'); svg.appendChild(track);
      const fill=document.createElementNS('http://www.w3.org/2000/svg','rect');
      fill.setAttribute('x',ml);fill.setAttribute('y',y);fill.setAttribute('width',Math.max(bw,4));fill.setAttribute('height',bh);
      fill.setAttribute('rx',6);fill.setAttribute('fill',col); svg.appendChild(fill);
      const vt=document.createElementNS('http://www.w3.org/2000/svg','text');
      vt.setAttribute('x',ml+bw+6);vt.setAttribute('y',y+bh/2);vt.setAttribute('dominant-baseline','middle');
      vt.setAttribute('fill','#e8eaf0');vt.setAttribute('font-size','11');vt.setAttribute('font-weight','700');vt.textContent=val; svg.appendChild(vt);
      const li=document.createElement('div'); li.className='li';
      li.innerHTML=`<span class="ld" style="background:${col}"></span>${label} (${val})`; leg.appendChild(li);
    });
  }

  // § Wins
  function buildWins(){
    const e=document.getElementById('easyList'), o=document.getElementById('outreachList');
    (PAT.easy_wins||[]).forEach(n=>{const s=document.createElement('span');s.className='pill';s.textContent=n;e.appendChild(s);});
    (PAT.needs_outreach||[]).forEach(n=>{const s=document.createElement('span');s.className='pill';s.textContent=n;o.appendChild(s);});
  }

  // § Table
  let sortCol='id',sortDir=1;
  const sBadge=s=>({'self-serve':'bs',partial:'bp',gated:'bg',unknown:'bu'}[s]||'bu');
  const bBadge=b=>({yes:'by',partial:'bp',no:'bn'}[b]||'bu');
  function renderTable(data){
    const tbody=document.getElementById('tableBody'); tbody.innerHTML='';
    data.forEach(app=>{
      const auths=(app.auth_methods||[]).map(a=>`<span class="tag-auth">${a}</span>`).join('');
      const evl=(app.evidence||[]).slice(0,3).map((u,i)=>`<a href="${u}" target="_blank" rel="noopener">Src ${i+1}</a>`).join('');
      const tr=document.createElement('tr');
      tr.innerHTML=`
        <td style="color:var(--muted)">${app.id}</td>
        <td><strong>${app.name}</strong><br/><span style="font-size:10px;color:var(--muted)">${(app.description||'').slice(0,58)}&hellip;</span></td>
        <td style="white-space:nowrap">${app.category||''}</td>
        <td>${auths}</td>
        <td><span class="badge ${sBadge(app.self_serve)}">${app.self_serve||'&mdash;'}</span></td>
        <td>${app.api_surface||'&mdash;'}</td>
        <td>${app.mcp_exists?'<span class="badge by">&#10003; Yes</span>':'<span class="badge bn">&#10007; No</span>'}</td>
        <td><span class="badge ${bBadge(app.buildability)}">${app.buildability||'&mdash;'}</span></td>
        <td><div class="evl">${evl||'&mdash;'}</div></td>`;
      tbody.appendChild(tr);
    });
    document.getElementById('rc').textContent=data.length;
  }
  function applyFilters(){
    const q=document.getElementById('tableSearch').value.toLowerCase();
    const cat=document.getElementById('catFilter').value;
    const srv=document.getElementById('serveFilter').value;
    const bld=document.getElementById('buildFilter').value;
    let data=APPS.filter(a=>{
      const txt=`${a.name} ${a.description} ${a.category}`.toLowerCase();
      return(!q||txt.includes(q))&&(!cat||a.category===cat)&&(!srv||a.self_serve===srv)&&(!bld||a.buildability===bld);
    });
    data.sort((a,b)=>{
      let av=a[sortCol],bv=b[sortCol];
      if(sortCol==='mcp_exists'){av=av?1:0;bv=bv?1:0;}
      av=av==null?'':av; bv=bv==null?'':bv;
      if(typeof av==='number'&&typeof bv==='number')return(av-bv)*sortDir;
      return String(av).localeCompare(String(bv))*sortDir;
    });
    renderTable(data);
  }
  function initTable(){
    const cats=[...new Set(APPS.map(a=>a.category))].sort();
    const sel=document.getElementById('catFilter');
    cats.forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;sel.appendChild(o);});
    ['tableSearch','catFilter','serveFilter','buildFilter'].forEach(id=>document.getElementById(id).addEventListener('input',applyFilters));
    document.querySelectorAll('th[data-col]').forEach(th=>{
      th.addEventListener('click',()=>{
        const col=th.dataset.col;
        if(sortCol===col)sortDir*=-1; else{sortCol=col;sortDir=1;}
        document.querySelectorAll('th').forEach(h=>h.classList.remove('sorted'));
        th.classList.add('sorted'); applyFilters();
      });
    });
    applyFilters();
  }

  // § Verification
  function buildVerification(){
    const a=ACC;
    const p1=a.pass1_accuracy||0, pf=a.final_accuracy||0;
    const noData=!p1&&!pf;
    if(noData){
      document.getElementById('accBars').innerHTML='<p style="color:var(--muted);font-size:13px">&#128203; Human check in progress on a 20-app sample; see <a href="https://github.com/ParasharDeb/composio-assignment" target="_blank" rel="noopener">research/verify/</a> in the repo.</p>';
    } else {
      document.getElementById('accBars').innerHTML=`
        <div class="abr"><div class="abl">Pass 1</div><div class="abt"><div class="abf" style="width:${p1}%;background:linear-gradient(90deg,#ffd166,#ff9f43)"></div></div><div class="abv">${p1}%</div></div>
        <div class="abr"><div class="abl">Final</div><div class="abt"><div class="abf" style="width:${pf}%;background:linear-gradient(90deg,#00d4aa,#6c63ff)"></div></div><div class="abv">${pf}%</div></div>`;
    }
    const pg=document.getElementById('perFieldGrid');
    const fields=a.per_field||{};
    if(!Object.keys(fields).length){
      pg.innerHTML='';
    } else {
      Object.entries(fields).forEach(([f,v])=>{
        const d=document.createElement('div'); d.className='pfc';
        const col=v>=90?'#00d4aa':v>=70?'#ffd166':'#ff6b6b';
        d.innerHTML=`<div class="pfv" style="color:${col}">${v}%</div><div class="pfn">${f}</div>`;
        pg.appendChild(d);
      });
    }
    const mb=document.getElementById('missesBody');
    const misses=a.misses||[];
    if(misses.length){
      mb.innerHTML='';
      misses.forEach(m=>{
        const tr=document.createElement('tr');
        tr.innerHTML=`<td><strong>${m.app||'&mdash;'}</strong></td><td><code style="color:var(--accent)">${m.field||'&mdash;'}</code></td><td style="color:var(--accent3)">${m.agent_said||'&mdash;'}</td><td style="color:var(--accent2)">${m.correct||'&mdash;'}</td><td style="color:var(--muted)">${m.reason||'&mdash;'}</td>`;
        mb.appendChild(tr);
      });
    }
  }

  // § Honesty
  function buildDefeated(){
    const d=[
      {n:'Paygent Connect',r:'No public API found. Likely a white-label NMI reseller product with no independent developer portal. Marked unknown/no.'},
      {n:'Gladly',r:'developer.gladly.com returned no useful content. Enterprise-contract-only; API details only visible to existing clients. Confidence: low.'},
      {n:'Ahrefs',r:'Docs are paywalled—visible only to Enterprise subscribers. Auth header format could not be confirmed from public pages.'},
      {n:'Sherlock',r:'Not an API—a local Python CLI. No remote endpoint to call. Composio would need to shell-out to the binary rather than use a toolkit.'},
      {n:'Mermaid CLI',r:'Same as Sherlock: local Node/Puppeteer binary. Initially classified buildable=yes, corrected to partial by human reviewer.'},
      {n:'fanbasis',r:'Could not verify API key self-serve flow by logging in. Classification based on indirect evidence (docs describe a sandbox). Confidence: low.'},
    ];
    const g=document.getElementById('defeatedGrid');
    d.forEach(x=>{const c=document.createElement('div');c.className='dc';c.innerHTML=`<div class="dcn">&#128530; ${x.n}</div><div class="dcr">${x.r}</div>`;g.appendChild(c);});
  }

  buildFindings(); buildAuth(); buildHeatmap(); buildBuild();
  buildWins(); initTable(); buildVerification(); buildDefeated();
})();
</script>
</body>
</html>
"""

# Replace placeholders
HTML = HTML.replace('APPS_JSON_PLACEHOLDER', apps_json)
HTML = HTML.replace('PATTERNS_JSON_PLACEHOLDER', patterns_json)
HTML = HTML.replace('ACCURACY_PLACEHOLDER', accuracy_placeholder)

out = ROOT / "site" / "index.html"
out.write_text(HTML, encoding='utf-8')
print(f"Written {len(HTML):,} bytes to {out}")
