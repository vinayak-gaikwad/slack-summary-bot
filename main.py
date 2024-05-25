import os
import ollama
import dateparser
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from dotenv import load_dotenv
from prompt import system_prompt

load_dotenv()

app = App(
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    token=os.environ.get("SLACK_BOT_TOKEN"),
)

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


def get_summary(user_prompt, model="phi3"):

    return ollama.chat(
        model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": user_prompt},
        ],
    )


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


def parse_input(text):
    parameters = {}
    if "messages" in text:
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
    ack()
    channel_id = body["channel_id"]
    text = body["text"]

    input_parameters = parse_input(text)
    if not input_parameters:
        respond(
            "You must provide at least one of the fields: number of messages, unread messages, or date range."
        )
        return
    messages = fetch_messages(channel_id, input_parameters)

    summary = summarize_messages(messages)

    respond(summary)
    return


def summarize_messages(messages):
    summary = []
    for message in messages:
        user_name = get_user_name(message["user"])
        summary.append(f"{user_name}: {message['text']}")
    return "\n".join(summary)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@flask_app.route("/summarize", methods=["POST"])
def summarize():
    return handler.handle(request)


if __name__ == "__main__":
    flask_app.run(port=3000, debug=True)
