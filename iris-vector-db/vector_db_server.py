from fastapi import FastAPI, Request
import json
from vector_db import VectorDatabase
from sentence_transformers import SentenceTransformer
import pandas as pd
from datetime import datetime
import re
import time

start_time = time.time()

# Load a pre-trained sentence transformer model. This model's output vectors are of size 384
model = SentenceTransformer('all-MiniLM-L6-v2')

db = VectorDatabase()
db.create_connection()

db.delete_schema("JamesChen")

data = {
    "conv_id" : 0,
    "time_stamp" : str(datetime.now().replace(microsecond=0)),
    "transcript" : """Hey, have you heard about LangChain? It’s a framework for building AI-powered applications using large language models.
Yeah, I’ve come across it. It’s mainly used for chaining multiple AI components together, right? I think it helps developers create more sophisticated AI agents.
Exactly! It’s designed to integrate language models with external tools like databases, APIs, and even search engines. The cool thing is that it allows developers to build more intelligent and context-aware applications instead of just making a simple chatbot.
That makes sense. So, instead of just taking input and generating an output in isolation, LangChain helps maintain context and reasoning across multiple steps?
Yes, that’s the idea. You can think of it as a way to build AI pipelines that involve multiple interactions with data sources, user inputs, or even different AI models. It also helps with memory, which is crucial for applications where you need continuity across multiple interactions.
I see. So, let’s say I’m building an AI agent that helps users with financial planning. If I use LangChain, I could make it not only understand the user’s question but also fetch real-time stock data or analyze their spending habits to provide a more useful response?
Exactly! Without LangChain, you’d have to manually manage API calls, store memory, and ensure smooth interactions between different components. With LangChain, you can structure all of these processes in a much more organized way using chains and agents.
That sounds powerful. I assume there are different types of agents that you can build using LangChain, right?
Yes, LangChain supports different types of agents. Some are more reactive, meaning they just take input, process it, and return an output, while others are more autonomous, allowing the model to decide what actions to take based on the user’s query.
Interesting. How do these agents actually work under the hood?
Well, LangChain provides agent classes that define how an agent interacts with external tools. There’s something called an Action-Observation Loop, where the agent first decides on an action, executes it, observes the result, and then repeats the process if needed.
That sounds like reinforcement learning. Is it similar to how AI plays games, where it takes an action, sees the reward or consequence, and then decides what to do next?
Kind of! The difference is that most LangChain agents aren’t trained in the same way reinforcement learning agents are. Instead, they follow predefined steps and logic to decide which tool to use or what data to retrieve before responding to the user.
Got it. So, do LangChain agents always rely on large language models like GPT-4, or can they also use other AI models?
They can definitely use other AI models. While OpenAI’s GPT models are commonly used, LangChain is model-agnostic, meaning you can integrate it with different AI models like Claude, PaLM, or even open-source models like Llama 2. You can also use embedding models for vector searches and retrieval-augmented generation (RAG).
That makes it even more flexible. I assume it also has built-in support for things like memory management?
Yes, that’s a big part of it. LangChain has memory components that allow agents to remember past interactions. This is useful for building AI assistants that need to keep track of previous conversations instead of treating each user input as a standalone question.
That’s something I’ve always found lacking in simple chatbot implementations. Without memory, AI conversations can feel disconnected.
Exactly! Imagine having an AI-powered travel assistant. If you tell it that you’re planning a trip to Japan and then ask for recommendations, it should remember that context rather than making you specify “for Japan” every single time. LangChain’s memory feature helps with that.
That’s a great example. So, is LangChain primarily used for conversational AI, or are there other use cases?
While conversational AI is a major use case, LangChain can do a lot more. You can use it for document analysis, data retrieval, automation workflows, summarization, and even complex reasoning tasks.
What do you mean by complex reasoning tasks?
I mean applications where the AI needs to plan and execute multiple steps autonomously. For example, let’s say you want to build an AI research assistant that finds academic papers, summarizes them, and then generates insights based on those summaries. LangChain allows you to set up a structured sequence of steps so that the AI can perform each task systematically.
That sounds really useful for researchers and analysts. How does LangChain handle tool integrations?
It provides easy-to-use modules for connecting with APIs, databases, search engines, and vector databases. It even has built-in support for tools like Wolfram Alpha, Google Search, and SQL databases. You just configure the tool and the agent can automatically decide when and how to use it.
So, let’s say I’m building an AI assistant that can fetch real-time weather data. I could connect it to a weather API and have the agent call that API whenever a user asks about the weather?
Exactly! You define the tool, and the agent decides when to use it based on the user’s query.
That’s really convenient. What about security? If an AI agent is making API calls and interacting with external services, is there a risk of it being exploited?
That’s a good point. LangChain doesn’t enforce security by itself, but developers need to follow best practices. For example, you should always validate user inputs, limit API calls to prevent abuse, and avoid exposing sensitive data. If the AI has access to databases, make sure to implement proper authentication and authorization.
That makes sense. You wouldn’t want an AI agent executing arbitrary code or leaking private information.
Exactly! LangChain is a powerful tool, but like any technology, it has to be used responsibly.
I’d love to try building something with it. Where do you recommend getting started?
The official LangChain documentation is a great place to start. They provide tutorials, examples, and detailed explanations of each component. There are also YouTube videos and open-source projects on GitHub that show how to implement different use cases.
Sounds good! Maybe I’ll start with a simple chatbot and then try building a more complex agent that integrates external data sources.
That’s a great approach. Let me know if you need any help!"""
}

conv_id = data["conv_id"]
time_stamp = data["time_stamp"]
transcript = data["transcript"]
min_length = 256 # characters

df = pd.DataFrame(columns=["conv_id", "index_in_conv", "time_stamp", "sentence"])

def split_transcript(text, min_length):
    sentences = re.split(r'([.!?])', text)  # Keep punctuation with split
    chunks = []
    current_chunk = ""

    for i in range(0, len(sentences) - 1, 2):  # Process sentences in pairs (sentence + punctuation)
        sentence = sentences[i].strip() + sentences[i + 1]  # Reattach punctuation

        if len(current_chunk) + len(sentence) >= min_length:
            if current_chunk:
                chunks.append(current_chunk.strip())  # Store current chunk
            current_chunk = sentence  # Start new chunk
        else:
            current_chunk += " " + sentence  # Append sentence to current chunk

    if current_chunk:  # Add any remaining text as last chunk
        chunks.append(current_chunk.strip())

    return chunks

chunks = split_transcript(transcript, min_length)
for chunk in chunks:
    df.loc[len(df)] = [conv_id, len(df), time_stamp, chunk]
    print(df.iloc[-1])

# embeddings
print("starting embedding calculation")
embeddings = model.encode(df['sentence'].tolist(), normalize_embeddings=True)
df['sentence_vector'] = embeddings.tolist()

# pushing to server
print("adding stuff to server")

db.write_data_many_df("JamesChen", "Conversation", df, True)

print(f"time: {time.time() - start_time}")

while True:
    continue

app = FastAPI()

# API endpoint to receive JSON string and parse it into a dictionary
@app.post("/receive")
async def receive_data(request: Request):
    json_string = await request.body()  # Read raw JSON string from the request
    json_string = json_string.decode("utf-8")  # Convert bytes to string

    try:
        data = json.loads(json_string)  # Convert JSON string to dictionary
        print(f"Received JSON string: {json_string}")
        print(f"Parsed Dictionary: {data}")  # Print dictionary

        conv_id = data["conv_id"]
        time_stamp = data["time_stamp"]
        transcript = data["transcript"]
        min_length = 500 # characters

        return {"message": "Data received successfully!", "parsed_data": data}

    except json.JSONDecodeError:
        return {"error": "Invalid JSON format"}

# Run the FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
