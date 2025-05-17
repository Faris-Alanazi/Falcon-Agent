import os
import json
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime

from src.config.config import DATA_DIR
from src.utils.logging_utils import setup_logger
from src.utils.file_utils import file_lock

logger = setup_logger(__name__)

class MemoryManager:
    """
    Manages both short-term and long-term memory for agents.
    Short-term memory is kept in-memory during agent execution.
    Long-term memory is persisted to disk for recall across sessions.
    """
    
    def __init__(self, agent_id: str, memory_dir: Optional[Path] = None):
        """
        Initialize the memory manager.
        
        Args:
            agent_id (str): ID of the agent
            memory_dir (Path, optional): Directory to store memory files
        """
        self.agent_id = agent_id
        
        # Set up memory directories
        self.memory_dir = memory_dir or DATA_DIR / "memories"
        self.agent_memory_dir = self.memory_dir / agent_id
        
        # Create the agent memory directory if it doesn't exist
        os.makedirs(self.agent_memory_dir, exist_ok=True)
        
        # Initialize short-term memory (in-memory)
        self.short_term_memory = []
        
        # Load long-term memory index
        self.long_term_index_path = self.agent_memory_dir / "memory_index.json"
        self.long_term_index = self._load_long_term_index()
    
    def _load_long_term_index(self) -> List[Dict[str, Any]]:
        """
        Load the long-term memory index file.
        
        Returns:
            List[Dict[str, Any]]: The memory index
        """
        if not os.path.exists(self.long_term_index_path):
            # Create an empty index file
            with file_lock(self.long_term_index_path, self.agent_id):
                with open(self.long_term_index_path, 'w') as f:
                    json.dump([], f)
            return []
        
        try:
            with file_lock(self.long_term_index_path, self.agent_id, exclusive=False):
                with open(self.long_term_index_path, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading memory index: {e}")
            return []
    
    def add_to_short_term(self, memory_item: Union[str, Dict[str, Any]], category: str = "general"):
        """
        Add an item to short-term memory.
        
        Args:
            memory_item (str or Dict): The memory item to add
            category (str): The category of the memory
        """
        if isinstance(memory_item, str):
            memory_item = {"content": memory_item}
        
        # Ensure the memory item has all required fields
        memory_entry = {
            "id": f"stm_{int(time.time())}_{len(self.short_term_memory)}",
            "timestamp": datetime.now().isoformat(),
            "category": category,
            **memory_item
        }
        
        self.short_term_memory.append(memory_entry)
        logger.debug(f"Added to short-term memory: {memory_entry['id']}")
    
    def add_to_long_term(self, memory_item: Union[str, Dict[str, Any]], category: str = "general", importance: int = 1):
        """
        Add an item to long-term memory.
        
        Args:
            memory_item (str or Dict): The memory item to add
            category (str): The category of the memory
            importance (int): Importance level (1-5)
        
        Returns:
            str: The ID of the stored memory
        """
        if isinstance(memory_item, str):
            memory_item = {"content": memory_item}
        
        # Ensure valid importance
        importance = min(max(importance, 1), 5)
        
        # Create a unique ID for this memory
        memory_id = f"ltm_{int(time.time())}_{len(self.long_term_index)}"
        
        # Create the memory entry
        memory_entry = {
            "id": memory_id,
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "importance": importance,
            **memory_item
        }
        
        # Store the memory in its own file
        memory_path = self.agent_memory_dir / f"{memory_id}.json"
        
        try:
            with file_lock(memory_path, self.agent_id):
                with open(memory_path, 'w') as f:
                    json.dump(memory_entry, f, indent=2)
            
            # Add to the index
            index_entry = {
                "id": memory_id,
                "timestamp": memory_entry["timestamp"],
                "category": category,
                "importance": importance,
                "path": str(memory_path)
            }
            
            # Add a summary if the memory item has content
            if "content" in memory_item:
                index_entry["summary"] = memory_item["content"][:200] + ("..." if len(memory_item["content"]) > 200 else "")
            
            # Update the index file
            with file_lock(self.long_term_index_path, self.agent_id):
                with open(self.long_term_index_path, 'r+') as f:
                    try:
                        index = json.load(f)
                    except json.JSONDecodeError:
                        index = []
                    
                    index.append(index_entry)
                    
                    # Write the updated index
                    f.seek(0)
                    f.truncate()
                    json.dump(index, f, indent=2)
            
            # Update the in-memory index
            self.long_term_index.append(index_entry)
            
            logger.debug(f"Added to long-term memory: {memory_id}")
            return memory_id
            
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error adding to long-term memory: {e}")
            return None
    
    def get_from_short_term(self, category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve items from short-term memory, optionally filtered by category.
        
        Args:
            category (str, optional): Filter by this category
            limit (int): Maximum number of items to retrieve
        
        Returns:
            List[Dict[str, Any]]: The memory items
        """
        # Filter by category if specified
        if category:
            filtered = [item for item in self.short_term_memory if item["category"] == category]
        else:
            filtered = self.short_term_memory.copy()
        
        # Sort by timestamp (newest first) and limit
        sorted_memories = sorted(filtered, key=lambda x: x["timestamp"], reverse=True)
        return sorted_memories[:limit]
    
    def get_from_long_term(self, category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve items from long-term memory, optionally filtered by category.
        
        Args:
            category (str, optional): Filter by this category
            limit (int): Maximum number of items to retrieve
        
        Returns:
            List[Dict[str, Any]]: The memory items
        """
        # Filter by category if specified
        if category:
            filtered = [item for item in self.long_term_index if item["category"] == category]
        else:
            filtered = self.long_term_index.copy()
        
        # Sort by importance and timestamp
        sorted_memories = sorted(
            filtered, 
            key=lambda x: (x.get("importance", 1), x["timestamp"]), 
            reverse=True
        )
        
        # Limit the number of results
        results = []
        for entry in sorted_memories[:limit]:
            try:
                memory_path = Path(entry["path"])
                with file_lock(memory_path, self.agent_id, exclusive=False):
                    with open(memory_path, 'r') as f:
                        memory_item = json.load(f)
                        results.append(memory_item)
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Error reading memory item {entry['id']}: {e}")
        
        return results
    
    def search_memory(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search both short-term and long-term memory for relevant items.
        
        Args:
            query (str): The search query
            category (str, optional): Filter by this category
            limit (int): Maximum number of items to retrieve
        
        Returns:
            List[Dict[str, Any]]: The memory items
        """
        query = query.lower()
        results = []
        
        # Search short-term memory
        for item in self.short_term_memory:
            if category and item["category"] != category:
                continue
            
            # Check if query is in content or other fields
            if self._item_matches_query(item, query):
                results.append(item)
        
        # Search long-term memory index
        for entry in self.long_term_index:
            if category and entry["category"] != category:
                continue
            
            # Check if query is in summary or other indexed fields
            if self._item_matches_query(entry, query):
                try:
                    memory_path = Path(entry["path"])
                    with file_lock(memory_path, self.agent_id, exclusive=False):
                        with open(memory_path, 'r') as f:
                            memory_item = json.load(f)
                            results.append(memory_item)
                except (IOError, json.JSONDecodeError) as e:
                    logger.error(f"Error reading memory item {entry['id']}: {e}")
        
        # Sort by timestamp (newest first) and limit
        sorted_results = sorted(results, key=lambda x: x["timestamp"], reverse=True)
        return sorted_results[:limit]
    
    def _item_matches_query(self, item: Dict[str, Any], query: str) -> bool:
        """
        Check if a memory item matches the search query.
        
        Args:
            item (Dict[str, Any]): The memory item
            query (str): The search query
        
        Returns:
            bool: True if the item matches, False otherwise
        """
        # Check in content field
        if "content" in item and query in item["content"].lower():
            return True
        
        # Check in summary field (index entries)
        if "summary" in item and query in item["summary"].lower():
            return True
        
        # Check in category
        if query in item["category"].lower():
            return True
        
        return False
    
    def clear_short_term_memory(self):
        """Clear all short-term memory."""
        self.short_term_memory = []
        logger.info(f"Cleared short-term memory for agent {self.agent_id}")
    
    def transfer_short_to_long_term(self, importance: int = 1):
        """
        Transfer all short-term memories to long-term storage.
        
        Args:
            importance (int): Importance level (1-5)
        """
        for item in self.short_term_memory:
            # Copy the item without its short-term specific fields
            memory_item = item.copy()
            memory_item.pop("id", None)  # Remove short-term ID
            
            # Add to long-term memory
            self.add_to_long_term(
                memory_item, 
                category=item["category"], 
                importance=importance
            )
        
        # Clear short-term memory
        self.clear_short_term_memory()
        logger.info(f"Transferred short-term memory to long-term storage for agent {self.agent_id}")
    
    def summarize_memory(self, category: Optional[str] = None, timeframe: Optional[str] = None) -> str:
        """
        Generate a summary of important memories.
        
        Args:
            category (str, optional): Filter by this category
            timeframe (str, optional): Timeframe to summarize (e.g., "today", "week")
            
        Returns:
            str: Summary of memories
        """
        # For now, just return a simple summary
        # In a real implementation, this would use the LLM to generate a summary
        
        st_count = len(self.get_from_short_term(category=category))
        lt_count = len(self.get_from_long_term(category=category))
        
        return (
            f"Memory Summary for agent {self.agent_id}:\n"
            f"- {st_count} items in short-term memory"
            f"{f' (category: {category})' if category else ''}\n"
            f"- {lt_count} items in long-term memory"
            f"{f' (category: {category})' if category else ''}\n"
        ) 