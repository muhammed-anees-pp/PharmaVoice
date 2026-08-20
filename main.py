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


"""
SEND AUDIO TO DEEPGRAM
"""
async def send_audio_to_deepgram(deepgram_ws, audio_queue):
    print("Deepgram audio sender started")

    while True:
        audio_chunk = await audio_queue.get()
        await deepgram_ws.send(audio_chunk)


"""
RECEIVE AUDIO AND MESSAGES FROM DEEPGRAM
"""
async def receive_from_deepgram(deepgram_ws, twilio_ws, stream_sid_queue):
    print("Deepgram receiver started")
    stream_sid = await stream_sid_queue.get()

    async for message in deepgram_ws:
        if isinstance(message, str):
            print(message)
            message_data = json.loads(message)

            await handle_deepgram_message(
                message_data,
                twilio_ws,
                deepgram_ws,
                stream_sid
            )
            continue

        raw_mulaw_audio = message
        media_message = {
            "event": "media",
            "streamSid": stream_sid,
            "media": {
                "payload": base64.b64encode(
                    raw_mulaw_audio
                ).decode("ascii")
            }
        }
        await twilio_ws.send(
            json.dumps(media_message)
        )


"""
RECEIVE AUDIO FROM TWILIO
"""
async def receive_from_twilio(twilio_ws, audio_queue, stream_sid_queue):
    BUFFER_SIZE = 20 * 160
    audio_buffer = bytearray()

    async for message in twilio_ws:
        try:
            data = json.loads(message)
            event = data["event"]

            if event == "start":
                print("Getting Stream SID")

                start = data["start"]
                stream_sid = start["streamSid"]

                stream_sid_queue.put_nowait(stream_sid)

            elif event == "connected":
                continue

            elif event == "media":
                media = data["media"]

                chunk = base64.b64decode(
                    media["payload"]
                )

                if media["track"] == "inbound":
                    audio_buffer.extend(chunk)

            elif event == "stop":
                break

            while len(audio_buffer) >= BUFFER_SIZE:
                chunk = audio_buffer[:BUFFER_SIZE]

                audio_queue.put_nowait(chunk)

                audio_buffer = audio_buffer[BUFFER_SIZE:]

        except Exception as error:
            print(f"Error receiving Twilio audio: {error}")
            break


"""
TWILIO CONNECTION HANDLER
"""
async def handle_twilio_connection(twilio_ws):
    audio_queue = asyncio.Queue()
    stream_sid_queue = asyncio.Queue()

    async with connect_to_deepgram_agent() as deepgram_ws:
        config_message = load_agent_config()

        await deepgram_ws.send(
            json.dumps(config_message)
        )

        await asyncio.wait(
            [
                asyncio.ensure_future(
                    send_audio_to_deepgram(
                        deepgram_ws,
                        audio_queue
                    )
                ),
                asyncio.ensure_future(
                    receive_from_deepgram(
                        deepgram_ws,
                        twilio_ws,
                        stream_sid_queue
                    )
                ),
                asyncio.ensure_future(
                    receive_from_twilio(
                        twilio_ws,
                        audio_queue,
                        stream_sid_queue
                    )
                ),
            ]
        )
        await twilio_ws.close()


"""
APPLICATION ENTRY POINT
"""
async def main():
    await websockets.serve(
        handle_twilio_connection,
        "localhost",
        5000
    )

    print("Started server")
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())