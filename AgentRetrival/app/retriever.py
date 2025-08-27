import os, json
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.preprocessing import normalize

class FaissStore:
	def __init__(self, index_dir: str):
		self.index_dir = index_dir
		self.index_path = os.path.join(index_dir, 'faiss.index')
		self.meta_path = os.path.join(index_dir, 'meta.json')
		self.index = None
		self.meta = []


	def load(self):
		self.index = faiss.read_index(self.index_path)
		with open(self.meta_path, 'r', encoding='utf-8') as f:
			self.meta = json.load(f)


	def save(self, index, meta):
		os.makedirs(self.index_dir, exist_ok=True)
		faiss.write_index(index, self.index_path)
		with open(self.meta_path, 'w', encoding='utf-8') as f:
			json.dump(meta, f, ensure_ascii=False)


class Retriever:
	def __init__(self):
		self.emb_model_id = os.getenv('EMB_MODEL', 'intfloat/multilingual-e5-base')
		self.model = SentenceTransformer(self.emb_model_id)
		self.store = FaissStore(os.getenv('INDEX_DIR', './index'))
		self.store.load()


	def _embed(self, texts: List[str]) -> np.ndarray:
		# E5: ajouter le préfixe "query:" / "passage:" pour de meilleurs résultats
		prepped = [f"query: {t}" for t in texts]
		vecs = self.model.encode(prepped, normalize_embeddings=True, batch_size=32)
		return vecs.astype('float32')


	def search(self, query: str, k: int = 8, mmr_lambda: float = 0.4) -> List[Dict]:
		q = self._embed([query])
		D, I = self.store.index.search(q, k*3)
		cands = [self.store.meta[i] | {"score": float(1 - D[0][j])} for j, i in enumerate(I[0])]
		# MMR diversification simple
		selected, selected_vecs = [], []
		seen = set()
		for c in cands:
			if c['id'] in seen: continue
			seen.add(c['id'])
			if not selected:
				selected.append(c)
				selected_vecs.append(c['embedding'])
			else:
				sim_to_selected = [np.dot(c['embedding'], sv) for sv in selected_vecs]
				diversity = 1 - (max(sim_to_selected) if sim_to_selected else 0)
				mmr_score = mmr_lambda * c['score'] + (1 - mmr_lambda) * diversity
				c['mmr'] = mmr_score
				selected.append(c)
				selected_vecs.append(c['embedding'])
				if len(selected) >= k:
					break
		return selected