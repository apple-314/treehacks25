from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage, AIMessage

from vector_db import VectorDatabase

# Initialize the base LLM model (this can be replaced with your RAG-enabled chain later)
llm = init_chat_model("llama3-8b-8192", model_provider="groq")
db = VectorDatabase()
db.create_connection()

# ============================
# Define the Agent Prompts
# ============================

# Manager Agent (Jarvis)
manager_system = SystemMessage(
    content=(
        "You are Jarvis, a friendly and helpful personal assistant. "
        "Your job is to decide which of the following agents should answer the user’s request. "
        "The available agents are:\n"
        "1. Normal Agent: Simply passes the prompt to the LLM if no specialization is needed.\n"
        "2. Administrative Agent: Has access to external APIs (calendar, texts, todo lists, etc.).\n"
        "3. Technical Agent: Has access to technical documents (with RAG capabilities).\n"
        "4. Conversational Agent: Has access to past conversations with people (with RAG capabilities).\n"
        "5. Healthcare Agent: Has access to healthcare documents (with RAG capabilities).\n"
        "Based on the user request and any relevant previous conversation context, "
        "select the most appropriate agent and output only the agent's name (one of: Normal, Administrative, Technical, Conversational, Healthcare) "
        "as your answer."
    )
)

# Specialized agents' system prompts
normal_system = SystemMessage(
    content=(
        "You are the Normal Agent. Simply answer the following user prompt by passing it directly to the LLM "
        "and returning the answer."
    )
)

administrative_system = SystemMessage(
    content=(
        "You are the Administrative Agent. You have access to external APIs such as calendar, texts, and todo lists. "
        "In a real-world scenario, you would integrate with these services. "
        "For now, simply indicate where such API calls would be made, and provide a helpful answer."
    )
)

conversational_prompt=(
    "You are the Conversational Agent. You have access to all of my conversation history with other people. "
    "Your job is to answer questions about past discussions, including who was involved, when they took place, and what was discussed. "
    "You should provide concise, factual responses while maintaining accuracy and relevance. "
    "DO NOT GUESS OR MAKE UP DETAILS. "
)
conversational_system = SystemMessage(content=conversational_prompt)

technical_prompt=(
    "You are the Technical Agent. You have access to excerpts of technical documents to use in your analysis. "
    "You should use your domain knowledge and any relevant information from the provided excerpts. "
    "You should include statistics and quotes in your answer if they are relevant. "
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

# ============================
# Helper Functions for Each Agent
# ============================

def invoke_agent(system_message: SystemMessage, user_prompt: str) -> str:
    """Helper function to invoke an agent with a simple system and user message."""
    messages = [
        system_message,
        HumanMessage(content=user_prompt)
    ]
    response = llm.invoke(messages)
    return response.content.strip()

def decide_agent(user_request: str, conversation_context: str = "") -> str:
    """
    The manager agent uses the user_request (and optionally conversation_context)
    to decide which agent should handle the prompt.
    """
    # You can include previous conversation context here if needed.
    prompt = conversation_context + "\nUser Request: " + user_request
    messages = [
        manager_system,
        HumanMessage(content=prompt)
    ]
    response = llm.invoke(messages)
    # Expecting a response like "Normal", "Administrative", "Technical", or "Healthcare"
    chosen_agent = response.content.strip()
    print(f"Manager chose: {chosen_agent}")
    return chosen_agent

# ============================
# Main Handler (Jarvis)
# ============================

def jarvis_handle(user_request: str, conversation_context: str = "") -> str:
    """
    Jarvis receives the user_request, uses the manager to decide which agent to use,
    and then routes the request accordingly.
    """
    # Decide which agent should handle the request.
    chosen_agent = decide_agent(user_request, conversation_context)
    
    # Route to the appropriate agent
    if chosen_agent.lower() == "administrative":
        answer = invoke_agent(administrative_system, user_request)
    elif chosen_agent.lower() == "conversational":
        answer = invoke_agent(conversational_system, user_request)
    elif chosen_agent.lower() == "technical":
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
        technical_prompt_rag += "DO NOT CITE ANY PAPERS AT THE END OF YOUR ANSWER. "
        technical_prompt_rag += "DO NOT CITE [...] IF IT SHOWS UP IN EXCERPT QUOTE. "
                
        technical_system_rag = SystemMessage(content=f"{technical_prompt_rag}\n")
        answer = invoke_agent(technical_system_rag, user_request)
    elif chosen_agent.lower() == "healthcare":
        answer = invoke_agent(healthcare_system, user_request)
    else:
        # Default to normal agent if choice is unclear
        answer = invoke_agent(normal_system, user_request)
    
    return answer

# ============================
# Example Usage
# ============================

if __name__ == "__main__":
    # Example conversation context. This could be maintained externally.
    conversation_context = "Previous conversation context could be stored here for RAG."

    # Example user request
    # administrative agent expected
    # user_request = "Can you schedule a meeting for tomorrow at 10 AM and also tell me the latest update on our technical documentation?"
    
    # technical agent expected
    user_request = "How does retrieval augmented generation relate to the concept of fact verification?"
    # user_request = "What are some extensions to the ADAM stochastic optimizer?"

    # Jarvis processes the request.
    final_answer = jarvis_handle(user_request, conversation_context)
    
    print("\nFinal Answer from Jarvis:")
    print(final_answer)
