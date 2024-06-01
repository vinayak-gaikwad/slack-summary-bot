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
model = os.environ.get("MODEL", "llama3")
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


def get_summary(user_prompt, model=model):
    prompt = f"""
Give one line summary of following conversation, conversation is delimited by triple backticks.
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
            client.chat_postEphemeral(
                channel=channel,
                user=user,
                text="Please mention me in a thread to get a summary of the conversation.",
            )
    except Exception as e:
        print(f"Error posting message: {e}")


def fetch_messages(channel_id, parameters):
    try:
        response = app.client.conversations_history(
            channel=channel_id,
            limit=parameters.get("messages", 100),
            oldest=parameters.get("from", 0),
        )
        return response["messages"]
    except Exception as e:
        print(f"Error fetching messages: {e}")


@app.command("/summarize")
def handle_summarize_command(ack, body, respond):
    ack(response_type="ephemeral", text="Summarizing your messages... :hourglass:")
    channel_id = body["channel_id"]
    text = body["text"]
    user_id = body["user_id"]

    input_parameters = parse_input(text)
    if not input_parameters:
        respond(
            "You must provide at least one of the fields: number of messages or duration"
        )
        return

    messages = fetch_messages(channel_id, input_parameters)
    messages_size = len(messages)

    if messages_size == 0:
        respond("No messages to summarize.")
        return

    first_message_link = app.client.chat_getPermalink(
        channel=channel_id, message_ts=messages[messages_size - 1]["ts"]
    )["permalink"]

    summary = summarize_messages(messages)
    response_text = f":wave: Hi <@{get_user_name(user_id)}>! Here is the summary of your requested messages:\n\n{summary}\n\n<{first_message_link}|Go to the conversation>"

    respond(response_text)
    return


@app.command("/summary-help")
def handle_summary_help_command(ack, _, respond):
    ack()
    help_message = """
*Welcome to the Slack Summarizer Bot! :robot_face:*

Use the following commands to get summaries of your Slack conversations:

1. `/summary messages <number>` 
   - *Description:* Summarizes the last `<number>` messages in the channel.
   - *Example:* `/summary messages 10`

2. `/summary from <time>` 
   - *Description:* Summarizes messages sent from the specified time until now.
   - *Examples:* 
     - `/summary from 1 day ago` (Summarizes messages from the past day)
     - `/summary from 1 hour ago` (Summarizes messages from the past hour)
3. `@Summary App`
   - Mention bot to summarize threads

*Additional Information:*
- The summaries will be posted as ephemeral messages, visible only to you. :lock:
- You cannot combine parameters for now but we are working on it :calendar:

Happy summarizing!!
"""
    respond(help_message)
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


@flask_app.route("/summary-help", methods=["POST"])
def get_summary_help():
    return handler.handle(request)


if __name__ == "__main__":
    flask_app.run(port=3000, debug=True)
