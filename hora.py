from openai import OpenAI
from dotenv import load_dotenv
import os 

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
audio_file = open("media/uploads/audio.ogg", "rb")

transcription = client.audio.transcriptions.create(
  file=audio_file,
  model="whisper-1",
  response_format="verbose_json",
  timestamp_granularities=["word", "segment"]
)

print(transcription.words, transcription.segments)