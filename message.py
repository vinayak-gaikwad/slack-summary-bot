HELP_MESSAGE = """
*Welcome to the Slack Summarizer Bot! :robot_face:*

Use the following commands to get summaries of your Slack conversations:

1. `/summarize messages <number>` 
   - *Description:* Summarizes the last `<number>` messages in the channel.
   - *Example:* `/summary messages 10`

2. `/summarize from <time>` 
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

MISSING_PARAMETER_MESSAGE = """
You must provide at least one of the fields: `messages` or `from`\n
For more details use `/summary-help`
"""

EMPTY_CONVERSATION_MESSAGE = "No messages to summarize."

CHANNEL_MENTION_ERROR = (
    "Please mention me in a thread to get a summary of the conversation."
)
