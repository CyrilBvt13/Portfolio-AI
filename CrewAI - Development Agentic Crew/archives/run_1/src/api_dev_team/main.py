import sys
import yaml
from api_dev_team.crew import GameBuilderCrew


def run():
    # Replace with your inputs, it will automatically interpolate any tasks and agents information
    print("## Welcome to the Dev Crew")
    print('-------------------------------')

    with open('src/api_dev_team/config/appdesign.yaml', 'r', encoding='utf-8') as file:
        examples = yaml.safe_load(file)

    inputs = {
        'app' :  examples['app']
    }
    app= GameBuilderCrew().crew().kickoff(inputs=inputs)

    # Nom du fichier où le texte sera écrit
    fichier_nom = 'app.py'

    # Ouvrir le fichier en mode écriture ('w')
    with open(fichier_nom, 'w') as fichier:
        # Écrire la chaîne de caractères dans le fichier
        fichier.write(str(app))

    print(f"Le résultat a été sauvegardé dans {fichier_nom}")   

def train():
    """
    Train the crew for a given number of iterations.
    """

    with open('src/api_dev_team/config/appdesign.yaml', 'r', encoding='utf-8') as file:
        examples = yaml.safe_load(file)

    inputs = {
        'app' : examples['app']
    }
    try:
        GameBuilderCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")