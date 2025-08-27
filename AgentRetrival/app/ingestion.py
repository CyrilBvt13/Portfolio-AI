import os, hashlib
import numpy as np
from sentence_transformers import SentenceTransformer
from utils import load_any, recursive_split
from retriever import FaissStore
import faiss

# === Configuration ===
# Dossiers par défaut (peuvent être redéfinis via variables d'environnement)
DATA_DIR = os.getenv('DATA_DIR', './data/source')
INDEX_DIR = os.getenv('INDEX_DIR', './index')

# Paramètres de segmentation des textes
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1200))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 200))

# Modèle d'embeddings (Sentence Transformers)
EMB_ID = os.getenv('EMB_MODEL', 'intfloat/multilingual-e5-base')

# Création du dossier index si nécessaire
os.makedirs(INDEX_DIR, exist_ok=True)

# Chargement du modèle d'embeddings et du store FAISS
emb = SentenceTransformer(EMB_ID)
store = FaissStore(INDEX_DIR)

# Listes pour stocker les métadonnées et les vecteurs
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
        # Découpe du texte en chunks avec overlap
        chunks = recursive_split(text, CHUNK_SIZE, CHUNK_OVERLAP)
        passages = [f"passage: {c}" for c in chunks]
        # Encodage des chunks en vecteurs normalisés
        embs = emb.encode(passages, normalize_embeddings=True, batch_size=32)
        for i, (c, v) in enumerate(zip(chunks, embs)):
            # Génération d'un identifiant unique pour chaque chunk
            cid = hashlib.md5(f"{path}-{i}".encode()).hexdigest()[:10]
            record = {
                "id": len(meta), # Identifiant numérique interne
                "cid": cid, # Identifiant unique court (hash)
                "source": os.path.relpath(path, DATA_DIR),
                "chunk_index": i, # Position du chunk dans le document
                "text": c, # Contenu textuel du chunk
                "embedding": v.tolist(), # Vecteur d'embedding associé
            }
            meta.append(record)
            vecs.append(v.astype('float32'))

# === Construction et normalisation de l'index FAISS ===
vecs = np.vstack(vecs)
faiss.normalize_L2(vecs)
index = faiss.IndexFlatIP(vecs.shape[1])
index.add(vecs)

# Sauvegarde de l'index et des métadonnées
store.save(index, meta)
print("Index construit:", len(meta), "chunks")