#!/usr/bin/env python3
"""生成 stations.json：radio-browser 中文台 + cooltv.top 中文电台，去重并校验可播放。"""

import concurrent.futures
import json
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; radio-static/1.0)"}
RB_HOSTS = [
    "https://de1.api.radio-browser.info",
    "https://at1.api.radio-browser.info",
    "https://nl1.api.radio-browser.info",
]
RB_QUERY = ("/json/stations/search?limit=2000&hidebroken=true"
            "&order=clickcount&reverse=true&countrycode=CN")
COOL_URL = "https://cooltv.top/radio_public.json"

HLS_TAG = {
    "音乐": "音乐", "中文流行": "音乐", "古典音乐": "音乐",
    "轻音乐": "音乐", "爵士乐": "音乐", "怀旧金曲": "音乐",
    "交通": "交通", "综合": "综合", "电视": "电视", "网络": "",
}


def is_hls(url):
    return ".m3u8" in url.split("?")[0]


def fetch_radio_browser():
    for host in RB_HOSTS:
        try:
            req = urllib.request.Request(host + RB_QUERY, headers=UA)
            data = json.loads(urllib.request.urlopen(req, timeout=40).read().decode())
            if isinstance(data, list) and data:
                out = []
                for s in data:
                    url = (s.get("url_resolved") or s.get("url") or "").strip()
                    if not url.startswith("https://"):
                        continue
                    name = (s.get("name") or "").strip()
                    if not name:
                        continue
                    out.append({
                        "name": name,
                        "url": url,
                        "favicon": s.get("favicon") or "",
                        "country": s.get("country") or "",
                        "countrycode": s.get("countrycode") or "",
                        "tags": s.get("tags") or "",
                        "clickcount": s.get("clickcount") or 0,
                    })
                return out
        except Exception as e:
            print("radio-browser fail", host, e)
    return []


def fetch_cool_stations():
    try:
        req = urllib.request.Request(COOL_URL, headers=UA)
        data = json.loads(urllib.request.urlopen(req, timeout=40).read().decode())
        items = data.get("data") or []
        print("cooltv 条目", len(items))
        return [x for x in items if (x.get("country") or "") == "中国"]
    except Exception as e:
        print("cooltv fail", e)
        return []


def candidate_urls(item):
    for u in (item.get("stream_url") or "").split(";"):
        u = u.strip()
        if u.startswith("https://") and "/api/stream/" not in u:
            yield u


def check(url):
    """HLS 需要允许跨域；普通音频只需能取到。"""
    try:
        req = urllib.request.Request(url, method="HEAD", headers={**UA, "Origin": "https://radio.example"})
        r = urllib.request.urlopen(req, timeout=8)
        if not (200 <= r.status < 400):
            return False
        if is_hls(url):
            acao = (r.headers.get("Access-Control-Allow-Origin") or "").strip()
            return acao == "*" or acao.lower().startswith("https://radio.example")
        return True
    except Exception:
        try:
            req = urllib.request.Request(url, headers={**UA, "Range": "bytes=0-0"})
            r = urllib.request.urlopen(req, timeout=8)
            return 200 <= r.status < 400
        except Exception:
            return False


def main():
    base = fetch_radio_browser()
    print("radio-browser 保留", len(base))

    cool = fetch_cool_stations()
    urls, seen_url = [], set()
    for item in cool:
        for u in candidate_urls(item):
            if u not in seen_url:
                seen_url.add(u)
                urls.append(u)

    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as ex:
        ok = dict(zip(urls, ex.map(check, urls)))
    print("候选", len(urls), "可用", sum(ok.values()))

    names = {s["name"].strip().lower() for s in base}
    added = []
    for item in cool:
        name = (item.get("name") or "").strip()
        if not name or name.lower() in names:
            continue
        for u in candidate_urls(item):
            if ok.get(u):
                added.append({
                    "name": name,
                    "url": u,
                    "favicon": "",
                    "country": "中国",
                    "countrycode": "CN",
                    "tags": HLS_TAG.get(item.get("category") or "", ""),
                    "clickcount": 0,
                })
                names.add(name.lower())
                break

    final = base + added
    with open("stations.json", "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, separators=(",", ":"))
    print("写入", len(final), "台")


if __name__ == "__main__":
    main()
#（注：内容由AI生成）
