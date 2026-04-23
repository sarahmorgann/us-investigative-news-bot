import os, re, time, random, hashlib, feedparser, requests
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

BB_URL   = "https://neighborhoodnurturers.com"
BB_USER  = os.environ["BB_USER2"]
BB_PASS  = os.environ["BB_PASS2"]
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
    "this is exactly what gets buried",
    "pay attention to this one",
    "sharing because i think people need to see this",
    "they wont cover this so im sharing it",
    "found this independently",
    "big story, small coverage",
    "seeing this nowhere in mainstream news",
    "this is why you follow independent sources",
    "not a peep about this from major outlets",
    "this matters and its not getting coverage",
    "real journalism still exists",
    "solid reporting on something major",
    "the press isnt covering this",
    "thought this was important enough to share",
    "posting because this shouldnt be ignored",
    "if you only get news from tv you wont see this",
    "independent sources are all over this",
    "this story is being ignored",
    "worth your time to read",
    "found through independent reporting",
    "nobody wants to touch this",
    "its buried but its important",
    "sharing for awareness",
    "following the independent reporters on this one",
    "this wont be on the evening news",
    "passing this along",
    "saw this and had to share",
    "not seeing any mainstream coverage",
    "worth following",
    "this is the news they skip",
    "important and underreported",
    "dug this up",
    "serious story, minimal coverage",
    "im sharing this because its not getting out",
    "just found this",
    "this one is getting buried",
    "real reporting on a real issue",
    "thought this was worth spreading",
    "sharing so it doesnt get lost",
    "good investigative piece",
    "this should be bigger news",
    "cant believe this isnt everywhere",
    "worth the read",
    "passing this on",
    "saw it, sharing it",
    "this is huge and no one is saying anything",
    "major story, zero coverage",
    "came across this today",
    "sharing for the community",
    "this one matters",
    "keeping an eye on this",
    "saw this and thought you all should know",
    "found this outside of mainstream",
    "this is getting ignored",
    "important reporting",
    "no one is covering this and they should be",
    "reading between the lines here",
    "this is why independent media matters",
    "the networks wont touch this",
    "sharing from independent sources",
    "came across this in independent reporting",
    "not on any major network",
    "quietly happening and barely covered",
    "sharing what the mainstream skips",
    "this is the kind of thing that gets buried fast",
    "wont see this trending anywhere",
    "pulling this from independent reporting",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "news - this isnt getting coverage",
    "news worth sharing",
    "national news that got buried",
    "news you wont see on tv",
    "news from independent sources",
    "news the mainstream skipped",
    "news - this matters",
    "news worth reading",
    "news - found this outside mainstream",
    "news that deserves attention",
    "news - nobody is reporting on this",
    "news from investigative reporters",
    "news they dont want trending",
    "news - underreported",
    "news worth knowing",
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
    "follow the link for more",
    "read it yourself",
    "this is worth your time",
    "follow the reporting",
    "more at the link",
    "full piece at the link",
    "go read it",
    "check the link",
    "this is ongoing",
    "keep an eye on this",
    "stay informed",
    "share if you think others should see this",
    "spread the word",
    "dont let this get buried",
    "pass it on",
    "hope this is useful",
    "sharing for awareness",
    "the full story is at the link",
    "this deserves to be read",
    "tell me what you think",
    "this is real reporting",
    "support independent journalism",
    "read the original source",
    "a lot more context in the full article",
    "this is just the surface",
    "there is more to this story",
    "stay tuned on this one",
    "this is developing",
    "follow closely",
    "glad this got reported",
    "took guts to publish this",
    "independent press doing what it should",
    "this is what journalism is supposed to look like",
    "more people need to see this",
    "not going to pretend i know all the details",
    "read it and decide for yourself",
    "make of it what you will",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
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

    # Random punctuation style
    drop_punct = random.random() < 0.35
    lower_start = random.random() < 0.45

    def humanize(s):
        if not s:
            return s
        if lower_start:
            s = s[0].lower() + s[1:] if len(s) > 1 else s.lower()
        if drop_punct and s and s[-1] in '.,:':
            s = s[:-1]
        return s

    parts = []
    if intro:
        parts.append(humanize(intro))
    parts.append(f'"{title}"')
    if summary:
        from bs4 import BeautifulSoup
        clean = BeautifulSoup(summary, "html.parser").get_text()[:220].strip()
        if clean:
            parts.append(clean)
    parts.append(link)
    if outro:
        parts.append(humanize(outro))
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
