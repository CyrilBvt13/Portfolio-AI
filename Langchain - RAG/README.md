# Simple RAG

Cette application est un RAG (Retrieval Augmented Generation) utilisant un version locale de Mistral 4b (Ollama), LangChain et SickitLearn en local pour traiter des documents CSV, DOCX et PDF,
générer les embeddings et intégrer un retriever pour la recherche de réponse dans une base documentaire locale.

Les documents pris en charge peuvent être des CSV, des DOCX et des PDF.

Cette application fonctionne sur le principe d'un serveur et de clients :
- Le serveur est une API Flask gérant l'execution du RAG
- Le client permet d'interroger l'API en transmettant la question de l'utilisateur puis en affichant la réponse renvoyée par l'API.

Pour une expérience utilisateur (UX) fluide, l'API fonctionne sur le principe du polling : une fois une question reçue nous avertissons l'utilisateur que
la question est en cours de traitement. Le client interroge ensuite l'API jusqu'à ce que la réponse soit disponible.

## **Table des Matières**

1. [Contribution](#contribution)
2. [Dépendances](#dépendances)
3. [Fonctionnement](#fonctionnement)
4. [Sources](#sources)

## Contribution
- **Auteur Principal** : Cyril Bouvart

## Dépendances

Pour fonctionner ce programme a besoin des librairies suivantes :
- langchain_community 
- sentence_transformers 
- langchain-ollama pymupdf 
- docx2txt tiktoken 
- pandas 
- pyarrow 
- flask 
- flask-socketio

Le dossier contient un fichier requirements.txt permettant d'installer les dépendances grâce aux commandes suivantes :

```bash
python -m venv simplerag

.\simplerag\Scripts\activate

pip install -r requirements.txt
```

## Fonctionnement
### Prérequis

Déposez vos documents dans :
- \Sources
	- \CSV : documents au format CSV
	- \PDF : document au format PDF
	- \DOCX : document au format DOCX (Word)

Pour générer le vector store contenant les embeddings des documents :
```bash
python .\generateStore.py
```

### Execution de l'application

Pour lancer le serveur Flask :
```bash
python .\app.py
```

## Sources

- https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag_local/#create-index
- https://www.datacamp.com/tutorial/how-to-improve-rag-performance-5-key-techniques-with-examples


