import os
from typing import Dict, List, Any, Optional, Union
import json
from pathlib import Path

from crewai.tasks import Task

from src.agents.base_agent import BaseAgent
from src.tools.brave_search_tool import BraveSearchTool
from src.tools.context7_tool import Context7Tool
from src.utils.logging_utils import setup_logger
from src.utils.memory_utils import MemoryManager
from src.utils.file_utils import file_lock

logger = setup_logger(__name__)

class QualitatorAgent(BaseAgent):
    """
    Qualitator Agent: Ensures code quality and alignment with requirements through
    comprehensive review.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the Qualitator Agent.
        
        Args:
            **kwargs: Additional arguments to pass to the base agent
        """
        # Set default role, goal, and backstory
        role = "Quality Assurance Engineer"
        goal = "Ensure code quality and alignment with requirements through comprehensive review."
        backstory = (
            "You are a senior QA engineer with exceptional attention to detail and a deep understanding "
            "of software architecture and best practices. You've spent years developing expertise in code "
            "review, performance optimization, and security analysis. You excel at identifying subtle bugs, "
            "design flaws, and edge cases that others miss. Your thoroughness and commitment to quality "
            "have prevented countless production issues. You are well-versed in industry standards and "
            "have a talent for ensuring code not only works correctly but is also maintainable, secure, "
            "and aligned with business requirements."
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
        self.add_tool(Context7Tool())
        
        # Initialize memory manager
        self.memory = MemoryManager(self.id)
    
    def run(self, task: Dict[str, Any], implementation_report: Dict[str, Any], task_files: List[str]) -> Dict[str, Any]:
        """
        Review a completed task and its implementation.
        
        Args:
            task (Dict[str, Any]): The task that was implemented
            implementation_report (Dict[str, Any]): Report of the implementation
            task_files (List[str]): Paths to files related to the task
            
        Returns:
            Dict[str, Any]: Review results including approval status and any issues
        """
        logger.info(f"Qualitator Agent starting review of task {task.get('id', 'unknown')}...")
        
        # Store the task and implementation report in memory
        self.memory.add_to_short_term(
            {"content": json.dumps(task, indent=2), "type": "task_to_review"},
            category="input"
        )
        self.memory.add_to_short_term(
            {"content": json.dumps(implementation_report, indent=2), "type": "implementation_report"},
            category="input"
        )
        
        # Create a task for the agent to perform
        review_task = Task(
            description=(
                f"Review the following task implementation to ensure code quality and alignment with requirements:\n\n"
                f"Task:\n{json.dumps(task, indent=2)}\n\n"
                f"Implementation Report:\n{json.dumps(implementation_report, indent=2)}\n\n"
                f"Files to review:\n{', '.join(task_files)}\n\n"
                f"Follow these steps:\n"
                f"1. Analyze the original task requirements\n"
                f"2. Check the implementation against the requirements\n"
                f"3. Review the code for quality, efficiency, and best practices\n"
                f"4. Verify proper error handling and edge case coverage\n"
                f"5. Check for any security vulnerabilities\n"
                f"6. Identify any areas for improvement\n"
                f"7. Determine if the implementation meets the requirements and can be approved\n"
                f"8. Return a comprehensive review report with approval status and any issues"
            ),
            expected_output=(
                "A comprehensive review report in JSON format with approval status and any issues."
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
            {"content": json.dumps(review_report, indent=2), "type": "review_report"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Update the report with task ID
        review_report["task_id"] = task["id"]
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=4)
        
        logger.info(f"Qualitator Agent completed review of task {task.get('id', 'unknown')} with approval status: {review_report.get('approved', False)}")
        return review_report
    
    def verify_fix(self, task: Dict[str, Any], issues: List[Dict[str, Any]], fix_report: Dict[str, Any], task_files: List[str]) -> Dict[str, Any]:
        """
        Verify fixes applied to issues identified in a previous review.
        
        Args:
            task (Dict[str, Any]): The original task
            issues (List[Dict[str, Any]]): The issues that were identified
            fix_report (Dict[str, Any]): Report of the fixes applied
            task_files (List[str]): Paths to files related to the task
            
        Returns:
            Dict[str, Any]: Verification results including fixed status and any remaining issues
        """
        logger.info(f"Qualitator Agent starting verification of fixes for task {task.get('id', 'unknown')}...")
        
        # Store the task, issues, and fix report in memory
        self.memory.add_to_short_term(
            {"content": json.dumps(task, indent=2), "type": "task"},
            category="input"
        )
        self.memory.add_to_short_term(
            {"content": json.dumps(issues, indent=2), "type": "issues"},
            category="input"
        )
        self.memory.add_to_short_term(
            {"content": json.dumps(fix_report, indent=2), "type": "fix_report"},
            category="input"
        )
        
        # Create a task for the agent to perform
        verification_task = Task(
            description=(
                f"Verify that the issues identified in the previous review have been properly fixed:\n\n"
                f"Task:\n{json.dumps(task, indent=2)}\n\n"
                f"Original Issues:\n{json.dumps(issues, indent=2)}\n\n"
                f"Fix Report:\n{json.dumps(fix_report, indent=2)}\n\n"
                f"Files to verify:\n{', '.join(task_files)}\n\n"
                f"Follow these steps:\n"
                f"1. Review each original issue and the claimed fix\n"
                f"2. Verify that each issue has been properly addressed in the code\n"
                f"3. Check that no new issues have been introduced by the fixes\n"
                f"4. Determine if all issues have been satisfactorily resolved\n"
                f"5. If any issues remain, provide detailed feedback\n"
                f"6. Return a comprehensive verification report with status and any remaining issues"
            ),
            expected_output=(
                "A comprehensive verification report in JSON format with fix status and any remaining issues."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(verification_task)
        
        # Extract the verification report from the response
        verification_report = self._extract_json(result)
        
        # Ensure the verification report has the required structure
        verification_report = self._validate_verification_report(verification_report)
        
        # Store the verification report in memory
        self.memory.add_to_long_term(
            {"content": json.dumps(verification_report, indent=2), "type": "verification_report"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Update the report with task ID
        verification_report["task_id"] = task["id"]
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=4)
        
        logger.info(f"Qualitator Agent completed verification of fixes for task {task.get('id', 'unknown')} with all fixed status: {verification_report.get('all_fixed', False)}")
        return verification_report
    
    def perform_security_audit(self, files: List[str], audit_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a comprehensive security audit on the specified files.
        
        Args:
            files (List[str]): Paths to files to audit
            audit_criteria (Dict[str, Any]): Criteria for the security audit
            
        Returns:
            Dict[str, Any]: Audit results including vulnerabilities found and recommendations
        """
        logger.info(f"Qualitator Agent starting security audit of {len(files)} files...")
        
        # Store the audit request in memory
        self.memory.add_to_short_term(
            {
                "content": f"Security audit request for files: {', '.join(files)}",
                "type": "security_audit_request"
            },
            category="input"
        )
        self.memory.add_to_short_term(
            {"content": json.dumps(audit_criteria, indent=2), "type": "audit_criteria"},
            category="input"
        )
        
        # Create a task for the agent to perform
        audit_task = Task(
            description=(
                f"Perform a comprehensive security audit on the following files:\n\n"
                f"Files to audit:\n{', '.join(files)}\n\n"
                f"Audit criteria:\n{json.dumps(audit_criteria, indent=2)}\n\n"
                f"Follow these steps:\n"
                f"1. Examine each file for security vulnerabilities (OWASP Top 10, etc.)\n"
                f"2. Check for insecure code patterns\n"
                f"3. Identify potential injection points\n"
                f"4. Verify proper authentication and authorization\n"
                f"5. Check for sensitive data exposure\n"
                f"6. Verify secure communication protocols\n"
                f"7. Assess error handling for security implications\n"
                f"8. Return a comprehensive security audit report with vulnerabilities and recommendations"
            ),
            expected_output=(
                "A comprehensive security audit report in JSON format with vulnerabilities and recommendations."
            ),
            agent=self.agent
        )
        
        # Execute the task
        result = self.agent.execute_task(audit_task)
        
        # Extract the audit report from the response
        audit_report = self._extract_json(result)
        
        # Ensure the audit report has the required structure
        audit_report = self._validate_audit_report(audit_report)
        
        # Store the audit report in memory
        self.memory.add_to_long_term(
            {"content": json.dumps(audit_report, indent=2), "type": "security_audit_report"},
            category="output",
            importance=5  # Highest importance
        )
        
        # Transfer all short-term memory to long-term
        self.memory.transfer_short_to_long_term(importance=4)
        
        logger.info(f"Qualitator Agent completed security audit with {len(audit_report.get('vulnerabilities', []))} vulnerabilities found")
        return audit_report
    
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
        if "approved" not in report:
            report["approved"] = False
        
        if "issues" not in report:
            report["issues"] = []
        
        if "feedback" not in report:
            report["feedback"] = []
        
        if "timestamp" not in report:
            from datetime import datetime
            report["timestamp"] = datetime.now().isoformat()
        
        return report
    
    def _validate_verification_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure the verification report has the required structure.
        
        Args:
            report (Dict[str, Any]): The report to validate
            
        Returns:
            Dict[str, Any]: The validated report
        """
        # Ensure the report is a dictionary
        if not isinstance(report, dict):
            logger.warning("Verification report is not a dictionary, creating default structure")
            report = {}
        
        # Ensure the report has the required keys
        if "all_fixed" not in report:
            report["all_fixed"] = False
        
        if "fixed_issues" not in report:
            report["fixed_issues"] = []
        
        if "remaining_issues" not in report:
            report["remaining_issues"] = []
        
        if "feedback" not in report:
            report["feedback"] = []
        
        if "timestamp" not in report:
            from datetime import datetime
            report["timestamp"] = datetime.now().isoformat()
        
        return report
    
    def _validate_audit_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure the audit report has the required structure.
        
        Args:
            report (Dict[str, Any]): The report to validate
            
        Returns:
            Dict[str, Any]: The validated report
        """
        # Ensure the report is a dictionary
        if not isinstance(report, dict):
            logger.warning("Audit report is not a dictionary, creating default structure")
            report = {}
        
        # Ensure the report has the required keys
        if "vulnerabilities" not in report:
            report["vulnerabilities"] = []
        
        if "recommendations" not in report:
            report["recommendations"] = []
        
        if "risk_level" not in report:
            # Default to "medium" if not specified
            report["risk_level"] = "medium"
        
        if "timestamp" not in report:
            from datetime import datetime
            report["timestamp"] = datetime.now().isoformat()
        
        return report 