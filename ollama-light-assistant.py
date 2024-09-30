"""
Ollama Light Assistant

Author: Shawn Hymel
Date: September 17, 2024
License: BSD-0 (https://opensource.org/license/0bsd)
"""

from collections import deque
import json
import queue

from gpiozero import LED
import ollama
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# Settings
LED_PIN = 17
AUDIO_INPUT_INDEX = 0
MODEL = "allenporter/xlam:1b" # You could also try "llama3.1:8b"
OLLAMA_HOST = "http://localhost:11434"
MAX_MESSAGES = 5
PREAMBLE = "You are a helpful assistant that can turn the light on and off."

# Define tools for the model to use (i.e. functions)
TOOLS = [
    {
        'type': 'function',
        'function': {
            'name': "led_write",
            'description': "Turn the light off or on",
            'parameters': {
                'type': 'object',
                'properties': {
                    'value': {
                        'type': 'number',
                        'description': "The value to write to the light pin " \
                            "to turn it off and on. 0 for off, 1 for on.",
                    },
                },
                'required': ['value'],
            },
        }
    }
]

# -----------------------------------------------------------------------------
# Classes

class FixedSizeQueue:
    """
    Fixed size array with FIFO and optional preamble.
    """
    def __init__(self, max_size, preamble=None):
        self.queue = deque(maxlen=max_size)
        self.preamble = {
            'role': 'system',
            'content': preamble
        }

    def push(self, item):
        self.queue.append(item)

    def get(self):
        if self.preamble['content'] is None:
            return list(self.queue)
        else:
            return [self.preamble] + list(self.queue)

# -----------------------------------------------------------------------------
# Functions

def led_write(led, value):
    """
    Turn the LED on or off.
    """
    if int(value) > 0:
        led.on()
        print("The LED is now on")
    else:
        led.off()
        print("The LED is now off")

def send(chat, msg_history, client, model, tools, led):
    """
    Send a message to the LLM server and print the response.
    """

    # Add user message to the conversation history
    msg_history.push({
        'role': 'user',
        'content': chat
    })

    # Send message to LLM server
    response = client.chat(
        model=model,
        messages=msg_history.get(),
        tools=tools,
        stream=False
    )

    # Print the full response
    print(f"Response: {response['message']}")

    # Add the model's response to the conversation history
    msg_history.push({
        'role': 'assistant',
        'content': response['message']['content']
    })

    # Check if the model used any of the provided tools
    if response['message'].get('tool_calls') is None:
        print("Tools not used.")
        return

    # Call the function(s) the model used
    else:
        print("Tools used. Calling:")
        for tool in response['message']['tool_calls']:
            print(tool)
            if tool['function']['name'] == "led_write":
                led_write(led, tool['function']['arguments']['value'])

def record_callback(indata, frames, time, status, q):
    """
    Callback for recording audio from the microphone.
    """
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

# -----------------------------------------------------------------------------
# Main

if __name__ == "__main__":

    # Get the sample rate of the input device
    device_info = sd.query_devices(sd.default.device[0], 'input')
    sample_rate = int(device_info['default_samplerate'])

    # Build the STT model
    stt_model = Model(lang='en-us')
    stt_recognizer = KaldiRecognizer(stt_model, sample_rate)
    stt_recognizer.SetWords(False)

    # Configure chat history and connect to the LLM server
    msg_history = FixedSizeQueue(MAX_MESSAGES, PREAMBLE)
    chat_client = ollama.Client(host=OLLAMA_HOST)

    # Initialize the audio recording queue
    q = queue.Queue()

    # Initialize the LED and turn it off
    led = LED(LED_PIN)
    led.off()

    while True:

        # Listen for user input
        print("Listening...")
        result_text = ""
        with sd.RawInputStream(
            dtype='int16',
            channels=1,
            callback=lambda in_data, frames, time, status: record_callback(
                in_data,
                frames,
                time,
                status,
                q
            )
        ):

            # Collect audio data until we have a full phrase
            while True:
                data = q.get()
                if stt_recognizer.AcceptWaveform(data):

                    # Perform speech-to-text (STT) on the audio data
                    result = json.loads(stt_recognizer.Result())
                    result_text = result.get("text", "")
                    break

        # Send the user's message to the LLM server
        if not result_text:
            print("No speech detected")
        else:
            print(f"Speech detected: {result_text}")
            send(result_text, msg_history, chat_client, MODEL, TOOLS, led)