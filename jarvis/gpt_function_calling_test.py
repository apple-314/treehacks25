import json
from langchain.agents import initialize_agent, Tool
from langchain_community.chat_models import ChatOpenAI  # Updated import per deprecation message

# Simulated helper function to get tomorrow's date.
def get_tomorrow_date() -> str:
    # In a real implementation, calculate tomorrow's date.
    return "2025-03-01"

# Original meeting scheduling function.
def schedule_meeting(date: str, time: str) -> str:
    return f"Meeting scheduled for {date} at {time}."

# A wrapper that processes the input (supports positional dict, JSON string, or keyword args)
def schedule_meeting_wrapper(*args, **kwargs) -> str:
    # If a positional argument is provided:
    if args:
        first_arg = args[0]
        if isinstance(first_arg, dict):
            kwargs = first_arg
        elif isinstance(first_arg, str):
            try:
                kwargs = json.loads(first_arg)
            except Exception as e:
                return f"Error: Could not parse input string: {e}"
    date = kwargs.get("date")
    time = kwargs.get("time")
    if date is None or time is None:
        return "Error: 'date' and 'time' parameters are required."
    # Convert "tomorrow" to an actual date.
    if isinstance(date, str) and date.lower() == "tomorrow":
        date = get_tomorrow_date()
    return schedule_meeting(date, time)

# Create a Tool for the wrapped function.
schedule_meeting_tool = Tool(
    name="schedule_meeting",
    func=schedule_meeting_wrapper,
    description="Schedules a meeting given a date and time. If the date is 'tomorrow', it converts it to the proper date."
)

# Initialize the Chat LLM with your OpenAI API key.
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0,
    openai_api_key="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"  # Replace with your actual API key.
)

# Create an agent with the tool included.
agent = initialize_agent(
    tools=[schedule_meeting_tool],
    llm=llm,
    agent="zero-shot-react-description",  # Use an agent type that supports tool calling.
    verbose=True
)

# Use the agent to handle a request.
user_request = "Please schedule a meeting for tomorrow at 10 AM."
result = agent.invoke(user_request)  # Using .invoke() per deprecation warning of .run()
print(result)
