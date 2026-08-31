import os
import asyncio
import tempfile
import struct
import logging
import imageio_ffmpeg
from google import genai
from google.genai import types
from config import Config

# Suppress harmless google-genai AFC deprecation logger warning to keep logs clean
logging.getLogger("google_genai").setLevel(logging.ERROR)

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
    Bulletproof text-to-speech engine with Model Cascade and API key rotation.
    Converts text to an OGG Opus voice message compatible with Telegram.
    Returns the file path to the generated OGG file, or an error string starting with "Error:".
    """
    if not text.strip():
        return "Error: No text provided."
    if not api_keys:
        return "Error: No API keys provided."

    # Define cascade models to failover seamlessly
    models_to_try = [Config.GEMINI_TTS_MODEL]
    if Config.GEMINI_TTS_MODEL == "gemini-3.1-flash-tts-preview":
        models_to_try.append("gemini-2.5-flash-tts")
    elif Config.GEMINI_TTS_MODEL == "gemini-2.5-flash-tts":
        models_to_try.append("gemini-3.1-flash-tts-preview")

    last_error = None

    for model_name in models_to_try:
        for attempt in range(len(api_keys)):
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
                    model=model_name,
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

                # Convert WAV to OGG Opus for Telegram Voice Note by piping directly to ffmpeg
                fd, temp_ogg = tempfile.mkstemp(suffix=".ogg")
                os.close(fd)
                
                # Apply surgical FFmpeg filters: 
                # 1. Bandpass filter (highpass 200, lowpass 4000) to simulate a smartphone microphone's frequency response.
                # 2. Pink noise overlay (anoisesrc) to simulate natural room ambiance and mic static.
                cmd = [
                    FFMPEG_EXE, "-y", 
                    "-i", "pipe:0",
                    "-f", "lavfi", "-i", "anoisesrc=c=pink:r=24000:a=0.012",
                    "-filter_complex", "[0:a]highpass=f=200,lowpass=f=4000[v];[v][1:a]amix=inputs=2:duration=shortest[a]",
                    "-map", "[a]",
                    "-c:a", "libopus", "-b:a", "32k",
                    temp_ogg
                ]

                process = await asyncio.create_subprocess_exec(
                    *cmd, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
                )
                _, stderr = await process.communicate(input=wav_bytes)

                if process.returncode != 0:
                    if os.path.exists(temp_ogg):
                        try:
                            os.remove(temp_ogg)
                        except:
                            pass
                    return f"Error: FFMPEG conversion failed.\n{stderr.decode(errors='ignore')}"

                return temp_ogg

            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                
                if "503" in err_str or "500" in err_str or "unavailable" in err_str or "internal" in err_str or "timeout" in err_str:
                    print(f"⚠️ Gemini Network Error on TTS ({model_name}) (503/Timeout). Forcing immediate cascade to next model...")
                    break  # Break API key loop, go immediately to next model!
                elif "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                    print(f"⏳ Key {key_preview} hit rate limit on TTS ({model_name}). Rotating...")
                    continue
                elif "403" in err_str or "api_key_invalid" in err_str:
                    print(f"❌ Key {key_preview} is invalid. Rotating...")
                    continue
                else:
                    print(f"⚠️ Unknown error on TTS with key {key_preview} ({model_name}): {e}. Rotating...")
                    continue

    return f"Error: All keys and models exhausted during TTS generation. Last Error: {last_error}"
