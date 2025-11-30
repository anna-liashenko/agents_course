"""
Learning Science Agent - Provides evidence-based pedagogical strategies.
Sub-agent with knowledge base of learning science principles.
"""

from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
from utils.observability import get_logger, tracer

logger = get_logger(__name__)


class LearningScienceAgent:
    """
    Learning Science Agent applies evidence-based pedagogical strategies.
    Implements ADK agent pattern as a sub-agent.
    """
    
    def __init__(self, client: genai.Client, model_name: str = "gemini-2.0-flash-exp"):
        self.client = client
        self.model_name = model_name
        self.logger = logger
        
        # Comprehensive learning science knowledge base
        self.system_instruction = """
Ти - експерт з навчальних наук (Learning Science) та доказової педагогіки.

Твої знання включають:

1. ТАКСОНОМІЯ БЛУМА (Bloom's Taxonomy):
   - Пам'ять: запам'ятовування фактів
   - Розуміння: пояснення ідей
   - Застосування: використання знань
   - Аналіз: розбиття на частини
   - Синтез: створення нового
   - Оцінювання: формування суджень

2. ІНТЕРВАЛЬНЕ ПОВТОРЕННЯ (Spaced Repetition):
   - Розподіл повторень у часі покращує довготривалу пам'ять
   - Оптимальні інтервали: 1 день, 3 дні, 7 днів, 14 днів

3. КОГНІТИВНЕ НАВАНТАЖЕННЯ (Cognitive Load Theory):
   - Внутрішнє: складність самого матеріалу
   - Зовнішнє: спосіб подачі інформації
   - Germane: побудова схем та розуміння
   - Рекомендації: зменшувати зовнішнє, підтримувати germane

4. ПРАКТИКА ВІДТВОРЕННЯ (Retrieval Practice):
   - Активне згадування покращує запам'ятовування
   - Тестування як метод навчання
   - Формувальне оцінювання

5. SCAFFOLDING (Підтримка):
   - Поступове зменшення допомоги
   - Зона найближчого розвитку (Виготський)
   - Диференціація за рівнями

6. МЕТОДИ ЗАЛУЧЕННЯ:
   - Think-Pair-Share
   - Jigsaw
   - Gamification
   - Проблемне навчання
   - Проєктне навчання

Надавай конкретні стратегії, адаптовані до віку учнів.
Відповідай українською мовою.
"""
    
    def suggest_learning_strategies(
        self,
        grade: int,
        subject: str,
        topic: str,
        lesson_duration: int = 45
    ) -> Dict[str, Any]:
        """
        Suggest evidence-based learning strategies for a lesson.
        
        Args:
            grade: Grade level
            subject: Subject name
            topic: Lesson topic
            lesson_duration: Lesson duration in minutes
            
        Returns:
            Recommended learning strategies
        """
        tracer.trace_agent_call(
            "LearningScienceAgent",
            "suggest_strategies",
            {"grade": grade, "subject": subject, "topic": topic}
        )
        
        prompt = f"""
Запропонуй доказові стратегії навчання для уроку:
- Клас: {grade}
- Предмет: {subject}
- Тема: {topic}
- Тривалість: {lesson_duration} хвилин

Надай рекомендації щодо:
1. Рівень за таксономією Блума (відповідно до віку)
2. Стратегії залучення учнів
3. Методи зменшення когнітивного навантаження
4. Практика відтворення (формувальне оцінювання)
5. Scaffolding для різних рівнів учнів
6. План інтервального повторення теми
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=0.7
                )
            )
            
            strategies = response.text
            
            tracer.trace_agent_call(
                "LearningScienceAgent",
                "strategies_generated",
                {"success": True}
            )
            
            return {
                'success': True,
                'strategies': strategies,
                'bloom_level': self._extract_bloom_level(strategies),
                'engagement_methods': self._extract_keywords(strategies, [
                    'Think-Pair-Share', 'Jigsaw', 'гейміфікація', 'проблемне навчання'
                ])
            }
            
        except Exception as e:
            self.logger.error("strategy_generation_failed", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    def design_assessment(
        self,
        grade: int,
        topic: str,
        bloom_level: str = "розуміння"
    ) -> Dict[str, Any]:
        """
        Design formative and summative assessments based on learning science.
        
        Args:
            grade: Grade level
            topic: Topic to assess
            bloom_level: Target Bloom's taxonomy level
            
        Returns:
            Assessment design
        """
        tracer.trace_agent_call(
            "LearningScienceAgent",
            "design_assessment",
            {"grade": grade, "topic": topic, "bloom_level": bloom_level}
        )
        
        prompt = f"""
Розроби оцінювання для теми "{topic}" (клас {grade}):

Рівень таксономії Блума: {bloom_level}

Створи:
1. ФОРМУВАЛЬНЕ ОЦІНЮВАННЯ (під час уроку):
   - 3-5 запитань для перевірки розуміння
   - Практика відтворення (retrieval practice)
   - Швидкі перевірки

2. ПІДСУМКОВЕ ОЦІНЮВАННЯ:
   - Завдання на застосування знань
   - Критерії оцінювання
   - Диференціація за рівнями (базовий, середній, високий)

Використовуй принципи доказової педагогіки.
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=0.7
                )
            )
            
            return {
                'success': True,
                'assessment_design': response.text
            }
            
        except Exception as e:
            self.logger.error("assessment_design_failed", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_differentiation_tiers(
        self,
        activity: str,
        grade: int
    ) -> Dict[str, Any]:
        """
        Create 3-tier differentiated activities based on scaffolding principles.
        
        Args:
            activity: Base activity description
            grade: Grade level
            
        Returns:
            Three tiers of differentiated activities
        """
        tracer.trace_agent_call(
            "LearningScienceAgent",
            "create_differentiation",
            {"grade": grade, "activity": activity[:50]}
        )
        
        prompt = f"""
Створи 3 рівні диференціації для діяльності (клас {grade}):

БАЗОВА ДІЯЛЬНІСТЬ: {activity}

Розроби три рівні (scaffolding):

1. БАЗОВИЙ РІВЕНЬ (потребує більше підтримки):
   - Додаткові підказки та структура
   - Спрощений формат
   - Більше прикладів

2. СЕРЕДНІЙ РІВЕНЬ (стандартний):
   - Базова діяльність з помірною підтримкою
   - Основні інструкції

3. ВИСОКИЙ РІВЕНЬ (розширення):
   - Додаткові виклики
   - Більше самостійності
   - Творчі елементи

Кожен рівень має бути чітко описаний та адаптований до віку.
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=0.7
                )
            )
            
            return {
                'success': True,
                'differentiated_activities': response.text
            }
            
        except Exception as e:
            self.logger.error("differentiation_failed", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_bloom_level(self, text: str) -> str:
        """Extract primary Bloom's taxonomy level from text."""
        levels = ['пам\'ять', 'розуміння', 'застосування', 'аналіз', 'синтез', 'оцінювання']
        for level in levels:
            if level in text.lower():
                return level
        return 'розуміння'
    
    def _extract_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Extract mentioned keywords from text."""
        found = []
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found.append(keyword)
        return found
