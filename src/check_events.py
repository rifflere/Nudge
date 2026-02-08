'''
check_events.py
- Load config
- Launch Playwright
- Load URL
- Extract text
- Normalize text
- Compare to previous run
- Email if changes exist
- Save updated state
'''

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError

from emailer import send_email


DATA_PATH = Path("data/last_events.json")


def load_env():
    """Load environment variables and fail fast if required ones are missing."""
    load_dotenv()

    required_vars = [
        "TARGET_URL",
        "EVENTS_CONTAINER_SELECTOR",
        "EVENT_ITEM_SELECTOR",
        "NOTIFY_EMAIL",
        "FROM_EMAIL",
        "EMAIL_PASSWORD",
        "SMTP_HOST",
        "SMTP_PORT",
    ]

    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")


def load_previous_events():
    """Load the previously-seen events from disk."""
    if not DATA_PATH.exists():
        return set()

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return set(json.load(f))


def save_events(events):
    """Persist the current set of events to disk."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(events), f, indent=2)


def normalize_event_text(text):
    """
    Normalize text so small formatting changes don't trigger false positives.
    """
    return " ".join(text.split())


def fetch_current_events():
    """Use Playwright to load the page and extract event text."""
    url = os.getenv("TARGET_URL")
    container_selector = os.getenv("EVENTS_CONTAINER_SELECTOR")
    item_selector = os.getenv("EVENT_ITEM_SELECTOR")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, timeout=60_000)

        try:
            page.wait_for_selector(container_selector, timeout=30_000)
        except TimeoutError:
            browser.close()
            raise RuntimeError("Timed out waiting for events container")

        container = page.locator(container_selector)
        items = container.locator(item_selector).all()

        events = set()
        for item in items:
            text = item.inner_text().strip()
            if not text:
                continue

            normalized = normalize_event_text(text)
            events.add(normalized)

        browser.close()
        return events


def main():
    load_env()

    previous_events = load_previous_events()
    current_events = fetch_current_events()

    new_events = current_events - previous_events

    if new_events:
        send_email(sorted(new_events))

    save_events(current_events)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
