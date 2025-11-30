"""
Orchestrator Agent - Coordinates all sub-agents to generate complete lesson plans.
Root agent that implements multi-agent workflow with parallel and sequential execution.
"""

import asyncio
from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
from agents.standards_agent import StandardsAgent
from agents.learning_science_agent import LearningScienceAgent
from agents.content_generator_agent import ContentGeneratorAgent
from agents.quality_assurance_agent import QualityAssuranceAgent
from utils.session_manager import InMemorySessionService
from utils.memory_bank import MemoryBank
from utils.observability import get_logger, tracer

logger = get_logger(__name__)


class OrchestratorAgent:
    """
    Orchestrator Agent coordinates all sub-agents to generate lesson plans.
    Implements ADK multi-agent pattern with parallel and sequential execution.
    """
    
    def __init__(
        self,
        client: genai.Client,
        model_name: str = "gemini-2.0-flash-exp",
        session_service: Optional[InMemorySessionService] = None,
        memory_bank: Optional[MemoryBank] = None
    ):
        self.client = client
        self.model_name = model_name
        self.logger = logger
        
        # Initialize sub-agents
        self.standards_agent = StandardsAgent(client, model_name)
        self.learning_science_agent = LearningScienceAgent(client, model_name)
        self.content_generator = ContentGeneratorAgent(client, model_name)
        self.qa_agent = QualityAssuranceAgent(client, model_name)
        
        # Session and memory management
        self.session_service = session_service or InMemorySessionService()
        self.memory_bank = memory_bank or MemoryBank()
        
        self.system_instruction = """
Ти - головний координатор системи підтримки вчителів "Pedagogue AI".

Твоя роль:
- Аналізувати запити українських вчителів
- Координувати роботу спеціалізованих агентів
- Збирати результати в повноцінний план уроку
- Враховувати особливості та уподобання вчителя

Завжди спілкуйся українською мовою та будь корисним помічником вчителя.
"""
    
    async def generate_lesson_plan(
        self,
        grade: int,
        subject: str,
        topic: str,
        duration: int = 45,
        teacher_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete lesson plan by orchestrating sub-agents.
        Implements parallel and sequential execution patterns.
        
        Args:
            grade: Grade level (1-11)
            subject: Subject name in Ukrainian
            topic: Lesson topic
            duration: Lesson duration in minutes
            teacher_id: Optional teacher ID for personalization
            session_id: Optional session ID for conversation tracking
            
        Returns:
            Complete lesson plan with all components
        """
        tracer.trace_agent_call(
            "OrchestratorAgent",
            "generate_lesson_plan",
            {
                "grade": grade,
                "subject": subject,
                "topic": topic,
                "duration": duration
            }
        )
        
        self.logger.info(
            "lesson_plan_generation_started",
            grade=grade,
            subject=subject,
            topic=topic
        )
        
        # Record in session if provided
        if session_id:
            self.session_service.add_message(
                session_id,
                "user",
                f"Створити план уроку: {grade} клас, {subject}, тема: {topic}",
                {"grade": grade, "subject": subject, "topic": topic}
            )
        
        # Get personalized suggestions if teacher_id provided
        suggestions = {}
        if teacher_id:
            suggestions = self.memory_bank.get_personalized_suggestions(teacher_id)
            self.logger.info("personalized_suggestions_loaded", teacher_id=teacher_id)
        
        # PHASE 1: PARALLEL EXECUTION - Standards + Learning Science
        # These can run in parallel as they don't depend on each other
        self.logger.info("phase_1_parallel_execution")
        
        standards_task = asyncio.create_task(
            asyncio.to_thread(self.standards_agent.get_standards, grade, subject)
        )
        
        learning_science_task = asyncio.create_task(
            asyncio.to_thread(
                self.learning_science_agent.suggest_learning_strategies,
                grade, subject, topic, duration
            )
        )
        
        # Wait for both to complete
        standards_result, learning_strategies = await asyncio.gather(
            standards_task,
            learning_science_task
        )
        
        self.logger.info(
            "phase_1_completed",
            standards_success=standards_result.get('success'),
            strategies_success=learning_strategies.get('success')
        )
        
        # PHASE 2: SEQUENTIAL EXECUTION - Content Generation
        # Generate content sequentially, building on previous results
        self.logger.info("phase_2_sequential_execution")
        
        # 2.1: Learning objectives (based on standards)
        objectives = await asyncio.to_thread(
            self.content_generator.generate_learning_objectives,
            grade, subject, topic,
            standards_result.get('standards') if standards_result.get('success') else None
        )
        
        # 2.2: Warm-up activity
        warmup = await asyncio.to_thread(
            self.content_generator.generate_warmup,
            grade, topic, 5
        )
        
        # 2.3: Direct instruction
        key_concepts = self._extract_key_concepts(topic, standards_result)
        instruction = await asyncio.to_thread(
            self.content_generator.generate_direct_instruction,
            grade, topic, key_concepts, 15
        )
        
        # 2.4: Guided practice
        guided_practice = await asyncio.to_thread(
            self.content_generator.generate_practice_activities,
            grade, topic, "guided"
        )
        
        # 2.5: Differentiated activities (3-tier)
        differentiation = await asyncio.to_thread(
            self.learning_science_agent.create_differentiation_tiers,
            guided_practice.get('activity', ''), grade
        )
        
        # 2.6: Independent practice
        independent_practice = await asyncio.to_thread(
            self.content_generator.generate_practice_activities,
            grade, topic, "independent"
        )
        
        # 2.7: Assessment (formative and summative)
        formative_assessment = await asyncio.to_thread(
            self.content_generator.generate_assessment_items,
            grade, topic, "formative", 5
        )
        
        summative_assessment = await asyncio.to_thread(
            self.learning_science_agent.design_assessment,
            grade, topic, learning_strategies.get('bloom_level', 'розуміння')
        )
        
        self.logger.info("phase_2_completed", all_components_generated=True)
        
        # PHASE 3: Quality Assurance (sequential after content)
        self.logger.info("phase_3_quality_assurance")
        
        lesson_plan = {
            'metadata': {
                'grade': grade,
                'subject': subject,
                'topic': topic,
                'duration': duration
            },
            'standards': standards_result,
            'learning_strategies': learning_strategies,
            'objectives': objectives,
            'warmup': warmup,
            'instruction': instruction,
            'guided_practice': guided_practice,
            'differentiation': differentiation,
            'independent_practice': independent_practice,
            'formative_assessment': formative_assessment,
            'summative_assessment': summative_assessment
        }
        
        # QA Review
        qa_review = await asyncio.to_thread(
            self.qa_agent.review_lesson_plan,
            lesson_plan, grade, subject
        )
        
        lesson_plan['qa_review'] = qa_review
        
        self.logger.info(
            "lesson_plan_generation_completed",
            grade=grade,
            subject=subject,
            qa_score=qa_review.get('scores', {}).get('average', 0),
            ready=qa_review.get('ready_to_use', False)
        )
        
        # Record in memory bank
        if teacher_id:
            self.memory_bank.record_lesson_request(
                teacher_id,
                subject,
                grade,
                learning_strategies.get('engagement_methods', []),
                [warmup.get('warmup', '')]
            )
        
        # Record in session
        if session_id:
            self.session_service.add_message(
                session_id,
                "assistant",
                "План уроку згенеровано успішно",
                {"qa_score": qa_review.get('scores', {}).get('average', 0)}
            )
            self.session_service.add_generated_plan(
                session_id,
                {
                    'grade': grade,
                    'subject': subject,
                    'topic': topic,
                    'qa_score': qa_review.get('scores', {}).get('average', 0)
                }
            )
        
        return {
            'success': True,
            'lesson_plan': lesson_plan,
            'personalized_suggestions': suggestions
        }
    
    def _extract_key_concepts(
        self,
        topic: str,
        standards_result: Dict[str, Any]
    ) -> List[str]:
        """Extract key concepts from topic and standards."""
        concepts = [topic]
        
        if standards_result.get('success'):
            # Add up to 3 competencies as key concepts
            competencies = standards_result.get('competencies', [])
            for comp in competencies[:3]:
                if len(comp) > 10:  # Filter out very short items
                    concepts.append(comp)
        
        return concepts[:5]  # Limit to 5 key concepts
    
    async def handle_teacher_request(
        self,
        request: str,
        teacher_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Handle natural language teacher request.
        Uses AI to parse the request and generate lesson plan.
        
        Args:
            request: Teacher's request in Ukrainian
            teacher_id: Teacher identifier
            session_id: Session identifier
            
        Returns:
            Generated lesson plan or response
        """
        tracer.trace_agent_call(
            "OrchestratorAgent",
            "handle_teacher_request",
            {"teacher_id": teacher_id, "session_id": session_id}
        )
        
        # Add to session
        self.session_service.add_message(session_id, "user", request)
        
        # Parse request using AI
        parse_prompt = f"""
Проаналізуй запит українського вчителя та визнач параметри для генерації плану уроку.

ЗАПИТ ВЧИТЕЛЯ: {request}

Визнач та надай у форматі JSON:
{{
    "grade": <номер класу 1-11>,
    "subject": "<назва предмету українською>",
    "topic": "<тема уроку>",
    "duration": <тривалість в хвилинах, за замовчуванням 45>
}}

Якщо якась інформація відсутня, використовуй null.
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=parse_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            
            import json
            # Handle different response formats
            if hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text
            elif hasattr(response, 'text'):
                response_text = response.text
            else:
                response_text = str(response)
            
            params = json.loads(response_text)
            
            # Handle if AI returns a list instead of a dict
            if isinstance(params, list):
                if len(params) > 0:
                    params = params[0]
                else:
                    return {
                        'success': False,
                        'message': 'Не вдалося розпізнати параметри запиту. Спробуйте ще раз.'
                    }
            
            # Validate required fields
            if not all([params.get('grade'), params.get('subject'), params.get('topic')]):
                return {
                    'success': False,
                    'message': 'Будь ласка, вкажіть клас, предмет та тему уроку.',
                    'missing_fields': [k for k in ['grade', 'subject', 'topic'] if not params.get(k)]
                }
            
            # Generate lesson plan
            result = await self.generate_lesson_plan(
                grade=params['grade'],
                subject=params['subject'],
                topic=params['topic'],
                duration=params.get('duration', 45),
                teacher_id=teacher_id,
                session_id=session_id
            )
            
            return result
            
        except Exception as e:
            self.logger.error("request_handling_failed", error=str(e), error_type=type(e).__name__)
            
            # Log the raw response for debugging
            if 'response_text' in locals():
                self.logger.error("raw_response", response_text=response_text[:500])
            
            import traceback
            self.logger.error("traceback", trace=traceback.format_exc())
            
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'message': 'Вибачте, не вдалося обробити запит. Спробуйте ще раз.'
            }
