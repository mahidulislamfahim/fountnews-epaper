#!/usr/bin/env python3
"""FountNews ই-পেপার জেনারেটর: Blogger ফিড -> ৪ পাতার ছবি + PDF + docs/index.json"""
import base64, datetime as dt, html, json, re, shutil, urllib.parse, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

BLOG = "https://fountnews24.blogspot.com"
# (পাতার নাম, Blogger লেবেল; None = সব খবর থেকে)। লেবেলের বানান ব্লগের লেবেলের সঙ্গে হুবহু মিলতে হবে।
PAGES = [("প্রথম পাতা", None), ("জাতীয়", "National"), ("রাজনীতি", "Politics"), ("আন্তর্জাতিক", "World")]
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
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", content))).strip()
        posts.append(dict(title=e["title"]["$t"].strip(), link=link, img=img, text=text,
                          time=dt.datetime.fromisoformat(e["published"]["$t"])))
    posts.sort(key=lambda p: p["time"], reverse=True)
    return posts

def recent(posts):
    cut = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24)
    r = [p for p in posts if p["time"] >= cut]
    return r if len(r) >= 3 else posts[:7]

def clip(t, n):
    if len(t) <= n: return t
    return t[:n].rsplit(" ", 1)[0] + "…"

E = html.escape
def item(p): return f'<div class="item"><h3>{E(p["title"])}</h3><p>{E(clip(p["text"], 120))}</p></div>'

def sheet(name, posts, logo, dateline, no):
    if not posts:
        body = '<p class="empty">আজ এই বিভাগে নতুন খবর নেই।</p>'
    else:
        i = next((k for k, p in enumerate(posts) if p["img"]), 0)
        lead, rest = posts[i], posts[:i] + posts[i + 1:]
        img = f'<img class="pic" src="{E(lead["img"])}" alt="">' if lead["img"] else ""
        body = (f'<div class="grid"><div class="lead">{img}<h2>{E(lead["title"])}</h2><p>{E(clip(lead["text"], 260))}</p></div>'
                f'<div>{"".join(item(p) for p in rest[:3])}</div></div>')
        if rest[3:]:
            body += f'<div class="cols">{"".join(item(p) for p in rest[3:6])}</div>'
    return (f'<section class="sheet"><div class="mast"><img src="{logo}" alt="ফাউন্ট নিউজ">'
            f'<p><span>{dateline}</span><span>তথ্যের স্বচ্ছ ঝর্ণাধারা</span><span>পাতা {bn(no)}</span></p></div>'
            f'<div class="sec">{E(name)}</div>{body}</section>')

CSS = """@page{size:A3;margin:8mm}*{box-sizing:border-box}
body{margin:0;background:#fff;color:#161616;font-family:'Noto Serif Bengali',serif;line-height:1.55}
.sheet{width:1100px;padding:28px;background:#fff;break-after:page}
@media print{.sheet{width:auto;padding:0}}
.mast{text-align:center;border-bottom:3px double #161616;padding-bottom:8px;margin-bottom:12px}
.mast img{height:84px;display:block;margin:0 auto 6px}
.mast p{margin:0;font-size:13px;color:#6b6560;display:flex;justify-content:space-between}
.sec{background:#161616;color:#fff;display:inline-block;padding:2px 14px;font-weight:600;margin:0 0 12px}
.grid{display:grid;grid-template-columns:2fr 1fr;gap:22px}
.pic{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}
.lead h2{font-size:34px;line-height:1.3;margin:10px 0;font-weight:800}
.lead p,.item p{margin:0 0 8px;font-size:15px;text-align:justify}
.item{border-top:1px solid #d9d4cf;padding:10px 0}.item h3{margin:0 0 4px;font-size:18px;line-height:1.4}
.cols{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin-top:16px;border-top:3px double #161616;padding-top:12px}
.cols .item:first-child{border-top:0}.empty{text-align:center;color:#6b6560;padding:80px 0}"""

def page_html(day, pages):
    logo = "data:image/png;base64," + base64.b64encode((ROOT / "logo.png").read_bytes()).decode()
    d = dt.date.fromisoformat(day)
    line = f"{DAYS[d.weekday()]}, {bn(d.day)} {MONTHS[d.month - 1]} {bn(d.year)}"
    secs = "".join(sheet(n, p, logo, line, i + 1) for i, (n, p) in enumerate(pages))
    return ('<!DOCTYPE html><html lang="bn"><head><meta charset="utf-8"><link rel="stylesheet" '
            'href="https://fonts.googleapis.com/css2?family=Noto+Serif+Bengali:wght@400;600;800&display=swap">'
            f'<style>{CSS}</style></head><body>{secs}</body></html>')

def render(day, pages, folder):
    from playwright.sync_api import sync_playwright
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / "_src.html"
    tmp.write_text(page_html(day, pages), encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1100, "height": 1500}, device_scale_factor=1.5)
        pg.goto(tmp.resolve().as_uri(), wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_function("[...document.images].every(i=>i.complete)", timeout=30000)
        for i in range(len(pages)):
            pg.locator(".sheet").nth(i).screenshot(path=str(folder / f"page-{i + 1}.png"))
        pg.emulate_media(media="print")
        pg.pdf(path=str(folder / "fountnews-epaper.pdf"), format="A3", print_background=True, prefer_css_page_size=True)
        b.close()
    tmp.unlink()

def main():
    day = dt.datetime.now(TZ).strftime("%Y-%m-%d")
    allp, used, pages = recent(fetch()), set(), []
    for name, label in PAGES:
        src = allp if label is None else recent(fetch(label))
        pool = [p for p in src if p["link"] not in used] or src
        pick = pool[:7]
        used.update(p["link"] for p in pick)
        pages.append((name, pick if (label is None or pick) else []))
    render(day, pages, OUT / day)
    idx_path = OUT / "index.json"
    days = json.loads(idx_path.read_text(encoding="utf-8"))["days"] if idx_path.exists() else []
    days = [d for d in days if d["date"] != day]
    days.insert(0, dict(date=day, pdf=f"{day}/fountnews-epaper.pdf",
                        pages=[dict(n=n, img=f"{day}/page-{i + 1}.png") for i, (n, _) in enumerate(pages)]))
    days = sorted(days, key=lambda d: d["date"], reverse=True)[:KEEP_DAYS]
    for old in OUT.iterdir():
        if old.is_dir() and old.name not in {d["date"] for d in days}:
            shutil.rmtree(old)
    idx_path.write_text(json.dumps(dict(latest=day, days=days), ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main()
