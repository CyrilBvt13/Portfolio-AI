import os, hashlib
import numpy as np
from sentence_transformers import SentenceTransformer
from utils import load_any, recursive_split
from retriever import FaissStore
import faiss

# === Configuration ===
# Dossiers par d�faut (peuvent �tre red�finis via variables d'environnement)
DATA_DIR = os.getenv('DATA_DIR', './data/source')
INDEX_DIR = os.getenv('INDEX_DIR', './index')

# Param�tres de segmentation des textes
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1200))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 200))

# Mod�le d'embeddings (Sentence Transformers)
EMB_ID = os.getenv('EMB_MODEL', 'intfloat/multilingual-e5-base')

# Cr�ation du dossier index si n�cessaire
os.makedirs(INDEX_DIR, exist_ok=True)

# Chargement du mod�le d'embeddings et du store FAISS
emb = SentenceTransformer(EMB_ID)
store = FaissStore(INDEX_DIR)

# Listes pour stocker les m�tadonn�es et les vecteurs
meta = []
vecs = []

# === Parcours des fichiers dans DATA_DIR ===
for root, _, files in os.walk(DATA_DIR):
    for f in files:
        # On ne traite que PDF, CSV, DOCX
        if not f.lower().endswith((".pdf", ".csv", ".docx")):
            continue
        path = os.path.join(root, f)
        print("Parsing:", path)
        try:
            text = load_any(path) # Extraction du texte selon le type de fichier
        except Exception as e:
            print("Skip", path, e)
            continue
        # D�coupe du texte en chunks avec overlap
        chunks = recursive_split(text, CHUNK_SIZE, CHUNK_OVERLAP)
        passages = [f"passage: {c}" for c in chunks]
        # Encodage des chunks en vecteurs normalis�s
        embs = emb.encode(passages, normalize_embeddings=True, batch_size=32)
        for i, (c, v) in enumerate(zip(chunks, embs)):
            # G�n�ration d'un identifiant unique pour chaque chunk
            cid = hashlib.md5(f"{path}-{i}".encode()).hexdigest()[:10]
            record = {
                "id": len(meta), # Identifiant num�rique interne
                "cid": cid, # Identifiant unique court (hash)
                "source": os.path.relpath(path, DATA_DIR),
                "chunk_index": i, # Position du chunk dans le document
                "text": c, # Contenu textuel du chunk
                "embedding": v.tolist(), # Vecteur d'embedding associ�
            }
            meta.append(record)
            vecs.append(v.astype('float32'))

# === Construction et normalisation de l'index FAISS ===
vecs = np.vstack(vecs)
faiss.normalize_L2(vecs)
index = faiss.IndexFlatIP(vecs.shape[1])
index.add(vecs)

# Sauvegarde de l'index et des m�tadonn�es
store.save(index, meta)
print("Index construit:", len(meta), "chunks")