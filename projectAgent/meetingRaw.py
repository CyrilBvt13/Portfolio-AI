from faster_whisper import WhisperModel
import subprocess
from pathlib import Path

model = WhisperModel("medium", compute_type="float16")  # "base", "medium", "large"

segments, info = model.transcribe("reunion.wav")

transcription = ""
for segment in segments:
    transcription += f"{segment.text.strip()} "

with open("transcription.txt", "w") as f:
    f.write(transcription)

with open("transcription.txt", "r") as f:
    transcription = f.read()

prompt = f"""
Tu es un assistant projet. À partir de cette transcription de réunion, génère un compte-rendu structuré avec les sections suivantes :
- Titre de la réunion
- Date (à deviner ou laisser vide)
- Participants (si mentionnés)
- Décisions prises
- Tâches à faire (avec responsables si possible)
- Points bloquants ou questions

Transcription :
{transcription}
"""

# Appel à Ollama local
response = subprocess.run(
    ["ollama", "run", "mistral"],
    input=prompt.encode(),
    capture_output=True
)

with open("compte_rendu.txt", "w") as f:
    f.write(response.stdout.decode())