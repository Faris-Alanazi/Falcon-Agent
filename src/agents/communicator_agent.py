import os
from typing import Dict, List, Any, Optional, Union
import json

from crewai.tasks import Task

from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import setup_logger
from src.utils.memory_utils import MemoryManager

logger = setup_logger(__name__)

class CommunicatorAgent(BaseAgent):
    """
    Communicator Agent: Provides the final communication to the user, presenting
    the completed project and relevant information.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the Communicator Agent.
        
        Args:
            **kwargs: Additional arguments to pass to the base agent
        """
        # Set default role, goal, and backstory
        role = "Technical Communication Specialist"
        goal = "Present completed projects to users in a clear, accessible format."
        backstory = (
            "You are an expert technical writer and presenter with years of experience in translating "
            "complex technical achievements into clear, accessible communications. You excel at organizing "
            "information in a logical flow, highlighting key points, and providing appropriate context "
            "for non-technical audiences. You're known for your ability to create compelling narratives "
            "around technical projects, making complex work understandable and showcasing its value. "
            "Your presentations and documentation have consistently received praise for their clarity, "
            "thoroughness, and user-friendliness."
        )
        
        # Initialize base agent
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            **kwargs
        )
        
        # Initialize memory manager
        self.memory = MemoryManager(self.id)
    
    def run(self, project_summary: Dict[str, Any], completed_tasks: List[Dict[str, Any]], files_changed: List[str]) -> str:
        """
        Create a comprehensive project summary for the user.
        
        Args:
            project_summary (Dict[str, Any]): Summary information about the project
            completed_tasks (List[Dict[str, Any]]): List of all completed tasks
            files_changed (List[str]): List of files created or modified
            
        Returns:
            str: A comprehensive project summary in markdown format
        """
        logger.info(f"Communicator Agent starting project summary creation...")
        
        # Store the input data in memory
        self.memory.add_to_short_term(
            {"content": json.dumps(project_summary, indent=2), "type": "project_summary"},
            category="input"
        )
        self.memory.add_to_short_term(
            {"content": json.dumps(completed_tasks, indent=2), "type": "completed_tasks"},
            category="input"
        )
        self.memory.add_to_short_term(
            {"content": json.dumps(files_changed, indent=2), "type": "files_changed"},
            category="input"
        )
        
        # Create a task for the agent to perform
        summary_task = Task(
            description=(
                f"Create a comprehensive project summary for the user based on the following information:\n\n"
                f"Project Summary:\n{json.dumps(project_summary, indent=2)}\n\n"
                f"Completed Tasks ({len(completed_tasks)}):\n{json.dumps(completed_tasks[:10], indent=2)}"
                f"{' ... and more' if len(completed_tasks) > 10 else ''}\n\n"
                f"Files Changed ({len(files_changed)}):\n{json.dumps(files_changed[:20], indent=2)}"
                f"{' ... and more' if len(files_changed) > 20 else ''}\n\n"
                f"Follow these steps:\n"
                f"1. Create a clear, well-structured summary of the project\n"
                f"2. Highlight key achievements and features implemented\n"
                f"3. Provide an overview of the project structure\n"
                f"4. Include any important technical details the user should know\n"
                f"5. Add instructions for how to use or deploy the project\n"
                f"6. Format the summary in markdown for readability\n"
                f"7. Keep the tone professional but approachable"
            ),
            expected_output=(
                "A comprehensive project summary in markdown format."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(summary_task)
        
        # Store the summary in memory
        self.memory.add_to_long_term(
            {"content": result, "type": "project_summary_output"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=4)
        
        logger.info(f"Communicator Agent completed project summary creation: {len(result)} characters")
        return result
    
    def create_readme(self, project_info: Dict[str, Any], features: List[str], installation_steps: List[str], usage_examples: List[str]) -> str:
        """
        Create a detailed README file for the project.
        
        Args:
            project_info (Dict[str, Any]): Basic information about the project
            features (List[str]): List of features implemented
            installation_steps (List[str]): Installation instructions
            usage_examples (List[str]): Examples of how to use the project
            
        Returns:
            str: A complete README file in markdown format
        """
        logger.info(f"Communicator Agent starting README creation...")
        
        # Store the input data in memory
        self.memory.add_to_short_term(
            {"content": json.dumps(project_info, indent=2), "type": "project_info"},
            category="input"
        )
        
        # Create a task for the agent to perform
        readme_task = Task(
            description=(
                f"Create a detailed README.md file for the project based on the following information:\n\n"
                f"Project Information:\n{json.dumps(project_info, indent=2)}\n\n"
                f"Features:\n{json.dumps(features, indent=2)}\n\n"
                f"Installation Steps:\n{json.dumps(installation_steps, indent=2)}\n\n"
                f"Usage Examples:\n{json.dumps(usage_examples, indent=2)}\n\n"
                f"Follow these steps:\n"
                f"1. Create a compelling project title and short description\n"
                f"2. Add badges for build status, version, etc. if applicable\n"
                f"3. Include a table of contents for longer READMEs\n"
                f"4. List all features with brief explanations\n"
                f"5. Provide clear installation instructions\n"
                f"6. Include usage examples with code snippets\n"
                f"7. Add sections for configuration, API documentation, etc. if relevant\n"
                f"8. Include information about contributing, license, etc.\n"
                f"9. Format everything in clean, readable markdown"
            ),
            expected_output=(
                "A complete README.md file in markdown format."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(readme_task)
        
        # Store the README in memory
        self.memory.add_to_long_term(
            {"content": result, "type": "readme_output"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=4)
        
        logger.info(f"Communicator Agent completed README creation: {len(result)} characters")
        return result
    
    def create_user_guide(self, project_info: Dict[str, Any], features: List[Dict[str, Any]], usage_scenarios: List[Dict[str, Any]]) -> str:
        """
        Create a comprehensive user guide for the project.
        
        Args:
            project_info (Dict[str, Any]): Basic information about the project
            features (List[Dict[str, Any]]): Detailed information about each feature
            usage_scenarios (List[Dict[str, Any]]): Various usage scenarios with examples
            
        Returns:
            str: A comprehensive user guide in markdown format
        """
        logger.info(f"Communicator Agent starting user guide creation...")
        
        # Store the input data in memory
        self.memory.add_to_short_term(
            {"content": json.dumps(project_info, indent=2), "type": "project_info"},
            category="input"
        )
        self.memory.add_to_short_term(
            {"content": json.dumps(features, indent=2), "type": "features"},
            category="input"
        )
        self.memory.add_to_short_term(
            {"content": json.dumps(usage_scenarios, indent=2), "type": "usage_scenarios"},
            category="input"
        )
        
        # Create a task for the agent to perform
        user_guide_task = Task(
            description=(
                f"Create a comprehensive user guide for the project based on the following information:\n\n"
                f"Project Information:\n{json.dumps(project_info, indent=2)}\n\n"
                f"Features ({len(features)}):\n{json.dumps(features[:5], indent=2)}"
                f"{' ... and more' if len(features) > 5 else ''}\n\n"
                f"Usage Scenarios ({len(usage_scenarios)}):\n{json.dumps(usage_scenarios[:5], indent=2)}"
                f"{' ... and more' if len(usage_scenarios) > 5 else ''}\n\n"
                f"Follow these steps:\n"
                f"1. Create a clear introduction explaining the purpose of the guide\n"
                f"2. Include a table of contents for easy navigation\n"
                f"3. Provide a getting started section with installation and basic setup\n"
                f"4. Create a detailed section for each feature\n"
                f"5. Include step-by-step instructions for common tasks\n"
                f"6. Add screenshots or diagrams where helpful (described in text)\n"
                f"7. Include troubleshooting information for common issues\n"
                f"8. Add an FAQ section\n"
                f"9. Format everything in clean, readable markdown"
            ),
            expected_output=(
                "A comprehensive user guide in markdown format."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(user_guide_task)
        
        # Store the user guide in memory
        self.memory.add_to_long_term(
            {"content": result, "type": "user_guide_output"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=4)
        
        logger.info(f"Communicator Agent completed user guide creation: {len(result)} characters")
        return result
    
    def create_presentation(self, project_info: Dict[str, Any], key_achievements: List[str], metrics: Dict[str, Any], future_work: List[str]) -> str:
        """
        Create a presentation summarizing the project, achievements, and future work.
        
        Args:
            project_info (Dict[str, Any]): Basic information about the project
            key_achievements (List[str]): List of key achievements and milestones
            metrics (Dict[str, Any]): Performance metrics and other measurable outcomes
            future_work (List[str]): Potential future enhancements or next steps
            
        Returns:
            str: A presentation in markdown format (convertible to slides)
        """
        logger.info(f"Communicator Agent starting presentation creation...")
        
        # Store the input data in memory
        self.memory.add_to_short_term(
            {"content": json.dumps(project_info, indent=2), "type": "project_info"},
            category="input"
        )
        self.memory.add_to_short_term(
            {"content": json.dumps(key_achievements, indent=2), "type": "key_achievements"},
            category="input"
        )
        self.memory.add_to_short_term(
            {"content": json.dumps(metrics, indent=2), "type": "metrics"},
            category="input"
        )
        self.memory.add_to_short_term(
            {"content": json.dumps(future_work, indent=2), "type": "future_work"},
            category="input"
        )
        
        # Create a task for the agent to perform
        presentation_task = Task(
            description=(
                f"Create a presentation summarizing the project based on the following information:\n\n"
                f"Project Information:\n{json.dumps(project_info, indent=2)}\n\n"
                f"Key Achievements:\n{json.dumps(key_achievements, indent=2)}\n\n"
                f"Metrics:\n{json.dumps(metrics, indent=2)}\n\n"
                f"Future Work:\n{json.dumps(future_work, indent=2)}\n\n"
                f"Follow these steps:\n"
                f"1. Create a title slide with project name and high-level description\n"
                f"2. Include an agenda/outline slide\n"
                f"3. Provide background/context for the project\n"
                f"4. Highlight key features and achievements\n"
                f"5. Present metrics and results\n"
                f"6. Discuss challenges and how they were addressed\n"
                f"7. Include future work and next steps\n"
                f"8. Add a summary/conclusion slide\n"
                f"9. Format in markdown with '---' to separate slides\n"
                f"10. Keep content concise - bullet points where appropriate"
            ),
            expected_output=(
                "A presentation in markdown format, with '---' separating slides."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(presentation_task)
        
        # Store the presentation in memory
        self.memory.add_to_long_term(
            {"content": result, "type": "presentation_output"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=4)
        
        logger.info(f"Communicator Agent completed presentation creation: {len(result)} characters")
        return result 