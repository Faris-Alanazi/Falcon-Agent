import os
from typing import Dict, List, Any, Optional, Union

from crewai.tasks import Task

from src.agents.base_agent import BaseAgent
from src.tools.brave_search_tool import BraveSearchTool
from src.tools.sequential_thinking_tool import SequentialThinkingTool
from src.utils.logging_utils import setup_logger
from src.utils.memory_utils import MemoryManager

logger = setup_logger(__name__)

class RequirementerAgent(BaseAgent):
    """
    Requirementer Agent: The entry point to the system, analyzing user requests
    deeply using reasoning and iterative approaches. Refines requirements into
    a comprehensive Product Requirement Document (PRD).
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the Requirementer Agent.
        
        Args:
            **kwargs: Additional arguments to pass to the base agent
        """
        # Set default role, goal, and backstory
        role = "Requirements Analyst"
        goal = "Analyze user requests deeply and produce a comprehensive Product Requirement Document (PRD)."
        backstory = (
            "You are a world-class requirements analyst with decades of experience in software development. "
            "Your expertise lies in understanding user needs and translating them into clear, comprehensive, "
            "and actionable requirements. You excel at identifying implicit requirements, asking strategic "
            "questions, and organizing information into well-structured documentation. You have a reputation "
            "for thoroughness and clarity, ensuring that development teams have everything they need to "
            "build exactly what users want."
        )
        
        # Initialize base agent
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            **kwargs
        )
        
        # Add required tools
        self.add_tool(BraveSearchTool())
        self.add_tool(SequentialThinkingTool())
        
        # Initialize memory manager
        self.memory = MemoryManager(self.id)
    
    def run(self, user_request: str) -> str:
        """
        Analyze the user request and produce a PRD.
        
        Args:
            user_request (str): The initial user request
            
        Returns:
            str: The comprehensive PRD
        """
        logger.info(f"Requirementer Agent starting analysis of user request: {user_request[:50]}...")
        
        # Store the initial request in memory
        self.memory.add_to_short_term(
            {"content": user_request, "type": "initial_request"},
            category="user_input"
        )
        
        # Create a task for the agent to perform
        analysis_task = Task(
            description=(
                f"Analyze the following user request and produce a comprehensive PRD:\n\n"
                f"{user_request}\n\n"
                f"Follow these steps:\n"
                f"1. Use Sequential Thinking to break down and understand the request\n"
                f"2. Identify any ambiguities or missing information\n"
                f"3. Research any domain-specific knowledge needed using Brave Search\n"
                f"4. Organize the requirements in a clear, structured format\n"
                f"5. Include all necessary sections in the PRD:\n"
                f"   - Goals and Vision\n"
                f"   - User Requirements\n"
                f"   - Functional Requirements\n"
                f"   - Technical Requirements\n"
                f"   - User Interface\n"
                f"   - Performance Requirements\n"
                f"   - Security Requirements\n"
                f"   - Timeline and Milestones\n"
                f"   - Success Metrics\n\n"
                f"Ask clarifying questions ONLY if absolutely necessary to produce a complete PRD."
            ),
            expected_output=(
                "A comprehensive PRD document in markdown format with all required sections."
            ),
            agent=self.agent
        )
        
        # Execute the task
        prd = self.agent.execute_task(analysis_task)
        
        # Store the PRD in memory
        self.memory.add_to_long_term(
            {"content": prd, "type": "prd"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=3)
        
        logger.info(f"Requirementer Agent completed PRD creation: {len(prd)} characters")
        return prd
    
    def refine_requirements(self, prd: str, additional_input: str) -> str:
        """
        Refine an existing PRD based on additional input.
        
        Args:
            prd (str): The existing PRD
            additional_input (str): Additional information or feedback
            
        Returns:
            str: The refined PRD
        """
        logger.info(f"Requirementer Agent refining PRD with additional input: {additional_input[:50]}...")
        
        # Store the additional input in memory
        self.memory.add_to_short_term(
            {"content": additional_input, "type": "additional_input"},
            category="user_input"
        )
        
        # Create a task for the agent to perform
        refinement_task = Task(
            description=(
                f"Refine the following PRD based on additional input from the user:\n\n"
                f"Current PRD:\n{prd}\n\n"
                f"Additional Input:\n{additional_input}\n\n"
                f"Follow these steps:\n"
                f"1. Analyze how the additional input affects the current requirements\n"
                f"2. Determine which sections need updates\n"
                f"3. Make appropriate changes while maintaining the document's structure\n"
                f"4. Ensure all requirements remain clear, consistent, and actionable\n"
                f"5. Highlight the changes you've made\n\n"
                f"Ask clarifying questions ONLY if absolutely necessary."
            ),
            expected_output=(
                "A refined PRD document in markdown format with highlighted changes."
            ),
            agent=self.agent
        )
        
        # Execute the task
        refined_prd = self.agent.execute_task(refinement_task)
        
        # Store the refined PRD in memory
        self.memory.add_to_long_term(
            {"content": refined_prd, "type": "refined_prd"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=3)
        
        logger.info(f"Requirementer Agent completed PRD refinement: {len(refined_prd)} characters")
        return refined_prd
    
    def ask_clarifying_questions(self, user_request: str) -> List[str]:
        """
        Generate clarifying questions for ambiguous or incomplete requirements.
        
        Args:
            user_request (str): The user request
            
        Returns:
            List[str]: List of clarifying questions
        """
        logger.info(f"Requirementer Agent generating clarifying questions for: {user_request[:50]}...")
        
        # Store the request in memory
        self.memory.add_to_short_term(
            {"content": user_request, "type": "request_for_clarification"},
            category="user_input"
        )
        
        # Create a task for the agent to perform
        questions_task = Task(
            description=(
                f"Analyze the following user request and generate clarifying questions:\n\n"
                f"{user_request}\n\n"
                f"Follow these steps:\n"
                f"1. Identify ambiguous or incomplete aspects of the request\n"
                f"2. Determine what additional information is needed\n"
                f"3. Formulate clear, specific questions to address these gaps\n"
                f"4. Prioritize questions by importance\n"
                f"5. Ensure questions are concise and focused\n\n"
                f"Output only the essential questions needed to create a complete PRD."
            ),
            expected_output=(
                "A numbered list of clarifying questions in order of importance."
            ),
            agent=self.agent
        )
        
        # Execute the task
        questions_text = self.agent.execute_task(questions_task)
        
        # Parse the questions into a list
        questions = []
        for line in questions_text.split("\n"):
            # Remove number prefixes and whitespace
            line = line.strip()
            if line and (line[0].isdigit() or line[0] in ["•", "-", "*"]):
                # Remove prefix and clean up
                cleaned_line = line.lstrip("0123456789.-*• ").strip()
                if cleaned_line and cleaned_line not in questions:
                    questions.append(cleaned_line)
        
        # Store the questions in memory
        self.memory.add_to_long_term(
            {"content": questions_text, "type": "clarifying_questions"},
            category="output",
            importance=4
        )
        
        logger.info(f"Requirementer Agent generated {len(questions)} clarifying questions")
        return questions 