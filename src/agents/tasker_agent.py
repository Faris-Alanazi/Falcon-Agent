import os
from typing import Dict, List, Any, Optional, Union
import json

from crewai.tasks import Task

from src.agents.base_agent import BaseAgent
from src.tools.brave_search_tool import BraveSearchTool
from src.tools.sequential_thinking_tool import SequentialThinkingTool
from src.tools.context7_tool import Context7Tool
from src.utils.logging_utils import setup_logger
from src.utils.memory_utils import MemoryManager
from src.utils.file_utils import file_lock
from src.config.config import DATA_DIR

logger = setup_logger(__name__)

class TaskerAgent(BaseAgent):
    """
    Tasker Agent: Transforms the PRD into an actionable "Goal Graph" - a hierarchical 
    representation of tasks required to fulfill the requirements.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the Tasker Agent.
        
        Args:
            **kwargs: Additional arguments to pass to the base agent
        """
        # Set default role, goal, and backstory
        role = "Project Task Planner"
        goal = "Transform requirements into an actionable Goal Graph for software development."
        backstory = (
            "You are a highly experienced project planner with a background in software architecture "
            "and technical leadership. Your specialty is breaking down complex requirements into "
            "logical, well-structured tasks with clear dependencies. You have an exceptional ability "
            "to identify potential challenges early and plan for them. You're known for creating "
            "comprehensive, actionable task plans that development teams can easily follow, ensuring "
            "that nothing is overlooked and that the final product meets all requirements."
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
        self.add_tool(Context7Tool())
        
        # Initialize memory manager
        self.memory = MemoryManager(self.id)
        
        # Initialize goal graph directory
        self.goal_graph_dir = DATA_DIR / "goal_graphs"
        os.makedirs(self.goal_graph_dir, exist_ok=True)
    
    def run(self, prd: str) -> Dict[str, Any]:
        """
        Create a Goal Graph from the PRD.
        
        Args:
            prd (str): The Product Requirements Document
            
        Returns:
            Dict[str, Any]: The Goal Graph
        """
        logger.info(f"Tasker Agent starting creation of Goal Graph from PRD ({len(prd)} characters)...")
        
        # Store the PRD in memory
        self.memory.add_to_short_term(
            {"content": prd, "type": "prd"},
            category="input"
        )
        
        # Create a task for the agent to perform
        analysis_task = Task(
            description=(
                f"Analyze the following PRD and create a comprehensive Goal Graph of tasks required "
                f"to fulfill the requirements:\n\n{prd}\n\n"
                f"Follow these steps:\n"
                f"1. Use Sequential Thinking to break down the PRD into logical components\n"
                f"2. Research any technical requirements using Brave Search and Context7\n"
                f"3. Create a hierarchical structure of tasks with dependencies\n"
                f"4. Ensure each task has the following attributes:\n"
                f"   - Task ID: Unique identifier\n"
                f"   - Name: Descriptive task name\n"
                f"   - Priority: Importance level (High, Medium, Low)\n"
                f"   - Detailed Description: Comprehensive explanation\n"
                f"   - Dependencies: List of tasks that must be completed before this one\n"
                f"   - Task Status: Initial status (Not Started)\n"
                f"   - Owner: 'Unassigned' initially\n"
                f"5. Validate the Goal Graph for completeness and consistency\n"
                f"6. Return the Goal Graph as a structured JSON object"
            ),
            expected_output=(
                "A comprehensive Goal Graph in JSON format with all required task attributes."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(analysis_task)
        
        # Extract the JSON from the response
        goal_graph = self._extract_json(result)
        
        # Validate and clean up the goal graph
        goal_graph = self._validate_goal_graph(goal_graph)
        
        # Save the goal graph
        self._save_goal_graph(goal_graph)
        
        # Store the goal graph in memory
        self.memory.add_to_long_term(
            {"content": json.dumps(goal_graph, indent=2), "type": "goal_graph"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=3)
        
        logger.info(f"Tasker Agent completed Goal Graph creation with {len(goal_graph['tasks'])} tasks")
        return goal_graph
    
    def update_goal_graph(self, goal_graph: Dict[str, Any], updates: str) -> Dict[str, Any]:
        """
        Update an existing Goal Graph based on changes or new requirements.
        
        Args:
            goal_graph (Dict[str, Any]): The existing Goal Graph
            updates (str): Description of updates needed
            
        Returns:
            Dict[str, Any]: The updated Goal Graph
        """
        logger.info(f"Tasker Agent updating Goal Graph based on: {updates[:50]}...")
        
        # Store the updates in memory
        self.memory.add_to_short_term(
            {"content": updates, "type": "goal_graph_updates"},
            category="input"
        )
        
        # Convert the goal graph to a JSON string for the task
        goal_graph_json = json.dumps(goal_graph, indent=2)
        
        # Create a task for the agent to perform
        update_task = Task(
            description=(
                f"Update the following Goal Graph based on these changes:\n\n"
                f"Current Goal Graph:\n{goal_graph_json}\n\n"
                f"Updates Needed:\n{updates}\n\n"
                f"Follow these steps:\n"
                f"1. Analyze how the updates affect the current Goal Graph\n"
                f"2. Determine which tasks need to be added, modified, or removed\n"
                f"3. Update the dependencies to maintain consistency\n"
                f"4. Ensure all tasks have the required attributes\n"
                f"5. Validate the updated Goal Graph\n"
                f"6. Return the complete updated Goal Graph as a JSON object"
            ),
            expected_output=(
                "An updated Goal Graph in JSON format with all required task attributes."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(update_task)
        
        # Extract the JSON from the response
        updated_goal_graph = self._extract_json(result)
        
        # Validate and clean up the goal graph
        updated_goal_graph = self._validate_goal_graph(updated_goal_graph)
        
        # Save the updated goal graph
        self._save_goal_graph(updated_goal_graph)
        
        # Store the updated goal graph in memory
        self.memory.add_to_long_term(
            {"content": json.dumps(updated_goal_graph, indent=2), "type": "updated_goal_graph"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=3)
        
        logger.info(f"Tasker Agent completed Goal Graph update with {len(updated_goal_graph['tasks'])} tasks")
        return updated_goal_graph
    
    def validate_goal_graph(self, goal_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate a Goal Graph for completeness, consistency, and circular dependencies.
        
        Args:
            goal_graph (Dict[str, Any]): The Goal Graph to validate
            
        Returns:
            List[Dict[str, Any]]: List of validation issues, empty if valid
        """
        logger.info("Tasker Agent validating Goal Graph...")
        
        # Store the goal graph in memory
        self.memory.add_to_short_term(
            {"content": json.dumps(goal_graph, indent=2), "type": "goal_graph_to_validate"},
            category="input"
        )
        
        # Create a task for the agent to perform
        validation_task = Task(
            description=(
                f"Validate the following Goal Graph for completeness, consistency, and circular dependencies:\n\n"
                f"{json.dumps(goal_graph, indent=2)}\n\n"
                f"Follow these steps:\n"
                f"1. Check if all tasks have the required attributes\n"
                f"2. Verify that all dependencies refer to valid task IDs\n"
                f"3. Check for circular dependencies\n"
                f"4. Ensure there are no orphaned tasks (tasks not connected to the graph)\n"
                f"5. Verify that the graph is complete (covers all requirements)\n"
                f"6. List any issues found, or confirm the graph is valid"
            ),
            expected_output=(
                "A list of validation issues in JSON format, or confirmation that the graph is valid."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(validation_task)
        
        # Extract the results
        issues = []
        
        # If the response contains a JSON array, parse it as issues
        if '[' in result and ']' in result:
            try:
                # Try to extract a JSON array from the response
                issues_str = result[result.find('['):result.rfind(']')+1]
                issues = json.loads(issues_str)
            except json.JSONDecodeError:
                # If there's an error parsing the JSON, assume there was a formatting issue
                # Create a single issue with the raw response
                issues = [{"type": "parsing_error", "message": "Could not parse validation results.", "details": result}]
        else:
            # If the response does not contain a JSON array, check if it indicates the graph is valid
            if "valid" in result.lower() and not any(error_term in result.lower() for error_term in ["error", "issue", "problem", "invalid"]):
                # No issues found
                issues = []
            else:
                # Create a single issue with the raw response
                issues = [{"type": "unknown", "message": "Validation produced non-JSON results.", "details": result}]
        
        # Store the validation results in memory
        self.memory.add_to_long_term(
            {"content": json.dumps(issues, indent=2), "type": "goal_graph_validation"},
            category="output",
            importance=4
        )
        
        logger.info(f"Tasker Agent completed Goal Graph validation with {len(issues)} issues found")
        return issues
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract a JSON object from a text response.
        
        Args:
            text (str): The text containing a JSON object
            
        Returns:
            Dict[str, Any]: The extracted JSON object
        """
        # Look for JSON object in the text
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            logger.warning("No JSON object found in response, returning empty object")
            return {"tasks": []}
        
        json_str = text[start_idx:end_idx+1]
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {e}")
            # Try to clean up the JSON string and parse again
            cleaned_json_str = self._clean_json_string(json_str)
            try:
                return json.loads(cleaned_json_str)
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON even after cleanup")
                return {"tasks": []}
    
    def _clean_json_string(self, json_str: str) -> str:
        """
        Clean up a JSON string to make it parseable.
        
        Args:
            json_str (str): The JSON string to clean
            
        Returns:
            str: The cleaned JSON string
        """
        # Replace common issues
        cleaned = json_str.replace("'", '"')  # Replace single quotes with double quotes
        cleaned = cleaned.replace("\n", " ")  # Remove newlines
        
        # Handle trailing commas (common issue)
        cleaned = cleaned.replace(",}", "}")
        cleaned = cleaned.replace(",]", "]")
        
        return cleaned
    
    def _validate_goal_graph(self, goal_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean up a Goal Graph.
        
        Args:
            goal_graph (Dict[str, Any]): The Goal Graph to validate
            
        Returns:
            Dict[str, Any]: The validated and cleaned Goal Graph
        """
        # Ensure the goal graph has the necessary top-level structure
        if not isinstance(goal_graph, dict):
            logger.warning("Goal Graph is not a dictionary, creating default structure")
            goal_graph = {"tasks": []}
        
        if "tasks" not in goal_graph:
            logger.warning("Goal Graph does not have a 'tasks' key, adding it")
            goal_graph["tasks"] = []
        
        # Ensure all tasks have the required attributes
        for i, task in enumerate(goal_graph["tasks"]):
            if not isinstance(task, dict):
                logger.warning(f"Task {i} is not a dictionary, skipping")
                continue
            
            # Ensure each task has the required attributes
            if "id" not in task:
                task["id"] = str(i + 1)
            
            if "name" not in task:
                task["name"] = f"Task {task['id']}"
            
            if "priority" not in task:
                task["priority"] = "Medium"
            
            if "description" not in task:
                task["description"] = "No description provided."
            
            if "dependencies" not in task:
                task["dependencies"] = []
            
            if "status" not in task:
                task["status"] = "Not Started"
            
            if "owner" not in task:
                task["owner"] = "Unassigned"
        
        return goal_graph
    
    def _save_goal_graph(self, goal_graph: Dict[str, Any]) -> None:
        """
        Save a Goal Graph to disk.
        
        Args:
            goal_graph (Dict[str, Any]): The Goal Graph to save
        """
        # Generate a timestamp-based filename
        timestamp = int(os.path.getmtime(self.goal_graph_dir)) if os.path.exists(self.goal_graph_dir) else 0
        filename = f"goal_graph_{timestamp}.json"
        file_path = self.goal_graph_dir / filename
        
        # Also save as latest
        latest_path = self.goal_graph_dir / "latest.json"
        
        try:
            # Save the timestamped version
            with file_lock(file_path, self.id):
                with open(file_path, 'w') as f:
                    json.dump(goal_graph, f, indent=2)
            
            # Save as latest
            with file_lock(latest_path, self.id):
                with open(latest_path, 'w') as f:
                    json.dump(goal_graph, f, indent=2)
            
            logger.info(f"Goal Graph saved to {file_path} and {latest_path}")
            
        except Exception as e:
            logger.error(f"Error saving Goal Graph: {e}")
    
    def load_goal_graph(self, filename: Optional[str] = "latest.json") -> Dict[str, Any]:
        """
        Load a Goal Graph from disk.
        
        Args:
            filename (str, optional): The filename to load. Defaults to "latest.json".
            
        Returns:
            Dict[str, Any]: The loaded Goal Graph
        """
        file_path = self.goal_graph_dir / filename
        
        if not os.path.exists(file_path):
            logger.warning(f"Goal Graph file {file_path} not found")
            return {"tasks": []}
        
        try:
            with file_lock(file_path, self.id, exclusive=False):
                with open(file_path, 'r') as f:
                    return json.load(f)
                
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading Goal Graph: {e}")
            return {"tasks": []} 