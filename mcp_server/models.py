from typing import List, Optional
from pydantic import BaseModel, Field


class ReadFileResponse(BaseModel):
    """Structured response model for read_file MCP tool."""
    status: str = Field("success", description="Status of the operation ('success' or 'error')")
    file_path: str = Field(..., description="Relative canonical path of the accessed file")
    sanitized_code: str = Field(..., description="The sanitized content of the file")
    redactions_applied: List[str] = Field(default_factory=list, description="List of sensitive data redactions applied")
    size_bytes: int = Field(0, description="Size of the file in bytes")
    error_message: Optional[str] = Field(None, description="Detailed error message if status is 'error'")


class FileErrorResponse(BaseModel):
    """Standard error response model."""
    status: str = "error"
    file_path: str
    sanitized_code: str = ""
    redactions_applied: List[str] = Field(default_factory=list)
    size_bytes: int = 0
    error_message: str


class DirectoryItem(BaseModel):
    """Model for an individual item inside a listed directory."""
    name: str = Field(..., description="File or folder name")
    type: str = Field(..., description="'file' or 'directory'")
    size_bytes: int = Field(0, description="Size in bytes for files, 0 for directories")
    extension: Optional[str] = Field(None, description="File extension if applicable")


class ListDirectoryResponse(BaseModel):
    """Structured response model for list_directory MCP tool."""
    status: str = Field("success", description="Status of the operation ('success' or 'error')")
    directory: str = Field(..., description="Relative path of the listed directory")
    items: List[DirectoryItem] = Field(default_factory=list, description="Structured items in directory")
    files: List[str] = Field(default_factory=list, description="List of file names in directory")
    subdirectories: List[str] = Field(default_factory=list, description="List of subdirectory names")
    error_message: Optional[str] = Field(None, description="Detailed error message if status is 'error'")
