# pip install transformers accelerate torch sentencepiece
# pip install faster-whisper
# pip install watchdog

from transformers import AutoTokenizer, AutoModelForCausalLM, TextGenerationPipeline
from faster_whisper import WhisperModel
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import time

model_id = "aixplain/SmolLM-3B-v0.1"  # ou un autre modèle LLM 100% local

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", torch_dtype="auto")

generator = TextGenerationPipeline(model=model, tokenizer=tokenizer)

def formater_prompt(transcription):
    return f"""
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

def transcrire_audio(fichier_audio):
    model = WhisperModel("medium", compute_type="float16")
    segments, _ = model.transcribe(fichier_audio)
    return " ".join([s.text.strip() for s in segments])

def generer_cr(transcription):
    prompt = formater_prompt(transcription)
    resultat = generator(prompt, max_new_tokens=1024, do_sample=True)[0]["generated_text"]
    return resultat

class AgentIA(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith(".wav"):
            print(f"🎤 Nouveau fichier détecté : {event.src_path}")
            transcription = transcrire_audio(event.src_path)
            compte_rendu = generer_cr(transcription)

            nom_base = os.path.splitext(os.path.basename(event.src_path))[0]
            with open(f"compte_rendus/{nom_base}_cr.txt", "w") as f:
                f.write(compte_rendu)
            print("✅ Compte-rendu généré.")

# Surveillance dossier
chemin_dossier = "./audios"
observer = Observer()
observer.schedule(AgentIA(), path=chemin_dossier, recursive=False)
observer.start()

print("🚀 Agent IA démarré... (Ctrl+C pour arrêter)")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()