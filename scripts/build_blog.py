#!/usr/bin/env python3
"""生成 blog.json：抓取「人文故事」三个节目的 RSS，取最近剧集，按发布时间从新到旧。"""

import json
import re
import urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (compatible; radio-static/1.0)"}
ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"

SHOWS = [
    {"id": "storyfm", "name": "故事FM", "feed": "https://feeds.storyfm.cn/storyfm.xml"},
    {"id": "hzyh", "name": "忽左忽右", "feed": "https://feed.xyzfm.space/cv4bkgpuglwp"},
    {"id": "whyx", "name": "文化有限", "feed": "https://s1.proxy.wavpub.com/weknownothing.xml"},
]

LIMIT = 100

MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}


def parse_date(text):
    """把 RSS 的 pubDate 归一成 YYYY-MM-DD。"""
    if not text:
        return ""
    m = re.search(r"(\d{1,2})\s+(\w{3})\s+(\d{4})", text)
    if m and m.group(2) in MONTHS:
        return "%s-%02d-%02d" % (m.group(3), MONTHS[m.group(2)], int(m.group(1)))
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return text[:10]
    return ""


def parse_duration(text):
    if not text:
        return ""
    if text.isdigit():
        sec = int(text)
        return "%d 分钟" % max(1, round(sec / 60))
    parts = [int(x) for x in re.findall(r"\d+", text)[:3]]
    if len(parts) == 3:
        h, m, s = parts
        total = h * 60 + m + round(s / 60)
    elif len(parts) == 2:
        total = parts[0] * 60 + parts[1]
    else:
        return ""
    return "%d 分钟" % max(1, total)


def fetch(feed):
    req = urllib.request.Request(feed, headers=UA)
    return ET.fromstring(urllib.request.urlopen(req, timeout=40).read())


def show_cover(channel):
    img = channel.find(ITUNES + "image")
    if img is not None and img.get("href"):
        return img.get("href")
    it = channel.find("image")
    if it is not None and it.findtext("url"):
        return it.findtext("url")
    return ""


def build_show(spec):
    try:
        root = fetch(spec["feed"])
    except Exception as e:
        print("feed fail", spec["name"], e)
        return None

    channel = root.find("channel")
    cover = show_cover(channel)
    episodes = []
    for item in channel.findall("item"):
        audio = ""
        for enc in item.findall("enclosure"):
            u = enc.get("url") or ""
            if u.startswith("https://"):
                audio = u
                break
        if not audio:
            continue
        title = (item.findtext("title") or "").strip()
        if not title:
            continue
        date = parse_date(item.findtext("pubDate"))
        item_cover = item.find(ITUNES + "image")
        episodes.append({
            "title": title,
            "date": date,
            "audio": audio,
            "duration": parse_duration(item.findtext(ITUNES + "duration")),
            "cover": (item_cover.get("href") if item_cover is not None and item_cover.get("href") else cover),
            "link": (item.findtext("link") or "").strip(),
        })

    # 按日期从新到旧
    episodes.sort(key=lambda e: e["date"], reverse=True)
    print(spec["name"], "剧集", len(episodes))
    return {
        "id": spec["id"],
        "name": spec["name"],
        "cover": cover,
        "episodes": episodes[:LIMIT],
    }


def main():
    shows = []
    for spec in SHOWS:
        s = build_show(spec)
        if s:
            shows.append(s)
    out = {"shows": shows}
    with open("blog.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("写入 blog.json，节目", len(shows),
          "剧集", sum(len(s["episodes"]) for s in shows))


if __name__ == "__main__":
    main()
#（注：内容由AI生成）
