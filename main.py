import os
from dotenv import load_dotenv
import requests
import time
import smtplib
from email.message import EmailMessage
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

load_dotenv()

API_URL = "https://www.arpej.fr/wp-json/sn/residences?lang=fr&display=map&price_from=0&price_to=1000&show_if_full=false&show_if_colocations=false"
CHECK_INTERVAL = 300
CITIES_TO_WATCH = {"Suresnes", "Vincennes", "Saint-Mandé", "Le Kremlin-Bicêtre", "Puteaux", "Courbevoie", "Paris"}

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_ADDRESS = os.getenv("TO_ADDRESS")

seen_residences = set()

def send_email(subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = TO_ADDRESS

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def check_new_residences():
    global seen_residences
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        residences = data.get("residences", [])

        new_entries = []

        for res in residences:
            nom = res.get("title", "Sans titre")
            extra = res.get("extra_data", {})
            ville = extra.get("city", "").strip()
            url = res.get("link", "")

            key = f"{nom}::{ville}"

            if ville in CITIES_TO_WATCH and key not in seen_residences:
                seen_residences.add(key)
                new_entries.append(f"🏠 {nom}\n📍 {ville}\n🔗 {url}\n")

        if new_entries:
            body = "\n\n".join(new_entries)
            send_email("📢 Nouvelle résidence ARPEJ détectée", body)
            print(f"[📬] Notification envoyée ({len(new_entries)} nouvelles résidences).")
        else:
            print("[ℹ️] Aucune nouvelle résidence détectée.")
    except Exception as e:
        print(f"[❌] Erreur : {e}")

def run_script():
    print("🚀 Surveillance des résidences ARPEJ démarrée…")
    while True:
        check_new_residences()
        time.sleep(CHECK_INTERVAL)

def run_dummy_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ARPEJ bot is running.")

    server = HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 10000))), Handler)
    print(f"🌐 Faux serveur HTTP sur le port {server.server_port}")
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_script, daemon=True).start()
    run_dummy_server()

