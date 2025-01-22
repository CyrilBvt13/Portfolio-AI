import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA, TruncatedSVD
import matplotlib.pyplot as plt
import numpy as np
from kneed import KneeLocator
from matplotlib.backends.backend_pdf import PdfPages
import argparse
import os

'''
Utilisation :
- Extraire les logs avec IPP, NDA et Commentaires
- Appeler le script : python main.py -file NomDuFichier.csv
'''

# Parse arguments
parser = argparse.ArgumentParser(description="Process and cluster logs from a CSV file.")
parser.add_argument("-file", type=str, required=True, help="Path to the input CSV file.")
args = parser.parse_args()

# Check if file exists
if not os.path.exists(args.file):
    print(f"Error: The file '{args.file}' does not exist.")
    exit(1)

# Load and clean the file
with open(args.file, "r", encoding="utf-8") as infile:
    lines = infile.readlines()

# Preprocess the lines
cleaned_lines = []
buffer = ""
pattern_to_remove = "Erreur : Message rejeté, aucune salle paramétrée pour l'UF"

for line in lines:
    stripped_line = line.strip()
    if stripped_line.startswith(pattern_to_remove):
        continue
    if buffer:
        buffer += " " + stripped_line
        if not stripped_line:
            continue
        else:
            cleaned_lines.append(buffer)
            buffer = ""
    elif "Rejeté" in stripped_line:
        buffer = stripped_line
    else:
        cleaned_lines.append(stripped_line)

if buffer:
    cleaned_lines.append(buffer)

# Create a DataFrame directly from the cleaned lines
logs = pd.DataFrame([line.split(";") for line in cleaned_lines], columns=["IPP", "NDA", "Commentaire"])

'''
On remplace les valeurs numériques par un token <NUM> puis on remplace toutes les majuscules par des minuscules.
'''

# Nettoyer les messages
logs["cleaned_message"] = logs["Commentaire"].str.replace(r"\d+", "<NUM>", regex=True)
logs["cleaned_message"] = logs["cleaned_message"].str.lower()

'''
On vectorise ensuite les messages pour pouvoir les traiter par la suite.
'''

# Étape 2 : Vectorisation
vectorizer = TfidfVectorizer(max_features=500, stop_words="english")
vectorized_logs = vectorizer.fit_transform(logs["cleaned_message"])

# Réduction de dimensions
svd = TruncatedSVD(n_components=20)
reduced_logs = svd.fit_transform(vectorized_logs)
#reduced_logs = vectorized_logs

'''
Pour la clusterisation on va chercher automatiquement les hyperparamètres. 

Nous choisissons d'utiliser la méthode DBSCAN car les clusters ne seront pas forcement centriques.
'''

# Étape 3 : Calcul des distances des k plus proches voisins
k = 5
nearest_neighbors = NearestNeighbors(n_neighbors=k)
nearest_neighbors.fit(reduced_logs)
distances, indices = nearest_neighbors.kneighbors(reduced_logs)
distances = np.sort(distances[:, k - 1], axis=0)

# Étape 4 : Trouver le coude et tracer les distances
knee = KneeLocator(range(len(distances)), distances, curve="convex", direction="increasing")
eps_optimal = distances[knee.knee]
#print(f"Valeur optimale pour eps : {eps_optimal}")

# Étape 5 : Clustering
dbscan = DBSCAN(eps=eps_optimal, min_samples=5)
clusters = dbscan.fit_predict(reduced_logs)
logs["cluster"] = clusters

'''
Nous remarquons que dans le cluster 0 nous avons 2 sous-groupes qui se distinguent (cf rapport PDF).

1er sous-groupe : Y > 0
2ème sous-groupe : Y < 0

On va donc les séparer par la méthode des K-moyens.
'''

# Étape 5.1 : Filtrer les données du cluster 0
cluster_0_data = logs[logs["cluster"] == 0]  # Filtrer uniquement le cluster 0
pca_coordinates = reduced_logs[logs["cluster"] == 0]  # Coordonnées PCA pour cluster 0

# Étape 5.2 : Appliquer un clustering sur les données du cluster 0
kmeans = KMeans(n_clusters=2, random_state=42)  # Fixer à 2 sous-clusters
sub_clusters = kmeans.fit_predict(pca_coordinates)

# Étape 5.3 : Ajouter les sous-clusters au DataFrame principal
logs.loc[logs["cluster"] == 0, "sub_cluster"] = sub_clusters

'''
On stocke dans un PDF les graphiques suivants :
- Recherche des hyperparamètres pour la clusterisation DBSCAN (recherche du coude des k-plus proches voisins)
- Visualisation des clusters
'''

# Étape 6 : Visualisation et rapport PDF
pca = PCA(n_components=2)
reduced_data = pca.fit_transform(reduced_logs)

with PdfPages("rapport.pdf") as pdf:
    # Graphique 1 : Distance aux k plus proches voisins
    plt.figure(figsize=(8, 5))
    plt.plot(distances)
    plt.axvline(x=knee.knee, color='r', linestyle='--', label=f"Coude: {knee.knee}")
    plt.title("Distance aux k plus proches voisins (k=5)")
    plt.xlabel("Points ordonnés")
    plt.ylabel("Distance au 5ème voisin")
    plt.legend()
    pdf.savefig()
    plt.close()

    # Graphique 2 : Visualisation des clusters
    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(reduced_data[:, 0], reduced_data[:, 1], c=logs["cluster"], cmap="viridis", s=10)
    plt.colorbar(scatter, label="Cluster")
    plt.title("Visualisation des clusters de logs")
    pdf.savefig()
    plt.close()

'''
On sauvegarde les logs traités dans un nouveau fichier csv.
'''

# Étape 7 : Sauvegarde des résultats
# Trier les résultats par cluster et sous-cluster
logs["sub_cluster"] = logs["sub_cluster"].fillna(-1).astype(int)  # Remplir les NaN par -1 pour les clusters sans sous-cluster
logs = logs.sort_values(by=["cluster", "sub_cluster", "cleaned_message"], ascending=True)

# Sauvegarder les résultats triés dans le fichier CSV
output_file = "logs_sorted.csv"
logs.to_csv(output_file, sep=";", index=False, encoding="utf-8")