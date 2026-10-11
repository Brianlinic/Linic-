from flask import Flask, request, render_template_string
import requests, base64
from datetime import datetime
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{font-family:Arial;padding:20px;background:#f0f9f0}
.box{background:white;padding:20px;border-radius:10px;max-width:400px;margin:auto;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
input{width:100%;padding:12px;margin:8px 0;border:1px solid #ccc;border-radius:6px}
button{background:#27ae60;color:white;padding:12px;width:100%;border:none;border-radius:6px;font-size:16px}
.msg{background:#fff3cd;padding:10px;margin-top:10px;border-radius:6px}
</style>
</head>
<body>
<div class="box">
<h2 style="color:#27ae60">Linic Clinic - Malipo Unit A1</h2>
<form method="POST" action="/lipa">
<label>Phone (254...):</label>
<input name="phone" value="254769365256" required>
<label>Amount:</label>
<input name="amount" value="10" required>
<button type="submit">Lipa Sasa via M-Pesa</button>
</form>
{% if msg %}<div class="msg">{{msg}}</div>{% endif %}
</div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML, msg="")

@app.route('/li')
def li():
    return render_template_string(HTML, msg="Karibu! Weka namba na ulipe.")

@app.route('/lipa', methods=['POST'])
def lipa():
    phone = request.form.get('phone','254769365256').strip()
    amount = request.form.get('amount','10').strip()
    try:
        consumer_key = os.getenv("MPESA_CONSUMER_KEY")
        consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
        passkey = os.getenv("MPESA_PASSKEY")
        shortcode = os.getenv("MPESA_SHORTCODE", "174379")
        
        if not consumer_key or not consumer_secret or not passkey:
            return render_template_string(HTML, msg="Weka MPESA keys kwa Render > Environment")
        
        auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        r = requests.get(auth_url, auth=(consumer_key, consumer_secret), timeout=10)
        token = r.json().get('access_token')
        if not token:
            return render_template_string(HTML, msg=f"Token failed: {r.text}")

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode((shortcode + passkey + timestamp).encode()).decode()

        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": shortcode,
            "PhoneNumber": phone,
            "CallBackURL": "https://linic.onrender.com/callback",
            "AccountReference": "UnitA1",
            "TransactionDesc": "Clinic Payment"
        }
        headers = {"Authorization": f"Bearer {token}"}
        stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        resp = requests.post(stk_url, json=payload, headers=headers, timeout=10)
        return render_template_string(HTML, msg=f"STK imetumwa kwa {phone}. Angalia simu! {resp.json()}")
    except Exception as e:
        return render_template_string(HTML, msg=f"Error: {e}")

@app.route('/callback', methods=['POST'])
def callback():
    print(request.json)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}

if __name__ == '__main__':
    app.run()
