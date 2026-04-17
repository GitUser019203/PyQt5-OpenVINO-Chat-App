"""Chat management logic and conversation state."""

import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..storage.base import StorageBackend
from ..utils.logger import setup_logger
from ..utils.constants import Device

logger = setup_logger(__name__)


class ChatManager:
    """
    Manages conversation state and coordinates with storage.
    Handles message history, context management, and persistence.
    """
    
    def __init__(self, storage: StorageBackend):
        """
        Initialize chat manager.
        
        Args:
            storage: Storage backend for conversation persistence
        """
        self.storage = storage
        self.current_conversation_id: Optional[str] = None
        self.current_messages: List[Dict[str, str]] = []
        self.model_name: str = ""
        self.model_device: str = Device.CPU.value
        self.max_tokens: int = 4096
        self.use_thinking: bool = False
    
    def new_conversation(
        self,
        model_name: str,
        model_device: str,
        max_tokens: int,
        use_thinking: bool = False,
        title: Optional[str] = None,
    ) -> str:
        """
        Create a new conversation.
        
        Args:
            model_name: Name/path of the model
            model_device: Device used (CPU/GPU)
            max_tokens: Max tokens setting
            use_thinking: Whether to enable /think mode
            title: Optional conversation title (auto-generated if not provided)
            
        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        
        # Auto-generate title from timestamp if not provided
        if not title:
            now = datetime.now()
            title = f"Chat - {now.strftime('%Y-%m-%d %H:%M')}"
        
        self.storage.create_conversation(
            conversation_id=conversation_id,
            title=title,
            model_name=model_name,
            model_device=model_device,
            max_tokens=max_tokens,
            use_thinking=use_thinking,
        )
        
        self.current_conversation_id = conversation_id
        self.current_messages = []
        self.model_name = model_name
        self.model_device = model_device
        self.max_tokens = max_tokens
        self.use_thinking = use_thinking
        
        logger.info(f"Created new conversation: {conversation_id}")
        return conversation_id
    
    def load_conversation(self, conversation_id: str) -> bool:
        """
        Load an existing conversation.
        
        Args:
            conversation_id: Conversation ID to load
            
        Returns:
            True if successful, False otherwise
        """
        data = self.storage.get_conversation(conversation_id)
        if not data:
            logger.error(f"Conversation not found: {conversation_id}")
            return False
        
        self.current_conversation_id = conversation_id
        self.current_messages = data.get("messages", [])
        
        meta = data["metadata"]
        self.model_name = meta.get("model_name", "")
        self.model_device = meta.get("model_device", Device.CPU.value)
        self.max_tokens = meta.get("max_tokens", 4096)
        self.use_thinking = meta.get("use_thinking", False)
        
        logger.info(f"Loaded conversation: {conversation_id}")
        return True
    
    def add_user_message(self, content: str) -> None:
        """
        Add a user message to the current conversation.
        
        Args:
            content: Message content
        """
        if not self.current_conversation_id:
            raise RuntimeError("No active conversation")
        
        # Validate input
        if not content or not content.strip():
            raise ValueError("Message cannot be empty")
        
        # Add to storage
        self.storage.add_message(
            self.current_conversation_id,
            role="user",
            content=content,
        )
        
        # Add to in-memory list
        self.current_messages.append({
            "role": "user",
            "content": content,
        })
        
        logger.debug(f"Added user message to {self.current_conversation_id}")
    
    def add_assistant_message(self, content: str) -> None:
        """
        Add an assistant message to the current conversation.
        
        Args:
            content: Message content
        """
        if not self.current_conversation_id:
            raise RuntimeError("No active conversation")
        
        # Add to storage
        self.storage.add_message(
            self.current_conversation_id,
            role="assistant",
            content=content,
        )
        
        # Add to in-memory list
        self.current_messages.append({
            "role": "assistant",
            "content": content,
        })
        
        logger.debug(f"Added assistant message to {self.current_conversation_id}")
    
    def get_conversation_context(self) -> str:
        """
        Get formatted conversation context for model input.
        
        Returns:
            Formatted conversation history
        """
        if not self.current_messages:
            return ""
        
        context_lines = []
        for msg in self.current_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            context_lines.append(f"{role}: {msg['content']}")
        
        return "\n\n".join(context_lines)
    
    def format_prompt(self, prompt: str, use_thinking: bool = False) -> str:
        """
        Format a prompt with the appropriate thinking directive.
        
        Args:
            prompt: The user's prompt
            use_thinking: Whether to enable extended thinking mode (/think)
            
        Returns:
            Formatted prompt with thinking directive
        """
        thinking_prefix = "/think" if use_thinking else "/no_think"
        return f"{thinking_prefix}\n\n{prompt}"
    
    def get_conversation_messages(self) -> List[Dict[str, str]]:
        """Get current conversation messages."""
        return self.current_messages.copy()
    
    def get_last_assistant_message(self) -> Optional[str]:
        """Get the last assistant message."""
        for msg in reversed(self.current_messages):
            if msg["role"] == "assistant":
                return msg["content"]
        return None
    
    def close_conversation(self) -> None:
        """Close the current conversation."""
        self.current_conversation_id = None
        self.current_messages = []
        logger.debug("Conversation closed")
    
    def rename_conversation(self, conversation_id: str, new_title: str) -> None:
        """
        Rename a conversation.
        
        Args:
            conversation_id: Conversation ID
            new_title: New title
        """
        self.storage.update_title(conversation_id, new_title)
        
        if self.current_conversation_id == conversation_id:
            logger.info(f"Renamed current conversation to: {new_title}")
    
    def delete_conversation(self, conversation_id: str) -> None:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation ID
        """
        self.storage.delete_conversation(conversation_id)
        
        if self.current_conversation_id == conversation_id:
            self.close_conversation()
        
        logger.info(f"Deleted conversation: {conversation_id}")
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all conversations.
        
        Returns:
            List of conversation metadata dictionaries
        """
        metadata_list = self.storage.list_conversations()
        return [
            {
                "id": m.id,
                "title": m.title,
                "created_date": m.created_date,
                "updated_date": m.updated_date,
                "model_name": m.model_name,
                "message_count": m.message_count,
            }
            for m in metadata_list
        ]
    
    def set_use_thinking(self, enabled: bool) -> None:
        """
        Toggle extended thinking mode.
        
        Args:
            enabled: Whether to enable /think mode
        """
        self.use_thinking = enabled
        logger.info(f"Thinking mode set to: {enabled}")
