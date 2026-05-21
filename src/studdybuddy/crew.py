from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

@CrewBase
class Studdybuddy():
    """Studdybuddy crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def learning_guide(self) -> Agent:
        return Agent(
            config=self.agents_config['learning_guide'], # type: ignore[index]
            verbose=True
        )

    @agent
    def problem_decoder(self) -> Agent:
        return Agent(
            config=self.agents_config['problem_decoder'], # type: ignore[index]
            verbose=True
        )

    @agent
    def cognitive_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['cognitive_analyst'], # type: ignore[index]
            verbose=True
        )

    @agent
    def assessment_examiner(self) -> Agent:
        return Agent(
            config=self.agents_config['assessment_examiner'], # type: ignore[index]
            verbose=True
        )

    @task
    def learning_guidance(self) -> Task:
        return Task(
            config=self.tasks_config['learning_guidance'], # type: ignore[index]
        )

    @task
    def problem_decoding(self) -> Task:
        return Task(
            config=self.tasks_config['problem_decoding'], # type: ignore[index]
        )

    @task
    def cognitive_analysis(self) -> Task:
        return Task(
            config=self.tasks_config['cognitive_analysis'], # type: ignore[index]
        )

    @task
    def adaptive_assessment(self) -> Task:
        return Task(
            config=self.tasks_config['adaptive_assessment'], # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Studdybuddy crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
