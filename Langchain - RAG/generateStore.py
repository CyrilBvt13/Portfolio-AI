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
import pickle
import json

'''
   Cette application est un Self-RAG utilisant Mistral (Ollama), LangChain et SickitLearn en local pour traiter des documents CSV et PDF,
   générer les embeddings et intégrer un retriever pour la recherche de réponse.

   Auteur : Cyril Bouvart

   Sources : https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag_local/#create-index

   Prérequis :
       pip install langchain_community sentence_transformers langchain-ollama pymupdf docx2txt tiktoken pandas pyarrow
'''

# Chemin de sauvegarde du VectorStore
PERSIST_PATH = os.path.join('./Store/', "vectorstore.pqt")

active_log = True # Activer/désactiver l'affichage des logs

def log(message):
    if active_log:
        print(message)

log("🔄 Chargement des documents")

# Chargement des documents CSV
csv_docs = []
csv_folder = "./Sources/CSV/"

for filename in os.listdir(csv_folder):
    if filename.endswith(".csv"):
        csv_path = os.path.join(csv_folder, filename)
        loader = CSVLoader(file_path=csv_path,
            csv_args={
                'delimiter': ';',
                'quotechar': '"',
                'fieldnames': ['Interface', 'Description', 'Solution']
            }
        )
        csv_docs.extend(loader.load())
        log(f'  🔄 Chargement du document {filename}')

# Chargement des documents PDF
pdf_docs = []
pdf_folder = "./Sources/PDF/"  # Dossier contenant les PDF

for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(pdf_folder, filename)
        loader = PyMuPDFLoader(pdf_path)
        pdf_docs.extend(loader.load())
        log(f'  🔄 Chargement du document {filename}')

# Chargement des documents Word
docx_docs = []
docx_folder = "./Sources/DOCX/"

for filename in os.listdir(docx_folder):
    if filename.endswith(".docx"):
        docx_path = os.path.join(docx_folder, filename)
        loader = Docx2txtLoader(docx_path)
        docx_docs.extend(loader.load())
        log(f'  🔄 Chargement du document {filename}')

# Fusion de tous les documents (CSV + PDF + DOCX)
docs = csv_docs + pdf_docs + docx_docs

# Découpage des documents en truncks
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=124, chunk_overlap=24
)
doc_splits = text_splitter.split_documents(docs)

# Extraction du texte des documents pour stockage
texts = [doc.page_content for doc in doc_splits]

# Généreation des embeddings avec SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(texts)

# Encapsulation dans la classe Embeddings pour respecter l'interface attendue
class PrecomputedEmbeddings(Embeddings):
    def __init__(self, precomputed_vectors):
        self.precomputed_vectors = precomputed_vectors  # Stocke les embeddings calculés
    
    def embed_documents(self, texts):
        return self.precomputed_vectors # Retourne les embeddings déjà calculés.
    
    def embed_query(self, text):
        return model.encode([text])[0]  # Génère l'embedding pour une nouvelle requête et retourne un seul vecteur

# Instanciation des embeddings calculés
embedding_function = PrecomputedEmbeddings(precomputed_vectors=embeddings.tolist())

# Création et stockage dans un SKLearnVectorStore
log(f'- Génération de la base vectorielle')
vectorstore = SKLearnVectorStore.from_texts(
    texts=texts,
    persist_path=PERSIST_PATH,
    embedding=embedding_function,
    metadatas=[doc.metadata for doc in doc_splits],
    serializer="parquet",
)

# Sauvegarde du VectorStore
vectorstore.persist()
log("✅ Base vectorielle créée et sauvegardée.") 