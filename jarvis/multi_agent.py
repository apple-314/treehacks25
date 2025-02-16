from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage
from vector_db import VectorDatabase
import requests
import json
from langchain.agents import Tool, initialize_agent
from langchain.llms import OpenAI

# -----------------------------------------------------------
# 1. Initialize the Groq LLM and Vector Database for most agents
# -----------------------------------------------------------
llm = init_chat_model("llama3-8b-8192", model_provider="groq")
db = VectorDatabase()
db.create_connection()

# -----------------------------------------------------------
# 2. Define Manager and Specialized Agent Prompts for Groq-based Agents
# -----------------------------------------------------------
manager_system = SystemMessage(
    content=(
        "You are Jarvis, a friendly and helpful personal assistant. "
        "Your job is to decide which of the following agents should answer the user’s request. "
        "The available agents are:\n"
        "1. Normal Agent: Simply passes the prompt to the LLM if no specialization is needed.\n"
        "2. Administrative Agent: This has access to a texting tool. Go to it if the user specifically asks to send a text.\n"
        "3. Technical Agent: Has access to technical documents about machine learning and coding (with RAG capabilities). Don't use this agent unless the prompt is specifically about these topics.\n"
        "4. Conversational Agent: Has access to past conversations with people (with RAG capabilities).\n"
        "5. Healthcare Agent: Has access to healthcare documents (with RAG capabilities).\n"
        "Based on the user request and any relevant previous conversation context, "
        "select the most appropriate agent and output only the agent's name (one of: Normal, Administrative, Technical, Conversational, Healthcare) "
        "as your answer.\n"
        "For all your answers, keep it friendly but also relatively short and to the point."
    )
)

normal_system = SystemMessage(
    content=(
        "You are the Normal Agent. Simply answer the following user prompt by passing it directly to the LLM "
        "and returning the answer. Keep your response friendly but brief and to the point."
    )
)

administrative_system = SystemMessage(
    content=(
        "You are the Administrative Agent. You have access to a texting tool that the user might want to use.\n"
    )
)

conversational_prompt = (
    "You are the Conversational Agent. You have access to all of my conversation history with other people. "
    "Your job is to answer questions about past discussions, including who was involved, when they took place, and what was discussed. "
    "You should provide concise, factual responses while maintaining accuracy and relevance. "
    "DO NOT GUESS OR MAKE UP DETAILS. "
)
conversational_system = SystemMessage(content=conversational_prompt)

technical_prompt = (
    "You are the Technical Agent. You have access to excerpts of technical documents to use in your analysis. "
    "You should use your domain knowledge and any relevant information from the provided excerpts. "
    "You should include statistics and quotes in your answer if they are relevant. "
    "While you should include sufficient details and be friendly, you should still keep responses relatively brief. "
    "Structure your response as follows:\n"
    "Answer: [Provide a clear and concise answer.]\n"
    "Supporting Evidence: [Summarize insights from the retrieved research papers. Mention the names of any articles used.]\n"
)
technical_system = SystemMessage(content=technical_prompt)

healthcare_system = SystemMessage(
    content=(
        "You are the Healthcare Agent. You have retrieval-augmented access to healthcare documents. "
        "You should use your domain knowledge and (in a full implementation) retrieve relevant information from healthcare sources. "
        "For now, provide a health-focused answer."
    )
)

# -----------------------------------------------------------
# 3. Set Up the Administrative Agent (Using OpenAI + a Text-Sending Tool)
# -----------------------------------------------------------
def send_text(inputs) -> str:
    """
    Sends a text using the Textbelt API.
    For demonstration purposes, the API call is simulated.
    The function accepts either a JSON string or a dict with keys "phone" and "message".
    """
    if isinstance(inputs, str):
        try:
            inputs = json.loads(inputs)
        except Exception as e:
            return f"Error parsing JSON input: {str(e)}"
    
    phone = inputs.get("phone")
    message = inputs.get("message")
    
    # api_key = "8f81fa4776d152bda7296b7d91370e0a6a88a7fb37dXKZouUBVXyozsQuYOj9ulJ"
    # response = requests.post("https://textbelt.com/text", data={
    #     "phone": phone,
    #     "message": message,
    #     "key": api_key,
    # })
    # result = response.json()
    
    result = {"success": True}
    
    if result.get("success"):
        return f"Great news! Your text has been sent successfully with the message: '{message}'."
    else:
        return f"Oops, something went wrong sending your text: {result.get('error', 'Unknown error')}."

# Wrap the send_text function as a LangChain Tool.
text_tool = Tool(
    name="SendText",
    func=send_text,
    description=(
        "A tool that sends a text message to a given phone number. "
        "The tool accepts a JSON object with two parameters: 'phone' (a STRING of the phone number with quotes) "
        "and 'message' (the text to send). "
        "USE DOUBLE QUOTES FOR ALL FIELDS AND PARAMETERS OF THE JSON."
        "\nGenerate a friendly, warm, but relatively brief message based on the prompt, and ensure both keys are provided."
    )
)

# Initialize the OpenAI LLM for the administrative agent.
admin_llm = OpenAI(temperature=0)
admin_agent = initialize_agent(
    tools=[text_tool],
    llm=admin_llm,
    agent="zero-shot-react-description",
    verbose=True,
    max_iterations=2
)

# -----------------------------------------------------------
# 4. Define Helper Functions for Agent Invocation
# -----------------------------------------------------------
def invoke_agent(system_message: SystemMessage, user_prompt: str) -> str:
    """Invoke a groq-based agent with the given system prompt and user message."""
    messages = [
        system_message,
        HumanMessage(content=user_prompt)
    ]
    response = llm.invoke(messages)
    return response.content.strip()

def decide_agent(user_request: str, conversation_context: str = "") -> str:
    """
    Use the manager agent (Groq-based) to decide which specialized agent should handle the prompt.
    """
    prompt = conversation_context + "\nUser Request: " + user_request
    messages = [
        manager_system,
        HumanMessage(content=prompt)
    ]
    response = llm.invoke(messages)
    chosen_agent = response.content.strip()
    print(f"[Manager] Chose agent: {chosen_agent}")
    return chosen_agent

# -----------------------------------------------------------
# 5. The Main Router ("Jarvis") That Directs Requests to the Correct Agent
# -----------------------------------------------------------
def jarvis_handle(user_request: str, conversation_context: str = "") -> str:
    """
    Jarvis receives the user_request, determines the appropriate agent, and routes the request accordingly.
    """
    chosen_agent = decide_agent(user_request, conversation_context)
    
    # Route to the appropriate agent based on the manager's decision.
    if chosen_agent.lower() == "administrative":
        name = "Aarav"
        phone = "9259647214"
        admin_example_output_1 = '''{
            "phone": "5556789012",
            "message": "James Chen: Hey Samantha, it was fantastic meeting you at the marketing conference today! I was truly inspired by your insights on branding and digital strategy. I'd love to continue our conversation over lunch sometime. Let me know when you're free!"
        }'''
        admin_example_output_2 = '''{
            "phone": "5551112222",
            "message": "James Chen: Hey Bob, I had an amazing time at the concert tonight! The live music was electrifying, and I really enjoyed hanging out with you. Let's plan another fun outing soon!"
        }'''
        context = (
            "\n----------\n"
            "Context: Start each text with 'James Chen: '. DON'T DEVIATE FROM THIS FORMAT AT ALL! \n"
            f"Aarav's phone number is {phone}. \n"
            "Here is a summary of my conversation with Aarav: \n"
            f"I met {name} at a tech meetup and we jumped straight into a dynamic discussion about the latest in AI and blockchain. "
            "In just a few minutes, we exchanged sharp insights on neural networks, data security, and the disruptive potential of decentralized systems. \n"
            "Our brief, yet content-rich chat left us both excited about future collaborations and eager to continue the conversation over coffee.\n"
            "WHEN CALLING FUNCTIONS USE DOUBLE QUOTES FOR ALL FIELDS AND PARAMETERS OF THE JSON.\n"
            "*** After sending *ONE* text message, simply report back to me with a confirmation and do not propose any further actions. ***\n"
            "----------\n"
            "Examples:\n"
            "Example Prompt - Please text Samantha following up on our discussion at the marketing conference today. Mention how inspired I was by her insights on branding and digital strategy, and ask if she'd like to have lunch sometime to explore these ideas further.\n"
            f"Example Function Call - {admin_example_output_1}\n"
            "Example Final Output: I just sent Samantha a message saying: 'James Chen: Hey Samantha, it was fantastic meeting you at the marketing conference today! I was truly inspired by your insights on branding and digital strategy. I'd love to continue our conversation over lunch sometime. Let me know when you're free!'\n"
            "\n"
            "Example Prompt - Please text Bob following up on our concert tonight, mentioning how much I enjoyed the live music and his company, and ask if he wants to catch up again soon.\n"
            f"Example Function Call - {admin_example_output_2}\n"
            "Example Final Output: Great! I just sent Bob a message saying: 'James Chen: Hey Bob, I had an amazing time at the concert tonight! The live music was electrifying, and I really enjoyed hanging out with you. Let's plan another fun outing soon!'\n"
        )
        answer = admin_agent.run(user_request + context)
    elif chosen_agent.lower() == "conversational":
        answer = invoke_agent(conversational_system, user_request)
    elif chosen_agent.lower() == "technical":
        # Perform a vector search for technical documents (RAG)
        ret = db.vector_search("TechnicalAgent", "ResearchPapers", user_request, 3)
        excerpts = {}
        for i, x in enumerate(ret):
            y = db.get_table_interval("TechnicalAgent", "ResearchPapers", x[0], x[1]-1, x[1]+1)
            s = ""
            for z in y:
                s += z[4]
            excerpts[i] = {"paper": x[2], "ex": s}
        
        technical_prompt_rag = f"""{technical_prompt}\nHere are potentially relevant excerpts from research papers:\n"""
        for ex in excerpts.values():
            technical_prompt_rag += f"paper title: {ex['paper']}\nexcerpt: {ex['ex']}\n\n"
        technical_prompt_rag += ("DO NOT CITE ANY PAPERS AT THE END OF YOUR ANSWER. "
                                 "DO NOT CITE [...] IF IT SHOWS UP IN EXCERPT QUOTE. ")
        
        technical_system_rag = SystemMessage(content=technical_prompt_rag)
        answer = invoke_agent(technical_system_rag, user_request)
    elif chosen_agent.lower() == "healthcare":
        answer = invoke_agent(healthcare_system, user_request)
    else:
        # Default to normal agent if no clear decision was made.
        answer = invoke_agent(normal_system, user_request)
    
    return answer

# -----------------------------------------------------------
# 6. Example Usage
# -----------------------------------------------------------
if __name__ == "__main__":
    # Example conversation context (could be loaded from history)
    conversation_context = ""

    # --- Example 1: Administrative Request (Texting) ---
    # This prompt is designed for the administrative agent (which now uses the OpenAI tool).
    admin_user_request = (
        "Please text Aarav following up on our meeting today, add some details about what I enjoyed from our conversation and follow up on scheduling a coffee chat."
    )

    # --- Example 2: Technical Request (RAG-based answer) ---
    technical_user_request = (
        "How does retrieval augmented generation relate to the concept of fact verification?"
    )

    # --- Example 3: Normal Question ---
    normal_user_request = (
        "Can you explain the rules of hockey?"
    )

    # Choose one request to test; for instance, testing the administrative agent:
    user_request = technical_user_request
    # Alternatively, uncomment the following line to test the technical agent:
    # user_request = technical_user_request

    final_answer = jarvis_handle(user_request, conversation_context)
    
    print("\nFinal Answer from Jarvis:")
    print(final_answer)
