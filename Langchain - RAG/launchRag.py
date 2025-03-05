from langchain_community.document_loaders import CSVLoader, PyMuPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import SKLearnVectorStore
from sentence_transformers import SentenceTransformer # https://www.sbert.net/index.html
from langchain.embeddings.base import Embeddings

from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.schema import Document

import os

# Chemin de sauvegarde du VectorStore
PERSIST_PATH = os.path.join('./Store/', "vectorstore.pqt")

active_log = False # Activer/désactiver l'affichage des logs

def log(message):
    if active_log:
        print(message)

def startRag():
    print("🔄 Chargement du RAG...")

    # Charger le modèle d'embedding
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Fonction de récupération des embeddings
    class PrecomputedEmbeddings(Embeddings):
        def __init__(self, precomputed_vectors):
            self.precomputed_vectors = precomputed_vectors  # Stocke les embeddings calculés
    
        def embed_documents(self, texts):
            return self.precomputed_vectors # Retourne les embeddings déjà calculés.
    
        def embed_query(self, text):
            return model.encode([text])[0]  # Génère l'embedding pour une nouvelle requête et retourne un seul vecteur

    # Vérifier si le VectorStore existe déjà
    if os.path.exists(PERSIST_PATH):   
        # Charger le VectorStore existant
        vectorstore = SKLearnVectorStore(
            persist_path=PERSIST_PATH,
            embedding=PrecomputedEmbeddings([]),  # Embeddings fictifs pour respecter l'interface
            serializer="parquet"
        )

        # Créer un retriver
        retriever = vectorstore.as_retriever(k=1)

        ### Retrieval Grader
        llm = ChatOllama(
            model="mistral:latest",
            format="json",
            temperature=0,
        )

        prompt = PromptTemplate(
            template="""Tu es un évaluateur évaluant la pertinence d'un document récupéré par rapport à une question d'un utilisateur. \n 
            Voici le document récupéré : \n\n {document} \n\n
            Voici la question de l'utilisateur : {question} \n
            Si le document contient des mots-clés liés à la question de l'utilisateur, note-le comme pertinent. \n
            Ce n'est pas nécessaire que ce soit un test rigoureux. Le but est de filtrer les récupérations erronées. \n
            Donne un score binaire « oui » ou « non » pour indiquer si le document est pertinent par rapport à la question. \n
            Fournis le score binaire au format JSON avec une clé unique « score » et sans préambule ni explication.""",
            input_variables=["question", "document"],
        )

        retrieval_grader = prompt | llm | JsonOutputParser()
        question = "agent memory"
        docs = retriever.invoke(question)
        doc_txt = docs[1].page_content

        ### Generate
        llm = ChatOllama(
            model="mistral:latest",
            temperature=0,
        )

        prompt = PromptTemplate(
            template="""Utilise les documents suivants pour répondre à la question.
            Ne donne pas de réponse sans utiliser les documents.
            Tu devras obligatoirement répondre en français.
            Question: {question}
            Documents: {documents}
            Réponse:
            """,
            input_variables=["question", "documents"],
        )

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = prompt | llm | StrOutputParser()
        generation = rag_chain.invoke({"documents": docs, "question": question})

        ### Hallucination Grader
        llm = ChatOllama(
            model="mistral:latest",
            format="json",
            temperature=0,
        )

        prompt = PromptTemplate(
            template="""Tu es un évaluateur qui évalue si une réponse est fondée/étayée par un ensemble de faits. \n 
            Voici les faits :
            \n ------- \n
            {documents} 
            \n ------- \n
            Voici la réponse : {generation}
            Donne un score binaire « oui » ou « non » pour indiquer si la réponse est fondée / étayée par un ensemble de faits. \n
            Fournis le score binaire au format JSON avec une clé unique « score » et sans préambule ni explication.""",
            input_variables=["generation", "documents"],
        )

        hallucination_grader = prompt | llm | JsonOutputParser()
        hallucination_grader.invoke({"documents": docs, "generation": generation})

        ### Answer Grader
        llm = ChatOllama(
            model="mistral:latest",
            format="json",
            temperature=0,
        )

        prompt = PromptTemplate(
            template="""Tu es un évaluateur qui évalue si une réponse est utile pour résoudre une question. \n 
            Voici la réponse :
            \n ------- \n
            {generation} 
            \n ------- \n
            Voici la question : {question}
            Donne un score binaire « oui » ou « non » pour indiquer si la réponse est utile pour résoudre une question. \n
            Fournis le score binaire au format JSON avec une clé unique « score » et sans préambule ni explication.""",
            input_variables=["generation", "question"],
        )

        answer_grader = prompt | llm | JsonOutputParser()
        answer_grader.invoke({"question": question, "generation": generation})

        ### Question Re-writer
        llm = ChatOllama(
            model="mistral:latest",
            temperature=0,
        )

        re_write_prompt = PromptTemplate(
            template="""Tu es un reformulateur de questions qui convertit une question d'entrée en une meilleure version optimisée \n 
                pour la récupération du magasin vectoriel. Regarde la question initiale et formule une question améliorée. \n
                Tu devras obligatoirement répondre en français. \n
                Voici la question initiale : \n\n {question}. Question améliorée sans préambule : \n""",
            input_variables=["generation", "question"],
        )

        question_rewriter = re_write_prompt | llm | StrOutputParser()
        question_rewriter.invoke({"question": question})

        # 1️⃣ Étape : Récupération des documents
        def retrieve(question, retriever):
            log("---RETRIEVE---")
            documents = retriever.invoke(question)
            for document in documents:
                log(f'  📃 Document : {document.page_content}')
            return documents

        # 2️⃣ Étape : Filtrage des documents
        def grade_documents(question, documents, retrieval_grader):
            log("---CHECK RELEVANCE---")
            filtered_docs = []
            for d in documents:
                score = retrieval_grader.invoke({"question": question, "document": d.page_content})
                if score["score"] == "oui":
                    log(f'  ✅ Relevant : {d.page_content}')
                    filtered_docs.append(d)
                else:
                    log(f'  ❌ Not relevant : {d.page_content}')
            return filtered_docs

        # 3️⃣ Étape : Réécriture de la question si nécessaire
        def transform_query(question, question_rewriter):
            log("---TRANSFORM QUERY---")
            better_question = question_rewriter.invoke({"question": question})
            log(f'📩 Nouvelle question : {better_question}')
            return better_question

        # 4️⃣ Étape : Generation de la réponse avec le modèle LLM
        def generate(question, documents, rag_chain):
            log("---GENERATE---")
            generation = rag_chain.invoke({"documents": documents, "question": question})
            log(f'📩 Réponse : {generation}')
            return generation

        # 5️⃣ Étape : Vérification de la réponse (hallucination et pertinence)
        def validate_answer(question, documents, generation, hallucination_grader, answer_grader):
            log("---CHECK HALLUCINATIONS---")
            score = hallucination_grader.invoke({"documents": documents, "generation": generation})
    
            if score["score"] != "oui":
                log(f'❌ Hallucination détectée')
                return False
            log(f"✅ Pas d'hallucination!")

            log("---CHECK ANSWER---")
            score = answer_grader.invoke({"question": question, "generation": generation})
    
            if score["score"] != "oui":
                log(f'❌ Réponse incorrecte')
                return False
    
            log(f'✅ Réponse validée!')
            return True  # Réponse validée

        # Fonction principale qui exécute toutes les étapes
        def rag_pipeline(question, retriever, rag_chain, retrieval_grader, question_rewriter, hallucination_grader, answer_grader):
            max_attempts = 3  # Nombre maximum de reformulations
            attempt = 0  # Compteur de tentatives

            while attempt < max_attempts:
                # Étape 1 : Récupération
                documents = retrieve(question, retriever)

                # Étape 2 : Filtrage des documents
                filtered_docs = grade_documents(question, documents, retrieval_grader)

                if not filtered_docs:
                    # Aucun document pertinent → reformuler la question
                    attempt += 1
                    if attempt < max_attempts:
                        question = transform_query(question, question_rewriter)
                        continue  # Recommencer avec la question reformulée
                    else:
                        # Si on atteint la limite de tentatives
                        return "😞 Oups, nous n'avons pas trouvé l'information souhaitée! Tentez de reformuler votre question pour de meilleurs résultats."

                # Étape 3 : Generation de la réponse
                generation = generate(question, filtered_docs, rag_chain)

                # Étape 4 : Vérification de la réponse
                if validate_answer(question, filtered_docs, generation, hallucination_grader, answer_grader):
                    return generation  # Réponse validée, on sort de la boucle
                else:
                    # Si la réponse n'est pas fiable, reformuler la question
                    attempt += 1
                    if attempt < max_attempts:
                        question = transform_query(question, question_rewriter)
                    else:
                        return "😞 Oups, nous n'avons pas trouvé l'information souhaitée! Tentez de reformuler votre question pour de meilleurs résultats."
        
        print("✅ RAG chargé.")

        return rag_pipeline, retriever, rag_chain, retrieval_grader, question_rewriter, hallucination_grader, answer_grader
    else:
        # Si la base vectorielle n'existe pas
        print("❌ Aucun VectorStore existant, créez en un avec generateStore.")
        return None
