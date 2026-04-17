"""Chat display widget with message bubbles and streaming support."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from typing import Optional
import markdown
import re
import html

from ..utils.constants import CHAT_BUBBLE_MAX_WIDTH

# CSS for markdown rendering
def get_markdown_css(theme: str = "dark") -> str:
    """Get CSS for markdown rendering based on theme."""
    if theme == "light":
        bg_color = "#ffffff"
        text_color = "#222222"
        code_bg = "#f0f0f0"
        code_text = "#d32f2f"
        pre_bg = "#f8f8f8"
        blockquote_bg = "#f0f0f0"
        table_border = "#dddddd"
        th_bg = "#f5f5f5"
        strong_color = "#000000"
    else:
        bg_color = "#1e1e1e"
        text_color = "#ffffff"
        code_bg = "#2d2d2d"
        code_text = "#00ff00"
        pre_bg = "#1e1e1e"
        blockquote_bg = "#252525"
        table_border = "#3d3d3d"
        th_bg = "#252525"
        strong_color = "#ffffff"

    return f"""
body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    background-color: {bg_color};
    color: {text_color};
}}

p {{ margin: 0.5em 0; }}

h1, h2, h3, h4, h5, h6 {{
    margin: 0.8em 0 0.4em 0;
    font-weight: bold;
    color: {strong_color};
}}

code {{
    background-color: {code_bg};
    color: {code_text};
    padding: 2px 4px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
}}

pre {{
    background-color: {pre_bg};
    color: {code_text};
    padding: 10px;
    border-radius: 5px;
    overflow-x: auto;
    margin: 0.5em 0;
    font-family: 'Courier New', monospace;
    font-size: 0.85em;
}}

blockquote {{
    border-left: 4px solid #0d7377;
    margin: 0.5em 0;
    padding: 0.5em 1em;
    background-color: {blockquote_bg};
    color: {text_color};
}}

table {{
    border-collapse: collapse;
    margin: 0.5em 0;
    width: 100%;
}}

th, td {{
    border: 1px solid {table_border};
    padding: 8px;
    text-align: left;
}}

th {{
    background-color: {th_bg};
    font-weight: bold;
}}

hr {{
    border: none;
    border-top: 1px solid {table_border};
    margin: 1em 0;
}}

strong {{
    font-weight: bold;
    color: {strong_color};
}}
"""


def markdown_to_html(text: str, theme: str = "dark") -> str:
    """
    Convert markdown text to HTML with styling.
    
    Args:
        text: Markdown text
        theme: Current theme ("dark" or "light")
        
    Returns:
        HTML string
    """
    # Strip <think> blocks
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    
    # Sanitize input to prevent HTML injection
    escaped_text = html.escape(text)

    # Convert markdown to HTML
    html_content = markdown.markdown(
        escaped_text,
        extensions=['tables', 'fenced_code', 'codehilite'],
        extension_configs={
            'codehilite': {'use_pygments': False}
        }
    )
    
    return html_content


class MessageBubble(QWidget):
    """A single message bubble in the chat."""
    
    def __init__(self, text: str, is_user: bool, theme: str = "dark", parent=None):
        """
        Initialize message bubble.
        
        Args:
            text: Message text (can be markdown)
            is_user: True if user message, False if assistant
            theme: Current UI theme
            parent: Parent widget
        """
        super().__init__(parent)
        self.is_user = is_user
        self.theme = theme
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        
        # Message browser for markdown rendering
        self.message_browser = QTextBrowser()
        self.message_browser.setOpenExternalLinks(True)
        
        # Make it non-editable and read-only
        self.message_browser.setReadOnly(True)
        self.message_browser.setFocusPolicy(Qt.NoFocus)
        self.message_browser.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Constraint width for readability
        self.message_browser.setMinimumWidth(500)
        self.message_browser.setMaximumWidth(CHAT_BUBBLE_MAX_WIDTH)
        
        # Style the bubble
        if is_user:
            # User message - right aligned
            bg_color = "#0d7377"
            text_color = "#ffffff"
            radius_style = "border-top-right-radius: 2px;"
            layout.addWidget(self.message_browser, 1)
        else:
            # Assistant message - left aligned
            bg_color = "#3d3d3d" if theme == "dark" else "#eeeeee"
            text_color = "#ffffff" if theme == "dark" else "#222222"
            radius_style = "border-top-left-radius: 2px;"
            layout.addWidget(self.message_browser, 1)

        self.message_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: 12px;
                {radius_style}
                margin: 0;
                padding: 15px;
                font-size: 14px;
            }}
        """)
        
        # Initial content - MUST BE AFTER width/style setup for correct height calculation
        self.message_browser.document().setDefaultStyleSheet(get_markdown_css(self.theme))
        self.update_text(text)
        
        self.setLayout(layout)

    def update_text(self, text: str, auto_scroll: bool = False) -> None:
        """Update the bubble text and adjust height."""
        html_content = markdown_to_html(text, self.theme)
        
        # Suppress updates during layout changes to prevent flicker
        self.message_browser.setUpdatesEnabled(False)
        try:
            self.message_browser.setHtml(html_content)
            
            # Dynamically adjust height to content
            doc = self.message_browser.document()
            doc.adjustSize()
            height = int(doc.size().height()) + 30
            
            # Maximum height before internal scrollbar appears
            max_height = 600
            if height > max_height:
                self.message_browser.setFixedHeight(max_height)
                self.message_browser.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            else:
                self.message_browser.setFixedHeight(height)
                self.message_browser.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            if auto_scroll:
                # Use a timer to ensure the scroll happens after the content is rendered
                QTimer.singleShot(1, lambda: self.message_browser.verticalScrollBar().setValue(
                    self.message_browser.verticalScrollBar().maximum()
                ))
        finally:
            self.message_browser.setUpdatesEnabled(True)
            self.message_browser.viewport().update()


class ChatWidget(QWidget):
    """Widget for displaying chat messages with streaming support."""
    
    def __init__(self, parent=None):
        """
        Initialize chat widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.theme = "dark"
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container for messages
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setContentsMargins(20, 20, 20, 20)
        self.messages_layout.setSpacing(15)
        self.messages_container.setLayout(self.messages_layout)
        
        self.scroll_area.setWidget(self.messages_container)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)
        
        self.messages = []  # List of (text, is_user) tuples
        self.current_streaming_widget: Optional[MessageBubble] = None
        self.current_streaming_text = ""  # Accumulate streaming text
        self.words_at_last_update = 0     # Count for buffered updates
        
        self.update_style()

    def set_theme(self, theme: str) -> None:
        """Update the widget theme."""
        self.theme = theme
        self.update_style()
        self.refresh_messages()
        
    def update_style(self) -> None:
        """Update colors based on theme."""
        bg_color = "#1e1e1e" if self.theme == "dark" else "#ffffff"
        self.scroll_area.setStyleSheet(f"background-color: {bg_color}; border: none;")
        self.messages_container.setStyleSheet(f"background-color: {bg_color};")
    
    def refresh_messages(self) -> None:
        """Refresh all messages with the current theme."""
        # Clear layout
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Re-add all messages
        for text, is_user in self.messages:
            bubble = MessageBubble(text, is_user, self.theme)
            self.messages_layout.addWidget(bubble)
        
        self.messages_layout.addStretch()
        self.scroll_to_bottom()

    def add_message(self, text: str, is_user: bool) -> None:
        """
        Add a complete message to the chat.
        
        Args:
            text: Message text (markdown)
            is_user: True if user message, False if assistant
        """
        # Remove the stretch before adding a new message
        if self.messages_layout.count() > 0:
            last_item = self.messages_layout.itemAt(self.messages_layout.count() - 1)
            if last_item and (isinstance(last_item, QHBoxLayout) or last_item.spacerItem()):
                self.messages_layout.removeItem(last_item)

        bubble = MessageBubble(text, is_user, self.theme)
        self.messages_layout.addWidget(bubble)
        self.messages_layout.addStretch()
        
        self.messages.append((text, is_user))
        self.scroll_to_bottom()
        self.current_streaming_widget = None
    
    def start_streaming_message(self, is_user: bool = False) -> None:
        """
        Start a new streaming message.
        
        Args:
            is_user: True if user message, False if assistant
        """
        self.current_streaming_text = ""
        self.words_at_last_update = 0
        
        # Remove stretch
        if self.messages_layout.count() > 0:
            last_item = self.messages_layout.itemAt(self.messages_layout.count() - 1)
            if last_item and last_item.spacerItem():
                self.messages_layout.removeItem(last_item)
                
        bubble = MessageBubble("", is_user, self.theme)
        self.messages_layout.addWidget(bubble)
        self.messages_layout.addStretch()
        
        self.current_streaming_widget = bubble
        self.scroll_to_bottom()
    
    def append_streaming_text(self, text: str) -> None:
        """
        Append text to the current streaming message.
        
        Args:
            text: Text to append
        """
        if self.current_streaming_widget:
            self.current_streaming_text += text
            
            # Count current words after adding new text
            current_words = len(self.current_streaming_text.split())
            
            # Update criteria: 
            # 1. 15 words have passed since last update
            # 2. Or a newline is detected (completes a block/line)
            if (current_words - self.words_at_last_update >= 15) or ("\n" in text):
                self.current_streaming_widget.update_text(self.current_streaming_text, auto_scroll=True)
                self.scroll_to_bottom()
                self.words_at_last_update = current_words
    
    def finish_streaming_message(self) -> Optional[str]:
        """
        Finish the current streaming message.
        
        Returns:
            The complete message text, or None if no streaming message
        """
        if self.current_streaming_widget and self.current_streaming_text:
            # Final update to ensure remaining buffered text is shown
            self.current_streaming_widget.update_text(self.current_streaming_text, auto_scroll=True)
            self.scroll_to_bottom()
            
            self.messages.append((self.current_streaming_text, self.current_streaming_widget.is_user))
            self.current_streaming_widget = None
            return self.current_streaming_text
        
        return None
    
    def scroll_to_bottom(self) -> None:
        """Scroll chat display to the bottom."""
        # Use a timer to ensure the scroll happens after layout update
        QTimer.singleShot(10, self._do_scroll)
    
    def _do_scroll(self) -> None:
        """Internal method to perform the scroll."""
        try:
            scrollbar = self.scroll_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception:
            pass
    
    def get_messages(self) -> list:
        """
        Get all messages.
        
        Returns:
            List of (text, is_user) tuples
        """
        return self.messages.copy()
    
    def get_last_assistant_message(self) -> Optional[str]:
        """
        Get the last assistant message text.
        
        Returns:
            Message text or None
        """
        for text, is_user in reversed(self.messages):
            if not is_user:
                return text
        return None
    
    def clear(self) -> None:
        """Clear all messages from the chat."""
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.messages = []
        self.current_streaming_widget = None
        self.current_streaming_text = ""
