import os
import json
import asyncio
from dotenv import load_dotenv
from apify_client import ApifyClient
import telegram

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

INSTAGRAM_ACCOUNTS = [
    "taliamenzel",
    "tina_schwarz.lipoedem_talk",
    "lipoedemkeinproblem"
]

LAST_SEEN_FILE = os.path.join(os.path.dirname(__file__), "last_seen.json")


def load_last_seen():
    if os.path.exists(LAST_SEEN_FILE):
        with open(LAST_SEEN_FILE, "r") as f:
            return json.load(f)
    return {}


def save_last_seen(data):
    with open(LAST_SEEN_FILE, "w") as f:
        json.dump(data, f, indent=2)


def scrape_instagram():
    client = ApifyClient(APIFY_TOKEN)
    run_input = {
        "usernames": INSTAGRAM_ACCOUNTS,
        "resultsLimit": 5
    }
    print("Starte Apify Scraper...")
    run = client.actor("apify/instagram-profile-scraper").call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"{len(items)} Profile geladen.")
    return items


async def send_message(text):
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)


async def main():
    last_seen = load_last_seen()
    profiles = scrape_instagram()

    lines = ["📊 Instagram Tagesreport\n"]

    for profile in profiles:
        username = profile.get("username", "unbekannt")
        latest_posts = profile.get("latestPosts", [])

        last_id = last_seen.get(username)
        new_posts = []

        for post in latest_posts:
            if post.get("id") == last_id:
                break
            new_posts.append(post)

        if new_posts:
            lines.append(f"@{username} — {len(new_posts)} neuer Beitrag(e):")
            for post in new_posts[:3]:
                caption = (post.get("caption") or "")[:120]
                url = post.get("url", "")
                lines.append(f"• {caption or 'Kein Text'}")
                if url:
                    lines.append(f"  {url}")
            last_seen[username] = latest_posts[0].get("id") if latest_posts else last_id
        else:
            lines.append(f"@{username} — Keine neuen Beiträge")

        lines.append("")

    save_last_seen(last_seen)

    message = "\n".join(lines)
    await send_message(message)
    print("Report gesendet!")
    print(message)


if __name__ == "__main__":
    asyncio.run(main())
