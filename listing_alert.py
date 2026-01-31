#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upbit & Bithumb Listing Alert Bot v2.0
======================================
Monitor new cryptocurrency listings on Upbit and Bithumb
and send alerts via Telegram.

Author: Claude AI Assistant
"""

import os
import json
import time
import logging
import re
import requests
from datetime import datetime
from typing import Optional, Dict, List, Set
from dataclasses import dataclass
from pathlib import Path

# ==================== CONFIGURATION ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))

DATA_FILE = Path(__file__).parent / "known_listings.json"
LOG_FILE = Path(__file__).parent / "listing_alert.log"

# Exchange URLs
UPBIT_NOTICE_URL = "https://api-manager.upbit.com/api/v1/notices"
UPBIT_MARKETS_URL = "https://api.upbit.com/v1/market/all"
BITHUMB_TICKER_URL = "https://api.bithumb.com/public/ticker/ALL_KRW"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== DATA CLASS ====================
@dataclass
class ListingInfo:
    exchange: str
    title: str
    coin_symbol: str
    url: str
    timestamp: str
    notice_id: str

# ==================== HELPER FUNCTIONS ====================
def load_known_listings() -> Dict:
    """Load known listings from JSON file."""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"upbit": [], "upbit_markets": [], "bithumb": [], "bithumb_markets": []}

def save_known_listings(data: Dict) -> None:
    """Save known listings to JSON file."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving data: {e}")

def send_telegram_message(message: str) -> bool:
    """Send message via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram token not configured!")
        print(f"\nALERT:\n{message}\n")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram message sent")
            return True
        else:
            logger.error(f"Telegram error: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Telegram failed: {e}")
        return False

def extract_coin_symbol(title: str) -> Optional[str]:
    """Extract coin symbol from listing title."""
    patterns = [
        r'\(([A-Z0-9]{2,10})\)',
        r'([A-Z]{2,10})\s*/\s*KRW',
        r'([A-Z]{2,10})\s*마켓',
        r'([A-Z]{2,10})\s*원화',
    ]
    for pattern in patterns:
        match = re.search(pattern, title.upper())
        if match:
            return match.group(1)
    return None

# ==================== UPBIT FUNCTIONS ====================
def fetch_upbit_markets() -> Set[str]:
    """Fetch current market list from Upbit."""
    try:
        response = requests.get(UPBIT_MARKETS_URL, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            markets = response.json()
            coins = set()
            for market in markets:
                code = market.get("market", "")
                if code.startswith("KRW-"):
                    coins.add(code.replace("KRW-", ""))
            logger.debug(f"Upbit: {len(coins)} markets")
            return coins
    except Exception as e:
        logger.error(f"Upbit markets error: {e}")
    return set()

def fetch_upbit_notices() -> List[Dict]:
    """Fetch notices from Upbit."""
    try:
        params = {"page": 1, "per_page": 20}
        response = requests.get(UPBIT_NOTICE_URL, headers=HEADERS, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("list", [])
    except Exception as e:
        logger.error(f"Upbit notices error: {e}")
    return []

def check_upbit_listings(known_data: Dict) -> List[ListingInfo]:
    """Check for new Upbit listings."""
    new_listings = []
    
    # Method 1: Check notices
    notices = fetch_upbit_notices()
    known_ids = set(known_data.get("upbit", []))
    keywords = ["신규", "상장", "거래지원", "마켓 추가", "원화 마켓", "디지털 자산 추가"]
    
    for notice in notices:
        nid = str(notice.get("id", ""))
        title = notice.get("title", "")
        
        if nid and nid not in known_ids and any(k in title for k in keywords):
            coin = extract_coin_symbol(title) or "UNKNOWN"
            listing = ListingInfo(
                exchange="Upbit",
                title=title,
                coin_symbol=coin,
                url=f"https://upbit.com/service_center/notice?id={nid}",
                timestamp=datetime.now().isoformat(),
                notice_id=nid
            )
            new_listings.append(listing)
            known_data["upbit"].append(nid)
    
    # Method 2: Check markets
    current = fetch_upbit_markets()
    known = set(known_data.get("upbit_markets", []))
    
    if known and current:
        for coin in current - known:
            listing = ListingInfo(
                exchange="Upbit",
                title=f"New Market Detected: {coin}/KRW",
                coin_symbol=coin,
                url=f"https://upbit.com/exchange?code=CRIX.UPBIT.KRW-{coin}",
                timestamp=datetime.now().isoformat(),
                notice_id=f"market_{coin}_{int(time.time())}"
            )
            new_listings.append(listing)
            logger.info(f"New Upbit market: {coin}")
    
    if current:
        known_data["upbit_markets"] = list(current)
    
    return new_listings

# ==================== BITHUMB FUNCTIONS ====================
def fetch_bithumb_markets() -> Set[str]:
    """Fetch current market list from Bithumb."""
    try:
        response = requests.get(BITHUMB_TICKER_URL, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "0000":
                ticker = data.get("data", {})
                coins = set()
                for key in ticker.keys():
                    if key != "date" and isinstance(ticker[key], dict):
                        coins.add(key)
                logger.debug(f"Bithumb: {len(coins)} markets")
                return coins
    except Exception as e:
        logger.error(f"Bithumb markets error: {e}")
    return set()

def check_bithumb_listings(known_data: Dict) -> List[ListingInfo]:
    """Check for new Bithumb listings."""
    new_listings = []
    
    current = fetch_bithumb_markets()
    known = set(known_data.get("bithumb_markets", []))
    
    if known and current:
        for coin in current - known:
            listing = ListingInfo(
                exchange="Bithumb",
                title=f"New Market Detected: {coin}/KRW",
                coin_symbol=coin,
                url=f"https://www.bithumb.com/trade/order/{coin}_KRW",
                timestamp=datetime.now().isoformat(),
                notice_id=f"bithumb_{coin}_{int(time.time())}"
            )
            new_listings.append(listing)
            logger.info(f"New Bithumb market: {coin}")
    
    if current:
        known_data["bithumb_markets"] = list(current)
    
    return new_listings

# ==================== ALERT FORMAT ====================
def format_alert(listing: ListingInfo) -> str:
    """Format listing info as Telegram message."""
    exchange_icon = "[UPBIT]" if listing.exchange == "Upbit" else "[BITHUMB]"
    
    return f"""
=== NEW LISTING ALERT ===

{exchange_icon}
Exchange: {listing.exchange}
Coin: {listing.coin_symbol}
Info: {listing.title}
Link: {listing.url}
Time: {listing.timestamp[:19]}

#NewListing #{listing.exchange} #{listing.coin_symbol}
""".strip()

# ==================== MAIN BOT ====================
def run_bot():
    """Main bot loop."""
    logger.info("=" * 50)
    logger.info("Listing Alert Bot v2.0 Started")
    logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
    logger.info("Monitoring: Upbit (notices + markets), Bithumb (markets)")
    logger.info("=" * 50)
    
    # Startup message
    startup_msg = """<b>Listing Alert Bot Started!</b>

Monitoring: Upbit, Bithumb
Interval: {} seconds
Time: {}""".format(CHECK_INTERVAL, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    send_telegram_message(startup_msg)
    
    known_data = load_known_listings()
    
    # First run - populate existing data
    if not known_data.get("upbit_markets") and not known_data.get("bithumb_markets"):
        logger.info("First run - loading existing market data...")
        
        # Load Upbit data
        upbit_markets = fetch_upbit_markets()
        if upbit_markets:
            known_data["upbit_markets"] = list(upbit_markets)
            logger.info(f"Upbit: Loaded {len(upbit_markets)} existing markets")
        
        notices = fetch_upbit_notices()
        known_data["upbit"] = [str(n.get("id", "")) for n in notices[:50] if n.get("id")]
        logger.info(f"Upbit: Loaded {len(known_data['upbit'])} existing notices")
        
        # Load Bithumb data
        bithumb_markets = fetch_bithumb_markets()
        if bithumb_markets:
            known_data["bithumb_markets"] = list(bithumb_markets)
            logger.info(f"Bithumb: Loaded {len(bithumb_markets)} existing markets")
        
        save_known_listings(known_data)
        logger.info("Initial data loaded. Now monitoring for new listings...")
    
    # Main loop
    error_count = 0
    while True:
        try:
            logger.info("Checking for new listings...")
            
            # Check Upbit
            upbit_listings = check_upbit_listings(known_data)
            for listing in upbit_listings:
                logger.info(f">>> NEW UPBIT LISTING: {listing.coin_symbol}")
                send_telegram_message(format_alert(listing))
            
            # Check Bithumb
            bithumb_listings = check_bithumb_listings(known_data)
            for listing in bithumb_listings:
                logger.info(f">>> NEW BITHUMB LISTING: {listing.coin_symbol}")
                send_telegram_message(format_alert(listing))
            
            # Save data
            save_known_listings(known_data)
            
            total = len(upbit_listings) + len(bithumb_listings)
            if total > 0:
                logger.info(f"Found {total} new listing(s)!")
            
            error_count = 0
            
        except Exception as e:
            error_count += 1
            logger.error(f"Loop error (#{error_count}): {e}")
            
            if error_count >= 5:
                send_telegram_message(f"<b>Bot Error Alert</b>\n\nRepeated errors: {error_count}x\nError: {str(e)[:100]}")
                error_count = 0
        
        time.sleep(CHECK_INTERVAL)

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
        send_telegram_message("<b>Bot Stopped</b>\n\nListing Alert Bot has been stopped manually.")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        send_telegram_message(f"<b>Bot Crashed!</b>\n\nError: {str(e)[:200]}")
