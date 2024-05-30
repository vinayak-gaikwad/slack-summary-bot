import os
from datetime import datetime
import ollama
import dateparser
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = App(
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    token=os.environ.get("SLACK_BOT_TOKEN"),
)

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


def get_summary(user_prompt, model="llama3"):
    prompt = f"""
Give only one line summary of following conversation, conversation is delimited by triple backticks.
Only give summary without anything else.
    
```{user_prompt}```
"""
    try:
        return ollama.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )["message"]["content"]
    except ollama.ResponseError as e:
        print("Error:", e.error)
        return e.error


user_id_to_username = {}


def get_user_name(user_id):
    try:
        if user_id in user_id_to_username:
            return user_id_to_username[user_id]

        result = app.client.users_info(user=user_id)
        if result["ok"]:
            username = result["user"]["profile"]["real_name"]
            user_id_to_username[user_id] = username
            return username

    except Exception as e:
        print(f"Error getting user name: {e}")

help_message = """
`/summary messages 10` => summarizes last 10 messages
`/summary from 1 day ago` => summarizes messages sent 1 day ago
`/summary from 1 hour ago` => summarizes messages sent 1 hour ago
`/summary help` => help menu 
"""
def parse_input(text):
    parameters = {}
    if "help" in text:
        parameters["help"] = help_message
    elif "messages" in text:
        parameters["messages"] = int(text.split("messages")[1].strip())
    elif "from" in text:
        ddp = dateparser.date.DateDataParser(languages=["en"])
        parameters["from"] = ddp.get_date_data(
            text.split("from")[1].strip()
        ).date_obj.timestamp()

    return parameters


@app.event("app_mention")
def greet_mention(event, say, client):
    user = event["user"]
    channel = event["channel"]
    thread_ts = event.get("thread_ts")
    try:
        if thread_ts:
            result = client.conversations_replies(channel=channel, ts=thread_ts)
            if result["ok"]:
                messages = result["messages"]
                summary = summarize_messages(messages)

                client.chat_postEphemeral(
                    channel=channel,
                    user=user,
                    text=summary,
                    thread_ts=thread_ts,
                )
        else:
            say("Error occured, fixing right away!!", channel=channel)
    except Exception as e:
        print(f"Error posting message: {e}")


def fetch_messages(channel_id, parameters):
    response = app.client.conversations_history(
        channel=channel_id,
        limit=parameters.get("messages", 100),
        oldest=parameters.get("from", 0),
    )
    return response["messages"]


@app.command("/summarize")
def handle_command(ack, body, respond):
    ack(response_type="ephemeral", text="Summarizing your messages... :hourglass:")
    channel_id = body["channel_id"]
    text = body["text"]

    input_parameters = parse_input(text)
    if not input_parameters:
        respond(
            "You must provide at least one of the fields: number of messages or duration"
        )
        return
    if "help" in input_parameters:
        respond(input_parameters["help"])
    messages = fetch_messages(channel_id, input_parameters)

    summary = summarize_messages(messages)

    respond(summary)
    return


def summarize_messages(messages):
    summary = []
    for message in messages:
        ts = datetime.fromtimestamp(float(message["ts"]))
        user_name = get_user_name(message["user"])
        summary.append(f"[{ts}] {user_name}: {message['text']}")

    return get_summary("\n".join(summary))


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@flask_app.route("/summarize", methods=["POST"])
def summarize():
    return handler.handle(request)


if __name__ == "__main__":
    flask_app.run(port=3000, debug=True)
