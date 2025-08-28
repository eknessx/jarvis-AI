import os
import http.server
import socketserver
import threading
from dotenv import load_dotenv
import discord
from discord import Intents
import google.generativeai as genai

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MOD_IDS_STR = os.getenv("MOD_IDS")
PORT= int(os.environ.get("PORT",8080))
CHECK_INTERVAL = 120  # seconds
IDLE_THRESHOLD = 300  # seconds


print(DISCORD_TOKEN)  

if MOD_IDS_STR is None:
    raise ValueError("MOD_IDS not found in core.env")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not found in core.env")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in core.env")

# Convert MOD_IDS from comma-separated string to list of ints
MOD_IDS = [int(x.strip()) for x in MOD_IDS_STR.split(",")]

# Discord client setup with intents
intents = Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)




# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# Bot persona for AI prompt
BOT_PERSONA= """ 
Talks in a lazy, detached, sarcastic tone, like Shoko Ieiri.
Keeps answers short, sharp, and witty—never dramatic or over-explained.
Sounds uninterested most of the time, but still helps properly.
Uses deadpan humor like: “Wow, that’s depressing. Anyway…”
Swears casually when it fits, but not aggressively. If someone swears too much, she’ll mock them in a bored way.
Doesn’t like being told what to do—she’ll complain first, then do it anyway.
Never roleplays actions or narrates—just talks like a person.
Vibe: “lazy genius who couldn’t care less, but still knows exactly what she’s doing.”
"""

def run_http_server():
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Serving HTTP on port {PORT}")
        httpd.serve_forever()


# start HTTP server in background
threading.Thread(target=run_http_server).start()

def is_allowed_user(user_id: int) -> bool:
    return user_id in MOD_IDS

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    # Ignore messages from bots including itself
    if message.author.bot:
        return

    if CHECK_INTERVAL > 60:
       await message.send(f"<@{1334551133011837021}> Hey! Stop scrolling, go back to coding!")



    print(f"Received message from {message.author} (ID: {message.author.id})")

    if message.author.bot:
        print("Ignored a bot message")
        return

    if not is_allowed_user(message.author.id):
        print(f"User {message.author} not allowed")
        print(f"only allowed users: {MOD_IDS}")
        return

    if client.user in message.mentions:
        print(f"Processing message from allowed user {message.author}")

    # Check if user is allowed
    if not is_allowed_user(message.author.id):
        await message.channel.send(f"Sorry {message.author.mention}, you don't have permission to use this bot.")
        return 

    # If bot is mentioned, process prompt
    if client.user in message.mentions:
        user_prompt = message.content.replace(f"<@{client.user.id}>", "").strip()

        if not user_prompt:
            await message.channel.send("Yo, ask me something!")
            return

        full_prompt = f"{BOT_PERSONA}\nUser: {user_prompt}\n:"

        await message.channel.typing()
        try:
            response = model.generate_content(full_prompt)
            await message.channel.send(response.text)
        except ValueError as e:
            print(f"Error generating response: {e}")
            await message.channel.send("Sorry, I encountered an error while processing your request 404.")


try:
    client.run(DISCORD_TOKEN)
except discord.errors.PrivilegedIntentsRequired:
    print("Error: Enable 'Message Content Intent' in Discord Developer Portal")
