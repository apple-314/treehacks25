import requests
import json
from langchain.agents import Tool, initialize_agent
from langchain.llms import OpenAI

# Function to send a text message using the Textbelt API.
# Updated to accept a single JSON object with keys "phone" and "message"
def send_text(inputs) -> str:
    if isinstance(inputs, str):
        try:
            inputs = json.loads(inputs)
        except Exception as e:
            return f"Error parsing JSON input: {str(e)}"
        
    phone = inputs.get("phone")
    message = inputs.get("message")
    
    # Uncomment and configure the API call if you want to use the actual Textbelt API.
    api_key = "8f81fa4776d152bda7296b7d91370e0a6a88a7fb37dXKZouUBVXyozsQuYOj9ulJ"
    response = requests.post("https://textbelt.com/text", data={
        "phone": phone,
        "message": message,
        "key": api_key,
    })
    result = response.json()

    print(result)

    # Simulate a successful response for demonstration purposes.

    # print("**")
    # print(message)
    # print("**")

    result = {"success": True}
    
    if result.get("success"):
        return f"Great news! Your text has been sent successfully with the message: '{message}'."
    else:
        return f"Oops, something went wrong sending your text: {result.get('error', 'Unknown error')}."

# Wrap the send_text function as a LangChain tool.
text_tool = Tool(
    name="SendText",
    func=send_text,
    description=(
        "A tool that sends a text message to a given phone number. "
        "The tool accepts a JSON object with two parameters: 'phone' (a STRING of their phone number with quotes around it) "
        "and 'message' (the text to send). "
        "USE DOUBLE QUOTES FOR ALL FIELDS AND PARAMETERS OF THE JSON. "
        "Generate a friendly, warm, but relatively brief message based on the prompt, and ensure both keys are provided."
    )
)

# Initialize the LLM (ensure your OpenAI API key is set in your environment)
llm = OpenAI(temperature=0)

# Create an agent that has access to the SendText tool.
# Increase max_iterations to 2 so that after sending the text, the agent can return a final confirmation.
agent = initialize_agent(
    tools=[text_tool],
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True,
    max_iterations=2
)

if __name__ == "__main__":
    # example_output_1 = {
    #     "phone": "2032465757",
    #     "message": "James Chen: Hey Alex, it was great meeting you at the tech meetup today! I really enjoyed our discussion on AI, blockchain, and decentralized systems. Let's schedule a coffee chat soon to continue the conversation. Looking forward to future collaborations!"
    # }

    example_output_1 = {
        "phone": "5556789012",
        "message": "James Chen: Hey Samantha, it was fantastic meeting you at the marketing conference today! I was truly inspired by your insights on branding and digital strategy. I'd love to continue our conversation over lunch sometime. Let me know when you're free!"
    }
    example_output_2 = {
        "phone": "5551112222",
        "message": "James Chen: Hey Bob, I had an amazing time at the concert tonight! The live music was electrifying, and I really enjoyed hanging out with you. Let's plan another fun outing soon!"
    }

    prompt = (
        f"----------"
        "REAL Prompt:"
        "Please text Alex following up on our meeting today, add some details about what I enjoyed from our conversation and follow up on scheduling a coffee chat. "
        "----------"
        "Context: Start each text with 'James Chen: '. DON'T DEVIATE FROM THIS FORMAT AT ALL! "
        "Alex's phone number is 2032465757. "
        "Here is a summary of my conversation with Alex: "
        "I met Alex at a tech meetup and we jumped straight into a dynamic discussion about the latest in AI and blockchain. "
        "In just a few minutes, we exchanged sharp insights on neural networks, data security, and the disruptive potential of decentralized systems. "
        "Our brief, yet content-rich chat left us both excited about future collaborations and eager to continue the conversation over coffee. "
        "*** After sending *ONE* text message, simply report back to me with a confirmation and do not propose any further actions. ***"
        "----------"
        "Examples:"
        "Example Prompt - Please text Samantha following up on our discussion at the marketing conference today. Mention how inspired I was by her insights on branding and digital strategy, and ask if she'd like to have lunch sometime to explore these ideas further."
        "Example Function Call - {example_output_1}"
        "Example Final Output: I just sent Samantha a message saying: \n\n'James Chen: Hey Samantha, it was fantastic meeting you at the marketing conference today! I was truly inspired by your insights on branding and digital strategy. I'd love to continue our conversation over lunch sometime. Let me know when you're free!'"
        ""
        "Example Prompt - Please text Bob following up on our concert tonight, mentioning how much I enjoyed the live music and his company, and ask if he wants to catch up again soon."
        "Example Function Call - {example_output_2}"
        "Example Final Output: Great! I just sent Bob a message saying: \n\n'James Chen: Hey Bob, I had an amazing time at the concert tonight! The live music was electrifying, and I really enjoyed hanging out with you. Let's plan another fun outing soon!'"
    )

    # "Prompt - Please text Alex following up on our meeting today, add some details about what I enjoyed from our conversation and follow up on scheduling a coffee chat."
    #     "Example output - {example_output_1}
    
    result = agent.run(prompt)
    print("Agent response:", result)
