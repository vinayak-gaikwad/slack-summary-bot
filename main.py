import os
import ollama
from slack_bolt import App
from prompt import system_prompt

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


app = App(
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    token=os.environ.get("SLACK_BOT_TOKEN"),
)


def get_user_name(user_id, client):
    try:
        result = client.users_info(user=user_id)
        if result["ok"]:
            return result["user"]["profile"]["real_name"]
    except Exception as e:
        print(f"Error getting user name: {e}")
    return None


@app.event("app_mention")
def greet_mention(event, say, client):
    user = event["user"]
    channel = event["channel"]
    thread_ts = event.get("thread_ts")
    try:
        if thread_ts:
            result = client.conversations_replies(channel=channel, ts=thread_ts)
            chat_history = "Dialogue: \n"
            if result["ok"]:
                messages = result["messages"]
                for message in messages:
                    # user_name = "User"
                    # if user != message["user"]:
                    user_name = get_user_name(message["user"], client)
                    chat_history += f"{user_name}: {message['text']}\n"
            print(chat_history)
            summary = get_summary(chat_history)["message"]["content"]
            client.chat_postEphemeral(
                channel=channel,
                user=user,
                text=f"{user_name}, here is your summary\n{summary}",
                thread_ts=thread_ts,
            )
        else:
            say("For now we can only summarize threads :(", channel=channel)
    except Exception as e:
        print(f"Error posting message: {e}")


if __name__ == "__main__":
    app.start(port=int(3000))
