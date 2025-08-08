# pip install langchain chromadb transformers

from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
import os

# 1. Chargement des fichiers
documents = []
dossier = "./compte_rendus"
for fichier in os.listdir(dossier):
    if fichier.endswith(".txt"):
        loader = TextLoader(os.path.join(dossier, fichier), encoding="utf-8")
        documents.extend(loader.load())

# 2. Découpage des documents en chunks (si longs)
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs_chunked = splitter.split_documents(documents)

# 3. Embedding + vectorisation locale
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(docs_chunked, embedding_model, persist_directory="db_meetings")

from langchain.chains import RetrievalQA
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# Charger SmolLM3 localement
model_id = "aixplain/SmolLM-3B-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", torch_dtype="auto")
llm_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer)

# Créer la chaîne RAG
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
rag_chain = RetrievalQA.from_chain_type(
    llm=llm_pipeline,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)

question = "Quelles décisions ont été prises en juillet ?"
result = rag_chain({"query": question})

print("📄 Réponse générée :")
print(result["result"])

# (Optionnel) Voir les documents sources :
for doc in result["source_documents"]:
    print(f"🔹 Source: {doc.metadata.get('source')}")