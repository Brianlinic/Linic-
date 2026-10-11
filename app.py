from flask import Flask, request, render_template_string
import requests, base64, os
from datetime import datetime

app = Flask(__name__)

HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Arial;padding:20px;background:#f0f9f0}.box{background:white;padding:20px;border-radius:10px;max-width:400px;margin:auto}
input{width:100%;padding:12px;margin:8px 0;border-radius:6px;border:1px solid #ccc;box-sizing:border-box}
button{background:#27ae60;color:white;padding:14px;width:100%;border:none;border-radius:6px;font-weight:bold}
.msg{background:#fff3cd;padding:10px;margin-top:10px;border-radius:6px;font-size:12px;word-break:break-all}</style></head>
<body><div class="box"><h2 style="color:#27ae60">Linic Clinic - Lipa</h2>
<form method="POST" action="/lipa"><input name="phone" value="254769365256" required>
<input name="amount" value="10" required><button>Lipa Sasa</button></form>{% if msg %}<div class="msg">{{msg}}</div>{% endif %}</div></body></html>"""

@app.route('/')
def home():
    return render_template_string(HTML, msg="")

@app.route('/lipa', methods=['POST'])
def lipa():
    try:
        ck = os.getenv("MPESA_CONSUMER_KEY","").strip()
        cs = os.getenv("MPESA_CONSUMER_SECRET","").strip()
        pk = os.getenv("MPESA_PASSKEY","").strip()
        sc = os.getenv("MPESA_SHORTCODE","").strip()
        phone = request.form.get("phone","").strip()
        amount = request.form.get("amount","").strip()

        auth_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        r = requests.get(auth_url, auth=(ck, cs), timeout=15)
        if r.status_code != 200:
            return render_template_string(HTML, msg=f"AUTH FAIL {r.status_code}: {r.text[:400]}")
        
        token = r.json().get("access_token")
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode((sc + pk + timestamp).encode()).decode()
        
        stk_url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        payload = {"BusinessShortCode": sc, "Password": password, "Timestamp": timestamp,
                   "TransactionType": "CustomerPayBillOnline", "Amount": amount,
                   "PartyA": phone, "PartyB": sc, "PhoneNumber": phone,
                   "CallBackURL": "https://linic.onrender.com/callback",
                   "AccountReference": "UnitA1", "TransactionDesc": "Clinic"}
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.post(stk_url, json=payload, headers=headers, timeout=15)
        return render_template_string(HTML, msg=f"RESPONSE: {resp.text}")
    except Exception as e:
        return render_template_string(HTML, msg=f"EXCEPTION: {e}")

@app.route('/callback', methods=['POST'])
def callback():
    return {"ResultCode": 0, "ResultDesc": "ok"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
