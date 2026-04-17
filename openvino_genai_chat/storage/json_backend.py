"""JSON file-based storage backend for conversations."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from .base import StorageBackend, Message, ConversationMetadata
from ..utils.logger import setup_logger
from ..utils.constants import CONVERSATIONS_DIR, CONVERSATION_FILE_EXTENSION

logger = setup_logger(__name__)


class JSONStorage(StorageBackend):
    """
    JSON file-based storage backend.
    Stores each conversation in a separate JSON file with metadata and messages.
    """
    
    def __init__(self, conversations_dir: Path = CONVERSATIONS_DIR):
        """
        Initialize JSON storage backend.
        
        Args:
            conversations_dir: Directory for storing conversation files
        """
        self.conversations_dir = conversations_dir
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"JSON Storage initialized at {self.conversations_dir}")
    
    def _get_conversation_path(self, conversation_id: str) -> Path:
        """Get file path for a conversation."""
        return self.conversations_dir / f"{conversation_id}{CONVERSATION_FILE_EXTENSION}"
    
    def _load_conversation_file(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation data from file."""
        path = self._get_conversation_path(conversation_id)
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading conversation {conversation_id}: {e}")
        return None
    
    def _save_conversation_file(
        self,
        conversation_id: str,
        data: Dict[str, Any],
    ) -> None:
        """Save conversation data to file."""
        path = self._get_conversation_path(conversation_id)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Error saving conversation {conversation_id}: {e}")
    
    def create_conversation(
        self,
        conversation_id: str,
        title: str,
        model_name: str,
        model_device: str,
        max_tokens: int,
        use_thinking: bool = False,
    ) -> str:
        """Create a new conversation."""
        now = datetime.now().isoformat()
        
        conversation_data = {
            "metadata": {
                "id": conversation_id,
                "title": title,
                "created_date": now,
                "updated_date": now,
                "model_name": model_name,
                "model_device": model_device,
                "max_tokens": max_tokens,
                "use_thinking": use_thinking,
                "message_count": 0,
            },
            "messages": [],
        }
        
        self._save_conversation_file(conversation_id, conversation_data)
        logger.info(f"Created conversation {conversation_id}: {title}")
        return conversation_id
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> None:
        """Add a message to a conversation."""
        data = self._load_conversation_file(conversation_id)
        if not data:
            logger.error(f"Conversation {conversation_id} not found")
            return
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        
        data["messages"].append(message)
        data["metadata"]["updated_date"] = datetime.now().isoformat()
        data["metadata"]["message_count"] = len(data["messages"])
        
        self._save_conversation_file(conversation_id, data)
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a full conversation."""
        return self._load_conversation_file(conversation_id)
    
    def get_metadata(self, conversation_id: str) -> Optional[ConversationMetadata]:
        """Retrieve conversation metadata."""
        data = self._load_conversation_file(conversation_id)
        if not data:
            return None
        
        meta = data["metadata"]
        return ConversationMetadata(
            id=meta["id"],
            title=meta["title"],
            created_date=meta["created_date"],
            updated_date=meta["updated_date"],
            model_name=meta["model_name"],
            model_device=meta["model_device"],
            max_tokens=meta["max_tokens"],
            message_count=meta["message_count"],
            use_thinking=meta.get("use_thinking", False),
        )
    
    def list_conversations(self) -> List[ConversationMetadata]:
        """List all conversation metadata."""
        conversations = []
        
        for file_path in self.conversations_dir.glob(f"*{CONVERSATION_FILE_EXTENSION}"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                meta = data["metadata"]
                conversations.append(ConversationMetadata(
                    id=meta["id"],
                    title=meta["title"],
                    created_date=meta["created_date"],
                    updated_date=meta["updated_date"],
                    model_name=meta["model_name"],
                    model_device=meta["model_device"],
                    max_tokens=meta["max_tokens"],
                    message_count=meta["message_count"],
                    use_thinking=meta.get("use_thinking", False),
                ))
            except Exception as e:
                logger.error(f"Error reading conversation {file_path}: {e}")
        
        # Sort by updated date, most recent first
        conversations.sort(
            key=lambda c: c.updated_date,
            reverse=True,
        )
        
        return conversations
    
    def update_title(self, conversation_id: str, new_title: str) -> None:
        """Update conversation title."""
        data = self._load_conversation_file(conversation_id)
        if not data:
            logger.error(f"Conversation {conversation_id} not found")
            return
        
        data["metadata"]["title"] = new_title
        data["metadata"]["updated_date"] = datetime.now().isoformat()
        
        self._save_conversation_file(conversation_id, data)
        logger.info(f"Updated conversation {conversation_id} title to: {new_title}")
    
    def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation."""
        path = self._get_conversation_path(conversation_id)
        try:
            if path.exists():
                path.unlink()
                logger.info(f"Deleted conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
    
    def export_conversation(
        self,
        conversation_id: str,
        format: str = "json",
    ) -> str:
        """Export conversation in specified format."""
        data = self._load_conversation_file(conversation_id)
        if not data:
            logger.error(f"Conversation {conversation_id} not found")
            return ""
        
        if format == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)
        
        elif format == "txt":
            # Plain text export
            lines = []
            meta = data["metadata"]
            lines.append(f"Title: {meta['title']}")
            lines.append(f"Created: {meta['created_date']}")
            lines.append(f"Model: {meta['model_name']} ({meta['model_device']})")
            lines.append("-" * 80)
            lines.append("")
            
            for msg in data["messages"]:
                role_label = "You" if msg["role"] == "user" else "Assistant"
                lines.append(f"{role_label} ({msg['timestamp']}):")
                lines.append(msg["content"])
                lines.append("")
            
            return "\n".join(lines)
        
        else:
            logger.warning(f"Unknown export format: {format}")
            return json.dumps(data, indent=2, ensure_ascii=False)
