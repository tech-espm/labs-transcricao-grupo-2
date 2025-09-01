from openai import OpenAI
from dotenv import load_dotenv
import os 
import json

load_dotenv()

"""
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
audio_file = open("media/uploads/audio.ogg", "rb")

def transcribe_audio(file):
  transcription = client.audio.transcriptions.create(
      file=file,
      model="whisper-1",
      response_format="verbose_json",
      timestamp_granularities=["word", "segment"]
  )
  return transcription

#para criar o mock up
with open("transcricao.json", "w", encoding="utf-8") as arquivo_json:
    lista = []
    for word in transcribe_audio(audio_file).words:
        lista.append({
            "word": word.word,
            "start": word.start,
            "end": word.end
        })
    arquivo_json.write(json.dumps(lista))
"""

transcript = {
    "words": []
}

with open("transcricao.json", "r", encoding="utf-8") as arquivo_json:
	transcript["words"] = json.loads(arquivo_json.read())
 
for word in transcript["words"]:
	print(f"{(word['start'] * 1000):.0f}\t{(word['end'] * 1000):.0f}\t{word['word']}")


sentencas = []
sentenca_atual = []

for i, word in enumerate(transcript["words"]):
    if i == 0 or word["start"] == transcript["words"][i-1]["end"]:
        sentenca_atual.append(word["word"])
    else:
        if sentenca_atual:
            sentencas.append(" ".join(sentenca_atual))
        sentenca_atual = [word["word"]]
if sentenca_atual:
    sentencas.append(" ".join(sentenca_atual))

print(sentencas)

