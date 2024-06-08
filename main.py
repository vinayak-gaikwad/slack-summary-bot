import os
from datetime import datetime
import ollama
import dateparser
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from dotenv import load_dotenv
from ollama import Client
from message import *

load_dotenv()

model = os.environ.get("MODEL", "llama3")
ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
flask_host = os.environ.get("FLASK_HOST", "0.0.0.0")
flask_port = os.environ.get("FLASK_PORT", 3000)
flask_debug = os.environ.get("FLASK_DEBUG", False)


app = App(
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    token=os.environ.get("SLACK_BOT_TOKEN"),
)

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)
ollama_client = Client(host=ollama_host)


def get_summary(user_prompt, model=model):
    prompt = f"""
You are a Slack summary bot. Give brief summary of following conversation conversation is delimited by triple backticks.
- include key points and highlights.
- give summary in plain text.
- do not format summary.
- do not give text, code, or anything before and after summary.

```{user_prompt}```
"""
    try:
        return ollama_client.chat(
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
    if user_id in user_id_to_username:
        return user_id_to_username[user_id]
    try:
        result = app.client.users_info(user=user_id)
        if not result["ok"]:
            raise Exception(result["error"])

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


def fetch_messages(channel_id, parameters):
    try:
        response = app.client.conversations_history(
            channel=channel_id,
            limit=parameters.get("messages", 0),
            oldest=parameters.get("from", 0),
        )
        if not response["ok"]:
            raise Exception(response["error"])
        return response["messages"]
    except Exception as e:
        print(f"Error fetching messages: {e}")


def format_messages(messages):
    def get_formatted_message(message):
        timestamp = datetime.fromtimestamp(float(message["ts"]))
        user_name = get_user_name(message["user"])
        return f"[{timestamp}] {user_name}: {message['text']}"

    formatted_messages = [get_formatted_message(message) for message in messages]
    return "\n".join(formatted_messages)


@app.event("app_mention")
def summarize_thread(event, _, client):
    user = event["user"]
    channel = event["channel"]
    thread_ts = event.get("thread_ts")

    if not thread_ts:
        client.chat_postEphemeral(
            channel=channel,
            user=user,
            text=CHANNEL_MENTION_ERROR,
        )
    try:
        result = client.conversations_replies(channel=channel, ts=thread_ts)
        if not result["ok"]:
            raise Exception(request["error"])

        summary = get_summary(format_messages(result["messages"]))
        client.chat_postEphemeral(
            channel=channel,
            user=user,
            text=summary,
            thread_ts=thread_ts,
        )

    except Exception as e:
        print(f"Error occured: {e}")


@app.command("/summarize")
def handle_summarize_command(ack, body, respond):
    ack(response_type="ephemeral", text="Summarizing your messages... :hourglass:")

    channel_id = body["channel_id"]
    text = body["text"]
    user_id = body["user_id"]

    input_parameters = parse_input(text)
    if not input_parameters:
        respond(MISSING_PARAMETER_MESSAGE)
        return

    messages = fetch_messages(channel_id, input_parameters)
    if not messages:
        respond(EMPTY_CONVERSATION_MESSAGE)
        return

    first_message_link = app.client.chat_getPermalink(
        channel=channel_id, message_ts=messages[-1]["ts"]
    )["permalink"]

    summary = get_summary(format_messages(messages))
    response_text = f""":wave: Hi <@{user_id}>!
    Here is the summary of your requested messages:\n\n{summary}\n\n
    <{first_message_link}|Go to the conversation>"""

    respond(response_text)
    return


@app.command("/summary-help")
def handle_summary_help_command(ack, _, respond):
    ack()
    respond(HELP_MESSAGE)
    return


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@flask_app.route("/summarize", methods=["POST"])
def summarize():
    return handler.handle(request)


@flask_app.route("/summary-help", methods=["POST"])
def get_summary_help():
    return handler.handle(request)


if __name__ == "__main__":
    flask_app.run(host=flask_host, port=flask_port, debug=flask_debug)
