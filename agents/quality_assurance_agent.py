"""
Quality Assurance Agent - Reviews lesson plans for quality and completeness.
Sub-agent that validates and improves generated content.
"""

from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
from utils.observability import get_logger, tracer

logger = get_logger(__name__)


class QualityAssuranceAgent:
    """
    Quality Assurance Agent reviews lesson plans for accuracy and quality.
    Implements ADK agent pattern as a sub-agent.
    """
    
    def __init__(self, client: genai.Client, model_name: str = "gemini-2.0-flash-exp"):
        self.client = client
        self.model_name = model_name
        self.logger = logger
        
        self.system_instruction = """
Ти - експерт з педагогіки, який перевіряє якість навчальних матеріалів.

Твоя роль:
- Перевіряти плани уроків на повноту та якість
- Знаходити помилки, неточності та недоліки
- Оцінювати відповідність віку учнів
- Перевіряти культурну чутливість (контекст України)
- Надавати конкретні рекомендації щодо покращення

Критерії якості:
1. ТОЧНІСТЬ: чи є фактичні помилки?
2. ПОВНОТА: чи всі компоненти уроку присутні?
3. ВІДПОВІДНІСТЬ ВІКУ: чи підходить для даного класу?
4. ЧІТКІСТЬ: чи зрозумілі інструкції?
5. КУЛЬТУРНА ЧУТЛИВІСТЬ: чи відповідає українському контексту?
6. ЗАЛУЧЕННЯ: чи цікаво для учнів?
7. ДИФЕРЕНЦІАЦІЯ: чи враховані різні рівні учнів?

Будь конструктивним та надавай конкретні пропозиції.
Відповідай українською мовою.
"""
    
    def review_lesson_plan(
        self,
        lesson_plan: Dict[str, Any],
        grade: int,
        subject: str
    ) -> Dict[str, Any]:
        """
        Review complete lesson plan for quality.
        
        Args:
            lesson_plan: Dictionary containing all lesson components
            grade: Grade level
            subject: Subject name
            
        Returns:
            Review results with scores and suggestions
        """
        tracer.trace_agent_call(
            "QualityAssuranceAgent",
            "review_lesson_plan",
            {"grade": grade, "subject": subject}
        )
        
        # Format lesson plan for review
        plan_text = self._format_lesson_plan(lesson_plan)
        
        prompt = f"""
Перевір план уроку для {grade} класу з предмету "{subject}".

ПЛАН УРОКУ:
{plan_text}

Надай детальний відгук:

1. ОЦІНКА ЗА КРИТЕРІЯМИ (1-10 балів):
   - Точність та фактична правильність: __/10
   - Повнота (всі компоненти присутні): __/10
   - Відповідність віку: __/10
   - Чіткість інструкцій: __/10
   - Культурна відповідність: __/10
   - Рівень залучення учнів: __/10
   - Диференціація: __/10

2. СИЛЬНІ СТОРОНИ:
   Що добре зроблено в цьому плані?

3. ПОТРЕБУЄ ПОКРАЩЕННЯ:
   Що потрібно виправити або покращити?

4. КОНКРЕТНІ РЕКОМЕНДАЦІЇ:
   Надай 3-5 конкретних пропозицій щодо покращення.

5. ЗАГАЛЬНА ОЦІНКА:
   Готовий до використання / Потребує незначних змін / Потребує значного доопрацювання
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=0.3
                )
            )
            
            review_text = response.text
            
            # Parse scores
            scores = self._extract_scores(review_text)
            overall_status = self._extract_status(review_text)
            
            tracer.trace_agent_call(
                "QualityAssuranceAgent",
                "review_completed",
                {"average_score": scores.get('average', 0), "status": overall_status}
            )
            
            return {
                'success': True,
                'review': review_text,
                'scores': scores,
                'overall_status': overall_status,
                'ready_to_use': overall_status == 'ready'
            }
            
        except Exception as e:
            self.logger.error("review_failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def check_age_appropriateness(
        self,
        content: str,
        grade: int
    ) -> Dict[str, Any]:
        """
        Check if content is age-appropriate.
        
        Args:
            content: Content to check
            grade: Grade level
            
        Returns:
            Age-appropriateness assessment
        """
        tracer.trace_agent_call(
            "QualityAssuranceAgent",
            "check_age_appropriateness",
            {"grade": grade}
        )
        
        prompt = f"""
Оціни, чи відповідає наступний контент віковим особливостям учнів {grade} класу:

КОНТЕНТ:
{content}

Перевір:
1. Складність мови та термінології
2. Складність завдань та понять
3. Тривалість концентрації уваги
4. Емоційна зрілість
5. Попередні знання

Надай оцінку: Відповідає / Занадто складно / Занадто просто
Поясни чому та надай рекомендації щодо адаптації (якщо потрібно).
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=0.3
                )
            )
            
            assessment = response.text
            appropriate = 'відповідає' in assessment.lower()
            
            return {
                'success': True,
                'assessment': assessment,
                'appropriate': appropriate
            }
            
        except Exception as e:
            self.logger.error("age_check_failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def check_cultural_sensitivity(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        Check cultural sensitivity for Ukrainian context.
        
        Args:
            content: Content to check
            
        Returns:
            Cultural sensitivity assessment
        """
        tracer.trace_agent_call(
            "QualityAssuranceAgent",
            "check_cultural_sensitivity",
            {}
        )
        
        prompt = f"""
Перевір культурну відповідність для українського контексту:

КОНТЕНТ:
{content}

Оціни:
1. Чи використані відповідні приклади для України?
2. Чи враховані українські реалії та традиції?
3. Чи немає культурно невідповідних елементів?
4. Чи відповідає сучасним цінностям української освіти?
5. Чи коректна українська мова?

Вкажи будь-які проблеми та запропонуй альтернативи.
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=0.3
                )
            )
            
            assessment = response.text
            sensitive = 'проблем' not in assessment.lower() or 'відповідає' in assessment.lower()
            
            return {
                'success': True,
                'assessment': assessment,
                'culturally_sensitive': sensitive
            }
            
        except Exception as e:
            self.logger.error("cultural_check_failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def suggest_improvements(
        self,
        component: str,
        component_type: str,
        grade: int
    ) -> Dict[str, Any]:
        """
        Suggest specific improvements for a lesson component.
        
        Args:
            component: Component text
            component_type: Type (e.g., "objectives", "warmup", "activity")
            grade: Grade level
            
        Returns:
            Improvement suggestions
        """
        tracer.trace_agent_call(
            "QualityAssuranceAgent",
            "suggest_improvements",
            {"type": component_type, "grade": grade}
        )
        
        prompt = f"""
Проаналізуй компонент плану уроку та запропонуй покращення:

ТИП КОМПОНЕНТУ: {component_type}
КЛАС: {grade}

ПОТОЧНА ВЕРСІЯ:
{component}

Надай:
1. Що можна покращити?
2. Конкретні пропозиції змін
3. Покращену версію компоненту (якщо потрібно значне доопрацювання)
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
                'suggestions': response.text
            }
            
        except Exception as e:
            self.logger.error("improvement_suggestions_failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def _format_lesson_plan(self, lesson_plan: Dict[str, Any]) -> str:
        """Format lesson plan dictionary as text."""
        sections = []
        
        for key, value in lesson_plan.items():
            if isinstance(value, dict) and value.get('success'):
                # Extract the main content from nested dictionaries
                content = value.get('objectives') or value.get('warmup') or \
                         value.get('instruction_content') or value.get('activity') or \
                         value.get('assessment_items') or value.get('strategies') or \
                         value.get('differentiated_activities') or str(value)
            elif isinstance(value, str):
                content = value
            else:
                content = str(value)
            
            sections.append(f"=== {key.upper().replace('_', ' ')} ===\n{content}\n")
        
        return "\n".join(sections)
    
    def _extract_scores(self, review_text: str) -> Dict[str, float]:
        """Extract numerical scores from review."""
        import re
        scores = {}
        
        # Look for patterns like "Точність: 8/10" or "8/10"
        pattern = r'(\d+)/10'
        matches = re.findall(pattern, review_text)
        
        if matches:
            score_values = [int(m) for m in matches]
            scores['average'] = sum(score_values) / len(score_values)
            scores['individual'] = score_values
        else:
            scores['average'] = 7.0  # Default
        
        return scores
    
    def _extract_status(self, review_text: str) -> str:
        """Extract overall status from review."""
        text_lower = review_text.lower()
        
        if 'готовий до використання' in text_lower:
            return 'ready'
        elif 'потребує незначних змін' in text_lower:
            return 'minor_changes'
        elif 'потребує значного доопрацювання' in text_lower:
            return 'major_changes'
        else:
            return 'unknown'
