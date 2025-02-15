from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage, AIMessage

# Initialize the Groq chat model
chat = init_chat_model("llama3-8b-8192", model_provider="groq")

# Define agents with clear role instructions
agent_1_system = SystemMessage(
    content=(
        "You are Agent 1, an expert in history. "
        "When responding, provide historical context, analysis, and draw parallels with earlier events. Keep your responses brief."
    )
)
agent_2_system = SystemMessage(
    content=(
        "You are Agent 2, an expert in science. "
        "When responding, provide scientific insights, technological analysis, and ask follow-up questions if needed. Keep your responses brief."
    )
)

# Set the number of conversation rounds
conversation_rounds = 3

# Initial prompt for Agent 1
prompt = "What is the impact of the industrial revolution?"

for round in range(conversation_rounds):
    # Agent 1's turn: Provide historical insight
    messages_agent1 = [
        agent_1_system,
        HumanMessage(content=prompt)
    ]
    response_1 = chat.invoke(messages_agent1)
    print(f"Agent 1 (Round {round + 1}): {response_1.content}\n")

    # Agent 2's turn: Provide scientific perspective based on Agent 1's response
    messages_agent2 = [
        agent_2_system,
        HumanMessage(
            content=(
                f"Agent 1 said: {response_1.content}\n"
                "Please provide your scientific perspective on these historical developments."
            )
        )
    ]
    response_2 = chat.invoke(messages_agent2)
    print(f"Agent 2 (Round {round + 1}): {response_2.content}\n")

    # Prepare prompt for the next round: use Agent 2's response to guide Agent 1's historical context
    prompt = (
        f"Agent 2 said: {response_2.content}\n"
        "Based on the scientific insights provided, can you draw further historical parallels or context?"
    )
