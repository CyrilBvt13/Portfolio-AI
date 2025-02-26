# Simple RAG

Cette application est un RAG (Retrieval Augmented Generation) utilisant Mistral (Ollama), LangChain et SickitLearn en local pour traiter des documents CSV, DOCX et PDF,
générer les embeddings et intégrer un retriever pour la recherche de réponse.

## **Table des Matières**

1. [Contribution](#contribution)
7. [Dépendances](#dépendances)
8. [Fonctionnement](#cfonctionnement)


## Contribution
- **Auteur Principal** : Cyril Bouvart


## Dépendances

Un fichier requirements.txt contient toutes les dépendances Python nécessaires à l'execution de ce programme.

## Fonctionnement

### Prérequis
```bash
python -m venv simplerag

.\simplerag\Scripts\activate

pip install -r requirements.txt
```

Déposez vos documents dans :
- Sources
	- CSV
	- PDF
	- DOCX

Puis éxecutez :
```bash
python .\simpleRAG.py
```


