"""
Content Generator Agent - Creates lesson plan components in Ukrainian.
Sub-agent that generates educational materials.
"""

from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
from utils.observability import get_logger, tracer

logger = get_logger(__name__)


class ContentGeneratorAgent:
    """
    Content Generator Agent creates lesson plan components in Ukrainian.
    Implements ADK agent pattern as a sub-agent.
    """
    
    def __init__(self, client: genai.Client, model_name: str = "gemini-2.0-flash-exp"):
        self.client = client
        self.model_name = model_name
        self.logger = logger
        
        self.system_instruction = """
Ти - досвідчений український вчитель, який створює якісні навчальні матеріали.

Твоя роль:
- Створювати конкретні, практичні компоненти планів уроків
- Писати SMART цілі навчання (Specific, Measurable, Achievable, Relevant, Time-bound)
- Розробляти цікаві розминки та активності
- Створювати диференційовані завдання для різних рівнів учнів
- Розробляти якісні питання та завдання для оцінювання

Завжди пиши українською мовою. Враховуй вікові особливості учнів.
Матеріали мають бути практичними та готовими до використання.
"""
    
    def generate_learning_objectives(
        self,
        grade: int,
        subject: str,
        topic: str,
        standards: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate SMART learning objectives.
        
        Args:
            grade: Grade level
            subject: Subject name
            topic: Lesson topic
            standards: Optional НУШ standards for alignment
            
        Returns:
            Learning objectives
        """
        tracer.trace_agent_call(
            "ContentGeneratorAgent",
            "generate_objectives",
            {"grade": grade, "subject": subject, "topic": topic}
        )
        
        standards_text = ""
        if standards:
            outcomes = standards.get('learning_outcomes', [])
            if outcomes:
                standards_text = f"\n\nОЧІКУВАНІ РЕЗУЛЬТАТИ (НУШ):\n" + "\n".join(outcomes[:3])
        
        prompt = f"""
Створи 3-5 SMART цілей навчання для уроку:
- Клас: {grade}
- Предмет: {subject}
- Тема: {topic}{standards_text}

Кожна ціль має бути:
- Specific (конкретна)
- Measurable (вимірювана)
- Achievable (досяжна)
- Relevant (відповідна)
- Time-bound (обмежена в часі - протягом уроку)

Починай з дієслів: "Учні зможуть...", "Учні навчаться...", "Учні продемонструють..."
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=0.8
                )
            )
            
            return {
                'success': True,
                'objectives': response.text
            }
            
        except Exception as e:
            self.logger.error("objectives_generation_failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def generate_warmup(
        self,
        grade: int,
        topic: str,
        duration: int = 5
    ) -> Dict[str, Any]:
        """
        Generate engaging warm-up activity.
        
        Args:
            grade: Grade level
            topic: Lesson topic
            duration: Warm-up duration in minutes
            
        Returns:
            Warm-up activity
        """
        tracer.trace_agent_call(
            "ContentGeneratorAgent",
            "generate_warmup",
            {"grade": grade, "topic": topic, "duration": duration}
        )
        
        prompt = f"""
Створи цікаву розминку для уроку:
- Клас: {grade}
- Тема: {topic}
- Тривалість: {duration} хвилин

Розминка має:
- Активізувати попередні знання
- Зацікавити учнів темою
- Бути інтерактивною та цікавою
- Відповідати віку учнів
- Містити чіткі інструкції

Опиши крок за кроком, що робить вчитель і що роблять учні.
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=0.9
                )
            )
            
            return {
                'success': True,
                'warmup': response.text
            }
            
        except Exception as e:
            self.logger.error("warmup_generation_failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def generate_direct_instruction(
        self,
        grade: int,
        topic: str,
        key_concepts: List[str],
        duration: int = 15
    ) -> Dict[str, Any]:
        """
        Generate direct instruction content.
        
        Args:
            grade: Grade level
            topic: Lesson topic
            key_concepts: Key concepts to teach
            duration: Instruction duration in minutes
            
        Returns:
            Direct instruction content
        """
        tracer.trace_agent_call(
            "ContentGeneratorAgent",
            "generate_instruction",
            {"grade": grade, "topic": topic}
        )
        
        concepts_text = "\n".join([f"- {concept}" for concept in key_concepts])
        
        prompt = f"""
Створи зміст для прямого навчання:
- Клас: {grade}
- Тема: {topic}
- Тривалість: {duration} хвилин

КЛЮЧОВІ ПОНЯТТЯ:
{concepts_text}

Включи:
1. Пояснення кожного поняття простою мовою
2. Приклади з реального життя (адаптовані до віку)
3. Візуальні підказки / аналогії
4. Питання для перевірки розуміння
5. Поширені помилки та як їх уникнути

Структуруй матеріал для легкого викладання.
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
                'instruction_content': response.text
            }
            
        except Exception as e:
            self.logger.error("instruction_generation_failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def generate_practice_activities(
        self,
        grade: int,
        topic: str,
        activity_type: str = "guided"
    ) -> Dict[str, Any]:
        """
        Generate practice activities (guided or independent).
        
        Args:
            grade: Grade level
            topic: Lesson topic
            activity_type: "guided" or "independent"
            
        Returns:
            Practice activities
        """
        tracer.trace_agent_call(
            "ContentGeneratorAgent",
            "generate_practice",
            {"grade": grade, "type": activity_type}
        )
        
        activity_desc = {
            "guided": "під керівництвом вчителя (спільна робота)",
            "independent": "самостійну роботу (індивідуальну або групову)"
        }
        
        prompt = f"""
Створи {activity_desc.get(activity_type, 'практичну')} діяльність:
- Клас: {grade}
- Тема: {topic}

Діяльність має:
- Давати учням можливість застосувати знання
- Бути чітко структурованою
- Містити конкретні завдання
- Бути цікавою та мотивуючою
- Відповідати віковим особливостям

Опиши:
1. Назву та мету діяльності
2. Матеріали, що знадобляться
3. Покрокові інструкції
4. Орієнтовний час виконання
5. Критерії успіху
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=0.85
                )
            )
            
            return {
                'success': True,
                'activity': response.text,
                'type': activity_type
            }
            
        except Exception as e:
            self.logger.error("practice_generation_failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def generate_assessment_items(
        self,
        grade: int,
        topic: str,
        assessment_type: str = "formative",
        item_count: int = 5
    ) -> Dict[str, Any]:
        """
        Generate assessment items.
        
        Args:
            grade: Grade level
            topic: Topic to assess
            assessment_type: "formative" or "summative"
            item_count: Number of items to generate
            
        Returns:
            Assessment items
        """
        tracer.trace_agent_call(
            "ContentGeneratorAgent",
            "generate_assessment",
            {"grade": grade, "type": assessment_type, "count": item_count}
        )
        
        assessment_desc = {
            "formative": "формувального оцінювання (під час уроку, швидка перевірка)",
            "summative": "підсумкового оцінювання (в кінці теми, детальна перевірка)"
        }
        
        prompt = f"""
Створи {item_count} завдань для {assessment_desc.get(assessment_type, 'оцінювання')}:
- Клас: {grade}
- Тема: {topic}

Завдання мають:
- Перевіряти розуміння та застосування знань
- Бути різних типів (відкриті, закриті, практичні)
- Відповідати віку учнів
- Включати критерії оцінювання

Для кожного завдання вказуй:
1. Формулювання завдання
2. Тип завдання
3. Очікувану відповідь / критерії оцінювання
4. Можливі бали (якщо потрібно)
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
                'assessment_items': response.text,
                'type': assessment_type,
                'count': item_count
            }
            
        except Exception as e:
            self.logger.error("assessment_items_generation_failed", error=str(e))
            return {'success': False, 'error': str(e)}
