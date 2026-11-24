#!/usr/bin/env python3
"""FountNews ই-পেপার জেনারেটর: Blogger ফিড -> ৪ পাতার ছবি + PDF + docs/index.json"""
import base64, datetime as dt, html, json, re, shutil, urllib.parse, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

BLOG = "https://fountnews24.blogspot.com"
# (পাতার নাম, Blogger লেবেল; None = সব খবর থেকে)। লেবেলের বানান ব্লগের লেবেলের সঙ্গে হুবহু মিলতে হবে।
PAGES = [  # (পাতার নাম, Blogger লেবেল; None = সব খবর, ক'ঘণ্টার খবর নেবে)
    ("প্রথম পাতা", None, 24), ("জাতীয়", "National", 24), ("রাজনীতি", "Politics", 24),
    ("আন্তর্জাতিক", "World", 24), ("খেলা", "Sports", 24), ("মতামত", "Opinion", 72),
    ("ইসলাম", "Islam", 48), ("সম্পাদকীয়", "Editorial", 72),
]
KEEP_DAYS = 60
TZ = ZoneInfo("Asia/Dhaka")
ROOT = Path(__file__).parent
OUT = ROOT / "docs"
MONTHS = "জানুয়ারি ফেব্রুয়ারি মার্চ এপ্রিল মে জুন জুলাই আগস্ট সেপ্টেম্বর অক্টোবর নভেম্বর ডিসেম্বর".split()
DAYS = "সোমবার মঙ্গলবার বুধবার বৃহস্পতিবার শুক্রবার শনিবার রবিবার".split()

def bn(s): return str(s).translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))

def fetch(label=None, n=60):
    path = "/feeds/posts/default" + ("/-/" + urllib.parse.quote(label) if label else "")
    req = urllib.request.Request(f"{BLOG}{path}?alt=json&max-results={n}", headers={"User-Agent": "FountNewsEPaper/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    posts = []
    for e in data.get("feed", {}).get("entry", []):
        content = e.get("content", {}).get("$t", "")
        link = next((l["href"] for l in e.get("link", []) if l.get("rel") == "alternate"), "")
        img = e.get("media$thumbnail", {}).get("url", "")
        if img:
            img = re.sub(r"/s\d+(-c)?/", "/w900/", img)
        else:
            m = re.search(r'<img[^>]+src="([^"]+)"', content)
            img = m.group(1) if m else ""
        body = re.sub(r"(?is)<(style|script)\b.*?</\1>", " ", content)
        text = html.unescape(re.sub(r"<[^>]+>", " ", body))
        if "{" in text:
            text = re.sub(r"[^{}]*\{[^{}]*\}", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        posts.append(dict(title=e["title"]["$t"].strip(), link=link, img=img, text=text,
                          time=dt.datetime.fromisoformat(e["published"]["$t"])))
    posts.sort(key=lambda p: p["time"], reverse=True)
    return posts

def recent(posts, hours=24):
    cut = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    r = [p for p in posts if p["time"] >= cut]
    return r if len(r) >= 3 else posts[:7]

def clip(t, n):
    if len(t) <= n: return t
    return t[:n].rsplit(" ", 1)[0] + "…"

E = html.escape

def link_attr(p):
    return f'data-link="{E(p["link"])}" data-t="{E(clip(p["title"], 90))}"'

def ttl(p):
    return f'<a href="{E(p["link"])}">{E(p["title"])}</a>'

def thumb(p):
    return f'<img class="thumb" src="{E(p["img"])}" alt="">' if p["img"] else ""

def side_block(p):
    return f'<div class="sd" {link_attr(p)}>{thumb(p)}<h3>{ttl(p)}</h3><p>{E(clip(p["text"], 220))}</p></div>'

def rib_box(p):
    return f'<div class="rb" {link_attr(p)}><h3>{ttl(p)}</h3><p>{E(clip(p["text"], 100))}</p></div>'

def col_item(p):
    return f'<div class="col" {link_attr(p)}>{thumb(p)}<h3>{ttl(p)}</h3><p>{E(clip(p["text"], 90))}</p></div>'

def lead_block(p):
    img = f'<img class="pic" src="{E(p["img"])}" alt="">' if p["img"] else ""
    return (f'<div class="lead" {link_attr(p)}><h2>{ttl(p)}</h2>{img}'
            f'<p class="ls">{E(clip(p["text"], 520))}</p></div>')

ISLAM = """<div class="adi"><svg class="art" viewBox="0 0 300 100" xmlns="http://www.w3.org/2000/svg">
<g fill="#e9cc83" stroke="#e9cc83"><path d="M15 100V63H38V45Q52 13 66 45V100Z" opacity=".65"/><path d="M35 45L52 6L69 45Z" opacity=".8"/>
<path d="M105 100V51Q150 -15 195 51V100Z" opacity=".8"/><path d="M145 26L150 5L155 26Z"/>
<path d="M210 100V62H232V45Q245 14 258 45V100Z" opacity=".65"/><path d="M229 45L245 7L261 45Z" opacity=".8"/>
<path d="M130 100V69Q150 44 170 69V100Z" fill="#063b2d" stroke="none"/><path d="M150 5V0M52 6V0M245 7V0" stroke-width="2"/><path d="M15 100H270" stroke-width="2"/></g>
<path d="M265 13a12 12 0 1 0 15 15 13 13 0 0 1-15-15Z" fill="#ffe6a0"/></svg>
<div class="ct"><div class="tg">✦ FOUNTNEWS ISLAMIC LIBRARY ✦</div><h2>কুরআন-হাদিস ও দৈনন্দিন আমলের পাঠশালা</h2>
<p>আয়াত • হাদিস • দোয়া • সুন্নাহ • ইসলামি ক্যালেন্ডার</p></div>
<div class="ac"><a class="lib" data-t="ইসলামিক লাইব্রেরি" data-link="https://fountnews24.blogspot.com/p/islam.html" href="https://fountnews24.blogspot.com/p/islam.html">☪ ইসলামিক লাইব্রেরি</a>
<a class="dlb" data-t="অ্যাপ ডাউনলোড" data-link="https://apk.fountnews.workers.dev/" href="https://apk.fountnews.workers.dev/">↓ অ্যাপ ডাউনলোড</a></div></div>"""

FNAD = """<div class="adf"><img class="wl" src="LOGO" alt="">
<h2>আপনার বিজ্ঞাপন দিন এখানে</h2><p class="sb">আপনার ব্যবসাকে লাখো পাঠকের সামনে পৌঁছে দিন</p>
<div class="chips"><span>ওয়েবসাইট</span><span>ই-পেপার</span><span>সোশ্যাল মিডিয়া</span></div>
<a class="cta" data-t="বিজ্ঞাপন দিন" data-link="https://fountnews24.blogspot.com/p/advertise.html" href="https://fountnews24.blogspot.com/p/advertise.html">বিজ্ঞাপনের তথ্য জানুন ›</a>
<div class="fb">ফেসবুক: /FountNews &nbsp;•&nbsp; fountnews24.blogspot.com</div></div>"""

def sheet(name, posts, logo, dateline, no, total):
    wd, _, dm = dateline.partition(", ")
    head = (f'<div class="mast"><div class="mb"><b>{wd}</b><span>{dm}</span></div>'
            f'<div class="lg"><img src="{logo}" alt="ফাউন্ট নিউজ"></div>'
            f'<div class="mb r"><b>পাতা {bn(no)}</b><span>fountnews24.blogspot.com</span></div></div>'
            f'<div class="band"><b>{E(name)}</b><i>তথ্যের স্বচ্ছ ঝর্ণাধারা</i></div>')
    ad_f = FNAD.replace("LOGO", logo)
    if not posts:
        body = ISLAM + '<p class="empty">আজ এই বিভাগে নতুন খবর নেই।</p>' + f'<div class="bot one">{ad_f}</div>'
    else:
        i = next((k for k, p in enumerate(posts) if p["img"]), 0)
        lead, rest = posts[i], posts[:i] + posts[i + 1:]
        sides, rib, mid, bot = rest[:4], rest[4:7], rest[7:10], rest[10:11]
        left, right = sides[0::2], sides[1::2]
        body = f'<div class="rib">{"".join(rib_box(p) for p in rib)}</div>' if rib else ""
        body += ISLAM
        cls = "g3" if len(sides) > 1 else ("g2" if sides else "g1")
        main = f'<div>{"".join(side_block(p) for p in left)}</div>' if left else ""
        main += f'<div>{lead_block(lead)}</div>'
        main += f'<div>{"".join(side_block(p) for p in right)}</div>' if right else ""
        body += f'<div class="main {cls}">{main}</div>'
        if mid:
            body += f'<div class="cols">{"".join(col_item(p) for p in mid)}</div>'
        if bot:
            body += f'<div class="bot"><div class="col" {link_attr(bot[0])}>{thumb(bot[0])}<h3>{ttl(bot[0])}</h3><p>{E(clip(bot[0]["text"], 160))}</p></div>{ad_f}</div>'
        else:
            body += f'<div class="bot one">{ad_f}</div>'
    return (f'<section class="sheet">{head}{body}'
            f'<div class="foot"><span>fountnews24.blogspot.com</span><span>{bn(no)} / {bn(total)}</span></div></section>')

FONTS = """@font-face{font-family:'SolaimanLipi';font-weight:400;font-display:block;src:url(https://fonts.maateen.me/solaiman-lipi/solaimanlipi-normal-v1.0.woff2) format('woff2')}
@font-face{font-family:'SolaimanLipi';font-weight:700;font-display:block;src:url(https://fonts.maateen.me/solaiman-lipi/solaimanlipi-bold-v1.0.woff2) format('woff2')}"""

CSS = """@page{size:A3;margin:8mm}*{box-sizing:border-box}
body{margin:0;background:#fff;color:#151515;font-family:'SolaimanLipi','Noto Sans Bengali',sans-serif;line-height:1.5}
a{color:inherit;text-decoration:none}
.sheet{width:900px;padding:22px 30px 18px;background:#fff;break-after:page;border-top:10px solid #c8102e}
@media print{.sheet{width:auto;padding:0}}
.mast{display:grid;grid-template-columns:1fr 1.7fr 1fr;align-items:center;gap:12px;padding-bottom:8px;border-bottom:3px solid #151515}
.lg img{height:104px;display:block;margin:0 auto}
.mb{font-size:15px;color:#444;line-height:1.5}.mb b{display:block;font-size:20px;color:#151515}.mb.r{text-align:right}
.band{background:#c8102e;color:#fff;display:flex;justify-content:space-between;align-items:center;padding:3px 14px;margin:6px 0 12px}
.band b{font-size:24px;font-weight:700}.band i{font-style:normal;font-size:15px}
.rib{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:12px}
.rb{border:2px solid #9a9a9a;border-radius:12px;padding:9px 13px}
.rb h3{margin:0 0 3px;font-size:21px;line-height:1.35;font-weight:700;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.rb p{margin:0;font-size:16px;color:#444;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.adi{position:relative;overflow:hidden;display:flex;align-items:center;justify-content:space-between;gap:12px;height:116px;padding:10px 20px;margin:0 0 14px;border-radius:10px;border:1.5px solid #c9a75b;background:linear-gradient(105deg,#063b2d,#116044 65%,#073c30)}
.adi .art{position:absolute;right:26%;top:0;height:116px;width:300px;opacity:.3}
.adi .ct{position:relative;z-index:2}.adi .tg{font-size:12px;color:#f4d78d;font-weight:700;letter-spacing:1px}
.adi h2{font-size:28px;color:#fff;margin:3px 0;font-weight:700}.adi p{font-size:15px;color:#e1eadc;margin:0}
.adi .ac{position:relative;z-index:2;display:flex;flex-direction:column;gap:8px}
.adi .ac a{font-size:15px;font-weight:700;padding:8px 14px;border-radius:8px;white-space:nowrap;text-align:center}
.adi .lib{background:linear-gradient(135deg,#ffe9ae,#d5ae5c);color:#16412f}.adi .dlb{background:#b90d20;color:#fff;border:1px solid #f4d78d}
.main{display:grid;gap:16px;margin-bottom:14px}
.g3{grid-template-columns:1fr 2.25fr 1fr}.g2{grid-template-columns:1fr 2.25fr}.g1{grid-template-columns:1fr}
.main>div+div{border-left:1px solid #bdbdbd;padding-left:16px}
.lead h2{font-size:48px;line-height:1.28;margin:0 0 10px;text-align:center;font-weight:700;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.pic{width:100%;aspect-ratio:16/10;object-fit:cover;display:block;background:#ddd}
.ls{margin:10px 0 0;font-size:19px;color:#222;text-align:justify;column-count:2;column-gap:18px;column-rule:1px solid #ccc}
.sd{padding:0 0 12px;margin:0 0 12px;border-bottom:1px solid #cfcfcf}.sd:last-child{border:0}
.sd h3,.col h3{margin:0 0 5px;font-weight:700;line-height:1.38;display:-webkit-box;-webkit-box-orient:vertical;overflow:hidden}
.sd h3{font-size:24px;-webkit-line-clamp:5}
.sd p,.col p{margin:0;font-size:17px;color:#444;display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden}
.thumb{width:100%;aspect-ratio:16/10;object-fit:cover;display:block;margin-bottom:8px;background:#ddd}
.cols{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-bottom:14px;padding-top:12px;border-top:4px double #151515}
.col h3{font-size:24px;-webkit-line-clamp:4}.col p{-webkit-line-clamp:3}
.bot{display:grid;grid-template-columns:1fr 1.7fr;gap:18px;align-items:stretch;border-top:4px double #151515;padding-top:12px}
.bot.one{grid-template-columns:1fr}
.adf{position:relative;overflow:hidden;border-radius:12px;padding:20px 24px;color:#fff;text-align:center;min-height:250px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:9px;background:radial-gradient(circle at 12% 18%,rgba(255,255,255,.14),transparent 38%),radial-gradient(circle at 92% 88%,rgba(0,0,0,.28),transparent 45%),linear-gradient(125deg,#7d0719,#c8102e 60%,#8f0a1f);border:2px solid #f4d78d}
.adf .wl{height:46px;filter:brightness(0) invert(1)}
.adf h2{margin:0;font-size:38px;font-weight:700;line-height:1.25}.adf .sb{margin:0;font-size:18px;color:#ffe9ae}
.chips{display:flex;gap:8px;flex-wrap:wrap;justify-content:center}.chips span{border:1.5px solid rgba(255,255,255,.8);border-radius:999px;padding:3px 14px;font-size:15px;font-weight:600}
.cta{background:linear-gradient(135deg,#ffe9ae,#d5ae5c);color:#5a0a14;font-weight:700;font-size:17px;padding:9px 22px;border-radius:9px}
.fb{font-size:13px;color:#ffd7dc}
.foot{display:flex;justify-content:space-between;margin-top:14px;padding-top:6px;border-top:2px solid #151515;font-size:14px;color:#666}
.empty{text-align:center;color:#777;padding:90px 0;font-size:24px}"""

def page_html(day, pages):
    logo = "data:image/png;base64," + base64.b64encode((ROOT / "logo.png").read_bytes()).decode()
    d = dt.date.fromisoformat(day)
    line = f"{DAYS[d.weekday()]}, {bn(d.day)} {MONTHS[d.month - 1]} {bn(d.year)}"
    secs = "".join(sheet(n, p, logo, line, i + 1, len(pages)) for i, (n, p) in enumerate(pages))
    return ('<!DOCTYPE html><html lang="bn"><head><meta charset="utf-8"><link rel="stylesheet" '
            'href="https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;700&display=swap">'
            f'<style>{FONTS}{CSS}</style></head><body>{secs}</body></html>')

def render(day, pages, folder):
    from playwright.sync_api import sync_playwright
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / "_src.html"
    tmp.write_text(page_html(day, pages), encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 900, "height": 1400}, device_scale_factor=2)
        pg.goto(tmp.resolve().as_uri(), wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_function("[...document.images].every(i=>i.complete)", timeout=30000)
        hot = pg.evaluate("""() => [...document.querySelectorAll('.sheet')].map(s => {
            const r = s.getBoundingClientRect();
            return [...s.querySelectorAll('[data-link]')].map(e => {
                const b = e.getBoundingClientRect();
                return {x: +((b.left - r.left) / r.width * 100).toFixed(2), y: +((b.top - r.top) / r.height * 100).toFixed(2),
                        w: +(b.width / r.width * 100).toFixed(2), h: +(b.height / r.height * 100).toFixed(2),
                        u: e.dataset.link, t: e.dataset.t};
            });
        })""")
        for i in range(len(pages)):
            pg.locator(".sheet").nth(i).screenshot(path=str(folder / f"page-{i + 1}.png"))
        pg.emulate_media(media="print")
        pg.pdf(path=str(folder / "fountnews-epaper.pdf"), format="A3", print_background=True, prefer_css_page_size=True)
        b.close()
    tmp.unlink()
    return hot

def main():
    day = dt.datetime.now(TZ).strftime("%Y-%m-%d")
    allp, used, pages = recent(fetch()), set(), []
    for name, label, hrs in PAGES:
        src = allp if label is None else recent(fetch(label), hrs)
        pool = [p for p in src if p["link"] not in used] or src
        pick = pool[:12]
        used.update(p["link"] for p in pick)
        pages.append((name, pick if (label is None or pick) else []))
    hot = render(day, pages, OUT / day)
    idx_path = OUT / "index.json"
    days = json.loads(idx_path.read_text(encoding="utf-8"))["days"] if idx_path.exists() else []
    days = [d for d in days if d["date"] != day]
    days.insert(0, dict(date=day, pdf=f"{day}/fountnews-epaper.pdf",
                        pages=[dict(n=n, img=f"{day}/page-{i + 1}.png", hot=hot[i]) for i, (n, _) in enumerate(pages)]))
    days = sorted(days, key=lambda d: d["date"], reverse=True)[:KEEP_DAYS]
    for old in OUT.iterdir():
        if old.is_dir() and old.name not in {d["date"] for d in days}:
            shutil.rmtree(old)
    idx_path.write_text(json.dumps(dict(latest=day, days=days), ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main()
