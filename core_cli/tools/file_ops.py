"""
File Operations Tool - Safely manages file creation, updates, and backups.

Provides controlled file system operations with:
- Safe file writing (no accidental overwrites)
- Automatic backups before changes
- Directory structure creation
- Git integration (optional)
- Permission handling
"""

import os
import shutil
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class FileOpsError(Exception):
    """File operations error."""
    pass


class FileOperations:
    """Manages file creation and updates with safety mechanisms."""
    
    def __init__(self, project_root: str, backup_dir: Optional[str] = None):
        """
        Initialize file operations manager.
        
        Args:
            project_root: Root directory of the project
            backup_dir: Optional backup directory (defaults to .backups in project)
        """
        self.project_root = Path(project_root)
        self.backup_dir = Path(backup_dir) if backup_dir else self.project_root / ".backups"
        self.created_files: List[str] = []
        self.modified_files: List[str] = []
        self.change_log: List[Dict] = []
        
        # Ensure project root exists
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_file(
        self,
        relative_path: str,
        content: str,
        force_overwrite: bool = False,
        description: str = ""
    ) -> Tuple[bool, str]:
        """
        Create a new file safely.
        
        Args:
            relative_path: Path relative to project root (e.g., "src/main.py")
            content: File content to write
            force_overwrite: If True, overwrite existing files
            description: Description of what this file does
            
        Returns:
            Tuple of (success, message)
        """
        try:
            full_path = self.project_root / relative_path
            
            # Ensure parent directories exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists
            if full_path.exists() and not force_overwrite:
                error_msg = f"File already exists: {relative_path}. Use force_overwrite=True to replace."
                logger.warning(error_msg)
                return False, error_msg
            
            # Backup existing file
            if full_path.exists():
                self._backup_file(full_path, relative_path)
                self.modified_files.append(str(relative_path))
            else:
                self.created_files.append(str(relative_path))
            
            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Log change
            self._log_change("create" if relative_path not in self.modified_files else "modify", 
                           relative_path, description)
            
            logger.info(f"Created: {relative_path}")
            return True, f"Created successfully: {relative_path}"
            
        except Exception as e:
            error_msg = f"Error creating file {relative_path}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def create_directory(self, relative_path: str) -> Tuple[bool, str]:
        """
        Create a directory structure.
        
        Args:
            relative_path: Path relative to project root
            
        Returns:
            Tuple of (success, message)
        """
        try:
            full_path = self.project_root / relative_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            self._log_change("create_dir", relative_path, "")
            logger.info(f"Created directory: {relative_path}")
            return True, f"Directory created: {relative_path}"
            
        except Exception as e:
            error_msg = f"Error creating directory {relative_path}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def update_file(
        self,
        relative_path: str,
        content: str,
        description: str = ""
    ) -> Tuple[bool, str]:
        """
        Update an existing file with backup.
        
        Args:
            relative_path: Path relative to project root
            content: New content to write
            description: Description of changes
            
        Returns:
            Tuple of (success, message)
        """
        try:
            full_path = self.project_root / relative_path
            
            if not full_path.exists():
                error_msg = f"File does not exist: {relative_path}"
                logger.error(error_msg)
                return False, error_msg
            
            # Backup before modification
            self._backup_file(full_path, relative_path)
            self.modified_files.append(str(relative_path))
            
            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._log_change("modify", relative_path, description)
            logger.info(f"Updated: {relative_path}")
            return True, f"Updated successfully: {relative_path}"
            
        except Exception as e:
            error_msg = f"Error updating file {relative_path}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def read_file(self, relative_path: str) -> Optional[str]:
        """
        Read a file from the project.
        
        Args:
            relative_path: Path relative to project root
            
        Returns:
            File content or None if error
        """
        try:
            full_path = self.project_root / relative_path
            
            if not full_path.exists():
                logger.warning(f"File not found: {relative_path}")
                return None
            
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error reading file {relative_path}: {str(e)}")
            return None
    
    def file_exists(self, relative_path: str) -> bool:
        """Check if a file exists."""
        return (self.project_root / relative_path).exists()
    
    def create_project_structure(self, structure: Dict[str, List[str]]) -> Tuple[bool, str]:
        """
        Create a directory structure from a specification.
        
        Args:
            structure: Dict mapping directories to lists of files
                      e.g., {"src": ["main.py", "config.py"], "tests": []}
            
        Returns:
            Tuple of (success, message)
        """
        try:
            for directory, files in structure.items():
                # Create directory
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # Create files (empty if no content specified)
                for file in files:
                    if isinstance(file, str):
                        file_path = dir_path / file
                        if not file_path.exists():
                            file_path.touch()
            
            self._log_change("create_structure", "project_structure", "")
            return True, "Project structure created successfully"
            
        except Exception as e:
            error_msg = f"Error creating project structure: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def list_project_files(self, include_backups: bool = False) -> List[str]:
        """
        List all files in the project.
        
        Args:
            include_backups: Whether to include backup files
            
        Returns:
            List of file paths relative to project root
        """
        files = []
        exclude_dirs = {".backups", ".git", "__pycache__", "node_modules", ".venv", "venv"}
        
        for item in self.project_root.rglob("*"):
            if item.is_file():
                # Check if in excluded directory
                if any(excluded in item.parts for excluded in exclude_dirs):
                    if include_backups and excluded == ".backups":
                        pass
                    else:
                        continue
                
                rel_path = item.relative_to(self.project_root)
                files.append(str(rel_path))
        
        return sorted(files)
    
    def get_change_log(self) -> List[Dict]:
        """Get the change log."""
        return self.change_log.copy()
    
    def get_summary(self) -> Dict:
        """Get a summary of file operations."""
        return {
            "files_created": len(self.created_files),
            "files_modified": len(self.modified_files),
            "total_changes": len(self.change_log),
            "created_files": self.created_files,
            "modified_files": self.modified_files,
        }
    
    def _backup_file(self, full_path: Path, relative_path: str) -> None:
        """Create a backup of a file before modification."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_subdir = self.backup_dir / datetime.now().strftime("%Y/%m/%d")
            backup_subdir.mkdir(parents=True, exist_ok=True)
            
            # Create backup filename with timestamp
            backup_name = f"{full_path.stem}_{timestamp}{full_path.suffix}"
            backup_path = backup_subdir / backup_name
            
            shutil.copy2(full_path, backup_path)
            logger.info(f"  Backup created: {backup_path.relative_to(self.backup_dir)}")
            
        except Exception as e:
            logger.warning(f"Failed to create backup: {str(e)}")
    
    def _log_change(self, action: str, path: str, description: str) -> None:
        """Log a file operation."""
        self.change_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "path": path,
            "description": description
        })
    
    def rollback_last_change(self) -> Tuple[bool, str]:
        """
        Rollback the last file operation (if backup exists).
        
        Returns:
            Tuple of (success, message)
        """
        if not self.change_log:
            return False, "No changes to rollback"
        
        try:
            last_change = self.change_log[-1]
            action = last_change["action"]
            path = last_change["path"]
            
            if action == "create":
                full_path = self.project_root / path
                if full_path.exists():
                    full_path.unlink()
                    logger.info(f"Rolled back (deleted): {path}")
                    return True, f"Rolled back deletion of: {path}"
            
            elif action in ["modify", "create"]:
                # Try to restore from backup
                backups = list(self.backup_dir.rglob("*"))
                if backups:
                    latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
                    shutil.copy2(latest_backup, self.project_root / path)
                    logger.info(f"Rolled back (restored): {path}")
                    return True, f"Rolled back to previous version: {path}"
            
            return False, "Could not rollback last change"
            
        except Exception as e:
            error_msg = f"Rollback failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


def create_gitignore(project_root: str) -> bool:
    """
    Create a .gitignore file for the project.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        True if successful
    """
    try:
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Node
node_modules/
npm-debug.log
package-lock.json

# Environment
.env
.env.local
.env.*.local

# OS
.DS_Store
Thumbs.db

# Project specific
.backups/
data/flynt.db
logs/
*.log
"""
        
        gitignore_path = Path(project_root) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        
        logger.info("Created .gitignore")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create .gitignore: {str(e)}")
        return False
