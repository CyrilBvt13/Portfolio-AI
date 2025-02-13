import sys
import yaml
from api_dev_team.crew import DevCrew


def run():
    # Replace with your inputs, it will automatically interpolate any tasks and agents information
    print("## Welcome to the Dev Crew")
    print('-------------------------------')

    with open('src/api_dev_team/config/appdesign.yaml', 'r', encoding='utf-8') as file:
        examples = yaml.safe_load(file)

    inputs = {
        'app' :  examples['app']
    }
    app= DevCrew().crew().kickoff(inputs=inputs)

    print('-------------------------------')
    print("## End of task")

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
        DevCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")