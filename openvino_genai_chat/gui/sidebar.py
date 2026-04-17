"""Conversation sidebar widget."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog
)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Optional, List, Dict, Any
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ConversationSidebar(QWidget):
    """Sidebar showing conversation list with search and controls."""
    
    # Signals
    conversation_selected = pyqtSignal(str)  # conversation_id
    conversation_deleted = pyqtSignal(str)   # conversation_id
    conversation_renamed = pyqtSignal(str, str)  # conversation_id, new_title
    new_conversation_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Initialize conversation sidebar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.current_conversations: List[Dict[str, Any]] = []
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Title
        title_label = self._create_label("Conversations", bold=True)
        layout.addWidget(title_label)
        
        # New Chat button
        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.clicked.connect(self.new_conversation_clicked.emit)
        new_chat_btn.setMinimumHeight(36)
        layout.addWidget(new_chat_btn)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search conversations...")
        self.search_input.textChanged.connect(self.filter_conversations)
        layout.addWidget(self.search_input)
        
        # Conversations list
        self.conversations_list = QListWidget()
        self.conversations_list.itemSelectionChanged.connect(self._on_conversation_selected)
        layout.addWidget(self.conversations_list)
        
        self.setLayout(layout)
    
    def _create_label(self, text: str, bold: bool = False) -> QLineEdit:
        """Create a label (using QLabel would be better but this shows style)."""
        from PyQt5.QtWidgets import QLabel
        label = QLabel(text)
        if bold:
            font = label.font()
            font.setBold(True)
            label.setFont(font)
        return label
    
    def load_conversations(self, conversations: List[Dict[str, Any]]) -> None:
        """
        Load conversations to display.
        
        Args:
            conversations: List of conversation metadata dictionaries
        """
        self.current_conversations = conversations
        self.refresh_list()
    
    def refresh_list(self) -> None:
        """Refresh the conversations list display."""
        search_text = self.search_input.text().lower()
        
        # Block signals during refresh to avoid accidental selection triggers
        self.conversations_list.blockSignals(True)
        try:
            self.conversations_list.clear()
            
            for conv in self.current_conversations:
                title = conv.get("title", "Untitled")
                conv_id = conv.get("id", "")
            
                # Filter by search text
                if search_text and search_text not in title.lower():
                    continue
            
                item = QListWidgetItem(title)
                item.setData(Qt.UserRole, conv_id)
                self.conversations_list.addItem(item)
        finally:
            self.conversations_list.blockSignals(False)
    
    def filter_conversations(self) -> None:
        """Filter conversations based on search input."""
        self.refresh_list()
    
    def _on_conversation_selected(self) -> None:
        """Handle conversation selection."""
        current_item = self.conversations_list.currentItem()
        if current_item:
            conv_id = current_item.data(Qt.UserRole)
            self.conversation_selected.emit(conv_id)
    
    def get_selected_conversation_id(self) -> Optional[str]:
        """Get the currently selected conversation ID."""
        current_item = self.conversations_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None
    
    def select_conversation(self, conversation_id: str) -> None:
        """Select a conversation in the list by its ID."""
        for i in range(self.conversations_list.count()):
            item = self.conversations_list.item(i)
            if item.data(Qt.UserRole) == conversation_id:
                # Set as current item and ensure it's visible
                self.conversations_list.setCurrentRow(i)
                self.conversations_list.scrollToItem(item)
                # Manually trigger selection signal since blockSignals might have masked it 
                # or if setting current row doesn't fire selection change immediately
                self._on_conversation_selected()
                break
    
    def delete_conversation(self, conversation_id: str, title: str) -> bool:
        """
        Show delete confirmation and return user's choice.
        
        Args:
            conversation_id: Conversation to delete
            title: Conversation title for confirmation
            
        Returns:
            True if user confirmed deletion
        """
        reply = QMessageBox.warning(
            self,
            "Delete Conversation",
            f"Are you sure you want to delete '{title}'?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        
        if reply == QMessageBox.Yes:
            self.conversation_deleted.emit(conversation_id)
            return True
        
        return False
    
    def rename_conversation(self, conversation_id: str, current_title: str) -> Optional[str]:
        """
        Show rename dialog and return new title.
        
        Args:
            conversation_id: Conversation to rename
            current_title: Current conversation title
            
        Returns:
            New title if user confirmed, None otherwise
        """
        new_title, ok = QInputDialog.getText(
            self,
            "Rename Conversation",
            "New title:",
            text=current_title,
        )
        
        if ok and new_title.strip():
            new_title = new_title.strip()[:100]  # Max 100 chars
            self.conversation_renamed.emit(conversation_id, new_title)
            return new_title
        
        return None
