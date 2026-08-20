import asyncio
import base64
import json
import websockets
import os
from dotenv import load_dotenv
load_dotenv()


"""
DEEPGRAM AGENT CONNECTION
"""
def connect_to_deepgram_agent():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise Exception("Deepgram API Key Not Found")

    deepgram_ws = websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse",
        subprotocols=["token", api_key]
    )
    return deepgram_ws


"""
AGENT CONFIGURATION LOADING
"""
def load_agent_config():
    with open("config.json", "r") as f:
        return json.load(f)

async def handle_user_interrupt(decoded, twilio_ws, streamsid):
    pass


async def handle_deepgram_message(decoded, twilio_ws, deepgram_ws, streamsid):
    pass

async def send_audio_to_deepgram(deepgram_ws, audio_queue):
    pass

async def receive_from_deepgram(deepgram_ws, twilio_ws, streamsid_queue):
    pass

async def receive_from_twilio(twilio_ws, audio_queue, streamsid_queue):
    pass


async def handle_twilio_connection(twilio_ws):
    pass

async def main():
    await websockets.serve(handle_twilio_connection, "localhost", 5000)
    print("Started server")
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())