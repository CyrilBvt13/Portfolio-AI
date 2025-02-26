from langchain_community.document_loaders import CSVLoader, PyMuPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import SKLearnVectorStore
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings

from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

import os

'''
   Cette application est un RAG utilisant Mistral (Ollama), LangChain et SickitLearn en local pour traiter des documents CSV et PDF,
   générer les embeddings et intégrer un retriever pour la recherche de réponse.

   Auteur : Cyril Bouvart

   Sources : https://www.datacamp.com/tutorial/llama-3-1-rag

   Prérequis :
       pip install langchain_community sentence_transformers langchain-ollama pymupdf docx2txt tiktoken pandas pyarrow
'''

# Chemin de sauvegarde du VectorStore
PERSIST_PATH = os.path.join('./Store/', "vectorstore.pqt")

# Chargement des documents CSV
csv_loader = CSVLoader(file_path='./Sources/CSV/DICOM.csv',
    csv_args={
    'delimiter': ';',
    'quotechar': '"',
    'fieldnames': ['Interface', 'Description', 'Solution']

})

csv_docs = csv_loader.load()

# Chargement des documents PDF
pdf_docs = []
pdf_folder = "./Sources/PDF/"  # Dossier contenant les PDF

for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(pdf_folder, filename)
        loader = PyMuPDFLoader(pdf_path)
        pdf_docs.extend(loader.load())

# Chargement des documents Word
docx_docs = []
docx_folder = "./Sources/DOCX/"

for filename in os.listdir(docx_folder):
    if filename.endswith(".docx"):
        docx_path = os.path.join(docx_folder, filename)
        loader = Docx2txtLoader(docx_path)
        docx_docs.extend(loader.load())

# Fusion de tous les documents (CSV + PDF + DOCX)
docs = csv_docs + pdf_docs + docx_docs

# Découpage des documents en truncks
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=256, chunk_overlap=24
)
doc_splits = text_splitter.split_documents(docs)

# Extraction du texte des documents pour stockage
texts = [doc.page_content for doc in doc_splits]

# Généreation des embeddings avec SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(texts)

# print(embeddings.shape)
# [11, 384]

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
vectorstore = SKLearnVectorStore.from_texts(
    texts=texts,
    persist_path=PERSIST_PATH,
    embedding=embedding_function,  # On passe notre classe custom
    metadatas=[doc.metadata for doc in doc_splits],
    serializer="parquet",
)

vectorstore.persist() # Sauvegarde du VectorStore

# Chargement du VectorStore
# vectorstore = SKLearnVectorStore(
#     persist_path=PERSIST_PATH,
#     embedding=embedding_function,
#     serializer="parquet",
# )
# docs = vectorstore.similarity_search(query)

# Test : Rechercher un document pertinent et afficher le résultat
# query = "Mon fichier dicom ne s'ouvre pas dans ITO-DicomTools, que faire?"  # Exemple de requête
# docs_found = vectorstore.similarity_search(query, k=3)
# for doc in docs_found:
#     print(doc.page_content)

# Créer un retriver
#retriever = vectorstore.as_retriever(search_kwargs={"k": 1}) # On s'assure que la recherche ne retourne qu'un seul document
retriever = vectorstore.as_retriever(k=3)

# Définition du modèle de prompt pour le LLM
prompt = PromptTemplate(
    template="""Tu es un assistant pour des tâches de questions/réponses.
    Utilise les documents suivants pour répondre aux questions.
    Si tu connais pas la réponse, dit juste que tu ne sais pas.
    Utilise trois phrases maximum et garde la réponse concice.
    Tu devras obligatoirement répondre en français:
    Question: {question}
    Documents: {documents}
    Réponse:
    """,
    input_variables=["question", "documents"],
)

# Initialisation d'Ollama avec le modèle mistral:latest
llm = ChatOllama(
    model="mistral:latest",
    temperature=0,
)

# Création d'une chaine combinant le modèle de prompt et le LLM
rag_chain = prompt | llm | StrOutputParser()

# Définition de la classe RAGApplication
class RAGApplication:
    def __init__(self, retriever, rag_chain):
        self.retriever = retriever
        self.rag_chain = rag_chain
    def run(self, question):
        # Recherche des documents pertinents
        documents = self.retriever.invoke(question)
        # Extraction du contenu des documents pertinents
        doc_texts = "\\n".join([doc.page_content for doc in documents])
        # Récupération de la réponse du LLM
        answer = self.rag_chain.invoke({"question": question, "documents": doc_texts})
        return answer

# Initialisation du RAG
rag_application = RAGApplication(retriever, rag_chain)

# Exemple

question = "Mon fichier dicom ne s'ouvre pas dans ITO-DicomTools, que faire?"
docs_found = vectorstore.similarity_search(question, k=3)
answer = rag_application.run(question)

print(' ----- QUESTION ----- ')
print("Question:", question)
#print(' ----- RECHERCHE ----- ')
#for doc in docs_found:
#     print(doc.page_content)
print(' ----- REPONSE ----- ')
print("Answer:", answer)