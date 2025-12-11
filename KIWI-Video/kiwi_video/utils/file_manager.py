"""File management utilities for KIWI-Video."""

import shutil
from pathlib import Path

from kiwi_video.core.exceptions import ResourceNotFoundError
from kiwi_video.utils.logger import get_logger


class FileManager:
    """
    Utility class for file and directory operations.
    
    Provides safe file operations with proper error handling and logging.
    """

    def __init__(self, base_dir: Path) -> None:
        """
        Initialize file manager.
        
        Args:
            base_dir: Base directory for file operations
        """
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("file_manager")

    def resolve_path(self, relative_path: str) -> Path:
        """
        Resolve a relative path to absolute path within base directory.
        
        Args:
            relative_path: Relative path string
            
        Returns:
            Absolute Path object
            
        Raises:
            ValueError: If path tries to escape base directory
        """
        # Normalize and resolve the path
        full_path = (self.base_dir / relative_path).resolve()

        # Security check: ensure path is within base_dir
        try:
            full_path.relative_to(self.base_dir.resolve())
        except ValueError:
            raise ValueError(f"Path {relative_path} is outside base directory")

        return full_path

    def read_file(self, relative_path: str) -> str:
        """
        Read text file content.
        
        Args:
            relative_path: Relative path to file
            
        Returns:
            File content as string
            
        Raises:
            ResourceNotFoundError: If file doesn't exist
        """
        file_path = self.resolve_path(relative_path)

        if not file_path.exists():
            raise ResourceNotFoundError("file", str(relative_path))

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            self.logger.debug(f"Read file: {relative_path}")
            return content

        except Exception as e:
            self.logger.error(f"Failed to read file {relative_path}: {e}")
            raise

    def write_file(self, relative_path: str, content: str) -> None:
        """
        Write content to text file.
        
        Args:
            relative_path: Relative path to file
            content: Content to write
        """
        file_path = self.resolve_path(relative_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.debug(f"Wrote file: {relative_path}")

        except Exception as e:
            self.logger.error(f"Failed to write file {relative_path}: {e}")
            raise

    def create_directory(self, relative_path: str) -> Path:
        """
        Create a directory.
        
        Args:
            relative_path: Relative path to directory
            
        Returns:
            Path to created directory
        """
        dir_path = self.resolve_path(relative_path)
        dir_path.mkdir(parents=True, exist_ok=True)

        self.logger.debug(f"Created directory: {relative_path}")
        return dir_path

    def delete_file(self, relative_path: str) -> None:
        """
        Delete a file.
        
        Args:
            relative_path: Relative path to file
        """
        file_path = self.resolve_path(relative_path)

        if file_path.exists():
            file_path.unlink()
            self.logger.debug(f"Deleted file: {relative_path}")
        else:
            self.logger.warning(f"File not found for deletion: {relative_path}")

    def delete_directory(self, relative_path: str) -> None:
        """
        Delete a directory and all its contents.
        
        Args:
            relative_path: Relative path to directory
        """
        dir_path = self.resolve_path(relative_path)

        if dir_path.exists():
            shutil.rmtree(dir_path)
            self.logger.debug(f"Deleted directory: {relative_path}")
        else:
            self.logger.warning(f"Directory not found for deletion: {relative_path}")

    def copy_file(self, source: str, destination: str) -> None:
        """
        Copy a file.
        
        Args:
            source: Source file relative path
            destination: Destination file relative path
        """
        src_path = self.resolve_path(source)
        dst_path = self.resolve_path(destination)

        if not src_path.exists():
            raise ResourceNotFoundError("file", source)

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)

        self.logger.debug(f"Copied file: {source} -> {destination}")

    def move_file(self, source: str, destination: str) -> None:
        """
        Move a file.
        
        Args:
            source: Source file relative path
            destination: Destination file relative path
        """
        src_path = self.resolve_path(source)
        dst_path = self.resolve_path(destination)

        if not src_path.exists():
            raise ResourceNotFoundError("file", source)

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))

        self.logger.debug(f"Moved file: {source} -> {destination}")

    def list_files(
        self,
        relative_path: str = ".",
        pattern: str = "*",
        recursive: bool = False
    ) -> list[Path]:
        """
        List files in a directory.
        
        Args:
            relative_path: Relative path to directory
            pattern: Glob pattern for filtering
            recursive: Whether to search recursively
            
        Returns:
            List of file paths
        """
        dir_path = self.resolve_path(relative_path)

        if not dir_path.exists():
            return []

        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))

        # Return only files, not directories
        files = [f for f in files if f.is_file()]

        self.logger.debug(f"Listed {len(files)} files in {relative_path}")
        return files

    def file_exists(self, relative_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            relative_path: Relative path to file
            
        Returns:
            True if file exists, False otherwise
        """
        file_path = self.resolve_path(relative_path)
        return file_path.exists() and file_path.is_file()

    def directory_exists(self, relative_path: str) -> bool:
        """
        Check if a directory exists.
        
        Args:
            relative_path: Relative path to directory
            
        Returns:
            True if directory exists, False otherwise
        """
        dir_path = self.resolve_path(relative_path)
        return dir_path.exists() and dir_path.is_dir()

    def get_file_size(self, relative_path: str) -> int:
        """
        Get file size in bytes.
        
        Args:
            relative_path: Relative path to file
            
        Returns:
            File size in bytes
            
        Raises:
            ResourceNotFoundError: If file doesn't exist
        """
        file_path = self.resolve_path(relative_path)

        if not file_path.exists():
            raise ResourceNotFoundError("file", relative_path)

        return file_path.stat().st_size

