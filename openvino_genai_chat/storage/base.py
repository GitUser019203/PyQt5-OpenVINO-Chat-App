"""Abstract base class for conversation storage."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str  # ISO format datetime


@dataclass
class ConversationMetadata:
    """Metadata for a conversation."""
    id: str
    title: str
    created_date: str  # ISO format
    updated_date: str  # ISO format
    model_name: str
    model_device: str
    max_tokens: int
    message_count: int
    use_thinking: bool = False  # /think mode enabled


class StorageBackend(ABC):
    """
    Abstract base class for conversation storage.
    
    Implementations should handle persistence of conversations including
    messages, metadata, and enable future migrations to different storage
    backends (e.g., SQLite).
    """
    
    @abstractmethod
    def create_conversation(
        self,
        conversation_id: str,
        title: str,
        model_name: str,
        model_device: str,
        max_tokens: int,
        use_thinking: bool = False,
    ) -> str:
        """
        Create a new conversation.
        
        Args:
            conversation_id: Unique conversation identifier
            title: Human-readable conversation title
            model_name: Name/path of the model used
            model_device: Device used (CPU/GPU)
            max_tokens: Max tokens setting
            use_thinking: Whether /think mode is enabled
            
        Returns:
            The conversation ID
        """
        pass
    
    @abstractmethod
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> None:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            role: "user" or "assistant"
            content: Message text
        """
        pass
    
    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a full conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Dictionary with metadata and messages list, or None if not found
        """
        pass
    
    @abstractmethod
    def get_metadata(self, conversation_id: str) -> Optional[ConversationMetadata]:
        """
        Retrieve metadata for a conversation without loading full messages.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            ConversationMetadata or None if not found
        """
        pass
    
    @abstractmethod
    def list_conversations(self) -> List[ConversationMetadata]:
        """
        List all conversation metadata.
        
        Returns:
            List of ConversationMetadata objects
        """
        pass
    
    @abstractmethod
    def update_title(self, conversation_id: str, new_title: str) -> None:
        """
        Update a conversation's title.
        
        Args:
            conversation_id: Conversation ID
            new_title: New conversation title
        """
        pass
    
    @abstractmethod
    def delete_conversation(self, conversation_id: str) -> None:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation ID
        """
        pass
    
    @abstractmethod
    def export_conversation(self, conversation_id: str, format: str = "json") -> str:
        """
        Export a conversation in specified format.
        
        Args:
            conversation_id: Conversation ID
            format: Export format (json, txt, etc.)
            
        Returns:
            Exported data as string
        """
        pass
