"""
Memory Bank for long-term storage of teacher preferences and patterns.
Implements ADK's memory pattern for personalized agent behavior.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from collections import defaultdict
from utils.observability import get_logger

logger = get_logger(__name__)


@dataclass
class TeacherProfile:
    """Long-term profile of a teacher."""
    teacher_id: str
    name: Optional[str] = None
    preferred_subjects: List[str] = field(default_factory=list)
    preferred_grades: List[int] = field(default_factory=list)
    teaching_style: Optional[str] = None  # e.g., "visual", "hands-on", "discussion-based"
    class_size: Optional[int] = None
    frequent_learning_strategies: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    lesson_plan_count: int = 0
    favorite_activities: List[str] = field(default_factory=list)


class MemoryBank:
    """
    Long-term memory storage for teacher preferences and patterns.
    Learns from repeated interactions to provide personalized suggestions.
    """
    
    def __init__(self):
        self.profiles: Dict[str, TeacherProfile] = {}
        self.request_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.logger = logger
    
    def get_or_create_profile(self, teacher_id: str, name: Optional[str] = None) -> TeacherProfile:
        """
        Get existing profile or create new one.
        
        Args:
            teacher_id: Unique teacher identifier
            name: Optional teacher name
            
        Returns:
            TeacherProfile instance
        """
        if teacher_id not in self.profiles:
            profile = TeacherProfile(teacher_id=teacher_id, name=name)
            self.profiles[teacher_id] = profile
            self.logger.info("profile_created", teacher_id=teacher_id, name=name)
        
        return self.profiles[teacher_id]
    
    def record_lesson_request(
        self, 
        teacher_id: str, 
        subject: str, 
        grade: int,
        learning_strategies: Optional[List[str]] = None,
        activities: Optional[List[str]] = None
    ) -> None:
        """
        Record a lesson plan request to learn teacher preferences.
        
        Args:
            teacher_id: Teacher identifier
            subject: Subject area
            grade: Grade level
            learning_strategies: Learning strategies used
            activities: Activities included
        """
        profile = self.get_or_create_profile(teacher_id)
        
        # Track subject preferences
        if subject not in profile.preferred_subjects:
            profile.preferred_subjects.append(subject)
        
        # Track grade preferences
        if grade not in profile.preferred_grades:
            profile.preferred_grades.append(grade)
        
        # Track learning strategies
        if learning_strategies:
            for strategy in learning_strategies:
                if strategy not in profile.frequent_learning_strategies:
                    profile.frequent_learning_strategies.append(strategy)
        
        # Track favorite activities
        if activities:
            for activity in activities:
                if activity not in profile.favorite_activities:
                    profile.favorite_activities.append(activity)
        
        # Increment lesson plan count
        profile.lesson_plan_count += 1
        profile.updated_at = datetime.now().isoformat()
        
        # Record in history
        self.request_history[teacher_id].append({
            "timestamp": datetime.now().isoformat(),
            "subject": subject,
            "grade": grade,
            "learning_strategies": learning_strategies or [],
            "activities": activities or []
        })
        
        self.logger.info(
            "lesson_request_recorded",
            teacher_id=teacher_id,
            subject=subject,
            grade=grade,
            total_plans=profile.lesson_plan_count
        )
    
    def get_personalized_suggestions(self, teacher_id: str) -> Dict[str, Any]:
        """
        Get personalized suggestions based on teacher's history.
        
        Args:
            teacher_id: Teacher identifier
            
        Returns:
            Dictionary of personalized suggestions
        """
        profile = self.get_or_create_profile(teacher_id)
        
        suggestions = {
            "preferred_subjects": profile.preferred_subjects[:3],  # Top 3
            "preferred_grades": profile.preferred_grades[:3],
            "suggested_strategies": profile.frequent_learning_strategies[:5],
            "favorite_activities": profile.favorite_activities[:5],
            "teaching_style": profile.teaching_style,
            "class_size": profile.class_size
        }
        
        self.logger.debug("suggestions_generated", teacher_id=teacher_id)
        return suggestions
    
    def update_teaching_style(self, teacher_id: str, teaching_style: str) -> None:
        """
        Update teacher's preferred teaching style.
        
        Args:
            teacher_id: Teacher identifier
            teaching_style: Teaching style preference
        """
        profile = self.get_or_create_profile(teacher_id)
        profile.teaching_style = teaching_style
        profile.updated_at = datetime.now().isoformat()
        self.logger.info("teaching_style_updated", teacher_id=teacher_id, style=teaching_style)
    
    def update_class_size(self, teacher_id: str, class_size: int) -> None:
        """
        Update teacher's typical class size.
        
        Args:
            teacher_id: Teacher identifier
            class_size: Number of students
        """
        profile = self.get_or_create_profile(teacher_id)
        profile.class_size = class_size
        profile.updated_at = datetime.now().isoformat()
        self.logger.info("class_size_updated", teacher_id=teacher_id, size=class_size)
    
    def get_request_history(self, teacher_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get teacher's lesson request history.
        
        Args:
            teacher_id: Teacher identifier
            limit: Optional limit on number of recent requests
            
        Returns:
            List of previous requests
        """
        history = self.request_history.get(teacher_id, [])
        if limit:
            history = history[-limit:]
        return history
    
    def export_memory_bank(self, filepath: str) -> None:
        """
        Export entire memory bank to JSON file.
        
        Args:
            filepath: Output file path
        """
        data = {
            "profiles": {
                teacher_id: {
                    "teacher_id": p.teacher_id,
                    "name": p.name,
                    "preferred_subjects": p.preferred_subjects,
                    "preferred_grades": p.preferred_grades,
                    "teaching_style": p.teaching_style,
                    "class_size": p.class_size,
                    "frequent_learning_strategies": p.frequent_learning_strategies,
                    "lesson_plan_count": p.lesson_plan_count,
                    "favorite_activities": p.favorite_activities,
                    "created_at": p.created_at,
                    "updated_at": p.updated_at
                }
                for teacher_id, p in self.profiles.items()
            },
            "request_history": dict(self.request_history)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info("memory_bank_exported", filepath=filepath, teacher_count=len(self.profiles))
