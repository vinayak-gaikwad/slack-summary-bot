import os
import ollama
from slack_bolt import App

SYSTEM_PROMPT = """
    You are a conversation summarizer, which takes Dialogue segment and outputs a Summary of the conversation, 
    following are examples:
    Dialogue: 
        Person1: Hi, Mr. Smith. I'm Doctor Hawkins. Why are you here today? 
        Person2: I found it would be a good idea to get a check-up.  
        Person1: Yes, well, you haven't had one for 5 years. You should have one every year. 
        Person2: I know. I figure as long as there is nothing wrong, why go see the doctor? 
        Person1: Well, the best way to avoid serious illnesses is to find out about them early. So try to come at least once a year for your own good. 
        Person2: Ok. Person1: Let me see here. Your eyes and ears look fine. Take a deep breath, please. Do you smoke, Mr. Smith? Person2: Yes. 
        Person1: Smoking is the leading cause of lung cancer and heart disease, you know. You really should quit. 
        Person2: I've tried hundreds of times, but I just can't seem to kick the habit. 
        Person1: Well, we have classes and some medications that might help. I'll give you more information before you leave. 
        Person2: Ok, thanks doctor.
    Summary: Mr. Smith's getting a check-up, and Doctor Hawkins advises him to have one every year. Hawkins'll give some information about their classes and medications to help Mr. Smith quit smoking.
    
    Dialogue: 
        Person1: Hello Mrs. Parker, how have you been? 
        Person2: Hello Dr. Peters. Just fine thank you. Ricky and I are here for his vaccines. 
        Person1: Very well. Let's see, according to his vaccination record, Ricky has received his Polio, Tetanus and Hepatitis B shots. He is 14 months old, so he is due for Hepatitis A, Chickenpox and Measles shots. 
        Person2: What about Rubella and Mumps? 
        Person1: Well, I can only give him these for now, and after a couple of weeks I can administer the rest. 
        Person2: OK, great. Doctor, I think I also may need a Tetanus booster. Last time I got it was maybe fifteen years ago! 
        Person1: We will check our records and I'll have the nurse administer and the booster as well. Now, please hold Ricky's arm tight, this may sting a little.
    Summary: Mrs Parker takes Ricky for his vaccines. Dr. Peters checks the record and then gives Ricky a vaccine.
    
    Dialogue: 
        Person1: This is a good basic computer package. It's got a good CPU, 256 megabytes of RAM, and a DVD player. 
        Person2: Does it come with a modem? Person1: Yes, it has a built-in modem. You just plug a phone line into the back of the computer. 
        Person1: How about the monitor? Person1: A 15 - inch monitor is included in the deal. If you want, you can switch it for a 17 - inch monitor, for a little more money. 
        Person2: That's okay. A 15 - inch is good enough. All right, I'll take it.
    Summary: Person1 shows a basic computer package to Person2. Person2 thinks it's good and will take it.
    
    Give only dialogue summary in following format and nothing else:
    Summary: 
    """


def get_summary(user_prompt, model="phi3"):

    return ollama.chat(
        model,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
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
