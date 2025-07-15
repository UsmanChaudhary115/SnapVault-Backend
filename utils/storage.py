"""
Modular Storage System for SnapVault

This module provides a flexible storage interface that can be easily switched
between local file storage and cloud storage (S3) without changing the application logic.

Usage:
    from utils.storage import get_storage_handler
    
    storage = get_storage_handler()
    file_path = await storage.save_file(file_content, "photos", "image.jpg")
    await storage.delete_file(file_path)
"""

from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile
import shutil


class StorageHandler(ABC):
    """Abstract base class for storage handlers"""
    
    @abstractmethod
    async def save_file(self, file: UploadFile, directory: str, filename: Optional[str] = None) -> str:
        """
        Save a file and return the file path/URL
        
        Args:
            file: The uploaded file
            directory: Directory/bucket path to save to
            filename: Optional custom filename (will generate UUID if not provided)
            
        Returns:
            str: File path or URL where the file was saved
        """
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file
        
        Args:
            file_path: Path or URL of the file to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists
        
        Args:
            file_path: Path or URL of the file to check
            
        Returns:
            bool: True if file exists, False otherwise
        """
        pass
    
    @abstractmethod
    def get_file_url(self, file_path: str) -> str:
        """
        Get the public URL for a file
        
        Args:
            file_path: Internal file path
            
        Returns:
            str: Public URL for the file
        """
        pass


class LocalStorageHandler(StorageHandler):
    """Local file system storage handler"""
    
    def __init__(self, base_directory: str = "uploads"):
        self.base_directory = base_directory
        self._ensure_directory_exists(base_directory)
    
    def _ensure_directory_exists(self, directory: str):
        """Ensure directory exists, create if it doesn't"""
        os.makedirs(directory, exist_ok=True)
    
    def _generate_filename(self, original_filename: str) -> str:
        """Generate a unique filename preserving the extension"""
        if original_filename:
            ext = Path(original_filename).suffix.lower()
            return f"{uuid.uuid4()}{ext}"
        return str(uuid.uuid4())
    
    def _validate_file_type(self, filename: str, allowed_types: list = None) -> bool:
        """Validate file type based on extension"""
        if not allowed_types:
            allowed_types = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        
        ext = Path(filename).suffix.lower()
        return ext in allowed_types
    
    async def save_file(self, file: UploadFile, directory: str, filename: Optional[str] = None) -> str:
        """Save file to local storage"""
        try:
            # Validate file type
            if not self._validate_file_type(file.filename):
                raise ValueError(f"File type not allowed: {file.filename}")
            
            # Generate filename if not provided
            if not filename:
                filename = self._generate_filename(file.filename)
            
            # Create full directory path
            full_directory = os.path.join(self.base_directory, directory)
            self._ensure_directory_exists(full_directory)
            
            # Create full file path
            file_path = os.path.join(full_directory, filename)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            return file_path
            
        except Exception as e:
            raise Exception(f"Failed to save file: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage"""
        try:
            if self.file_exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists in local storage"""
        return os.path.exists(file_path)
    
    def get_file_url(self, file_path: str) -> str:
        """Get the URL for local file (relative to uploads directory)"""
        # For local storage, return the relative path
        # In production, this might be served through a web server
        return file_path.replace(self.base_directory, "/uploads").replace("\\", "/")


class S3StorageHandler(StorageHandler):
    """S3 cloud storage handler (placeholder for future implementation)"""
    
    def __init__(self, bucket_name: str, aws_access_key: str, aws_secret_key: str, region: str = "us-east-1"):
        """
        Initialize S3 storage handler
        
        Args:
            bucket_name: S3 bucket name
            aws_access_key: AWS access key
            aws_secret_key: AWS secret key
            region: AWS region
        """
        self.bucket_name = bucket_name
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.region = region
        # TODO: Initialize boto3 client when implementing S3
        # self.s3_client = boto3.client('s3', ...)
    
    async def save_file(self, file: UploadFile, directory: str, filename: Optional[str] = None) -> str:
        """Save file to S3 (to be implemented)"""
        # TODO: Implement S3 file upload
        # Example implementation:
        # 1. Generate unique filename
        # 2. Upload to S3 bucket
        # 3. Return S3 URL
        raise NotImplementedError("S3 storage not yet implemented")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from S3 (to be implemented)"""
        # TODO: Implement S3 file deletion
        raise NotImplementedError("S3 storage not yet implemented")
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists in S3 (to be implemented)"""
        # TODO: Implement S3 file existence check
        raise NotImplementedError("S3 storage not yet implemented")
    
    def get_file_url(self, file_path: str) -> str:
        """Get public URL for S3 file (to be implemented)"""
        # TODO: Implement S3 URL generation
        raise NotImplementedError("S3 storage not yet implemented")


# Storage configuration
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")  # "local" or "s3"


def get_storage_handler() -> StorageHandler:
    """
    Factory function to get the appropriate storage handler
    
    Returns:
        StorageHandler: Configured storage handler instance
    """
    if STORAGE_TYPE.lower() == "s3":
        # S3 configuration from environment variables
        bucket_name = os.getenv("S3_BUCKET_NAME")
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        region = os.getenv("AWS_REGION", "us-east-1")
        
        if not all([bucket_name, aws_access_key, aws_secret_key]):
            raise ValueError("S3 configuration incomplete. Please set S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, and AWS_SECRET_ACCESS_KEY")
        
        return S3StorageHandler(bucket_name, aws_access_key, aws_secret_key, region)
    
    else:
        # Default to local storage
        base_directory = os.getenv("UPLOAD_DIRECTORY", "uploads")
        return LocalStorageHandler(base_directory)


# Convenience functions for common storage operations
async def save_profile_picture(file: UploadFile) -> str:
    """Save a profile picture and return the file path"""
    storage = get_storage_handler()
    return await storage.save_file(file, "profile_pictures")


async def save_photo(file: UploadFile) -> str:
    """Save a photo and return the file path"""
    storage = get_storage_handler()
    return await storage.save_file(file, "photos")


async def delete_file(file_path: str) -> bool:
    """Delete a file using the configured storage handler"""
    storage = get_storage_handler()
    return await storage.delete_file(file_path)


def file_exists(file_path: str) -> bool:
    """Check if a file exists using the configured storage handler"""
    storage = get_storage_handler()
    return storage.file_exists(file_path)


def get_file_url(file_path: str) -> str:
    """Get public URL for a file using the configured storage handler"""
    storage = get_storage_handler()
    return storage.get_file_url(file_path)


# Storage statistics and utilities
class StorageStats:
    """Utility class for storage statistics and management"""
    
    @staticmethod
    def get_directory_size(directory: str) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, IOError):
                        pass
        except (OSError, IOError):
            pass
        return total_size
    
    @staticmethod
    def cleanup_orphaned_files(directory: str, referenced_files: list) -> int:
        """
        Clean up files that are not referenced in the database
        
        Args:
            directory: Directory to clean up
            referenced_files: List of file paths that should be kept
            
        Returns:
            int: Number of files deleted
        """
        deleted_count = 0
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file_path not in referenced_files:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except (OSError, IOError):
                            pass
        except (OSError, IOError):
            pass
        return deleted_count 