from flask import Flask, request, jsonify
import threading
import time
import uuid

from launchRag import startRag

'''
   API Flask permettant d'interroger le RAG.
'''

# Initialiser le RAG
rag_pipeline, retriever, rag_chain, retrieval_grader, question_rewriter, hallucination_grader, answer_grader = startRag()

# Initialisation de Flask
app = Flask(__name__)

# Stockage des requêtes en cours et des réponses
pending_requests = {}
EXPIRATION_TIME = 300  # 5 minutes en secondes

# Fonction de nettoyage des requêtes expirées
def cleanup_old_requests():
    while True:
        current_time = time.time()
        expired_ids = [
            question_id
            for question_id, data in pending_requests.items()
            if current_time - data["timestamp"] > EXPIRATION_TIME
        ]
        
        for question_id in expired_ids:
            print(f"🗑️ Suppression de la requête expirée : {question_id}")
            del pending_requests[question_id]

        time.sleep(60)  # Vérification toutes les 60 secondes

# Lancer le thread de nettoyage en arrière-plan
cleanup_thread = threading.Thread(target=cleanup_old_requests, daemon=True)
cleanup_thread.start()

# Traitement de la question en arrière-plan
def process_question(question_id, question):
    print(f"📩 Traitement en arrière-plan : {question}")

    try:
        # Appel du RAG
        response = rag_pipeline(
            question,
            retriever=retriever,
            rag_chain=rag_chain,
            retrieval_grader=retrieval_grader,
            question_rewriter=question_rewriter,
            hallucination_grader=hallucination_grader,
            answer_grader=answer_grader,
        )

        print(f"✅ Réponse générée pour {question_id}: {response}")

        # Stocke la réponse
        pending_requests[question_id]["response"] = response
        pending_requests[question_id]["status"] = "completed"

    except Exception as e:
        print(f"❌ Erreur : {e}")
        pending_requests[question_id]["response"] = "Erreur serveur"
        pending_requests[question_id]["status"] = "error"

# Définition de la route Flask
@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get("question", "")
    client_id = data.get("client_id", "")
    
    if not question:
        return jsonify({"error": "Aucune question fournie"}), 400

    # Générer un ID unique pour la question
    question_id = str(uuid.uuid4())

    # Enregistrer la requête comme "en attente"
    pending_requests[question_id] = {
        "status": "pending",
        "response": None,
        "timestamp": time.time()
    }

    print(f"📩 Question reçue (ID: {question_id})")

    # Lancer le traitement en arrière-plan
    thread = threading.Thread(target=process_question, args=(question_id, question))
    thread.start()

    return jsonify({"question_id": question_id, "status": "pending"}), 202

# Route HTTP pour vérifier l'état de la question
@app.route('/status/<question_id>', methods=['GET'])
def get_status(question_id):
    if question_id not in pending_requests:
        return jsonify({"error": "Question ID inconnu"}), 404

    status_data = pending_requests[question_id]

    if status_data["status"] == "completed":
        return jsonify({"status": "completed", "response": status_data["response"]}), 200
    elif status_data["status"] == "error":
        return jsonify({"status": "error", "response": status_data["response"]}), 500
    else:
        return jsonify({"status": "pending"}), 202

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True, use_reloader=False)