# chat.py
import os
import django
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()

# 2. Setup Django environment configuration
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

# Now we can safely import Django models (if any) and Chainlit/OpenAI
from django.contrib.auth.models import User
import chainlit as cl
from openai import AsyncOpenAI

# Initialize the Async OpenAI Client
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Instrument OpenAI with Chainlit for built-in step tracking
cl.instrument_openai()

@cl.on_chat_start
async def start_chat():
    """
    Triggers when a user opens the chat interface.
    """
    # Example of accessing Django ORM inside Chainlit:
    # Just as a demonstration, we count the total users in our Django Database
    from asgiref.sync import sync_to_async
    user_count = await sync_to_async(User.objects.count)()
    
    # Store a conversational thread state in the user's session
    cl.user_session.set(
        "history",
        [{"role": "system", "content": f"You are a helpful assistant. System note: There are currently {user_count} registered users in the connected Django DB."}]
    )
    
    await cl.Message(content="Hello! I am connected to your Django backend and OpenAI. How can I help you today?").send()

@cl.on_message
async def main(message: cl.Message):
    """
    Triggers every time a user sends a message.
    """
    # Retrieve the chat history from the session
    history = cl.user_session.get("history")
    
    # Append the incoming user message
    history.append({"role": "user", "content": message.content})
    
    # Prepare an empty Chainlit message to stream the token response into
    response_message = cl.Message(content="")
    await response_message.send()
    
    # Call OpenAI Async API with streaming enabled
    stream = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,
        stream=True,
        temperature=0.7
    )
    
    # Consume the stream and send chunks into the Chainlit UI in real-time
    async for chunk in stream:
        token = chunk.choices[0].delta.content or ""
        if token:
            await response_message.stream_token(token)
            
    # Append the model's finalized response back to history for context retention
    history.append({"role": "assistant", "content": response_message.content})
    cl.user_session.set("history", history)
    
    # Finalize the message stream
    await response_message.update()
