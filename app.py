from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime, timezone


app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")
db = client["webhookDB"]
collection = db["github_events"]

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/webhook', methods=['POST'])

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        print("🔔 New Webhook Received")
        print("🔹 Event Type:", request.headers.get("X-GitHub-Event"))
        print("🔹 Payload:", data)

        event = request.headers.get("X-GitHub-Event")
        author = data.get("sender", {}).get("login", "Unknown")

        now = datetime.now(timezone.utc)
        day = now.day
        timestamp = now.strftime(f'{day} %B %Y - %I:%M %p UTC')


        doc = {}

        if event == "push":
            ref = data.get("ref", "")
            if not ref:
                print(" Missing 'ref' in push payload")
                return jsonify({"error": "Invalid push payload"}), 400

            doc = {
                "event": "push",
                "author": author,
                "to_branch": ref.split("/")[-1],
                "timestamp": timestamp
            }

        elif event == "pull_request":
            pr = data.get("pull_request")
            if not pr:
                print("❌ Missing 'pull_request' data")
                return jsonify({"error": "Invalid PR payload"}), 400

            if data.get("action") == "closed" and pr.get("merged"):
                doc = {
                    "event": "merge",
                    "author": author,
                    "from_branch": pr["head"]["ref"],
                    "to_branch": pr["base"]["ref"],
                    "timestamp": timestamp
                }
            else:
                doc = {
                    "event": "pull_request",
                    "author": author,
                    "from_branch": pr["head"]["ref"],
                    "to_branch": pr["base"]["ref"],
                    "timestamp": timestamp
                }

        else:
            print(" Unsupported event:", event)
            return jsonify({"msg": "ignored"}), 200

        collection.insert_one(doc)
        print("Event stored:", doc)
        return jsonify({"msg": "stored"}), 200

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

@app.route('/events', methods=['GET'])
def get_events():
    events = list(collection.find({}, {"_id": 0}))
    return jsonify(events)

if __name__ == '__main__':
    app.run(port=5000)
