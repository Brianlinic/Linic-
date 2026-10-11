from flask import Flask, request, render_template_string
import requests, base64
from datetime import datetime
import os

app = Flask(__name__)

# PAGE YA MALIPO
HTML = """
<h2>Linic Clinic - Malipo Unit A1</h2>
<form method="POST" action="/lipa">
  Phone: <input name="phone" value="254769365256"><br><br>
  Amount: <input name="amount" value="10"><br><br>
  <button type="submit">Lipa Sasa</button>
</form>
<p>{{msg}}</p>
"""

@app.route('/')
def home():
    return render_template_string(HTML, msg="")

@app.route('/li')
def li():
    return render_template_string(HTML, msg="Malipo Yametumwa! Angalia simu.")

@app.route('/lipa', methods=['POST'])
def lipa():
    phone = request.form.get('phone','254769365256')
    amount = request.form.get('amount','10')
    
    # === MPESA DARAJA DIRECT - HAKUNA PROXY TENA ===
    try:
        consumer_key = os.getenv("MPESA_CONSUMER_KEY")
        consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
        # kama hamna env, tumia sandbox test
        if not consumer_key:
            return render_template_string(HTML, msg="Weka MPESA keys kwa Render > Environment")
        
        # pata token
        auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        r = requests.get(auth_url, auth=(consumer_key, consumer_secret))
        token = r.json().get('access_token')

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        shortcode = os.getenv("MPESA_SHORTCODE", "174379")
        passkey = os.getenv("MPESA_PASSKEY")
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
            "CallBackURL": "https://brianclinic.onrender.com/callback",
            "AccountReference": "Unit A1",
            "TransactionDesc": "Clinic Payment"
        }
        headers = {"Authorization": f"Bearer {token}"}
        stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        resp = requests.post(stk_url, json=payload, headers=headers)
        return render_template_string(HTML, msg=f"STK imetumwa kwa {phone}: {resp.text}")
    except Exception as e:
        return render_template_string(HTML, msg=f"Error: {e}")

@app.route('/callback', methods=['POST'])
def callback():
    print(request.json)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}

if __name__ == '__main__':
    app.run()
