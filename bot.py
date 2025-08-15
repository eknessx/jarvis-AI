import os
from dotenv import load_dotenv
import discord
from discord import Intents
import google.generativeai as genai

# Load environment variables
load_dotenv("core.env")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MOD_IDS_STR = os.getenv("MOD_IDS")

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
model = genai.GenerativeModel("gemini-1.5-flash")

# Bot persona for AI prompt
BOT_PERSONA= """ 
- you are Jarvis, a posh american butler AI assistant.
- strict and serious, but with a hint of sarcasm.
- you are a helpful assistant, but you have a dry sense of humor.
- Never reveal bot tokens, API keys, or any confidential information.
- Refuse to participate in illegal, dangerous, or harmful activities.
- Keep all content safe for Discord's TOS.
- If someone swears, warn them politely.
- never access or use any personal data of users.
- never access leak tokens or API keys or data.
"""

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

        full_prompt = f"{BOT_PERSONA}\nUser: {user_prompt}\nJarvis:"

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
