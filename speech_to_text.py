import os
import asyncio
import wave
import tempfile
import traceback
import subprocess
import logging

import imageio_ffmpeg
from google import genai
from google.genai import types
from config import Config
from logger import logger

# Suppress harmless google-genai AFC deprecation logger warning to keep logs clean
logging.getLogger("google_genai").setLevel(logging.ERROR)

# Get the bundled rock-solid ffmpeg binary path
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

MODEL = Config.GEMINI_STT_MODEL
CHUNK_SIZE = 1024

async def transcribe_audio_file(file_path: str, api_keys: list[str], lang_code: str = "fa") -> str:
    """
    Bulletproof speech-to-text engine with API key rotation.
    Converts any audio file to 16kHz Mono 16-bit PCM WAV and transcribes it using Gemini Live.
    """
    logger.debug(f"[MEDIA] STT started for file: {file_path}")
    if not os.path.exists(file_path):
        return "Error: File not found."
    if not api_keys:
        return "Error: No API keys provided."

    temp_wav_path = None
    last_error = None
    try:
        # 1. Flawless audio conversion to 16000Hz, mono, 16-bit PCM WAV using direct ffmpeg
        fd, temp_wav_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        # Run ffmpeg to convert any input format to strict 16kHz mono WAV, capped at timeout
        cmd = [
            FFMPEG_EXE, "-y", "-i", file_path, 
            "-t", str(Config.FFMPEG_TIMEOUT_SECONDS), 
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", 
            temp_wav_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await process.communicate()
        
        if process.returncode != 0:
            return f"Error: Audio conversion failed.\n{stderr.decode(errors='ignore')}"
        
        # 2. Connect to API with Rotation Logic
        max_attempts = len(api_keys)
        
        for attempt in range(max_attempts):
            api_key = api_keys[attempt % len(api_keys)]
            key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key
            
            client = genai.Client(
                http_options={"api_version": "v1beta"},
                api_key=api_key,
            )

            config = types.LiveConnectConfig(
                response_modalities=["TEXT"],
                input_audio_transcription=types.AudioTranscriptionConfig(
                    language_auto=types.LanguageAuto(),
                ),
                context_window_compression=types.ContextWindowCompressionConfig(
                    trigger_tokens=104857,
                    sliding_window=types.SlidingWindow(target_tokens=52428),
                ),
            )

            full_transcription = []

            try:
                async with client.aio.live.connect(model=MODEL, config=config) as session:
                    
                    audio_finished = False
                    raw_debug_data = []

                    async def send_audio():
                        nonlocal audio_finished
                        chunk_frames = 16000 
                        with wave.open(temp_wav_path, 'rb') as wf:
                            while True:
                                data = wf.readframes(chunk_frames)
                                if not data:
                                    break
                                await session.send(input={"data": data, "mime_type": "audio/pcm;rate=16000"})
                                await asyncio.sleep(0.1) # Upload at 10x real-time to prevent server buffer overflow
                                
                        await session.send(input="", end_of_turn=True)
                        audio_finished = True

                    async def receive_transcription():
                        ag = session.receive()
                        current_interim = ""
                        current_timeout = Config.STT_INITIAL_TIMEOUT_SECONDS  # Wait up to 45s for Gemini to start responding to large files
                        
                        while True:
                            try:
                                response = await asyncio.wait_for(ag.__anext__(), timeout=current_timeout)
                                current_timeout = Config.STT_STREAMING_TIMEOUT_SECONDS  # Once streaming, wait up to 25s for new tokens
                                
                                sc = getattr(response, "server_content", None)
                                if sc is not None:
                                    transcription_obj = getattr(sc, "input_transcription", None)
                                    if transcription_obj is not None and getattr(transcription_obj, "text", ""):
                                        full_transcription.append(transcription_obj.text.strip())
                                        current_interim = ""
                                        
                                    interim_obj = getattr(sc, "interim_input_transcription", None)
                                    if interim_obj is not None and getattr(interim_obj, "text", ""):
                                        current_interim = interim_obj.text.strip()
                                        
                                    model_turn = getattr(sc, "model_turn", None)
                                    if model_turn is not None:
                                        for part in getattr(model_turn, "parts", []):
                                            if getattr(part, "text", ""):
                                                full_transcription.append(part.text.strip())
                                    
                                    if audio_finished and (getattr(sc, "turn_complete", False) or getattr(sc, "generation_complete", False)):
                                        break
                            except (asyncio.TimeoutError, StopAsyncIteration):
                                break
                                
                        if current_interim:
                            full_transcription.append(current_interim)

                    await asyncio.gather(
                        send_audio(),
                        receive_transcription()
                    )

                final_res = " ".join(full_transcription).strip()
                if not final_res:
                    return f"Error: Empty transcription. Raw: {raw_debug_data[:3]}"
                pass
                return final_res

            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                if "404" in err_str:
                    logger.error(f"❌ NOT FOUND (404): Model '{MODEL}' is invalid!")
                    return f"Error: STT Model '{MODEL}' is invalid or deprecated."
                elif "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                    logger.warning(f"⏳ Key {key_preview} hit rate limit on live transcribe. Rotating...")
                    continue
                elif "403" in err_str or "api_key_invalid" in err_str:
                    logger.warning(f"❌ Key {key_preview} is invalid. Rotating...")
                    continue
                else:
                    logger.error(f"⚠️ Unknown error on live transcribe with key {key_preview}: {e}. Rotating...")
                    continue
                    
        logger.error(f"All keys exhausted during STT. Last Error: {last_error}")
        return f"Error: All keys exhausted or failed during transcription. Last Error: {last_error}"

    except Exception as e:
        logger.error(f"Error during audio processing: {e}", exc_info=True)
        return f"Error during audio processing: {str(e)}"
    finally:
        # 3. Cleanup
        if temp_wav_path and os.path.exists(temp_wav_path):
            try:
                os.remove(temp_wav_path)
            except:
                pass
