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

def side_item(p):
    return f'<div class="side" {link_attr(p)}><h3>{ttl(p)}</h3><p>{E(clip(p["text"], 110))}</p></div>'

def col_item(p):
    img = f'<img class="thumb" src="{E(p["img"])}" alt="">' if p["img"] else ""
    return f'<div class="col" {link_attr(p)}>{img}<h3>{ttl(p)}</h3><p>{E(clip(p["text"], 90))}</p></div>'

def sheet(name, posts, logo, dateline, no, total):
    if not posts:
        body = '<p class="empty">আজ এই বিভাগে নতুন খবর নেই।</p>'
    else:
        i = next((k for k, p in enumerate(posts) if p["img"]), 0)
        lead, rest = posts[i], posts[:i] + posts[i + 1:]
        img = f'<img class="pic" src="{E(lead["img"])}" alt="">' if lead["img"] else ""
        lead_html = f'<div class="lead" {link_attr(lead)}>{img}<h2>{ttl(lead)}</h2><p>{E(clip(lead["text"], 240))}</p></div>'
        if rest[:3]:
            body = f'<div class="grid">{lead_html}<div class="sides">{"".join(side_item(p) for p in rest[:3])}</div></div>'
        else:
            body = f'<div class="grid one">{lead_html}</div>'
        if rest[3:]:
            body += f'<div class="cols">{"".join(col_item(p) for p in rest[3:6])}</div>'
    return (f'<section class="sheet"><div class="mast"><img src="{logo}" alt="ফাউন্ট নিউজ">'
            f'<div class="bar"><span>{dateline}</span><span>তথ্যের স্বচ্ছ ঝর্ণাধারা</span><span>পাতা {bn(no)}</span></div></div>'
            f'<div class="sec"><b>{E(name)}</b></div>{body}'
            f'<div class="foot"><span>fountnews24.blogspot.com</span><span>{bn(no)} / {bn(total)}</span></div></section>')

CSS = """@page{size:A3;margin:8mm}*{box-sizing:border-box}
body{margin:0;background:#fff;color:#151515;font-family:'Noto Sans Bengali','Noto Serif Bengali',sans-serif;line-height:1.6}
h2,h3,.sec b{font-family:'Noto Serif Bengali',serif}
a{color:inherit;text-decoration:none}
.sheet{width:900px;padding:30px 34px 22px;background:#fff;break-after:page;border-top:10px solid #c8102e}
@media print{.sheet{width:auto;padding:0}}
.mast{text-align:center;padding-bottom:10px}
.mast img{height:110px;display:block;margin:0 auto 10px}
.bar{display:flex;justify-content:space-between;font-size:17px;color:#555;border-top:2px solid #151515;border-bottom:1px solid #151515;padding:6px 2px}
.sec{margin:20px 0 16px;display:flex;align-items:center;gap:14px}
.sec b{background:#c8102e;color:#fff;font-size:24px;font-weight:800;padding:4px 20px;border-radius:2px}
.sec:after{content:"";flex:1;border-top:3px solid #c8102e}
.grid{display:grid;grid-template-columns:1.7fr 1fr;gap:28px}.grid.one{grid-template-columns:1fr}
.pic{width:100%;aspect-ratio:16/10;object-fit:cover;display:block;background:#ddd}
.lead h2{font-size:46px;line-height:1.28;margin:16px 0 10px;font-weight:800;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.lead p{margin:0;font-size:21px;color:#333;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.side{padding:0 0 16px;margin:0 0 16px;border-bottom:1px solid #cfcfcf}.side:last-child{border:0}
.side h3,.col h3{margin:0 0 6px;font-weight:700;line-height:1.38;display:-webkit-box;-webkit-box-orient:vertical;overflow:hidden}
.side h3{font-size:27px;-webkit-line-clamp:4}
.side p,.col p{margin:0;font-size:18px;color:#444;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.cols{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:24px;padding-top:20px;border-top:4px double #151515}
.thumb{width:100%;aspect-ratio:16/10;object-fit:cover;display:block;margin-bottom:10px;background:#ddd}
.col h3{font-size:23px;-webkit-line-clamp:4}
.foot{display:flex;justify-content:space-between;margin-top:22px;padding-top:8px;border-top:2px solid #151515;font-size:15px;color:#666}
.empty{text-align:center;color:#777;padding:120px 0;font-size:24px}"""

def page_html(day, pages):
    logo = "data:image/png;base64," + base64.b64encode((ROOT / "logo.png").read_bytes()).decode()
    d = dt.date.fromisoformat(day)
    line = f"{DAYS[d.weekday()]}, {bn(d.day)} {MONTHS[d.month - 1]} {bn(d.year)}"
    secs = "".join(sheet(n, p, logo, line, i + 1, len(pages)) for i, (n, p) in enumerate(pages))
    return ('<!DOCTYPE html><html lang="bn"><head><meta charset="utf-8"><link rel="stylesheet" '
            'href="https://fonts.googleapis.com/css2?family=Noto+Serif+Bengali:wght@700;800&family=Noto+Sans+Bengali:wght@400;600&display=swap">'
            f'<style>{CSS}</style></head><body>{secs}</body></html>')

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
        pick = pool[:7]
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
