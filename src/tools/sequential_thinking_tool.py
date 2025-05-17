import os
import json
import requests
from typing import Dict, Any, Optional, Type, List
from pydantic import BaseModel, Field

from crewai.tools import BaseTool
from src.config.config import SEQ_THINKING_MCP_URL
from src.utils.logging_utils import setup_logger

logger = setup_logger(__name__)

class SequentialThinkingInput(BaseModel):
    """Input for the Sequential Thinking Tool."""
    problem: str = Field(..., description="The problem or question to analyze.")
    context: str = Field("", description="Additional context or background information.")
    max_steps: int = Field(5, description="Maximum number of thinking steps to generate.")

class SequentialThinkingTool(BaseTool):
    """
    Tool to perform methodical, step-by-step analysis using the Sequential Thinking MCP.
    """
    
    name: str = "sequential_thinking"
    description: str = "Analyze problems through a structured, step-by-step thinking process."
    args_schema: Type[BaseModel] = SequentialThinkingInput
    
    def _run(self, problem: str, context: str = "", max_steps: int = 5) -> str:
        """
        Execute the Sequential Thinking process.
        
        Args:
            problem (str): The problem or question to analyze
            context (str): Additional context or background information
            max_steps (int): Maximum number of thinking steps to generate
            
        Returns:
            str: The analysis result
        """
        try:
            # Ensure valid parameter values
            max_steps = min(max(max_steps, 1), 10)  # between 1 and 10
            
            # Call the Sequential Thinking MCP
            response = self._call_sequential_thinking_mcp(problem, context, max_steps)
            
            # Format the results
            formatted_results = self._format_results(response)
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error executing Sequential Thinking: {str(e)}")
            return f"Error during analysis: {str(e)}"
    
    def _call_sequential_thinking_mcp(self, problem: str, context: str, max_steps: int) -> Dict[str, Any]:
        """
        Call the Sequential Thinking MCP server.
        
        Args:
            problem (str): The problem or question to analyze
            context (str): Additional context or background information
            max_steps (int): Maximum number of thinking steps to generate
            
        Returns:
            Dict[str, Any]: The response from the MCP server
        """
        try:
            mcp_endpoint = f"{SEQ_THINKING_MCP_URL}/think"
            payload = {
                "problem": problem,
                "context": context,
                "max_steps": max_steps
            }
            
            response = requests.post(mcp_endpoint, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error calling Sequential Thinking MCP: {str(e)}")
            # If MCP fails, perform a simple step-by-step analysis
            return self._fallback_analysis(problem, context, max_steps)
    
    def _fallback_analysis(self, problem: str, context: str, max_steps: int) -> Dict[str, Any]:
        """
        Fallback method if the MCP server is unavailable.
        Performs a simple step-by-step analysis.
        
        Args:
            problem (str): The problem or question to analyze
            context (str): Additional context or background information
            max_steps (int): Maximum number of thinking steps to generate
            
        Returns:
            Dict[str, Any]: A structured analysis result
        """
        logger.warning("Using fallback analysis method")
        
        # In a real implementation, this would use the LLM to generate steps
        # For now, we'll just return a simple structure
        steps = [
            {
                "step_number": 1,
                "thought": f"First, let's understand the problem: {problem}"
            }
        ]
        
        if context:
            steps.append({
                "step_number": 2,
                "thought": f"Considering the context: {context}"
            })
        
        steps.append({
            "step_number": len(steps) + 1,
            "thought": "Without the Sequential Thinking MCP, I can't perform a thorough analysis. "
                      "Please ensure the MCP server is properly configured and running."
        })
        
        return {
            "problem": problem,
            "steps": steps,
            "conclusion": "Analysis incomplete due to unavailable MCP server."
        }
    
    def _format_results(self, response: Dict[str, Any]) -> str:
        """
        Format the analysis results in a readable format.
        
        Args:
            response (Dict[str, Any]): The response from the MCP
            
        Returns:
            str: Formatted analysis results
        """
        if not response or "steps" not in response or not response["steps"]:
            return "No analysis results available."
        
        steps = response.get("steps", [])
        conclusion = response.get("conclusion", "No conclusion provided.")
        
        formatted_results = "## Sequential Thinking Analysis\n\n"
        
        for step in steps:
            step_number = step.get("step_number", "?")
            thought = step.get("thought", "No thought provided.")
            
            formatted_results += f"### Step {step_number}:\n"
            formatted_results += f"{thought}\n\n"
        
        formatted_results += "### Conclusion:\n"
        formatted_results += f"{conclusion}\n"
        
        return formatted_results 