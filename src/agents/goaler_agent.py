import os
from typing import Dict, List, Any, Optional, Union
import json

from crewai.tasks import Task

from src.agents.base_agent import BaseAgent
from src.tools.brave_search_tool import BraveSearchTool
from src.tools.sequential_thinking_tool import SequentialThinkingTool
from src.utils.logging_utils import setup_logger
from src.utils.memory_utils import MemoryManager

logger = setup_logger(__name__)

class GoalerAgent(BaseAgent):
    """
    Goaler Agent: Serves as a supervisor, validating that the Goal Graph accurately
    represents a complete path to fulfilling the original user requirements.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the Goaler Agent.
        
        Args:
            **kwargs: Additional arguments to pass to the base agent
        """
        # Set default role, goal, and backstory
        role = "Requirements Validation Specialist"
        goal = "Ensure the Goal Graph accurately represents a complete path to fulfilling the original user requirements."
        backstory = (
            "You are a senior software architect with a background in quality assurance and "
            "requirements management. Your specialty is validating project plans against original "
            "requirements to ensure complete coverage. You have a keen eye for identifying gaps "
            "in implementation plans and can spot missing dependencies or overlooked requirements. "
            "You've saved countless projects from going off-track by catching issues early in the "
            "planning phase. Development teams appreciate your thorough approach and ability to "
            "ensure that a project plan truly addresses all user needs."
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
    
    def run(self, prd: str, goal_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the Goal Graph against the PRD and provide feedback.
        
        Args:
            prd (str): The Product Requirements Document
            goal_graph (Dict[str, Any]): The Goal Graph to validate
            
        Returns:
            Dict[str, Any]: Validation results containing feedback and any missing requirements
        """
        logger.info(f"Goaler Agent starting validation of Goal Graph against PRD...")
        
        # Store the PRD and Goal Graph in memory
        self.memory.add_to_short_term(
            {"content": prd, "type": "prd"},
            category="input"
        )
        self.memory.add_to_short_term(
            {"content": json.dumps(goal_graph, indent=2), "type": "goal_graph"},
            category="input"
        )
        
        # Create a task for the agent to perform
        validation_task = Task(
            description=(
                f"Validate that the Goal Graph accurately represents a complete path to fulfilling "
                f"the original user requirements in the PRD:\n\n"
                f"PRD:\n{prd}\n\n"
                f"Goal Graph:\n{json.dumps(goal_graph, indent=2)}\n\n"
                f"Follow these steps:\n"
                f"1. Use Sequential Thinking to analyze the PRD thoroughly\n"
                f"2. Identify all explicit and implicit requirements in the PRD\n"
                f"3. Check if each requirement is addressed by at least one task in the Goal Graph\n"
                f"4. Verify that the dependencies between tasks are logical and complete\n"
                f"5. Check if there are any missing tasks needed to fulfill the requirements\n"
                f"6. Provide detailed feedback on any gaps, inconsistencies, or improvements needed\n"
                f"7. Return a comprehensive validation report in JSON format"
            ),
            expected_output=(
                "A validation report in JSON format with feedback, missing requirements, "
                "and recommended improvements."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(validation_task)
        
        # Extract the validation report from the response
        validation_report = self._extract_json(result)
        
        # Ensure the validation report has the required structure
        validation_report = self._validate_report(validation_report)
        
        # Store the validation report in memory
        self.memory.add_to_long_term(
            {"content": json.dumps(validation_report, indent=2), "type": "validation_report"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=3)
        
        logger.info(f"Goaler Agent completed validation with {len(validation_report.get('issues', []))} issues found")
        return validation_report
    
    def review_updated_goal_graph(self, prd: str, original_graph: Dict[str, Any], 
                                 updated_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review an updated Goal Graph to ensure it addresses previous issues while
        maintaining alignment with the original requirements.
        
        Args:
            prd (str): The Product Requirements Document
            original_graph (Dict[str, Any]): The original Goal Graph
            updated_graph (Dict[str, Any]): The updated Goal Graph to review
            
        Returns:
            Dict[str, Any]: Review results containing feedback and any remaining issues
        """
        logger.info(f"Goaler Agent reviewing updated Goal Graph...")
        
        # Store the PRD and both versions of the Goal Graph in memory
        self.memory.add_to_short_term(
            {"content": prd, "type": "prd"},
            category="input"
        )
        self.memory.add_to_short_term(
            {"content": json.dumps(original_graph, indent=2), "type": "original_goal_graph"},
            category="input"
        )
        self.memory.add_to_short_term(
            {"content": json.dumps(updated_graph, indent=2), "type": "updated_goal_graph"},
            category="input"
        )
        
        # Create a task for the agent to perform
        review_task = Task(
            description=(
                f"Review the updated Goal Graph to ensure it addresses previous issues while "
                f"maintaining alignment with the original requirements:\n\n"
                f"PRD:\n{prd}\n\n"
                f"Original Goal Graph:\n{json.dumps(original_graph, indent=2)}\n\n"
                f"Updated Goal Graph:\n{json.dumps(updated_graph, indent=2)}\n\n"
                f"Follow these steps:\n"
                f"1. Compare the original and updated Goal Graphs\n"
                f"2. Identify what changes have been made\n"
                f"3. Verify that the changes address the issues in the original graph\n"
                f"4. Check that no new issues have been introduced\n"
                f"5. Ensure the updated graph still fulfills all requirements in the PRD\n"
                f"6. Provide detailed feedback on the changes and any remaining issues\n"
                f"7. Return a comprehensive review report in JSON format"
            ),
            expected_output=(
                "A review report in JSON format with feedback on the changes "
                "and any remaining issues."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(review_task)
        
        # Extract the review report from the response
        review_report = self._extract_json(result)
        
        # Ensure the review report has the required structure
        review_report = self._validate_report(review_report)
        
        # Store the review report in memory
        self.memory.add_to_long_term(
            {"content": json.dumps(review_report, indent=2), "type": "review_report"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=3)
        
        logger.info(f"Goaler Agent completed review with {len(review_report.get('issues', []))} issues found")
        return review_report
    
    def approve_goal_graph(self, goal_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Approve the Goal Graph for implementation.
        
        Args:
            goal_graph (Dict[str, Any]): The Goal Graph to approve
            
        Returns:
            Dict[str, Any]: Approval status and any notes or recommendations
        """
        logger.info(f"Goaler Agent approving Goal Graph for implementation...")
        
        # Store the Goal Graph in memory
        self.memory.add_to_short_term(
            {"content": json.dumps(goal_graph, indent=2), "type": "goal_graph_to_approve"},
            category="input"
        )
        
        # Create a task for the agent to perform
        approval_task = Task(
            description=(
                f"Review the Goal Graph one final time and provide formal approval for implementation:\n\n"
                f"Goal Graph:\n{json.dumps(goal_graph, indent=2)}\n\n"
                f"Follow these steps:\n"
                f"1. Review the Goal Graph for completeness and consistency\n"
                f"2. Ensure all tasks have clear descriptions and appropriate dependencies\n"
                f"3. Provide any final recommendations or notes for the implementation team\n"
                f"4. Formally approve the Goal Graph for implementation\n"
                f"5. Return an approval document in JSON format"
            ),
            expected_output=(
                "An approval document in JSON format with status, timestamp, and any notes."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(approval_task)
        
        # Extract the approval document from the response
        approval_doc = self._extract_json(result)
        
        # Ensure the approval document has the required structure
        approval_doc = self._validate_approval(approval_doc)
        
        # Store the approval document in memory
        self.memory.add_to_long_term(
            {"content": json.dumps(approval_doc, indent=2), "type": "approval_document"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=4)
        
        logger.info(f"Goaler Agent completed Goal Graph approval: {approval_doc['approved']}")
        return approval_doc
    
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
            logger.warning("No JSON object found in response, creating default structure")
            return {"status": "error", "message": "No JSON found in response", "issues": []}
        
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
                return {"status": "error", "message": "Failed to parse response", "issues": []}
    
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
    
    def _validate_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure the validation or review report has the required structure.
        
        Args:
            report (Dict[str, Any]): The report to validate
            
        Returns:
            Dict[str, Any]: The validated report
        """
        # Ensure the report is a dictionary
        if not isinstance(report, dict):
            logger.warning("Report is not a dictionary, creating default structure")
            report = {}
        
        # Ensure the report has the required keys
        if "status" not in report:
            report["status"] = "unknown"
        
        if "issues" not in report:
            report["issues"] = []
        
        if "recommendations" not in report:
            report["recommendations"] = []
        
        if "timestamp" not in report:
            from datetime import datetime
            report["timestamp"] = datetime.now().isoformat()
        
        return report
    
    def _validate_approval(self, approval: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure the approval document has the required structure.
        
        Args:
            approval (Dict[str, Any]): The approval document to validate
            
        Returns:
            Dict[str, Any]: The validated approval document
        """
        # Ensure the approval is a dictionary
        if not isinstance(approval, dict):
            logger.warning("Approval document is not a dictionary, creating default structure")
            approval = {}
        
        # Ensure the approval has the required keys
        if "approved" not in approval:
            # Default to approved if not explicitly set
            approval["approved"] = True
        
        if "notes" not in approval:
            approval["notes"] = []
        
        if "timestamp" not in approval:
            from datetime import datetime
            approval["timestamp"] = datetime.now().isoformat()
        
        if "approver" not in approval:
            approval["approver"] = f"Goaler Agent ({self.id})"
        
        return approval 