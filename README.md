# Ollama Light Assistant

Test the ability for LLMs to call tools (i.e. functions) from within the Ollama
environment on a Raspberry Pi with speech-to-text. Tested with a Raspberry Pi 5
(8 GB) and this USB microphone: https://www.adafruit.com/product/3367.

## Tutorial

Connect an LED to GPIO 17 (physical pin 11 on the board) in an active high
configuration:

```
GPIO 17 -> 220 Ohm resistor -> LED -> GND
```

Install dependencies:

```bash
$ curl -fsSL https://ollama.com/install.sh | sh
$ ollama serve
$ sudo apt install -y libportaudio2
```

Create a Python virtual environment and install necessary packages. We need
system site packages enabled so that gpiozero actually works.

```bash
$ python -m venv venv-ollama --system-site-packages
$ source venv-ollama/bin/activate
$ python -m pip install ollama vosk sounddevice
```

Download the LLM and Vosk STT model:

```bash
$ ollama pull allenporter/xlam:1b
$ python -c "from vosk import Model; Model(lang='en-us')"
```

Get the USB device number of your attached microphone:

```bash
$ python -c "import sounddevice; print(sounddevice.query_devices())"
```

For example, my device number is '0' for the "USB PnP Sound Device." Change the
AUDIO_INPUT_INDEX value to this number in the code below.

Run the script with:

```bash
$ python ollama-light-assistant.py
```

Give a voice command like "turn on the light" to have the LLM call the 
led_write() function.

For the xlam:1b model, you must be SUPER specific with your commands. For
example, it will accept "turn on the light" but not "turn the light on." You 
can try the llama3.1:8b model for more flexibility, but it's VERY slow on the 
Pi 5, taking up to 3 minutes to respond.

Note: LLMs are SUPER slow on the Raspberry Pi right now, and tool calling is
janky. Once we get better/smaller LLMs, more RAM, and/or AI accelerators, this
should (in theory) be much faster and more robust.

References:
    Ollama tools: https://ollama.com/blog/tool-support
    Tool-supported models: https://ollama.com/search?c=tools

## License

Unless otherwise specified, all code in this repository is released under the [BSD-0 license](ttps://opensource.org/license/0bsd).

Copyright (C) 2024 by Shawn Hymel

Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.