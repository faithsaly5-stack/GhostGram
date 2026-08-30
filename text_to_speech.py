import os
import asyncio
import tempfile
import struct
import imageio_ffmpeg
from google import genai
from google.genai import types
from config import Config

# Get the bundled rock-solid ffmpeg binary path
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

MODEL = Config.GEMINI_TTS_MODEL

def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    bits_per_sample = 16
    rate = 24000
    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate = int(param.split("=", 1)[1])
            except (ValueError, IndexError):
                pass
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass
    return {"bits_per_sample": bits_per_sample, "rate": rate}

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", chunk_size, b"WAVE", b"fmt ", 16, 1, num_channels,
        sample_rate, byte_rate, block_align, bits_per_sample, b"data", data_size
    )
    return header + audio_data

async def generate_voice_message(text: str, api_keys: list[str], voice_name: str = "Aoede") -> str:
    """
    Bulletproof text-to-speech engine with API key rotation.
    Converts text to an OGG Opus voice message compatible with Telegram.
    Returns the file path to the generated OGG file, or an error string starting with "Error:".
    """
    if not text.strip():
        return "Error: No text provided."
    if not api_keys:
        return "Error: No API keys provided."

    max_attempts = len(api_keys)
    last_error = None

    for attempt in range(max_attempts):
        api_key = api_keys[attempt % len(api_keys)]
        key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key

        client = genai.Client(api_key=api_key)

        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=text)],
            ),
        ]
        
        config = types.GenerateContentConfig(
            temperature=1,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                )
            ),
        )

        try:
            full_audio = b""
            mime_type = "audio/L16;rate=24000"

            response_stream = await client.aio.models.generate_content_stream(
                model=MODEL,
                contents=contents,
                config=config,
            )

            async for chunk in response_stream:
                if chunk.parts is None:
                    continue
                if chunk.parts[0].inline_data and chunk.parts[0].inline_data.data:
                    inline_data = chunk.parts[0].inline_data
                    full_audio += inline_data.data
                    mime_type = inline_data.mime_type

            if not full_audio:
                raise Exception("No audio data returned from the API.")

            # Convert raw PCM to WAV bytes
            wav_bytes = convert_to_wav(full_audio, mime_type)

            # Save temporary WAV
            temp_wav = tempfile.mktemp(suffix=".wav")
            with open(temp_wav, "wb") as f:
                f.write(wav_bytes)

            # Convert WAV to OGG Opus for Telegram Voice Note
            temp_ogg = tempfile.mktemp(suffix=".ogg")
            cmd = [
                FFMPEG_EXE, "-y", "-i", temp_wav,
                "-c:a", "libopus", "-b:a", "32k",
                temp_ogg
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()

            # Cleanup temp WAV
            if os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except:
                    pass

            if process.returncode != 0:
                return f"Error: FFMPEG conversion failed.\n{stderr.decode(errors='ignore')}"

            return temp_ogg

        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                print(f"⏳ Key {key_preview} hit rate limit on TTS. Rotating...")
                continue
            elif "403" in err_str or "api_key_invalid" in err_str:
                print(f"❌ Key {key_preview} is invalid. Rotating...")
                continue
            else:
                print(f"⚠️ Unknown error on TTS with key {key_preview}: {e}. Rotating...")
                continue

    return f"Error: All keys exhausted or failed during TTS generation. Last Error: {last_error}"
