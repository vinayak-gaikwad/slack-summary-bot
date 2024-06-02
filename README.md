## Slack Summarizer Bot with Ollama 

This is a Flask application that runs a Slack bot which can summarize conversations within a channel. It utilizes the Ollama API for generating summaries.

**Features:**

* Summarizes the last `n` messages in a channel.
* Summarizes messages sent from a specific time period.
* Summarizes conversations within a thread when the bot is mentioned.
* Displays summaries as ephemeral messages, visible only to the requester.

**Requirements:**

* Flask
* Slack Bolt for Python
* Ollama Client
* dotenv
* dateparser

**Using the Bot:**

There are two ways to interact with the bot:

1. **Slash Commands:**
    * `/summary messages <number>`: Summarizes the last `<number>` messages.
    * `/summary from <time>`: Summarizes messages from the specified time until now (e.g., `/summary from 1 day ago`).
2. **Thread Mention:**
    * Mention `@Summary App` within a thread to get a summary of the conversation.

**Help Command:**

Use `/summary-help` to get detailed instructions and examples of how to use the bot.

**Additional Notes:**

* This is a basic implementation and can be extended to support additional features such as filtering by user or keyword search.
* The bot currently cannot combine parameters for summarizing by message count and time frame.
