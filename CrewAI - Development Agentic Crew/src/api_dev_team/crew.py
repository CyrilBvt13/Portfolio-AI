from typing import List
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    FileWriterTool
)

file_tool = FileWriterTool()

@CrewBase
class DevCrew:
    """Dev Crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    file_tool = FileWriterTool()

    @agent
    def senior_engineer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['senior_engineer_agent'],
            allow_delegation=False,
            verbose=True
        )
    
    @agent
    def qa_engineer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['qa_engineer_agent'],
            allow_delegation=True,
            verbose=True
        )

    @agent
    def tester_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['tester_agent'],
            allow_code_execution= True,
            allow_delegation=True,
            verbose=True
        )

    @agent
    def writer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['writer_agent'],
            allow_delegation=False,
            tools=[file_tool],
            verbose=True
        )

    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_task'],
            agent=self.senior_engineer_agent()
        )

    @task
    def review_task(self) -> Task:
        return Task(
            config=self.tasks_config['review_task'],
            agent=self.qa_engineer_agent(),
        )
    
    @task
    def compile_task(self) -> Task:
        return Task(
            config=self.tasks_config['compile_task'],
            agent=self.tester_agent(),
        )
    
    @task
    def write_task(self) -> Task:
        return Task(
            config=self.tasks_config['write_task'],
            agent=self.writer_agent(),
            output_file='output/app.py'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the DevCrew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True, 
        )