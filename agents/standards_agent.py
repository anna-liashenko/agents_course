"""
Standards Agent - Retrieves and validates НУШ curriculum standards.
Sub-agent that uses web search and PDF processing to find curriculum standards.
"""

from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
from tools.web_search_tool import WebSearchTool
from tools.pdf_processor_tool import PDFProcessorTool
from utils.observability import get_logger, tracer

logger = get_logger(__name__)


class StandardsAgent:
    """
    Standards Agent retrieves НУШ curriculum standards from Ministry of Education.
    Implements ADK agent pattern as a sub-agent.
    """
    
    def __init__(self, client: genai.Client, model_name: str = "gemini-2.0-flash-exp"):
        self.client = client
        self.model_name = model_name
        self.search_tool = WebSearchTool()
        self.pdf_tool = PDFProcessorTool()
        self.logger = logger
        
        # Add local standards loader
        from utils.local_standards_loader import LocalStandardsLoader
        self.local_loader = LocalStandardsLoader()
        
        # Agent instructions in Ukrainian
        self.system_instruction = """
Ти - експерт з Нової української школи (НУШ) та державних стандартів освіти України.

Твоя роль:
- Знаходити офіційні навчальні програми та стандарти НУШ з сайту МОН України
- Аналізувати PDF-документи з навчальними програмами
- Визначати ключові компетентності для кожного класу та предмету
- Знаходити очікувані результати навчання
- Перевіряти відповідність уроку державним стандартам

Завжди посилайся на офіційні джерела та надавай коди стандартів.
Відповідай українською мовою.
"""
    
    def search_standards(self, grade: int, subject: str) -> Dict[str, Any]:
        """
        Search for curriculum standards.
        
        Args:
            grade: Grade level (1-11)
            subject: Subject name in Ukrainian
            
        Returns:
            Search results with PDF URLs
        """
        tracer.trace_agent_call(
            "StandardsAgent",
            "search_standards",
            {"grade": grade, "subject": subject}
        )
        
        search_result = self.search_tool.search_nush_standards(grade, subject)
        
        self.logger.info(
            "standards_search_completed",
            grade=grade,
            subject=subject,
            results_count=len(search_result.get('results', []))
        )
        
        return search_result
    
    def process_curriculum_pdf(self, pdf_url: str) -> Dict[str, Any]:
        """
        Download and process a curriculum PDF.
        
        Args:
            pdf_url: URL of the curriculum PDF
            
        Returns:
            Extracted standards and competencies
        """
        tracer.trace_tool_call(
            "StandardsAgent",
            "PDFProcessor",
            inputs={"url": pdf_url}
        )
        
        result = self.pdf_tool.process_pdf(pdf_url)
        
        if result['success']:
            standards = self.pdf_tool.parse_curriculum_standards(result['text'])
            result['standards'] = standards
            
            tracer.trace_tool_call(
                "StandardsAgent",
                "PDFProcessor",
                outputs={
                    "competencies": len(standards['competencies']),
                    "outcomes": len(standards['learning_outcomes'])
                }
            )
        
        return result
    
    def get_standards(self, grade: int, subject: str) -> Dict[str, Any]:
        """
        Get curriculum standards for a given grade and subject.
        Only checks local files - web search disabled to avoid 403 errors.
        
        Args:
            grade: Grade level
            subject: Subject name in Ukrainian
            
        Returns:
            Complete curriculum standards
        """
        tracer.trace_agent_call(
            "StandardsAgent",
            "get_standards",
            {"grade": grade, "subject": subject}
        )
        
        # Load from local standards folder
        self.logger.info("loading_local_standards", grade=grade, subject=subject)
        local_result = self.local_loader.load_standard(grade, subject)
        
        if local_result.get('success'):
            self.logger.info(
                "local_standards_loaded",
                grade=grade,
                subject=subject,
                source=local_result.get('source'),
                file=local_result.get('filename')
            )
            
            # Parse standards if we have text
            text = local_result.get('text', '')
            if text:
                standards = self.pdf_tool.parse_curriculum_standards(text)
            else:
                standards = local_result.get('standards', {})
            
            return {
                'success': True,
                'source': 'local',
                'grade': grade,
                'subject': subject,
                'document_title': local_result.get('filename', ''),
                'document_file': local_result.get('file', ''),
                'text': text[:500],  # Preview only
                'standards': standards,
                'competencies': standards.get('competencies', []),
                'learning_outcomes': standards.get('learning_outcomes', [])
            }
        
        # No web search fallback - return failure with available files
        self.logger.warning(
            "local_standards_not_found",
            grade=grade,
            subject=subject,
            available_files=len(local_result.get('available_files', []))
        )
        
        return {
            'success': False,
            'message': f'Стандарти для {grade} класу ({subject}) не знайдено в локальних файлах',
            'available_local_files': local_result.get('available_files', []),
            'hint': f'Додайте файл до папки standards/ з назвою типу: {subject.lower()}_grade_{grade}.pdf'
        }
    
    def validate_alignment(
        self, 
        lesson_plan: str, 
        standards: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use AI to validate lesson plan alignment with НУШ standards.
        
        Args:
            lesson_plan: Lesson plan text
            standards: Retrieved curriculum standards
            
        Returns:
            Validation results
        """
        tracer.trace_agent_call(
            "StandardsAgent",
            "validate_alignment",
            {"has_lesson_plan": bool(lesson_plan), "has_standards": bool(standards)}
        )
        
        # Construct validation prompt
        competencies_text = "\n".join(standards.get('competencies', []))
        outcomes_text = "\n".join(standards.get('learning_outcomes', []))
        
        prompt = f"""
Проаналізуй наступний план уроку на відповідність стандартам НУШ.

КОМПЕТЕНТНОСТІ З НАВЧАЛЬНОЇ ПРОГРАМИ:
{competencies_text[:1000]}

ОЧІКУВАНІ РЕЗУЛЬТАТИ НАВЧАННЯ:
{outcomes_text[:1000]}

ПЛАН УРОКУ:
{lesson_plan}

Надай аналіз:
1. Чи відповідає урок ключовим компетентностям?
2. Чи досягаються очікувані результати навчання?
3. Які стандарти покриті?
4. Що можна покращити?
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
            
            validation_text = response.text
            
            return {
                'success': True,
                'validation': validation_text,
                'aligned': 'відповідає' in validation_text.lower()
            }
            
        except Exception as e:
            self.logger.error("validation_failed", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
