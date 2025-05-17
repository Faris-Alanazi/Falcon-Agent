import os
import time
import uuid
import json
import fcntl
import signal
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timedelta

from src.config.config import FILE_LOCK_DIR, FILE_LOCK_TIMEOUT
from src.utils.logging_utils import setup_logger

logger = setup_logger(__name__)

class FileLockException(Exception):
    """Exception raised for file locking errors."""
    pass

class FileLock:
    """
    File locking mechanism to prevent concurrent access to files.
    Provides both exclusive locks for writing and shared locks for reading.
    """
    
    def __init__(self, file_path, owner_id, timeout=FILE_LOCK_TIMEOUT):
        """
        Initialize a FileLock.
        
        Args:
            file_path (str or Path): Path to the file to be locked
            owner_id (str): Identifier of the agent locking the file
            timeout (int): Lock timeout in seconds
        """
        self.file_path = Path(file_path).resolve()
        self.owner_id = owner_id
        self.timeout = timeout
        self.lock_file_path = self._get_lock_file_path()
        self.lock_data = None
        self.locked = False
    
    def _get_lock_file_path(self):
        """Get the path to the lock file for the target file."""
        file_hash = str(hash(str(self.file_path)))
        return FILE_LOCK_DIR / f"{file_hash}.lock"
    
    def acquire(self, exclusive=True):
        """
        Acquire a lock on the file.
        
        Args:
            exclusive (bool): If True, acquire an exclusive (write) lock,
                             otherwise acquire a shared (read) lock.
        
        Returns:
            bool: True if lock was successfully acquired, False otherwise.
            
        Raises:
            FileLockException: If the file is already locked by another agent
                              and the lock has not expired.
        """
        # Create lock file if it doesn't exist
        self.lock_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.lock_file_path.exists():
            with open(self.lock_file_path, 'w') as f:
                f.write("{}")
        
        # Check if the file is already locked
        try:
            with open(self.lock_file_path, 'r+') as f:
                # Try to get an exclusive lock on the lock file itself
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
                
                # Check if there's an existing lock
                if str(self.file_path) in data:
                    lock_info = data[str(self.file_path)]
                    
                    # Check if the lock has expired
                    lock_time = datetime.fromisoformat(lock_info["time"])
                    expires_at = lock_time + timedelta(seconds=lock_info["timeout"])
                    
                    if datetime.now() < expires_at:
                        # Lock has not expired
                        if lock_info["owner_id"] != self.owner_id:
                            # If another agent has the lock
                            if exclusive or lock_info["exclusive"]:
                                # If we want an exclusive lock or the existing lock is exclusive
                                error_msg = f"File {self.file_path} is locked by {lock_info['owner_id']} until {expires_at}"
                                logger.warning(error_msg)
                                raise FileLockException(error_msg)
                    else:
                        # Lock has expired, we can take it
                        logger.info(f"Lock on {self.file_path} has expired, acquiring new lock")
                
                # Create/Update the lock
                self.lock_data = {
                    "owner_id": self.owner_id,
                    "time": datetime.now().isoformat(),
                    "timeout": self.timeout,
                    "exclusive": exclusive
                }
                
                data[str(self.file_path)] = self.lock_data
                
                # Write the updated lock data
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2)
                
                self.locked = True
                logger.info(f"{'Exclusive' if exclusive else 'Shared'} lock acquired on {self.file_path} by {self.owner_id}")
                return True
                
        except IOError:
            # Could not get a lock on the lock file
            error_msg = f"Could not acquire lock on {self.file_path}, lock file is busy"
            logger.error(error_msg)
            raise FileLockException(error_msg)
    
    def release(self):
        """
        Release the lock on the file.
        
        Returns:
            bool: True if lock was successfully released, False otherwise.
        """
        if not self.locked:
            return False
        
        try:
            with open(self.lock_file_path, 'r+') as f:
                # Try to get an exclusive lock on the lock file itself
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
                
                # Remove the lock if it belongs to us
                if str(self.file_path) in data:
                    lock_info = data[str(self.file_path)]
                    if lock_info["owner_id"] == self.owner_id:
                        del data[str(self.file_path)]
                        
                        # Write the updated lock data
                        f.seek(0)
                        f.truncate()
                        json.dump(data, f, indent=2)
                        
                        self.locked = False
                        logger.info(f"Lock released on {self.file_path} by {self.owner_id}")
                        return True
                    else:
                        error_msg = f"Cannot release lock on {self.file_path}, it is owned by {lock_info['owner_id']}"
                        logger.warning(error_msg)
                        return False
                else:
                    # Lock doesn't exist
                    self.locked = False
                    return True
                    
        except IOError:
            error_msg = f"Could not release lock on {self.file_path}, lock file is busy"
            logger.error(error_msg)
            return False
    
    def is_locked(self, by_owner=None):
        """
        Check if the file is locked.
        
        Args:
            by_owner (str, optional): Check if the file is locked by a specific owner.
            
        Returns:
            bool: True if the file is locked (by the specified owner if provided),
                 False otherwise.
        """
        try:
            with open(self.lock_file_path, 'r') as f:
                # Try to get a shared lock on the lock file
                fcntl.flock(f, fcntl.LOCK_SH | fcntl.LOCK_NB)
                
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    return False
                
                if str(self.file_path) in data:
                    lock_info = data[str(self.file_path)]
                    
                    # Check if the lock has expired
                    lock_time = datetime.fromisoformat(lock_info["time"])
                    expires_at = lock_time + timedelta(seconds=lock_info["timeout"])
                    
                    if datetime.now() < expires_at:
                        # Lock has not expired
                        if by_owner is None or lock_info["owner_id"] == by_owner:
                            return True
                
                return False
                
        except (IOError, FileNotFoundError):
            return False
    
    def __enter__(self):
        """Enter context manager, acquire the lock."""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, release the lock."""
        self.release()


@contextmanager
def file_lock(file_path, owner_id, exclusive=True, timeout=FILE_LOCK_TIMEOUT):
    """
    Context manager for file locking.
    
    Args:
        file_path (str or Path): Path to the file to be locked
        owner_id (str): Identifier of the agent locking the file
        exclusive (bool): If True, acquire an exclusive (write) lock,
                         otherwise acquire a shared (read) lock
        timeout (int): Lock timeout in seconds
    
    Yields:
        FileLock: The file lock object
        
    Raises:
        FileLockException: If the file is already locked and the lock
                          has not expired.
    """
    lock = FileLock(file_path, owner_id, timeout)
    try:
        lock.acquire(exclusive=exclusive)
        yield lock
    finally:
        lock.release()


def get_active_locks():
    """
    Get a dictionary of all active locks.
    
    Returns:
        dict: A dictionary mapping file paths to lock information
    """
    active_locks = {}
    
    # Check all lock files in the lock directory
    for lock_file in FILE_LOCK_DIR.glob("*.lock"):
        try:
            with open(lock_file, 'r') as f:
                # Try to get a shared lock on the lock file
                fcntl.flock(f, fcntl.LOCK_SH | fcntl.LOCK_NB)
                
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    continue
                
                now = datetime.now()
                
                # Check each lock in the file
                for file_path, lock_info in data.items():
                    try:
                        lock_time = datetime.fromisoformat(lock_info["time"])
                        expires_at = lock_time + timedelta(seconds=lock_info["timeout"])
                        
                        # Only include non-expired locks
                        if now < expires_at:
                            active_locks[file_path] = {
                                "owner_id": lock_info["owner_id"],
                                "time": lock_time.isoformat(),
                                "expires_at": expires_at.isoformat(),
                                "exclusive": lock_info["exclusive"]
                            }
                    except (KeyError, ValueError):
                        # Skip invalid lock data
                        continue
                    
        except (IOError, FileNotFoundError):
            # Skip if we can't read the lock file
            continue
    
    return active_locks 