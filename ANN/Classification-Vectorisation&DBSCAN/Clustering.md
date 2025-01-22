
# Analyse des logs avec clustering non supervisé

## Introduction

Cette conversation explique comment mettre en évidence des comportements anormaux et regrouper les types d'erreurs dans un fichier de logs en utilisant une méthode non supervisée. Nous avons utilisé le clustering avec DBSCAN pour détecter et analyser ces erreurs.

---

## Étapes pour analyser les logs

### 1. Chargement et prétraitement des logs

- Lire les logs depuis un fichier.
- Nettoyer les données pour éliminer les éléments inutiles (timestamps, ID spécifiques, etc.).
- Normaliser les messages pour réduire les variations (par exemple, remplacer des valeurs dynamiques comme des adresses IP par un token).

```python
logs = pd.read_csv("logs.txt", header=None, names=["message"])
logs["cleaned_message"] = logs["message"].str.replace(r"\d+", "<NUM>")  # Remplace les chiffres par un token générique
logs["cleaned_message"] = logs["cleaned_message"].str.lower()  # Convertir en minuscules
```

### 2. Vectorisation des messages

Transformer les messages de logs en vecteurs numériques en utilisant des techniques comme :
- **TF-IDF** : Pondération en fonction de la fréquence des termes.
- **Embeddings** : Word2Vec, GloVe ou Sentence-BERT.

```python
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
X = vectorizer.fit_transform(logs["cleaned_message"])
```

### 3. Clustering avec DBSCAN

#### Détermination des paramètres `eps` et `min_samples`

- Utiliser la distance des k plus proches voisins pour estimer `eps`.
- Choisir `min_samples` en fonction des dimensions des données ou d'une règle empirique.

```python
from sklearn.neighbors import NearestNeighbors
import matplotlib.pyplot as plt

k = 5  # Nombre de voisins à considérer
neighbors = NearestNeighbors(n_neighbors=k, metric="cosine").fit(X)
distances, indices = neighbors.kneighbors(X)

distances = np.sort(distances[:, k-1], axis=0)

# Tracer les distances
plt.figure(figsize=(8, 5))
plt.plot(distances)
plt.title("Distance aux k plus proches voisins (k=5)")
plt.xlabel("Points ordonnés")
plt.ylabel("Distance au 5ème voisin")
plt.show()
```

#### Automatisation de la recherche du coude

```python
from kneed import KneeLocator

knee = KneeLocator(range(len(distances)), distances, curve="convex", direction="increasing")
eps_optimal = distances[knee.knee]

print(f"Valeur optimale pour eps : {eps_optimal}")
```

#### Appliquer DBSCAN

```python
from sklearn.cluster import DBSCAN

dbscan = DBSCAN(eps=eps_optimal, min_samples=k, metric="cosine").fit(X)
logs["cluster"] = dbscan.labels_

# Analyse des clusters
for cluster_id in logs["cluster"].unique():
    print(f"\nCluster {cluster_id}")
    print(logs[logs["cluster"] == cluster_id]["message"].head(10))
```

---

## Résumé

1. **Estimer `eps`** : Utilisez les distances des k plus proches voisins pour déterminer une valeur optimale.
2. **Définir `min_samples`** : Choisissez une valeur basée sur les dimensions des données ou les caractéristiques des clusters attendus.
3. **Clustering avec DBSCAN** : Appliquez l'algorithme pour regrouper les logs et détecter les anomalies.

---

## Suggestions

- Intégrer des modèles avancés comme Sentence-BERT pour une vectorisation plus précise.
- Utiliser des techniques de réduction de dimensionnalité (PCA, t-SNE) pour visualiser les résultats.

---
