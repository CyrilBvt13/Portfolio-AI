# PythonDevelopmentTeam Crew

Bienvenue dans le projet PytonDevelopmentTeam, basé sur [crewAI](https://crewai.com). Il met en avant la capacité de programmation d'une équipe multi-agent basé sur le LLM qwen2.5:7b.

## Installation

Une version Python >=3.10 <3.13 est requise pour le fonctionnement de ce projet. Il utilise également [UV](https://docs.astral.sh/uv/)  pour la gestion des dépendances.

Pour installer UV :

```bash
pip install uv
```

Pour installer les dépendances :

```bash
crewai install
```

Ce projet appelle également le LLM qwen2.5:7b en local grâce à Ollama. Pour l'installer/le lancer : 

```bash
ollama run qwen2.5:7b 
```

### Paramètres

- Modifiez `src/api_dev_team/config/agents.yaml` pour définir les agents
- Modifiez `src/api_dev_team/config/tasks.yaml` pour définir les tâches
- Modifiez `src/api_dev_team/crew.py` pour ajouter votre propre logique, outils et arguments
- Modifiez `src/api_dev_team/main.py` pour ajouter des entrées personnalisées pour vos agents et tâches

## Lancement du projet

Pour lancer l'équipe d'agents et démarrer l'execution de la tache, tapez cette commande à la racine du projet :

```bash
$ crewai run
```

Cette commande permet d'initier l'équipe de PythonDevelopmentTeam, assemblant les agents et leurs attribuant leurs tâches comme défini dans le paramétrage.

Cet exemple permet la création d'un fichier `app.py` contenant le code d'une API Flask pour la gestion d'utilisateurs.
