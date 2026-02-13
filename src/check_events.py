'''
check_events.py
- Load config
- Launch Playwright
- Load URL
- Extract text
- Normalize text
- Compare to previous run
- Email if changes exist
- Save updated state (encrypted for GitHub Actions)
'''

import json
import os
import sys
from pathlib import Path
import logging

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError
from cryptography.fernet import Fernet

from emailer import send_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


def get_encryption_key():
    """Get encryption key from environment."""
    key = os.getenv("ARTIFACT_ENCRYPTION_KEY")
    if not key:
        # Only required in GitHub Actions
        if os.getenv("GITHUB_ACTIONS"):
            raise RuntimeError("ARTIFACT_ENCRYPTION_KEY not set in GitHub Actions")
        return None
    return key.encode()


def load_previous_events():
    """Load the previously-seen events from disk."""
    # In GitHub Actions, try encrypted file first
    if os.getenv("GITHUB_ACTIONS"):
        encryption_key = get_encryption_key()
        encrypted_path = Path("data/last_events.json.enc")
        
        if encryption_key and encrypted_path.exists():
            logger.info(f"Loading encrypted artifact from: {encrypted_path}")
            try:
                fernet = Fernet(encryption_key)
                with open(encrypted_path, "rb") as f:
                    decrypted = fernet.decrypt(f.read())
                events = set(json.loads(decrypted.decode()))
                logger.info(f"Successfully loaded {len(events)} events from encrypted artifact")
                return events
            except Exception as e:
                logger.error(f"Failed to decrypt artifact: {e}", exc_info=True)
                # Don't fall through - if we're in GitHub Actions, we should use encrypted file
                return set()
    
    # Local development: use unencrypted file
    if DATA_PATH.exists():
        logger.info(f"Loading unencrypted local file from: {DATA_PATH}")
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f))
    
    logger.info("No previous events found, starting fresh")
    return set()


def save_events(events):
    """Persist events and prepare for GitHub artifact upload."""
    # In GitHub Actions, ONLY save encrypted version
    if os.getenv("GITHUB_ACTIONS"):
        encryption_key = get_encryption_key()
        if encryption_key:
            # Save to data/ for artifact upload
            Path("data").mkdir(exist_ok=True)
            
            # Encrypt the data
            fernet = Fernet(encryption_key)
            data = json.dumps(sorted(events)).encode()
            encrypted = fernet.encrypt(data)
            
            encrypted_path = Path("data/last_events.json.enc")
            with open(encrypted_path, "wb") as f:
                f.write(encrypted)
            logger.info(f"Saved encrypted artifact to: {encrypted_path}")
            return
    
    # Local development: save unencrypted
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(events), f, indent=2)
    logger.info(f"Saved {len(events)} events to local file: {DATA_PATH}")


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
        
        logger.info(f"Found {len(events)} events on page")
        return events


def main():
    load_env()

    previous_events = load_previous_events()
    current_events = fetch_current_events()
    new_events = current_events - previous_events

    logger.info(f"Previous events: {len(previous_events)}")
    logger.info(f"Current events: {len(current_events)}")
    logger.info(f"New events: {len(new_events)}")
    
    # Debug: show a sample if we have issues
    if previous_events and current_events and new_events:
        logger.info(f"Sample previous: {list(previous_events)[0][:100]}")
        logger.info(f"Sample current: {list(current_events)[0][:100]}")
        logger.info(f"Sample new: {list(new_events)[0][:100]}")

    if new_events:
        logger.info(f"Sending email notification for {len(new_events)} new events")
        send_email(sorted(new_events))
    else:
        logger.info("No new events detected")

    save_events(current_events)
    logger.info("Event state saved successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)