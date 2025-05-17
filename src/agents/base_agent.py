import uuid
from typing import Dict, List, Any, Optional, Union, Callable
from abc import ABC, abstractmethod

from crewai import Agent as CrewAgent
from crewai.tools import BaseTool

from src.config.config import (
    DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, 
    MAX_AGENT_ITERATIONS, MAX_AGENT_EXECUTION_TIME, AGENT_RPM_LIMIT
)
from src.utils.logging_utils import setup_logger

logger = setup_logger(__name__)

class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    Wraps the CrewAI Agent interface.
    """
    
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        memory: bool = True,
        verbose: bool = True,
        allow_delegation: bool = False,
        tools: List[BaseTool] = None,
        llm: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        max_iterations: int = MAX_AGENT_ITERATIONS,
        max_execution_time: int = MAX_AGENT_EXECUTION_TIME,
        rpm_limit: int = AGENT_RPM_LIMIT,
        step_callback: Optional[Callable] = None
    ):
        """
        Initialize the base agent.
        
        Args:
            role (str): The role of the agent
            goal (str): The goal the agent is trying to achieve
            backstory (str): The backstory of the agent
            memory (bool): Whether the agent has memory
            verbose (bool): Whether to output verbose logs
            allow_delegation (bool): Whether the agent can delegate tasks
            tools (List[BaseTool]): List of tools available to the agent
            llm (str): The language model to use
            temperature (float): The temperature for the LLM
            max_tokens (int): Maximum number of tokens to generate
            max_iterations (int): Maximum number of iterations
            max_execution_time (int): Maximum execution time in seconds
            rpm_limit (int): Rate limit for API calls
            step_callback (Callable): Callback function for each step
        """
        self.id = str(uuid.uuid4())
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools = tools or []
        
        # Create the CrewAI agent
        self.agent = CrewAgent(
            role=role,
            goal=goal,
            backstory=backstory,
            memory=memory,
            verbose=verbose,
            allow_delegation=allow_delegation,
            llm=llm,
            tools=self.tools,
            max_iter=max_iterations,
            max_execution_time=max_execution_time,
            max_rpm=rpm_limit,
            step_callback=step_callback or self._default_step_callback
        )
        
        logger.info(f"Initialized {role} agent with ID {self.id}")
    
    def _default_step_callback(self, step_output: Dict[str, Any]):
        """
        Default callback function for agent steps.
        
        Args:
            step_output (Dict[str, Any]): Output from the agent step
        """
        iteration = step_output.get("iteration", "unknown")
        logger.info(f"Agent {self.role} ({self.id}) - Iteration {iteration}")
    
    def add_tool(self, tool: BaseTool):
        """
        Add a tool to the agent.
        
        Args:
            tool (BaseTool): Tool to add
        """
        self.tools.append(tool)
        self.agent.tools = self.tools
        logger.info(f"Added tool {tool.name} to {self.role} agent ({self.id})")
    
    def remove_tool(self, tool_name: str):
        """
        Remove a tool from the agent.
        
        Args:
            tool_name (str): Name of the tool to remove
        """
        self.tools = [tool for tool in self.tools if tool.name != tool_name]
        self.agent.tools = self.tools
        logger.info(f"Removed tool {tool_name} from {self.role} agent ({self.id})")
    
    @abstractmethod
    def run(self, *args, **kwargs):
        """
        Run the agent.
        Must be implemented by subclasses.
        """
        pass 