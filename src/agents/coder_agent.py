import os
from typing import Dict, List, Any, Optional, Union
import json
from pathlib import Path

from crewai.tasks import Task

from src.agents.base_agent import BaseAgent
from src.tools.brave_search_tool import BraveSearchTool
from src.tools.sequential_thinking_tool import SequentialThinkingTool
from src.tools.context7_tool import Context7Tool
from src.utils.logging_utils import setup_logger
from src.utils.memory_utils import MemoryManager
from src.utils.file_utils import file_lock

logger = setup_logger(__name__)

class CoderAgent(BaseAgent):
    """
    Coder Agent: Implements code according to the Goal Graph specifications.
    Works collaboratively with other Coder agents on shared file system.
    """
    
    def __init__(self, team_id: str = None, **kwargs):
        """
        Initialize the Coder Agent.
        
        Args:
            team_id (str, optional): Team identifier for this agent
            **kwargs: Additional arguments to pass to the base agent
        """
        # Set default role, goal, and backstory
        role = "Software Engineer"
        goal = "Implement high-quality, efficient code according to specifications."
        backstory = (
            "You are an expert software engineer with years of experience in building enterprise-grade "
            "applications. You have deep knowledge of software design patterns, best practices, and "
            "multiple programming languages. You excel at translating requirements into clean, efficient, "
            "maintainable code. You're thorough in your approach, always ensuring your code is robust, "
            "well-tested, and clearly documented. You collaborate effectively with other engineers and "
            "follow team coding standards meticulously."
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
        
        # Initialize team status
        self.team_id = team_id or "default_team"
        self.assigned_tasks = []
        self.current_task = None
        self.locked_files = {}
    
    def run(self, task: Dict[str, Any], file_access: List[str]) -> Dict[str, Any]:
        """
        Implement a task from the Goal Graph.
        
        Args:
            task (Dict[str, Any]): The task to implement
            file_access (List[str]): Paths to files this agent can access
            
        Returns:
            Dict[str, Any]: Implementation results including status and any output
        """
        logger.info(f"Coder Agent starting implementation of task {task.get('id', 'unknown')}...")
        
        # Update current task and status
        self.current_task = task
        self.assigned_tasks.append(task["id"])
        
        # Store the task in memory
        self.memory.add_to_short_term(
            {"content": json.dumps(task, indent=2), "type": "assigned_task"},
            category="input"
        )
        
        # Lock files that need to be modified
        self._lock_files(file_access)
        
        # Create a task for the agent to perform
        implementation_task = Task(
            description=(
                f"Implement the following task according to the specifications:\n\n"
                f"Task: {json.dumps(task, indent=2)}\n\n"
                f"You have access to modify the following files:\n"
                f"{', '.join(file_access)}\n\n"
                f"Follow these steps:\n"
                f"1. Use Sequential Thinking to break down the implementation approach\n"
                f"2. Research and gather necessary documentation using Context7 and Brave Search\n"
                f"3. Examine existing code structure and patterns (if applicable)\n"
                f"4. Implement the required code with appropriate error handling and comments\n"
                f"5. Consider edge cases and ensure robust implementation\n"
                f"6. Document your implementation decisions\n"
                f"7. Return a detailed implementation report including files modified, code added/changed, and any notes"
            ),
            expected_output=(
                "A detailed implementation report in JSON format including files modified, "
                "code added/changed, and any implementation notes."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(implementation_task)
        
        # Extract the implementation report from the response
        implementation_report = self._extract_json(result)
        
        # Ensure the implementation report has the required structure
        implementation_report = self._validate_implementation_report(implementation_report)
        
        # Store the implementation report in memory
        self.memory.add_to_long_term(
            {"content": json.dumps(implementation_report, indent=2), "type": "implementation_report"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Release locked files
        self._release_files()
        
        # Update task status
        implementation_report["task_id"] = task["id"]
        implementation_report["agent_id"] = self.id
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=4)
        
        logger.info(f"Coder Agent completed implementation of task {task.get('id', 'unknown')}")
        return implementation_report
    
    def review_code(self, files: List[str], review_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review code in the specified files according to the review criteria.
        
        Args:
            files (List[str]): List of files to review
            review_criteria (Dict[str, Any]): Criteria for the code review
            
        Returns:
            Dict[str, Any]: Review results including issues found and recommendations
        """
        logger.info(f"Coder Agent starting code review of {len(files)} files...")
        
        # Store the review request in memory
        self.memory.add_to_short_term(
            {
                "content": f"Code review request for files: {', '.join(files)}",
                "type": "code_review_request"
            },
            category="input"
        )
        
        # Create a task for the agent to perform
        review_task = Task(
            description=(
                f"Review the code in the following files according to the specified criteria:\n\n"
                f"Files to review:\n{', '.join(files)}\n\n"
                f"Review criteria:\n{json.dumps(review_criteria, indent=2)}\n\n"
                f"Follow these steps:\n"
                f"1. Examine each file for code quality, efficiency, and adherence to requirements\n"
                f"2. Check for any security vulnerabilities or performance issues\n"
                f"3. Verify proper error handling and edge case coverage\n"
                f"4. Look for any duplicated code or opportunities for refactoring\n"
                f"5. Ensure documentation and comments are clear and sufficient\n"
                f"6. Return a comprehensive review report with issues found and recommendations"
            ),
            expected_output=(
                "A comprehensive code review report in JSON format with issues found and recommendations."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(review_task)
        
        # Extract the review report from the response
        review_report = self._extract_json(result)
        
        # Ensure the review report has the required structure
        review_report = self._validate_review_report(review_report)
        
        # Store the review report in memory
        self.memory.add_to_long_term(
            {"content": json.dumps(review_report, indent=2), "type": "code_review_report"},
            category="output",
            importance=4
        )
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=3)
        
        logger.info(f"Coder Agent completed code review with {len(review_report.get('issues', []))} issues found")
        return review_report
    
    def fix_issues(self, issues: List[Dict[str, Any]], file_access: List[str]) -> Dict[str, Any]:
        """
        Fix issues identified in a code review.
        
        Args:
            issues (List[Dict[str, Any]]): List of issues to fix
            file_access (List[str]): Paths to files this agent can access
            
        Returns:
            Dict[str, Any]: Results of the fixes including fixed issues and any notes
        """
        logger.info(f"Coder Agent starting to fix {len(issues)} issues...")
        
        # Store the issues in memory
        self.memory.add_to_short_term(
            {"content": json.dumps(issues, indent=2), "type": "issues_to_fix"},
            category="input"
        )
        
        # Lock files that need to be modified
        self._lock_files(file_access)
        
        # Create a task for the agent to perform
        fix_task = Task(
            description=(
                f"Fix the following issues identified in the code review:\n\n"
                f"Issues:\n{json.dumps(issues, indent=2)}\n\n"
                f"You have access to modify the following files:\n"
                f"{', '.join(file_access)}\n\n"
                f"Follow these steps:\n"
                f"1. Analyze each issue and determine the appropriate fix\n"
                f"2. Implement the fixes in the affected files\n"
                f"3. Ensure the fixes do not introduce new issues\n"
                f"4. Verify the fixes address the original issues completely\n"
                f"5. Return a detailed report of the fixes applied and any notes"
            ),
            expected_output=(
                "A detailed report in JSON format of the fixes applied to each issue."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(fix_task)
        
        # Extract the fix report from the response
        fix_report = self._extract_json(result)
        
        # Ensure the fix report has the required structure
        fix_report = self._validate_fix_report(fix_report)
        
        # Store the fix report in memory
        self.memory.add_to_long_term(
            {"content": json.dumps(fix_report, indent=2), "type": "fix_report"},
            category="output",
            importance=4
        )
        
        # Release locked files
        self._release_files()
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=3)
        
        logger.info(f"Coder Agent completed fixing {len(fix_report.get('fixed_issues', []))} issues")
        return fix_report
    
    def _lock_files(self, files: List[str]) -> None:
        """
        Lock files for exclusive access.
        
        Args:
            files (List[str]): Paths to files to lock
        """
        for file_path in files:
            try:
                path = Path(file_path)
                lock = file_lock(path, self.id)
                self.locked_files[str(path)] = lock
                logger.info(f"Coder Agent locked file: {file_path}")
            except Exception as e:
                logger.error(f"Error locking file {file_path}: {e}")
    
    def _release_files(self) -> None:
        """Release all locked files."""
        for file_path, lock in self.locked_files.items():
            try:
                lock.release()
                logger.info(f"Coder Agent released lock on file: {file_path}")
            except Exception as e:
                logger.error(f"Error releasing lock on file {file_path}: {e}")
        
        self.locked_files = {}
    
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
            return {"status": "error", "message": "No JSON found in response"}
        
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
                return {"status": "error", "message": "Failed to parse response"}
    
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
    
    def _validate_implementation_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure the implementation report has the required structure.
        
        Args:
            report (Dict[str, Any]): The report to validate
            
        Returns:
            Dict[str, Any]: The validated report
        """
        # Ensure the report is a dictionary
        if not isinstance(report, dict):
            logger.warning("Implementation report is not a dictionary, creating default structure")
            report = {}
        
        # Ensure the report has the required keys
        if "status" not in report:
            report["status"] = "completed"
        
        if "files_modified" not in report:
            report["files_modified"] = []
        
        if "implementation_notes" not in report:
            report["implementation_notes"] = []
        
        if "timestamp" not in report:
            from datetime import datetime
            report["timestamp"] = datetime.now().isoformat()
        
        return report
    
    def _validate_review_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure the review report has the required structure.
        
        Args:
            report (Dict[str, Any]): The report to validate
            
        Returns:
            Dict[str, Any]: The validated report
        """
        # Ensure the report is a dictionary
        if not isinstance(report, dict):
            logger.warning("Review report is not a dictionary, creating default structure")
            report = {}
        
        # Ensure the report has the required keys
        if "status" not in report:
            report["status"] = "completed"
        
        if "issues" not in report:
            report["issues"] = []
        
        if "recommendations" not in report:
            report["recommendations"] = []
        
        if "timestamp" not in report:
            from datetime import datetime
            report["timestamp"] = datetime.now().isoformat()
        
        return report
    
    def _validate_fix_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure the fix report has the required structure.
        
        Args:
            report (Dict[str, Any]): The report to validate
            
        Returns:
            Dict[str, Any]: The validated report
        """
        # Ensure the report is a dictionary
        if not isinstance(report, dict):
            logger.warning("Fix report is not a dictionary, creating default structure")
            report = {}
        
        # Ensure the report has the required keys
        if "status" not in report:
            report["status"] = "completed"
        
        if "fixed_issues" not in report:
            report["fixed_issues"] = []
        
        if "unfixed_issues" not in report:
            report["unfixed_issues"] = []
        
        if "notes" not in report:
            report["notes"] = []
        
        if "timestamp" not in report:
            from datetime import datetime
            report["timestamp"] = datetime.now().isoformat()
        
        return report 