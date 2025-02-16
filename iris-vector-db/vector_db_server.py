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
db = VectorDatabase()
db.create_connection()

db.delete_schema("JamesChen")

data = {
    "time_stamp" : str(datetime.now().replace(microsecond=0))
}

text_langchain = """Hey, have you heard about LangChain? It’s a framework for building AI-powered applications using large language models.
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

text_ar_vr_tech = """Have you been keeping up with the latest advancements in AR and VR? It feels like the technology is evolving at an incredible pace.
Absolutely! It’s fascinating to see how AR and VR are moving beyond just gaming and entertainment. Companies are now using them for everything from training simulations to medical applications.
Yeah, and with the rise of mixed reality headsets like Apple’s Vision Pro and Meta’s Quest, the line between AR and VR is starting to blur. These headsets are combining both worlds in a way that feels more immersive than ever.
Exactly. The idea of mixed reality—where digital elements interact with the real world—feels like the logical next step. Instead of switching between AR and VR, users can transition seamlessly between both. It opens up so many possibilities for work, education, and communication.
I think one of the biggest shifts we’re seeing is how AR and VR are integrating into professional environments. Remote work, for example, could be completely transformed with virtual offices and interactive collaboration spaces.
That’s true. I read about companies already experimenting with VR meetings where people wear headsets and feel like they’re in the same room. It adds a level of presence that video calls can’t really replicate.
And it’s not just offices. Industries like healthcare and manufacturing are leveraging AR and VR in ways that are incredibly practical. Surgeons are using AR overlays during procedures to get real-time guidance, and factory workers are using AR glasses to receive instructions without needing to check a manual.
The medical applications are particularly impressive. Training medical students with VR simulations allows them to practice procedures in a risk-free environment. That kind of hands-on experience is invaluable, especially for complex surgeries.
It’s also making education more engaging in general. Imagine history lessons where students can walk through ancient cities in VR or science classes where they can interact with molecules in 3D space. Learning could become so much more interactive.
Definitely! It reminds me of how museums and cultural institutions are adopting AR to enhance exhibits. Instead of just reading about historical artifacts, you could see holographic recreations or get additional layers of information through an AR headset or even just a phone.
One of the challenges, though, is the hardware. While we’ve come a long way from the bulky headsets of the past, AR and VR devices are still a bit too expensive and uncomfortable for mainstream daily use.
Yeah, affordability is a big issue. Meta’s Quest lineup is probably the most accessible in terms of price, but even then, it’s not something everyone can just buy on a whim. The real breakthrough will come when these devices become as lightweight and affordable as a pair of glasses.
That’s why companies are working so hard on AR glasses. Devices like the HoloLens and Magic Leap are pushing towards that vision, but we’re still not quite there in terms of sleekness and practicality for everyday use.
Battery life is another problem. Current AR and VR headsets don’t last long before they need a recharge, and nobody wants to be tethered to a power source all the time.
True. But processing power is also a limitation. Many high-end VR experiences still require a powerful PC or a cloud connection, which isn’t ideal for true mobility. Standalone headsets are improving, but they’re not at the level of dedicated hardware yet.
I think cloud computing and 5G will help with that. If rendering can be done remotely and streamed to the headset with ultra-low latency, we won’t need powerful processors built into the devices themselves.
That’s a good point. Cloud rendering could significantly reduce the cost and weight of headsets since they won’t need as much built-in processing power. But that depends on widespread high-speed internet access, which is still a challenge in some areas.
Another area I find interesting is haptics. Right now, VR mainly engages our vision and hearing, but haptic gloves and bodysuits are adding a sense of touch. Imagine being able to actually "feel" virtual objects in a realistic way.
Yeah, that’s where things get really futuristic. Full-body haptic feedback could make VR experiences so immersive that they feel indistinguishable from reality. Gaming would be incredible, but it could also revolutionize training simulations for firefighters, soldiers, or rescue teams.
I wonder if we’ll ever reach a point where AR and VR become as common as smartphones. Right now, it still feels like something you use occasionally rather than a daily necessity.
I think it’s a matter of time. Once AR glasses become lightweight and stylish enough to wear all day, they could replace smartphones entirely. Instead of looking at a screen, you’d just see your digital world overlaid onto reality.
That would change everything. Imagine walking around and getting real-time translations of signs in a foreign country, or seeing restaurant reviews floating above places as you pass by. Even things like navigation would be completely transformed.
There’s definitely potential for that, but there are also concerns. Privacy is a big issue—if everyone is wearing AR glasses, what happens to personal space and consent? Will people be constantly recorded without their knowledge?
That’s a valid concern. We already see debates about smart glasses with cameras, like Ray-Ban’s partnership with Meta. It’s convenient, but also raises ethical questions about surveillance and data collection.
And then there’s the question of how much digital augmentation is too much. If AR becomes our primary interface, will we ever truly disconnect from the digital world?
It’s a double-edged sword. On one hand, AR and VR can enhance how we work, learn, and connect. On the other hand, if it replaces real-world interactions too much, we might lose something valuable.
It’s definitely something to think about. But no matter what, it’s clear that AR and VR are shaping the future in ways we’re only beginning to understand. The next decade will be fascinating to watch.
Absolutely. Whether it’s for entertainment, work, or social interaction, these technologies are going to redefine how we experience the world. I can’t wait to see where it all goes."""

# conv_id = data["conv_id"]
# time_stamp = data["time_stamp"]
# transcript = data["transcript"]
# min_length = 256 # characters

# df = pd.DataFrame(columns=["conv_id", "index_in_conv", "time_stamp", "sentence"])

# def split_transcript(text, min_length):
#     sentences = re.split(r'([.!?])', text)  # Keep punctuation with split
#     chunks = []
#     current_chunk = ""

#     for i in range(0, len(sentences) - 1, 2):  # Process sentences in pairs (sentence + punctuation)
#         sentence = sentences[i].strip() + sentences[i + 1]  # Reattach punctuation

#         if len(current_chunk) + len(sentence) >= min_length:
#             if current_chunk:
#                 chunks.append(current_chunk.strip())  # Store current chunk
#             current_chunk = sentence  # Start new chunk
#         else:
#             current_chunk += " " + sentence  # Append sentence to current chunk

#     if current_chunk:  # Add any remaining text as last chunk
#         chunks.append(current_chunk.strip())

#     return chunks

# chunks = split_transcript(transcript, min_length)
# for chunk in chunks:
#     df.loc[len(df)] = [conv_id, len(df), time_stamp, chunk]
#     print(df.iloc[-1])

# # embeddings
# print("starting embedding calculation")
# embeddings = model.encode(df['sentence'].tolist(), normalize_embeddings=True)
# df['sentence_vector'] = embeddings.tolist()

# # pushing to server
# print("adding stuff to server")

# db.write_data_many_df("JamesChen", "Conversation", df, True)

# print(f"time: {time.time() - start_time}")

start = time.time()
db.add_text_to_table("JamesChen", "Conversation", text_langchain, 256, data)

data = {
    "time_stamp" : str(datetime.now().replace(microsecond=0))
}
db.add_text_to_table("JamesChen", "Conversation", text_ar_vr_tech, 256, data)

print(f"time: {time.time() - start}")

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
