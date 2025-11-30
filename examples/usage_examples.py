"""
Example usage of Pedagogue AI for teachers.
Demonstrates simple API usage without async complexity.
"""

import os
import asyncio
from dotenv import load_dotenv
from google import genai
from agents.orchestrator_agent import OrchestratorAgent
from utils.session_manager import InMemorySessionService
from utils.memory_bank import MemoryBank
from utils.observability import setup_logging

# Load environment
load_dotenv()

# Setup
setup_logging("INFO")


def create_pedagogue_ai():
    """Initialize Pedagogue AI system."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY in .env file")
    
    client = genai.Client(api_key=api_key)
    session_service = InMemorySessionService()
    memory_bank = MemoryBank()
    
    orchestrator = OrchestratorAgent(
        client=client,
        session_service=session_service,
        memory_bank=memory_bank
    )
    
    return orchestrator, session_service, memory_bank


async def example_1_explicit_params():
    """Example 1: Generate lesson plan with explicit parameters."""
    print("\n" + "="*70)
    print("📚 ПРИКЛАД 1: Математика, 5 клас - Дроби")
    print("="*70)
    
    orchestrator, session_service, memory_bank = create_pedagogue_ai()
    
    result = await orchestrator.generate_lesson_plan(
        grade=5,
        subject="Математика",
        topic="Додавання дробів з однаковими знаменниками",
        duration=45,
        teacher_id="teacher_001",
        session_id="session_001"
    )
    
    if result['success']:
        lesson = result['lesson_plan']
        print("\n✅ Успіх!")
        print(f"📊 Оцінка: {lesson['qa_review'].get('scores', {}).get('average', 0):.1f}/10")
        print(f"\n🎯 Цілі навчання:")
        print(lesson['objectives'].get('objectives', '')[:200] + "...\n")
    else:
        print(f"\n❌ Помилка: {result.get('message')}")


async def example_2_natural_language():
    """Example 2: Natural language request in Ukrainian."""
    print("\n" + "="*70)
    print("📚 ПРИКЛАД 2: Природний запит українською")
    print("="*70)
    
    orchestrator, session_service, memory_bank = create_pedagogue_ai()
    
    request = "Зроби урок про рослини для 2 класу, 35 хвилин"
    print(f"\n👩‍🏫 Запит: {request}")
    
    result = await orchestrator.handle_teacher_request(
        request=request,
        teacher_id="teacher_002",
        session_id="session_002"
    )
    
    if result['success']:
        lesson = result['lesson_plan']
        meta = lesson['metadata']
        print(f"\n✅ План створено!")
        print(f"   Клас: {meta['grade']}")
        print(f"   Предмет: {meta['subject']}")
        print(f"   Тема: {meta['topic']}")
    else:
        print(f"\n❌ Помилка: {result.get('message')}")


async def example_3_with_personalization():
    """Example 3: Using teacher preferences for personalization."""
    print("\n" + "="*70)
    print("📚 ПРИКЛАД 3: З персоналізацією")
    print("="*70)
    
    orchestrator, session_service, memory_bank = create_pedagogue_ai()
    
    # Set teacher preferences
    teacher_id = "teacher_maria"
    memory_bank.update_teaching_style(teacher_id, "hands-on")
    memory_bank.update_class_size(teacher_id, 20)
    
    print(f"\n👩‍🏫 Вчитель: {teacher_id}")
    print(f"   Стиль: hands-on learning")
    print(f"   Клас: 20 учнів")
    
    result = await orchestrator.generate_lesson_plan(
        grade=3,
        subject="Природознавство",
        topic="Вода та її властивості",
        duration=40,
        teacher_id=teacher_id,
        session_id="session_003"
    )
    
    if result['success']:
        suggestions = result.get('personalized_suggestions', {})
        print(f"\n✅ План створено з врахуванням уподобань!")
        if suggestions.get('teaching_style'):
            print(f"   Врахований стиль: {suggestions['teaching_style']}")
    else:
        print(f"\n❌ Помилка: {result.get('message')}")


async def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("🎓 PEDAGOGUE AI - Приклади використання")
    print("="*70)
    
    try:
        await example_1_explicit_params()
        await example_2_natural_language()
        await example_3_with_personalization()
        
        print("\n" + "="*70)
        print("✨ Всі приклади виконано успішно!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Помилка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
