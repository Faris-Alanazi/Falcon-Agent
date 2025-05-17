import os
from typing import Dict, List, Any, Optional, Union
import json
from pathlib import Path

from src.agents.requirementer_agent import RequirementerAgent
from src.agents.tasker_agent import TaskerAgent
from src.agents.goaler_agent import GoalerAgent
from src.agents.coder_agent import CoderAgent
from src.agents.qualitator_agent import QualitatorAgent
from src.agents.communicator_agent import CommunicatorAgent
from src.utils.logging_utils import setup_logger
from src.config.config import MODEL_CONFIGS, DEFAULT_MODEL, DATA_DIR

logger = setup_logger(__name__)

class AgentManager:
    """
    Manages the creation and coordination of all specialized agents.
    
    This class is responsible for:
    1. Creating the specialized agents
    2. Coordinating the flow of information between agents
    3. Managing the overall execution pipeline
    4. Tracking the state of the system
    """
    
    def __init__(self):
        """Initialize the agent manager."""
        # Create data directories
        self.data_dir = DATA_DIR
        self.prd_dir = self.data_dir / "prd"
        self.goal_graph_dir = self.data_dir / "goal_graphs"
        
        os.makedirs(self.prd_dir, exist_ok=True)
        os.makedirs(self.goal_graph_dir, exist_ok=True)
        
        # Initialize state
        self.state = {
            "current_stage": "initialization",
            "prd_created": False,
            "goal_graph_created": False,
            "goal_graph_approved": False,
            "tasks_assigned": {},  # dict of task_id -> agent_id
            "tasks_completed": {},  # dict of task_id -> status
            "files_modified": set(),  # set of file paths
            "agents_created": {},  # dict of agent_type -> agent_id
        }
        
        # Will be initialized later
        self.requirementer_agent = None
        self.tasker_agent = None
        self.goaler_agent = None
        self.coder_agents = []
        self.qualitator_agent = None
        self.communicator_agent = None
        
        # Load the latest PRD and Goal Graph if they exist
        self.prd = self._load_latest_prd()
        self.goal_graph = self._load_latest_goal_graph()
        
        # Update state based on loaded data
        self.state["prd_created"] = self.prd is not None
        self.state["goal_graph_created"] = self.goal_graph is not None
    
    def create_agents(self, 
                      requirementer_model: str = DEFAULT_MODEL,
                      tasker_model: str = DEFAULT_MODEL,
                      goaler_model: str = DEFAULT_MODEL,
                      coder_model: str = DEFAULT_MODEL,
                      qualitator_model: str = DEFAULT_MODEL,
                      communicator_model: str = DEFAULT_MODEL,
                      num_coder_agents: int = 3) -> None:
        """
        Create all specialized agents with the specified models.
        
        Args:
            requirementer_model (str): LLM to use for the Requirementer agent
            tasker_model (str): LLM to use for the Tasker agent
            goaler_model (str): LLM to use for the Goaler agent
            coder_model (str): LLM to use for the Coder agents
            qualitator_model (str): LLM to use for the Qualitator agent
            communicator_model (str): LLM to use for the Communicator agent
            num_coder_agents (int): Number of Coder agents to create
        """
        logger.info(f"Creating specialized agents...")
        
        # Create the Requirementer agent
        self.requirementer_agent = RequirementerAgent(
            llm=requirementer_model,
            **MODEL_CONFIGS.get(requirementer_model, {})
        )
        self.state["agents_created"]["requirementer"] = self.requirementer_agent.id
        
        # Create the Tasker agent
        self.tasker_agent = TaskerAgent(
            llm=tasker_model,
            **MODEL_CONFIGS.get(tasker_model, {})
        )
        self.state["agents_created"]["tasker"] = self.tasker_agent.id
        
        # Create the Goaler agent
        self.goaler_agent = GoalerAgent(
            llm=goaler_model,
            **MODEL_CONFIGS.get(goaler_model, {})
        )
        self.state["agents_created"]["goaler"] = self.goaler_agent.id
        
        # Create the Coder agents
        self.coder_agents = []
        for i in range(num_coder_agents):
            coder_agent = CoderAgent(
                team_id="coder_team",
                llm=coder_model,
                **MODEL_CONFIGS.get(coder_model, {})
            )
            self.coder_agents.append(coder_agent)
            self.state["agents_created"][f"coder_{i+1}"] = coder_agent.id
        
        # Create the Qualitator agent
        self.qualitator_agent = QualitatorAgent(
            llm=qualitator_model,
            **MODEL_CONFIGS.get(qualitator_model, {})
        )
        self.state["agents_created"]["qualitator"] = self.qualitator_agent.id
        
        # Create the Communicator agent
        self.communicator_agent = CommunicatorAgent(
            llm=communicator_model,
            **MODEL_CONFIGS.get(communicator_model, {})
        )
        self.state["agents_created"]["communicator"] = self.communicator_agent.id
        
        logger.info(f"Created all specialized agents successfully")
    
    def generate_prd(self, user_request: str) -> str:
        """
        Generate a Product Requirement Document from the user request.
        
        Args:
            user_request (str): The initial user request
            
        Returns:
            str: The generated PRD
        """
        logger.info(f"Generating PRD from user request...")
        
        # Check if Requirementer agent is initialized
        if self.requirementer_agent is None:
            raise ValueError("Requirementer agent is not initialized. Call create_agents() first.")
        
        # Update state
        self.state["current_stage"] = "generating_prd"
        
        # Generate the PRD
        self.prd = self.requirementer_agent.run(user_request)
        
        # Save the PRD
        self._save_prd(self.prd)
        
        # Update state
        self.state["prd_created"] = True
        self.state["current_stage"] = "prd_generated"
        
        logger.info(f"Generated PRD successfully")
        return self.prd
    
    def refine_prd(self, additional_input: str) -> str:
        """
        Refine the existing PRD based on additional input.
        
        Args:
            additional_input (str): Additional information or feedback
            
        Returns:
            str: The refined PRD
        """
        logger.info(f"Refining PRD with additional input...")
        
        # Check if Requirementer agent is initialized
        if self.requirementer_agent is None:
            raise ValueError("Requirementer agent is not initialized. Call create_agents() first.")
        
        # Check if PRD exists
        if self.prd is None:
            raise ValueError("No PRD exists. Call generate_prd() first.")
        
        # Update state
        self.state["current_stage"] = "refining_prd"
        
        # Refine the PRD
        self.prd = self.requirementer_agent.refine_requirements(self.prd, additional_input)
        
        # Save the PRD
        self._save_prd(self.prd)
        
        # Update state
        self.state["current_stage"] = "prd_refined"
        
        logger.info(f"Refined PRD successfully")
        return self.prd
    
    def create_goal_graph(self) -> Dict[str, Any]:
        """
        Create a Goal Graph from the PRD.
        
        Returns:
            Dict[str, Any]: The Goal Graph
        """
        logger.info(f"Creating Goal Graph from PRD...")
        
        # Check if Tasker agent is initialized
        if self.tasker_agent is None:
            raise ValueError("Tasker agent is not initialized. Call create_agents() first.")
        
        # Check if PRD exists
        if self.prd is None:
            raise ValueError("No PRD exists. Call generate_prd() first.")
        
        # Update state
        self.state["current_stage"] = "creating_goal_graph"
        
        # Create the Goal Graph
        self.goal_graph = self.tasker_agent.run(self.prd)
        
        # Update state
        self.state["goal_graph_created"] = True
        self.state["current_stage"] = "goal_graph_created"
        
        logger.info(f"Created Goal Graph successfully with {len(self.goal_graph.get('tasks', []))} tasks")
        return self.goal_graph
    
    def validate_goal_graph(self) -> Dict[str, Any]:
        """
        Validate the Goal Graph against the PRD.
        
        Returns:
            Dict[str, Any]: Validation results
        """
        logger.info(f"Validating Goal Graph against PRD...")
        
        # Check if Goaler agent is initialized
        if self.goaler_agent is None:
            raise ValueError("Goaler agent is not initialized. Call create_agents() first.")
        
        # Check if PRD and Goal Graph exist
        if self.prd is None:
            raise ValueError("No PRD exists. Call generate_prd() first.")
        if self.goal_graph is None:
            raise ValueError("No Goal Graph exists. Call create_goal_graph() first.")
        
        # Update state
        self.state["current_stage"] = "validating_goal_graph"
        
        # Validate the Goal Graph
        validation_results = self.goaler_agent.run(self.prd, self.goal_graph)
        
        # Update state
        self.state["current_stage"] = "goal_graph_validated"
        
        # If approved, update the approval status
        if validation_results.get("approved", False):
            self.state["goal_graph_approved"] = True
        
        logger.info(f"Validated Goal Graph with approval status: {validation_results.get('approved', False)}")
        return validation_results
    
    def update_goal_graph(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the Goal Graph based on validation results.
        
        Args:
            validation_results (Dict[str, Any]): Results from the validation
            
        Returns:
            Dict[str, Any]: The updated Goal Graph
        """
        logger.info(f"Updating Goal Graph based on validation results...")
        
        # Check if Tasker agent is initialized
        if self.tasker_agent is None:
            raise ValueError("Tasker agent is not initialized. Call create_agents() first.")
        
        # Check if Goal Graph exists
        if self.goal_graph is None:
            raise ValueError("No Goal Graph exists. Call create_goal_graph() first.")
        
        # Extract feedback from validation results
        issues = validation_results.get("issues", [])
        feedback = validation_results.get("feedback", [])
        
        # Format the updates as a string
        updates = "Updates needed:\n\n"
        
        # Add issues
        if issues:
            updates += "Issues to address:\n"
            for i, issue in enumerate(issues, 1):
                issue_type = issue.get("type", "unknown")
                description = issue.get("description", "No description provided")
                updates += f"{i}. Issue ({issue_type}): {description}\n"
            updates += "\n"
        
        # Add feedback
        if feedback:
            updates += "Feedback to incorporate:\n"
            for i, item in enumerate(feedback, 1):
                updates += f"{i}. {item}\n"
            updates += "\n"
        
        # Update state
        self.state["current_stage"] = "updating_goal_graph"
        
        # Update the Goal Graph
        self.goal_graph = self.tasker_agent.update_goal_graph(self.goal_graph, updates)
        
        # Update state
        self.state["current_stage"] = "goal_graph_updated"
        
        logger.info(f"Updated Goal Graph successfully with {len(self.goal_graph.get('tasks', []))} tasks")
        return self.goal_graph
    
    def approve_goal_graph(self) -> Dict[str, Any]:
        """
        Approve the Goal Graph for implementation.
        
        Returns:
            Dict[str, Any]: Approval status and any notes
        """
        logger.info(f"Approving Goal Graph for implementation...")
        
        # Check if Goaler agent is initialized
        if self.goaler_agent is None:
            raise ValueError("Goaler agent is not initialized. Call create_agents() first.")
        
        # Check if Goal Graph exists
        if self.goal_graph is None:
            raise ValueError("No Goal Graph exists. Call create_goal_graph() first.")
        
        # Update state
        self.state["current_stage"] = "approving_goal_graph"
        
        # Approve the Goal Graph
        approval_doc = self.goaler_agent.approve_goal_graph(self.goal_graph)
        
        # Update state
        if approval_doc.get("approved", False):
            self.state["goal_graph_approved"] = True
            self.state["current_stage"] = "goal_graph_approved"
        else:
            self.state["current_stage"] = "goal_graph_approval_failed"
        
        logger.info(f"Goal Graph approval status: {approval_doc.get('approved', False)}")
        return approval_doc
    
    def assign_tasks(self) -> Dict[str, List[str]]:
        """
        Assign tasks from the Goal Graph to Coder agents.
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping agent IDs to lists of assigned task IDs
        """
        logger.info(f"Assigning tasks to Coder agents...")
        
        # Check if Coder agents are initialized
        if not self.coder_agents:
            raise ValueError("No Coder agents are initialized. Call create_agents() first.")
        
        # Check if Goal Graph exists and is approved
        if self.goal_graph is None:
            raise ValueError("No Goal Graph exists. Call create_goal_graph() first.")
        if not self.state.get("goal_graph_approved", False):
            raise ValueError("Goal Graph is not approved. Call approve_goal_graph() first.")
        
        # Get the tasks from the Goal Graph
        tasks = self.goal_graph.get("tasks", [])
        
        # Filter for tasks that are not assigned and don't have dependencies
        # or all dependencies are completed
        available_tasks = []
        for task in tasks:
            task_id = task.get("id")
            status = task.get("status", "Not Started")
            dependencies = task.get("dependencies", [])
            
            # Skip if already assigned or completed
            if task_id in self.state["tasks_assigned"] or status == "Completed":
                continue
            
            # Check if all dependencies are completed
            all_deps_completed = True
            for dep_id in dependencies:
                dep_status = self.state["tasks_completed"].get(dep_id)
                if dep_status != "Completed":
                    all_deps_completed = False
                    break
            
            # If no dependencies or all dependencies are completed, add to available tasks
            if not dependencies or all_deps_completed:
                available_tasks.append(task)
        
        # Sort available tasks by priority
        priority_map = {"High": 3, "Medium": 2, "Low": 1}
        available_tasks.sort(key=lambda t: (priority_map.get(t.get("priority", "Medium"), 0), -len(t.get("dependencies", []))))
        
        # Initialize assignment dictionary
        assignments = {agent.id: [] for agent in self.coder_agents}
        
        # Assign tasks to agents (simple round-robin for now)
        for i, task in enumerate(available_tasks):
            agent_idx = i % len(self.coder_agents)
            agent_id = self.coder_agents[agent_idx].id
            task_id = task.get("id")
            
            # Assign task
            assignments[agent_id].append(task_id)
            self.state["tasks_assigned"][task_id] = agent_id
            task["owner"] = agent_id
            task["status"] = "In Progress"
        
        # Update state
        self.state["current_stage"] = "tasks_assigned"
        
        logger.info(f"Assigned {len(available_tasks)} tasks to {len(self.coder_agents)} Coder agents")
        return assignments
    
    def implement_task(self, task_id: str, file_access: List[str]) -> Dict[str, Any]:
        """
        Implement a task using the assigned Coder agent.
        
        Args:
            task_id (str): ID of the task to implement
            file_access (List[str]): Paths to files the agent can access
            
        Returns:
            Dict[str, Any]: Implementation results
        """
        logger.info(f"Implementing task {task_id}...")
        
        # Check if the task is assigned
        if task_id not in self.state["tasks_assigned"]:
            raise ValueError(f"Task {task_id} is not assigned. Call assign_tasks() first.")
        
        # Get the assigned agent
        agent_id = self.state["tasks_assigned"][task_id]
        agent = None
        for coder in self.coder_agents:
            if coder.id == agent_id:
                agent = coder
                break
        
        if agent is None:
            raise ValueError(f"No Coder agent found with ID {agent_id}")
        
        # Get the task from the Goal Graph
        task = None
        for t in self.goal_graph.get("tasks", []):
            if str(t.get("id")) == str(task_id):
                task = t
                break
        
        if task is None:
            raise ValueError(f"No task found with ID {task_id} in the Goal Graph")
        
        # Update state
        self.state["current_stage"] = f"implementing_task_{task_id}"
        
        # Implement the task
        implementation_results = agent.run(task, file_access)
        
        # Update modified files
        modified_files = implementation_results.get("files_modified", [])
        self.state["files_modified"].update(modified_files)
        
        # Update state
        self.state["tasks_completed"][task_id] = "Needs Review"
        task["status"] = "Needs Review"
        self.state["current_stage"] = f"task_{task_id}_implemented"
        
        logger.info(f"Implemented task {task_id} with status: {implementation_results.get('status', 'unknown')}")
        return implementation_results
    
    def review_task(self, task_id: str, implementation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review a completed task using the Qualitator agent.
        
        Args:
            task_id (str): ID of the task to review
            implementation_results (Dict[str, Any]): Results from the implementation
            
        Returns:
            Dict[str, Any]: Review results
        """
        logger.info(f"Reviewing task {task_id}...")
        
        # Check if Qualitator agent is initialized
        if self.qualitator_agent is None:
            raise ValueError("Qualitator agent is not initialized. Call create_agents() first.")
        
        # Check if the task is completed
        if self.state["tasks_completed"].get(task_id) != "Needs Review":
            raise ValueError(f"Task {task_id} is not ready for review.")
        
        # Get the task from the Goal Graph
        task = None
        for t in self.goal_graph.get("tasks", []):
            if str(t.get("id")) == str(task_id):
                task = t
                break
        
        if task is None:
            raise ValueError(f"No task found with ID {task_id} in the Goal Graph")
        
        # Get the file paths from the implementation results
        task_files = implementation_results.get("files_modified", [])
        
        # Update state
        self.state["current_stage"] = f"reviewing_task_{task_id}"
        
        # Review the task
        review_results = self.qualitator_agent.run(task, implementation_results, task_files)
        
        # Update state based on review results
        if review_results.get("approved", False):
            self.state["tasks_completed"][task_id] = "Completed"
            task["status"] = "Completed"
            self.state["current_stage"] = f"task_{task_id}_completed"
        else:
            self.state["tasks_completed"][task_id] = "Needs Fixes"
            task["status"] = "Needs Fixes"
            self.state["current_stage"] = f"task_{task_id}_needs_fixes"
        
        logger.info(f"Reviewed task {task_id} with approval status: {review_results.get('approved', False)}")
        return review_results
    
    def fix_task(self, task_id: str, review_results: Dict[str, Any], file_access: List[str]) -> Dict[str, Any]:
        """
        Fix issues identified in a task review.
        
        Args:
            task_id (str): ID of the task to fix
            review_results (Dict[str, Any]): Results from the review
            file_access (List[str]): Paths to files the agent can access
            
        Returns:
            Dict[str, Any]: Results of the fixes
        """
        logger.info(f"Fixing task {task_id}...")
        
        # Check if the task needs fixes
        if self.state["tasks_completed"].get(task_id) != "Needs Fixes":
            raise ValueError(f"Task {task_id} does not need fixes.")
        
        # Get the assigned agent
        agent_id = self.state["tasks_assigned"][task_id]
        agent = None
        for coder in self.coder_agents:
            if coder.id == agent_id:
                agent = coder
                break
        
        if agent is None:
            raise ValueError(f"No Coder agent found with ID {agent_id}")
        
        # Get the issues from the review results
        issues = review_results.get("issues", [])
        
        # Update state
        self.state["current_stage"] = f"fixing_task_{task_id}"
        
        # Fix the issues
        fix_results = agent.fix_issues(issues, file_access)
        
        # Update modified files
        modified_files = fix_results.get("files_modified", [])
        self.state["files_modified"].update(modified_files)
        
        # Update state
        self.state["tasks_completed"][task_id] = "Needs Review"
        
        # Get the task from the Goal Graph and update its status
        for t in self.goal_graph.get("tasks", []):
            if str(t.get("id")) == str(task_id):
                t["status"] = "Needs Review"
                break
        
        self.state["current_stage"] = f"task_{task_id}_fixes_implemented"
        
        logger.info(f"Fixed task {task_id} with {len(fix_results.get('fixed_issues', []))} issues fixed")
        return fix_results
    
    def verify_fixes(self, task_id: str, review_results: Dict[str, Any], fix_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify fixes applied to a task.
        
        Args:
            task_id (str): ID of the task to verify
            review_results (Dict[str, Any]): Results from the review
            fix_results (Dict[str, Any]): Results of the fixes
            
        Returns:
            Dict[str, Any]: Verification results
        """
        logger.info(f"Verifying fixes for task {task_id}...")
        
        # Check if Qualitator agent is initialized
        if self.qualitator_agent is None:
            raise ValueError("Qualitator agent is not initialized. Call create_agents() first.")
        
        # Check if the task is ready for verification
        if self.state["tasks_completed"].get(task_id) != "Needs Review":
            raise ValueError(f"Task {task_id} is not ready for verification.")
        
        # Get the task from the Goal Graph
        task = None
        for t in self.goal_graph.get("tasks", []):
            if str(t.get("id")) == str(task_id):
                task = t
                break
        
        if task is None:
            raise ValueError(f"No task found with ID {task_id} in the Goal Graph")
        
        # Get the issues from the review results
        issues = review_results.get("issues", [])
        
        # Get the file paths from the fix results
        task_files = fix_results.get("files_modified", [])
        
        # Update state
        self.state["current_stage"] = f"verifying_fixes_for_task_{task_id}"
        
        # Verify the fixes
        verification_results = self.qualitator_agent.verify_fix(task, issues, fix_results, task_files)
        
        # Update state based on verification results
        if verification_results.get("all_fixed", False):
            self.state["tasks_completed"][task_id] = "Completed"
            task["status"] = "Completed"
            self.state["current_stage"] = f"task_{task_id}_completed"
        else:
            self.state["tasks_completed"][task_id] = "Needs Fixes"
            task["status"] = "Needs Fixes"
            self.state["current_stage"] = f"task_{task_id}_needs_fixes"
        
        logger.info(f"Verified fixes for task {task_id} with all fixed status: {verification_results.get('all_fixed', False)}")
        return verification_results
    
    def create_project_summary(self) -> str:
        """
        Create a comprehensive project summary using the Communicator agent.
        
        Returns:
            str: A comprehensive project summary in markdown format
        """
        logger.info(f"Creating project summary...")
        
        # Check if Communicator agent is initialized
        if self.communicator_agent is None:
            raise ValueError("Communicator agent is not initialized. Call create_agents() first.")
        
        # Check if Goal Graph exists
        if self.goal_graph is None:
            raise ValueError("No Goal Graph exists. Call create_goal_graph() first.")
        
        # Create project summary information
        project_name = "Falcon Agent"
        project_summary = {
            "name": project_name,
            "description": "A multi-agent system for autonomous software development",
            "version": "1.0.0",
            "status": "Completed",
            "prd_summary": self.prd[:1000] + "..." if len(self.prd) > 1000 else self.prd,
        }
        
        # Get completed tasks from the Goal Graph
        completed_tasks = []
        for task in self.goal_graph.get("tasks", []):
            task_id = task.get("id")
            if self.state["tasks_completed"].get(task_id) == "Completed":
                completed_tasks.append(task)
        
        # Convert files_modified set to list
        files_changed = list(self.state["files_modified"])
        
        # Update state
        self.state["current_stage"] = "creating_project_summary"
        
        # Create the project summary
        summary = self.communicator_agent.run(project_summary, completed_tasks, files_changed)
        
        # Update state
        self.state["current_stage"] = "project_summary_created"
        
        logger.info(f"Created project summary: {len(summary)} characters")
        return summary
    
    def _save_prd(self, prd: str) -> None:
        """
        Save the PRD to disk.
        
        Args:
            prd (str): The PRD to save
        """
        timestamp = int(os.path.getmtime(self.prd_dir)) if os.path.exists(self.prd_dir) else 0
        filename = f"prd_{timestamp}.md"
        file_path = self.prd_dir / filename
        
        # Also save as latest
        latest_path = self.prd_dir / "latest.md"
        
        try:
            # Save the timestamped version
            with open(file_path, 'w') as f:
                f.write(prd)
            
            # Save as latest
            with open(latest_path, 'w') as f:
                f.write(prd)
            
            logger.info(f"PRD saved to {file_path} and {latest_path}")
            
        except Exception as e:
            logger.error(f"Error saving PRD: {e}")
    
    def _load_latest_prd(self) -> Optional[str]:
        """
        Load the latest PRD from disk.
        
        Returns:
            Optional[str]: The PRD or None if not found
        """
        latest_path = self.prd_dir / "latest.md"
        
        if not os.path.exists(latest_path):
            logger.warning(f"No PRD found at {latest_path}")
            return None
        
        try:
            with open(latest_path, 'r') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error loading PRD: {e}")
            return None
    
    def _load_latest_goal_graph(self) -> Optional[Dict[str, Any]]:
        """
        Load the latest Goal Graph from disk.
        
        Returns:
            Optional[Dict[str, Any]]: The Goal Graph or None if not found
        """
        latest_path = self.goal_graph_dir / "latest.json"
        
        if not os.path.exists(latest_path):
            logger.warning(f"No Goal Graph found at {latest_path}")
            return None
        
        try:
            with open(latest_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading Goal Graph: {e}")
            return None 