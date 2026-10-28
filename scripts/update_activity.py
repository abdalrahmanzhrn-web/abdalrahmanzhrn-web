"""Refresh the profile card using public GitHub data. Python standard library only."""
from datetime import date, datetime, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.request import Request, urlopen

LOGIN = "abdalrahmanzhrn-web"
ROOT = Path(__file__).resolve().parents[1]


def fetch(url):
    request = Request(url, headers={"User-Agent": f"{LOGIN}-profile-readme"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
        self.in_heading = False
        self.heading = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h2" and attrs.get("id") == "js-contribution-activity-description":
            self.in_heading = True
        if tag == "td" and attrs.get("data-date") and "data-level" in attrs:
            self.days[date.fromisoformat(attrs["data-date"])] = int(attrs["data-level"])

    def handle_endtag(self, tag):
        if tag == "h2":
            self.in_heading = False

    def handle_data(self, text):
        if self.in_heading:
            self.heading.append(text)


def main():
    calendar = Calendar()
    calendar.feed(fetch(f"https://github.com/users/{LOGIN}/contributions"))
    match = re.search(r"([\d,]+)\s+contributions?", " ".join(calendar.heading))
    if not match or len(calendar.days) < 350 or any(v not in range(5) for v in calendar.days.values()):
        raise RuntimeError("GitHub calendar response changed; retaining the last valid card.")
    total = int(match[1].replace(",", ""))
    days = sorted(calendar.days.items())
    active = sum(level > 0 for _, level in days)
    longest = streak = 0
    for _, level in days:
        streak = streak + 1 if level else 0
        longest = max(longest, streak)
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    colors = ["#211a17", "#482420", "#70332d", "#a65342", "#d29a76"]
    pieces = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="340" viewBox="0 0 1000 340" role="img" aria-labelledby="title desc">
<title id="title">GitHub activity</title>
<desc id="desc">{total} contributions, {active} active days and a longest streak of {longest} days in the displayed calendar. Refreshed {updated}.</desc>
<rect x="1" y="1" width="998" height="338" rx="16" fill="#0d0a08" stroke="#392c24"/>
<g font-family="Segoe UI,Arial,sans-serif" fill="#eee4d2">
<text x="32" y="39" fill="#c19b79" font-size="12" letter-spacing="2">CONTRIBUTIONS</text>''']
    stats = [(total, "CONTRIBUTIONS"), (active, "ACTIVE DAYS"), (longest, "LONGEST STREAK · DAYS")]
    for i, (value, label) in enumerate(stats):
        x = 32 + i * 322
        pieces.append(f'<text x="{x}" y="89" font-size="32" font-weight="600">{value:,}</text><text x="{x}" y="113" font-size="10" fill="#ab9983" letter-spacing="1">{label}</text>')
    start = days[0][0]
    last_month = None
    for day, level in days:
        index = (day - start).days
        week, weekday = divmod(index, 7)
        x, y = 56 + week * 17, 161 + weekday * 17
        if day.month != last_month:
            if week < 52 and day.day == 1:
                pieces.append(f'<text x="{x}" y="150" font-size="10" fill="#ab9983">{day:%b}</text>')
            last_month = day.month
        pieces.append(f'<rect x="{x}" y="{y}" width="13" height="13" rx="3" fill="{colors[level]}"><title>{day}: contribution level {level}/4</title></rect>')
    for label, row in [("M", 1), ("W", 3), ("F", 5)]:
        pieces.append(f'<text x="31" y="{171+row*17}" font-size="10" fill="#ab9983">{label}</text>')
    pieces.append(f'<text x="32" y="313" font-size="10" fill="#ab9983">{start} — {days[-1][0]} · Refreshed {escape(updated)}</text>')
    pieces.append('<text x="810" y="313" font-size="10" fill="#ab9983">Less</text>')
    for i, color in enumerate(colors):
        pieces.append(f'<rect x="{839+i*16}" y="303" width="12" height="12" rx="2" fill="{color}"/>')
    pieces.append('<text x="925" y="313" font-size="10" fill="#ab9983">More</text></g></svg>')
    target = ROOT / "assets" / "activity.svg"
    target.parent.mkdir(parents=True, exist_ok=True)
    generated = "\n".join(pieces)
    without_timestamp = lambda svg: re.sub(r"Refreshed \d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC", "Refreshed <time>", svg)
    if target.exists() and without_timestamp(target.read_text(encoding="utf-8")) == without_timestamp(generated):
        print("Contribution calendar unchanged.")
        return
    target.write_text(generated, encoding="utf-8")
    print(f"Updated activity card: {total} contributions, {len(days)} calendar days")


if __name__ == "__main__":
    main()
