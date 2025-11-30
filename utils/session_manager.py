"""
Session management utilities for Pedagogue AI.
Handles conversation state and context across teacher interactions.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from utils.observability import get_logger

logger = get_logger(__name__)


@dataclass
class ConversationMessage:
    """A single message in the conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TeacherSession:
    """Represents a teacher's session with conversation history."""
    session_id: str
    teacher_name: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    messages: List[ConversationMessage] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    generated_plans: List[Dict[str, Any]] = field(default_factory=list)


class InMemorySessionService:
    """
    In-memory session management service.
    Implements ADK's session pattern for conversation state tracking.
    """
    
    def __init__(self):
        self.sessions: Dict[str, TeacherSession] = {}
        self.logger = logger
    
    def create_session(self, session_id: str, teacher_name: Optional[str] = None) -> TeacherSession:
        """
        Create a new teacher session.
        
        Args:
            session_id: Unique session identifier
            teacher_name: Optional teacher name
            
        Returns:
            New TeacherSession instance
        """
        session = TeacherSession(
            session_id=session_id,
            teacher_name=teacher_name
        )
        self.sessions[session_id] = session
        self.logger.info("session_created", session_id=session_id, teacher=teacher_name)
        return session
    
    def get_session(self, session_id: str) -> Optional[TeacherSession]:
        """
        Retrieve an existing session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            TeacherSession if found, None otherwise
        """
        return self.sessions.get(session_id)
    
    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata about the message
        """
        session = self.get_session(session_id)
        if not session:
            self.logger.warning("session_not_found", session_id=session_id)
            return
        
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        session.messages.append(message)
        self.logger.debug("message_added", session_id=session_id, role=role)
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[ConversationMessage]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of recent messages
            
        Returns:
            List of conversation messages
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = session.messages
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def update_preferences(self, session_id: str, preferences: Dict[str, Any]) -> None:
        """
        Update teacher preferences for a session.
        
        Args:
            session_id: Session identifier
            preferences: Dictionary of teacher preferences
        """
        session = self.get_session(session_id)
        if not session:
            self.logger.warning("session_not_found", session_id=session_id)
            return
        
        session.preferences.update(preferences)
        self.logger.info("preferences_updated", session_id=session_id, prefs=list(preferences.keys()))
    
    def add_generated_plan(self, session_id: str, plan: Dict[str, Any]) -> None:
        """
        Track a generated lesson plan.
        
        Args:
            session_id: Session identifier
            plan: Lesson plan metadata
        """
        session = self.get_session(session_id)
        if not session:
            self.logger.warning("session_not_found", session_id=session_id)
            return
        
        plan['generated_at'] = datetime.now().isoformat()
        session.generated_plans.append(plan)
        self.logger.info("plan_tracked", session_id=session_id, plan_count=len(session.generated_plans))
    
    def compact_context(self, session_id: str, max_messages: int = 10) -> str:
        """
        Compact conversation context for long sessions.
        Implements context compaction by summarizing older messages.
        
        Args:
            session_id: Session identifier
            max_messages: Maximum number of recent messages to keep in full
            
        Returns:
            Compacted context summary
        """
        session = self.get_session(session_id)
        if not session or len(session.messages) <= max_messages:
            return ""
        
        # Keep recent messages, summarize older ones
        older_messages = session.messages[:-max_messages]
        summary = f"Previous conversation ({len(older_messages)} messages): "
        
        # Count requests by subject
        subjects = {}
        for msg in older_messages:
            if msg.role == "user" and "subject" in msg.metadata:
                subject = msg.metadata["subject"]
                subjects[subject] = subjects.get(subject, 0) + 1
        
        if subjects:
            summary += "Teacher requested lesson plans for: " + ", ".join(
                f"{subj} ({count}x)" for subj, count in subjects.items()
            )
        
        self.logger.info("context_compacted", session_id=session_id, 
                        older_msgs=len(older_messages), kept_msgs=max_messages)
        
        return summary
    
    def export_session(self, session_id: str, filepath: str) -> None:
        """
        Export session data to JSON file.
        
        Args:
            session_id: Session identifier
            filepath: Output file path
        """
        session = self.get_session(session_id)
        if not session:
            self.logger.warning("session_not_found", session_id=session_id)
            return
        
        session_data = {
            "session_id": session.session_id,
            "teacher_name": session.teacher_name,
            "created_at": session.created_at,
            "preferences": session.preferences,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }
                for msg in session.messages
            ],
            "generated_plans": session.generated_plans
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info("session_exported", session_id=session_id, filepath=filepath)
