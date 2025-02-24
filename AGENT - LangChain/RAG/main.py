from langchain_community.document_loaders import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import SKLearnVectorStore
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings

from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

'''
   Cette application est un RAG utilisant Mistral (Ollama), LangChain et SickitLearn en local pour traiter des documents CSV et PDF,
   générer les embeddings et intégrer un retriever pour la recherche de réponse.

   Auteur : Cyril Bouvart

   Sources : https://www.datacamp.com/tutorial/llama-3-1-rag

   Prérequis :
       pip install ollama langchain langchain_community langchain-openai scikit-learn langchain-ollama
'''

# Chargement des documents
loader = CSVLoader(file_path='./Sources/Doctolib.csv',
    csv_args={
    'delimiter': ';',
    'quotechar': '"',
    'fieldnames': ['Interface', 'Description', 'Solution']

})

docs = loader.load()

# Découpage des documents en truncks
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=100, chunk_overlap=50
)
doc_splits = text_splitter.split_documents(docs)

# Chargement du modèle pré-entrainé Sentence Transformer
model = SentenceTransformer("all-MiniLM-L6-v2")

# Calcul des embeddings
embeddings = model.encode([doc.page_content for doc in doc_splits])
# print(embeddings.shape)
# [11, 384]

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
vectorstore = SKLearnVectorStore.from_texts(
    texts=texts,
    embedding=embedding_function,  # On passe notre classe custom
    metadatas=[doc.metadata for doc in doc_splits]
)

# Sauvegarde locale
# vectorstore.save_local("sklearn_vectorstore") #Pas implémenté avec skLearnVectorStore!

# Test : Rechercher un document pertinent et afficher le résultat
# query = "J'ai l'erreur Exception dans le traitement lors de la réception d'un RDV Doctolib vers HM, que faire?"  # Exemple de requête
# docs_found = vectorstore.similarity_search(query, k=1)
# for doc in docs_found:
#     print(doc.page_content)

# Créer un retriver
retriever = vectorstore.as_retriever(search_kwargs={"k": 1}) # On s'assure que la recherche ne retourne qu'un seul document

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
print(' ----- TEST ----- ')
question = "J'ai l'erreur Exception dans le traitement lors de la réception d'un RDV Doctolib, que faire?"
answer = rag_application.run(question)
print("Question:", question)
print("Answer:", answer)