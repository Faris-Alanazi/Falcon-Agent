import os
from typing import Dict, List, Any, Optional, Union
import logging
import uuid

from crewai import Crew, Agent, Task, Process
from crewai.tools import BaseTool

from src.utils.logging_utils import setup_logger
from src.config.config import MODEL_CONFIGS, DEFAULT_MODEL

logger = setup_logger(__name__)

class CrewFactory:
    """
    Creates and manages CrewAI components for the agent system.
    
    This class is responsible for:
    1. Creating CrewAI agents from our agent specifications
    2. Converting our tasks to CrewAI tasks
    3. Creating and managing CrewAI crews
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the CrewFactory.
        
        Args:
            verbose (bool): Whether to enable verbose output from CrewAI
        """
        self.verbose = verbose
        self.crews = {}  # Dictionary mapping crew_id -> Crew object
    
    def create_agent(self, 
                     role: str, 
                     goal: str, 
                     backstory: str, 
                     tools: List[BaseTool] = None, 
                     llm: str = DEFAULT_MODEL,
                     **kwargs) -> Agent:
        """
        Create a CrewAI agent.
        
        Args:
            role (str): The agent's role
            goal (str): The agent's goal
            backstory (str): The agent's backstory
            tools (List[BaseTool], optional): Tools for the agent
            llm (str): LLM to use for this agent
            **kwargs: Additional arguments to pass to the Agent constructor
            
        Returns:
            Agent: The created CrewAI agent
        """
        # Get the model config for this LLM
        model_config = MODEL_CONFIGS.get(llm, {})
        
        # Create the agent
        agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools or [],
            llm=llm,
            verbose=self.verbose,
            **{**model_config, **kwargs}  # Merge model config with additional kwargs
        )
        
        return agent
    
    def create_task(self, 
                    description: str, 
                    agent: Agent, 
                    expected_output: str = None,
                    tools: List[BaseTool] = None,
                    context: List[Union[Task, str]] = None,
                    async_execution: bool = False,
                    **kwargs) -> Task:
        """
        Create a CrewAI task.
        
        Args:
            description (str): The task description
            agent (Agent): The agent assigned to this task
            expected_output (str, optional): Description of expected output
            tools (List[BaseTool], optional): Tools for this task
            context (List[Union[Task, str]], optional): Context for this task
            async_execution (bool): Whether to execute this task asynchronously
            **kwargs: Additional arguments to pass to the Task constructor
            
        Returns:
            Task: The created CrewAI task
        """
        # Create the task
        task = Task(
            description=description,
            agent=agent,
            expected_output=expected_output,
            tools=tools,
            context=context,
            async_execution=async_execution,
            **kwargs
        )
        
        return task
    
    def create_crew(self, 
                    agents: List[Agent], 
                    tasks: List[Task] = None, 
                    process: Process = Process.SEQUENTIAL,
                    crew_id: str = None,
                    verbose: bool = None,
                    **kwargs) -> Crew:
        """
        Create a CrewAI crew.
        
        Args:
            agents (List[Agent]): Agents in the crew
            tasks (List[Task], optional): Tasks for the crew
            process (Process): Execution process (Sequential or Hierarchical)
            crew_id (str, optional): ID for this crew
            verbose (bool, optional): Whether to enable verbose output
            **kwargs: Additional arguments to pass to the Crew constructor
            
        Returns:
            Crew: The created CrewAI crew
        """
        # Generate a crew ID if not provided
        if crew_id is None:
            crew_id = str(uuid.uuid4())
        
        # Use instance verbose setting if not specified
        if verbose is None:
            verbose = self.verbose
        
        # Create the crew
        crew = Crew(
            agents=agents,
            tasks=tasks or [],
            process=process,
            verbose=verbose,
            **kwargs
        )
        
        # Store the crew
        self.crews[crew_id] = crew
        
        return crew
    
    def get_crew(self, crew_id: str) -> Optional[Crew]:
        """
        Get a crew by ID.
        
        Args:
            crew_id (str): The crew ID
            
        Returns:
            Optional[Crew]: The crew or None if not found
        """
        return self.crews.get(crew_id)
    
    def run_crew(self, crew_or_id: Union[Crew, str]) -> Any:
        """
        Run a crew and return the result.
        
        Args:
            crew_or_id (Union[Crew, str]): The crew or crew ID to run
            
        Returns:
            Any: The result of the crew execution
        """
        # Get the crew if an ID was provided
        crew = crew_or_id
        if isinstance(crew_or_id, str):
            crew = self.get_crew(crew_or_id)
            if crew is None:
                raise ValueError(f"No crew found with ID {crew_or_id}")
        
        # Run the crew
        logger.info(f"Running crew with {len(crew.agents)} agents and {len(crew.tasks)} tasks")
        result = crew.kickoff()
        
        return result
    
    def create_agent_crew(self, 
                          agent_specs: List[Dict[str, Any]], 
                          tasks_specs: List[Dict[str, Any]],
                          process: Process = Process.SEQUENTIAL,
                          crew_id: str = None,
                          **kwargs) -> Crew:
        """
        Create a crew from agent and task specifications.
        
        Args:
            agent_specs (List[Dict[str, Any]]): Specifications for the agents
            tasks_specs (List[Dict[str, Any]]): Specifications for the tasks
            process (Process): Execution process (Sequential or Hierarchical)
            crew_id (str, optional): ID for this crew
            **kwargs: Additional arguments to pass to the Crew constructor
            
        Returns:
            Crew: The created CrewAI crew
        """
        # Create the agents
        agents = []
        agent_map = {}  # Map agent IDs to Agent objects
        
        for spec in agent_specs:
            agent_id = spec.pop("id", str(uuid.uuid4()))
            agent = self.create_agent(**spec)
            agents.append(agent)
            agent_map[agent_id] = agent
        
        # Create the tasks
        tasks = []
        
        for spec in tasks_specs:
            # Get the agent for this task
            agent_id = spec.pop("agent_id", None)
            if agent_id is None:
                raise ValueError("task_specs must contain 'agent_id'")
            
            agent = agent_map.get(agent_id)
            if agent is None:
                raise ValueError(f"No agent found with ID {agent_id}")
            
            # Create the task
            task = self.create_task(agent=agent, **spec)
            tasks.append(task)
        
        # Create and return the crew
        return self.create_crew(
            agents=agents,
            tasks=tasks,
            process=process,
            crew_id=crew_id,
            **kwargs
        )
    
    def create_sequential_crew(self, 
                              initial_agent_spec: Dict[str, Any], 
                              initial_task_spec: Dict[str, Any],
                              crew_id: str = None,
                              **kwargs) -> Crew:
        """
        Create a crew with a single agent and task for sequential processing.
        
        Args:
            initial_agent_spec (Dict[str, Any]): Specification for the agent
            initial_task_spec (Dict[str, Any]): Specification for the task
            crew_id (str, optional): ID for this crew
            **kwargs: Additional arguments to pass to the Crew constructor
            
        Returns:
            Crew: The created CrewAI crew
        """
        # Create the agent
        agent = self.create_agent(**initial_agent_spec)
        
        # Create the task
        task = self.create_task(agent=agent, **initial_task_spec)
        
        # Create and return the crew
        return self.create_crew(
            agents=[agent],
            tasks=[task],
            process=Process.SEQUENTIAL,
            crew_id=crew_id,
            **kwargs
        )
    
    def create_hierarchical_crew(self, 
                                manager_spec: Dict[str, Any],
                                worker_specs: List[Dict[str, Any]],
                                manager_task_spec: Dict[str, Any],
                                worker_task_specs: List[Dict[str, Any]],
                                crew_id: str = None,
                                **kwargs) -> Crew:
        """
        Create a hierarchical crew with a manager and workers.
        
        Args:
            manager_spec (Dict[str, Any]): Specification for the manager agent
            worker_specs (List[Dict[str, Any]]): Specifications for the worker agents
            manager_task_spec (Dict[str, Any]): Specification for the manager task
            worker_task_specs (List[Dict[str, Any]]): Specifications for the worker tasks
            crew_id (str, optional): ID for this crew
            **kwargs: Additional arguments to pass to the Crew constructor
            
        Returns:
            Crew: The created CrewAI crew
        """
        # Create the manager agent
        manager = self.create_agent(**manager_spec)
        
        # Create the worker agents
        workers = []
        for spec in worker_specs:
            worker = self.create_agent(**spec)
            workers.append(worker)
        
        # Create the manager task
        manager_task = self.create_task(agent=manager, **manager_task_spec)
        
        # Create the worker tasks
        worker_tasks = []
        for i, spec in enumerate(worker_task_specs):
            # Get the worker for this task (round-robin assignment)
            worker = workers[i % len(workers)]
            
            # Create the task
            task = self.create_task(agent=worker, **spec)
            worker_tasks.append(task)
        
        # Combine all agents and tasks
        agents = [manager] + workers
        tasks = [manager_task] + worker_tasks
        
        # Create and return the crew
        return self.create_crew(
            agents=agents,
            tasks=tasks,
            process=Process.HIERARCHICAL,
            crew_id=crew_id,
            **kwargs
        ) 