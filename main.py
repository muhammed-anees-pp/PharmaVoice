import asyncio
import base64
import json
import websockets
import os
from pathlib import Path
from dotenv import load_dotenv
from pharmacy_functions import FUNCTION_MAP
from pharmacy_storage import initialize_database
load_dotenv()


BASE_DIR = Path(__file__).resolve().parent


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
    with open(BASE_DIR / "config.json", "r") as f:
        return json.load(f)


"""
HANDLE USER INTERRUPTION
"""
async def handle_user_interrupt(message_data, twilio_ws, stream_sid):
    if message_data.get("type") == "UserStartedSpeaking":
        clear_message = {
            "event": "clear",
            "streamSid": stream_sid,
        }

        await twilio_ws.send(
            json.dumps(clear_message)
        )


"""
EXECUTE TOOL CALL
"""
def execute_tool_call(function_name, arguments):
    if function_name in FUNCTION_MAP:
        result = FUNCTION_MAP[function_name](**arguments)
        print(f"Function call result: {result}")
        return result

    result = {"error": f"Unknown function: {function_name}"}
    print(result)
    return result


"""
BUILD FUNCTION CALL RESPONSE
"""
def build_function_call_response(function_id, function_name, result):
    return {
        "type": "FunctionCallResponse",
        "id": function_id,
        "name": function_name,
        "content": json.dumps(result),
    }


"""
HANDLE FUNCTION CALLS
"""
async def handle_function_calls(message_data, deepgram_ws):
    try:
        for function_call in message_data["functions"]:
            function_name = function_call["name"]
            function_id = function_call["id"]
            arguments = function_call["arguments"]

            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            print(
                f"Function call: {function_name} "
                f"(ID: {function_id}), "
                f"arguments: {arguments}"
            )

            result = execute_tool_call(function_name,arguments)
            function_result = build_function_call_response(function_id,function_name,result)
            await deepgram_ws.send(json.dumps(function_result))

            print(
                f"Sent function result: "
                f"{function_result}"
            )

    except Exception as error:
        print(
            f"Error calling function: {error}"
        )

        error_result = build_function_call_response(
            (
                function_id
                if "function_id" in locals()
                else "unknown"
            ),
            (
                function_name
                if "function_name" in locals()
                else "unknown"
            ),
            {
                "error": (
                    f"Function call failed with: "
                    f"{str(error)}"
                )
            },
        )

        await deepgram_ws.send(json.dumps(error_result))


"""
HANDLE DEEPGRAM MESSAGES
"""
async def handle_deepgram_message(message_data, twilio_ws, deepgram_ws, stream_sid):
    await handle_user_interrupt(message_data,twilio_ws,stream_sid)


    if message_data.get("type") == "FunctionCallRequest":
        await handle_function_calls(message_data, deepgram_ws)


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
    initialize_database()

    await websockets.serve(
        handle_twilio_connection,
        "localhost",
        5000
    )

    print("Started server")

    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped")
