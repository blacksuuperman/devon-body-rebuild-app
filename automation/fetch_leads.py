#!/usr/bin/env python3
"""Refresh leads.json for Devon's Day Book.

Runs once a day from GitHub Actions. Uses only the Python standard library.
Pulls a short list of UGC creator opportunities from a few public sources,
keeps only the ones that look like UGC or creator work, and writes leads.json
next to the app's sw.js. Every item links back to the original listing.
If a source fails, the others still run. If every source fails, the old
leads.json is left alone.
"""
import json, os, re, sys, html, datetime, urllib.request, xml.etree.ElementTree as ET

UA = "DevonsDayBook-LeadsBot/1.0 (personal family app; once a day; contact via GitHub repo)"
TODAY = datetime.date.today()
MAX_KEEP_DAYS = 14
MAX_ITEMS = 60

INCLUDE = re.compile(r"\b(ugc|user[- ]generated|content creator|creator|tiktok|reels|short[- ]form|influencer|brand ambassador|product video|unboxing|testimonial|video review)\b", re.I)
EXCLUDE = re.compile(r"\b(engineer|developer|full[- ]stack|designer|manager|recruit|sales rep|accountant|analyst|editor|copywriter|translator|animator|director|devops|data scientist)\b", re.I)
FIT = re.compile(r"\b(mom|moms|mother|mothers|mum|baby|babies|newborn|postpartum|pregnan\w*|nursing|breastfeed\w*|parent\w*|kids?|toddler|famil\w+|home|skincare|wellness|women|female|lifestyle|food|kitchen|cleaning)\b", re.I)
PAY = re.compile(r"\$\s?[\d,]+(?:\.\d+)?(?:\s?[-–]\s?\$?\s?[\d,]+(?:\.\d+)?)?(?:\s?(?:/|per\s)\s?(?:video|videos|hour|hr|post|month|mo|piece))?", re.I)
POSTED = re.compile(r"Posted\s+(?:today|yesterday|\d+\s+\w+\s+ago)", re.I)


def get(url, accept="*/*", timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def clean(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def item(id_, title, url, src, pay="", posted="", snip="", kind="job"):
    text = f"{title} {snip}"
    return {
        "id": id_, "t": title[:140], "brand": "", "pay": pay, "posted": posted, "src": src,
        "url": url, "snip": snip[:220], "kind": kind, "fit": bool(FIT.search(text)),
        "seen": TODAY.isoformat(),
    }


def relevant(title, snip=""):
    return bool(INCLUDE.search(title + " " + snip)) and not EXCLUDE.search(title)


def pitchlo():
    page = get("https://www.pitchlo.com/ugc-creator-jobs", "text/html")
    anchors = list(re.finditer(r'<a\b[^>]*href="([^"]*?/jobs/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}))"[^>]*>(.*?)</a>', page, re.S | re.I))
    out, seen = [], {}
    for i, m in enumerate(anchors):
        href, jid, inner = m.group(1), m.group(2), clean(m.group(3))
        if len(inner) < 6:
            continue
        nxt = next((a.start() for a in anchors[i + 1:] if a.group(2) != jid), len(page))
        ctx = clean(page[m.end():min(nxt, m.end() + 2500)])
        before = clean(page[max(0, m.start() - 400):m.start()])
        pay = (PAY.search(ctx) or PAY.search(before) or [None])
        pay = pay.group(0).strip() if hasattr(pay, "group") else ""
        pm = POSTED.search(ctx) or POSTED.search(before)
        url = href if href.startswith("http") else "https://www.pitchlo.com" + href
        snip = ctx[:260]
        if jid in seen:
            if len(inner) > len(out[seen[jid]]["t"]):
                out[seen[jid]]["t"] = inner[:140]
            continue
        if not relevant(inner, snip[:200]):
            continue
        seen[jid] = len(out)
        out.append(item("pitchlo:" + jid, inner, url, "Pitchlo", pay, pm.group(0).replace("Posted ", "") if pm else "", snip))
    return out


def remoteok():
    data = json.loads(get("https://remoteok.com/api", "application/json"))
    out = []
    for j in data:
        if not isinstance(j, dict) or "position" not in j:
            continue
        title = j.get("position", "")
        tags = " ".join(j.get("tags") or [])
        desc = clean(j.get("description", ""))[:240]
        if not relevant(title, tags + " " + desc[:120]):
            continue
        out.append(item("remoteok:" + str(j.get("id")), f"{title} ({j.get('company', '')})", j.get("url") or j.get("apply_url") or "https://remoteok.com", "Remote OK", "", (j.get("date") or "")[:10], desc))
    return out


def himalayas():
    xml = get("https://himalayas.app/jobs/rss", "application/rss+xml")
    root = ET.fromstring(xml)
    out = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        desc = clean(it.findtext("description") or "")[:240]
        if link and relevant(title, desc[:120]):
            out.append(item("himalayas:" + link, title, link, "Himalayas", "", (it.findtext("pubDate") or "")[:16], desc))
    return out


def momcreators():
    xml = get("https://momcreators.substack.com/feed", "application/rss+xml")
    root = ET.fromstring(xml)
    out = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub = (it.findtext("pubDate") or "")[:16]
        if link and title:
            out.append(item("momcreators:" + link, title, link, "Mom Creators newsletter", "", pub, clean(it.findtext("description") or "")[:200], kind="news"))
        if len(out) >= 3:
            break
    for o in out:
        o["fit"] = True
    return out


def site_dir():
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", ".github")]
        if "sw.js" in files:
            return root
    return "."


def main():
    out_path = os.path.join(site_dir(), "leads.json")
    old = {}
    try:
        with open(out_path, encoding="utf-8") as f:
            old = json.load(f)
    except Exception:
        pass
    fresh, status = [], []
    for name, fn in (("Pitchlo", pitchlo), ("Remote OK", remoteok), ("Himalayas", himalayas), ("Mom Creators", momcreators)):
        try:
            got = fn()
            fresh += got
            status.append({"name": name, "ok": True, "count": len(got)})
        except Exception as e:  # keep going; one bad source must not stop the rest
            status.append({"name": name, "ok": False, "error": str(e)[:80]})
        print(status[-1], file=sys.stderr)
    if not any(s["ok"] for s in status):
        print("Every source failed. Leaving leads.json as it was.", file=sys.stderr)
        return
    merged = {i["id"]: i for i in fresh}
    for i in old.get("items", []):  # keep recent older items so a bad day does not empty the list
        if i["id"] not in merged:
            try:
                age = (TODAY - datetime.date.fromisoformat(i.get("seen", ""))).days
            except Exception:
                age = 99
            if age <= MAX_KEEP_DAYS:
                merged[i["id"]] = i
        else:
            merged[i["id"]]["seen"] = i.get("seen", merged[i["id"]]["seen"])
    items = sorted(merged.values(), key=lambda x: (x.get("kind") == "news", not x.get("fit"), x.get("seen", "")), reverse=False)
    items = sorted(items, key=lambda x: x.get("seen", ""), reverse=True)[:MAX_ITEMS]
    doc = {"updated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "sources": status, "items": items}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
    print(f"Wrote {len(items)} items to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
