import os, re, time, random, hashlib, feedparser, requests
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

BB_URL   = os.environ["BB_URL"]
BB_USER  = os.environ["BB_USER"]
BB_PASS  = os.environ["BB_PASS"]
GROUP_ID = 1020
USER_ID  = 14289

FEEDS = [
    ("The Intercept",          "https://theintercept.com/feed/?rss"),
    ("MuckRock",               "https://www.muckrock.com/news/archives/feed/"),
    ("WhoWhatWhy",             "https://whowhatwhy.org/feed/"),
    ("Bellingcat",             "https://www.bellingcat.com/feed/"),
    ("Democracy Now",          "https://www.democracynow.org/democracynow.rss"),
    ("The Appeal",             "https://theappeal.org/feed/"),
    ("Reveal News",            "https://revealnews.org/feed/"),
    ("Documented",             "https://documentedny.com/feed/"),
    ("Just the News",          "https://justthenews.com/rss.xml"),
    ("Washington Free Beacon", "https://freebeacon.com/feed/"),
    ("Texas Tribune",          "https://www.texastribune.org/feed/"),
    ("Radar Online",           "https://radaronline.com/feed/"),
    ("Court Watch",            "https://courtwatch.substack.com/feed"),
    ("Law and Crime",          "https://lawandcrime.com/feed/"),
    ("ProPublica",             "https://www.propublica.org/feeds/propublica/main"),
    ("The Markup",             "https://themarkup.org/feeds/rss.xml"),
]

INTROS = [
    "this flew under the radar",
    "not seeing this covered anywhere else",
    "the kind of story big outlets skip",
    "worth knowing about",
    "this came through recently",
    "sharing this because it matters",
    "nobody is talking about this",
    "underreported and it matters",
    "independent reporting at its best",
    "this is the stuff that gets buried",
    "saw this, thought it was worth sharing",
    "keep seeing this ignored in mainstream news",
    "found this through independent sources",
    "this deserves more attention",
    "important story not getting covered",
    "the media wont report on this",
    "real investigative work here",
    "straight reporting, no spin",
    "this is what they dont want covered",
    "worth reading before it disappears",
    "came across this and had to share",
    "nobody in the mainstream is touching this",
    "",
    "",
    "",
]

OUTROS = [
    "draw your own conclusions",
    "judge for yourself",
    "worth reading the full piece",
    "this is why independent journalism matters",
    "sharing so it doesnt disappear",
    "make of that what you will",
    "important to know about",
    "form your own opinion on this one",
    "glad someone is covering this",
    "link in post",
    "do your own research too",
    "the full story is worth reading",
    "pay attention to this one",
    "",
    "",
    "",
]

def is_recent(entry, hours=48):
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            pub = datetime(*t[:6], tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - pub) < timedelta(hours=hours)
    return True

def get_token():
    r = requests.post(f"{BB_URL}/wp-json/jwt-auth/v1/token",
        json={"username": BB_USER, "password": BB_PASS}, timeout=30)
    r.raise_for_status()
    return r.json()["token"]

def fetch_posted(token, limit=60):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(f"{BB_URL}/wp-json/buddyboss/v1/activity",
            params={"group_id": GROUP_ID, "per_page": limit},
            headers=headers, timeout=30)
        seen = set()
        for item in r.json():
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(item.get("content", {}).get("rendered", ""), "html.parser")
            txt = soup.get_text().strip()[:120]
            seen.add(hashlib.md5(txt.lower().encode()).hexdigest())
        return seen
    except Exception:
        return set()

def post_activity(token, content):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(f"{BB_URL}/wp-json/buddyboss/v1/activity",
        json={"content": content, "group_id": GROUP_ID, "type": "activity_update"},
        headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def build_post(title, summary, link):
    intro = random.choice(INTROS)
    outro = random.choice(OUTROS)
    parts = []
    if intro:
        parts.append(intro)
    parts.append(f'"{title}"')
    if summary:
        from bs4 import BeautifulSoup
        clean = BeautifulSoup(summary, "html.parser").get_text()[:220].strip()
        if clean:
            parts.append(clean)
    parts.append(link)
    if outro:
        parts.append(outro)
    return "\n".join(parts)

def run():
    token = get_token()
    seen = fetch_posted(token)
    items = []
    for source, url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                if not is_recent(entry):
                    continue
                title   = entry.get("title", "").strip()
                summary = entry.get("summary", "")[:300]
                link    = entry.get("link", "")
                if not title or not link:
                    continue
                key = hashlib.md5(title.lower().strip().encode()).hexdigest()
                if key in seen:
                    continue
                items.append((source, title, summary, link, key))
        except Exception as e:
            print(f"[WARN] {source}: {e}")

    random.shuffle(items)
    posted = 0
    for source, title, summary, link, key in items[:4]:
        try:
            content = build_post(title, summary, link)
            post_activity(token, content)
            seen.add(key)
            posted += 1
            print(f"[OK] {source}: {title[:60]}")
            time.sleep(random.randint(25, 70))
        except Exception as e:
            print(f"[ERR] {e}")

    print(f"[DONE] Posted {posted}")

if __name__ == "__main__":
    run()
