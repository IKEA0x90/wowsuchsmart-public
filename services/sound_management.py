import time
import azure.cognitiveservices.speech as speechsdk
import random
import asyncio
import os

class Voice:

    def __init__(self, name, language, styles):
        self.name = name
        self.language = language
        self.styles = styles
        
    @staticmethod
    def find_matching_voice(language, style):
        matching_voices = []
        matching_language_voices = []
        if language == "Unknown":
            language = "English"
        for voice in voices:
            if voice.language.lower() == language.lower():
                if style.lower() in [s.lower() for s in voice.styles]:
                    matching_voices.append(voice)
                else:
                    matching_language_voices.append(voice)

        if matching_voices:
            return random.choice(matching_voices)
        elif matching_language_voices:
            return random.choice(matching_language_voices)
        else:
            raise ValueError(f"Sowwy, I don't speak {language} yet :(")

unparsed = [{"name":"en-US-JennyNeural", "language":"English", "styles":['Default', 'Assistant', 'Chat', 'Customer-service', 'Newscast', 'Angry', 'Cheerful', 'Sad', 'Excited', 'Friendly', 'Terrified', 'Shouting', 'Unfriendly', 'Whispering', 'Hopeful']}]
voices = [Voice(voice["name"], voice["language"], voice["styles"]) for voice in unparsed]

all_styles = ["Angry",
"Assistant",
"Chat",
"Cheerful",
"Customer-service",
"Default",
"Empathetic",
"Excited",
"Friendly",
"Hopeful",
"Narration-professional",
"Newscast",
"Newscast-casual",
"Newscast-formal",
"Sad",
"Shouting",
"Terrified",
"Unfriendly",
"Whispering"]

speech_key = ""
service_region = ""
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

async def make_ssml(voice, language, style, text_to_speak):
    reason = ""
    if style.lower() not in [s.lower() for s in all_styles]:
        return
        
    if language == "Unknown":
        language = "English"

    voice = voice or Voice.find_matching_voice(language, style)

    return [f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">
    <voice name="{voice.name}">
        <mstts:express-as style="{style.lower()}">
        {text_to_speak}
        </mstts:express-as>
    </voice>
    </speak>
    """, language, style, reason]

async def text_to_speech(ssml):
    def synthesize_speech():
        return speech_synthesizer.speak_ssml_async(ssml).get()

    result = await asyncio.get_event_loop().run_in_executor(None, synthesize_speech)

    # Check the result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        # Create a log folder if it doesn't exist
        if not os.path.exists("log"):
            os.makedirs("log")

        # Save the MP3 file in the log folder
        file_name = f"{int(time.time())}.mp3"
        file_path = os.path.join("log", file_name)
        with open(file_path, "wb") as audio_file:
            audio_file.write(result.audio_data)
        return file_path
    else:
        cancellation_details = result.cancellation_details
        error_message = f"Speech synthesis canceled. Reason: {cancellation_details.reason}. Error details: {cancellation_details.error_details}"
        raise Exception(error_message)