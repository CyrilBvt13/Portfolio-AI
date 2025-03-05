import requests
import json
import time

'''
   Exemple d'un client interrogeant l'API Flask.
'''

# Identifiant unique du client
client_id = "user_123"

# Question de l'utilisateur
question = input("Question : ")

# Envoi de la question via HTTP
data = {
    "question": question,
    "client_id": client_id
}
response = requests.post("http://localhost:5000/ask", json=data)

if response.status_code == 202:
    question_id = response.json().get("question_id")
    print(f"✅ Question envoyée (ID: {question_id}) : En attente de réponse...")

    # Attente active de la réponse
    timeout = 10  # Temps max d'attente en secondes
    start_time = time.time()

    while True: # Pour ajouter un timeout : (time.time() - start_time) < timeout
        time.sleep(5)  # Polling toutes les 5 secondes
        status_response = requests.get(f"http://localhost:5000/status/{question_id}")

        if status_response.status_code == 200:
            status_data = status_response.json()
            if status_data["status"] == "completed":
                print("📩 Réponse reçue :", status_data["response"])
                break
            elif status_data["status"] == "error":
                print("❌ Erreur :", status_data["response"])
                break
        elif status_response.status_code == 404:
            print("❌ Question ID inconnu ou expiré")
            break

    else:
        print("❌ Temps d'attente dépassé, aucune réponse reçue.")