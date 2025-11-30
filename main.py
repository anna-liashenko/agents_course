"""
Pedagogue AI - Multi-Agent Teacher Assistant System
Main application demonstrating ADK multi-agent patterns.
"""

import os
import asyncio
from dotenv import load_dotenv
from google import genai
from agents.orchestrator_agent import OrchestratorAgent
from utils.session_manager import InMemorySessionService
from utils.memory_bank import MemoryBank
from utils.observability import setup_logging, get_logger, tracer

# Load environment variables
load_dotenv()

# Setup logging
setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)


async def main():
    """Main application entry point."""
    
    logger.info("pedagogue_ai_starting")
    
    # Initialize Gemini client
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("missing_api_key")
        print("❌ ПОМИЛКА: Відсутній GOOGLE_API_KEY")
        print("📝 Створіть файл .env на основі .env.example та додайте ваш API ключ")
        return
    
    client = genai.Client(api_key=api_key)
    model_name = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash-exp")
    
    logger.info("gemini_client_initialized", model=model_name)
    
    # Initialize session service and memory bank
    session_service = InMemorySessionService()
    memory_bank = MemoryBank()
    
    # Create orchestrator agent
    orchestrator = OrchestratorAgent(
        client=client,
        model_name=model_name,
        session_service=session_service,
        memory_bank=memory_bank
    )
    
    logger.info("orchestrator_initialized", sub_agents=5)
    
    # Example 1: Generate lesson plan with explicit parameters
    print("\n" + "="*80)
    print("🎓 PEDAGOGUE AI - Система підтримки українських вчителів")
    print("="*80)
    print("\n📚 Приклад 1: Створення плану уроку з математики для 5 класу")
    print("-"*80)
    
    session_id = "session_001"
    teacher_id = "teacher_maria"
    
    # Create session
    session_service.create_session(session_id, "Марія Петренко")
    
    # Set teacher preferences
    memory_bank.update_teaching_style(teacher_id, "hands-on")
    memory_bank.update_class_size(teacher_id, 25)
    
    result = await orchestrator.generate_lesson_plan(
        grade=5,
        subject="Математика",
        topic="Дроби: складання та віднімання дробів з однаковими знаменниками",
        duration=45,
        teacher_id=teacher_id,
        session_id=session_id
    )
    
    if result['success']:
        lesson_plan = result['lesson_plan']
        qa_review = lesson_plan['qa_review']
        
        print(f"\n✅ План уроку згенеровано успішно!")
        print(f"📊 Оцінка якості: {qa_review.get('scores', {}).get('average', 0):.1f}/10")
        print(f"🎯 Статус: {qa_review.get('overall_status', 'unknown')}")
        
        print("\n📋 КОМПОНЕНТИ УРОКУ:")
        print("-"*80)
        
        # Show objectives
        if lesson_plan['objectives'].get('success'):
            print("\n🎯 ЦІЛІ НАВЧАННЯ:")
            print(lesson_plan['objectives']['objectives'][:300] + "...")
        
        # Show warmup
        if lesson_plan['warmup'].get('success'):
            print("\n🔥 РОЗМИНКА:")
            print(lesson_plan['warmup']['warmup'][:300] + "...")
        
        # Show learning strategies
        if lesson_plan['learning_strategies'].get('success'):
            print("\n🧠 СТРАТЕГІЇ НАВЧАННЯ:")
            print(lesson_plan['learning_strategies']['strategies'][:300] + "...")
        
        # Show QA review summary
        if qa_review.get('success'):
            print("\n🔍 ВІДГУК ЕКСПЕРТА:")
            print(qa_review['review'][:400] + "...")
        
        print("\n" + "="*80)
        
    else:
        print(f"❌ Помилка: {result.get('message', result.get('error'))}")
    
    # Example 2: Natural language request
    print("\n📚 Приклад 2: Обробка запиту природною мовою")
    print("-"*80)
    
    session_id_2 = "session_002"
    session_service.create_session(session_id_2, "Олена Коваленко")
    
    request = "Створи урок для 3 класу з української літератури про казки. Урок на 40 хвилин."
    
    print(f"\n👩‍🏫 Запит вчителя: {request}")
    
    result_2 = await orchestrator.handle_teacher_request(
        request=request,
        teacher_id="teacher_olena",
        session_id=session_id_2
    )
    
    if result_2['success']:
        lesson_plan_2 = result_2['lesson_plan']
        qa_score = lesson_plan_2['qa_review'].get('scores', {}).get('average', 0)
        
        print(f"\n✅ План уроку згенеровано!")
        print(f"📊 Оцінка якості: {qa_score:.1f}/10")
        print(f"📝 Клас: {lesson_plan_2['metadata']['grade']}")
        print(f"📚 Предмет: {lesson_plan_2['metadata']['subject']}")
        print(f"🎯 Тема: {lesson_plan_2['metadata']['topic']}")
    else:
        print(f"❌ Помилка: {result_2.get('message')}")
    
    # Export traces and session data
    print("\n" + "="*80)
    print("💾 ЗБЕРЕЖЕННЯ ДАНИХ")
    print("-"*80)
    
    # Export traces
    trace_file = "traces.json"
    tracer.export_traces(trace_file)
    print(f"✅ Трейси збережено: {trace_file}")
    
    # Export session 1
    session_file_1 = "session_001.json"
    session_service.export_session(session_id, session_file_1)
    print(f"✅ Сесія 1 збережена: {session_file_1}")
    
    # Export memory bank
    memory_file = "memory_bank.json"
    memory_bank.export_memory_bank(memory_file)
    print(f"✅ Банк пам'яті збережено: {memory_file}")
    
    # Show statistics
    print("\n" + "="*80)
    print("📈 СТАТИСТИКА")
    print("-"*80)
    print(f"🔬 Всього трейсів: {len(tracer.get_traces())}")
    print(f"🧑‍🏫 Вчителів в банку пам'яті: {len(memory_bank.profiles)}")
    print(f"💬 Сесій: {len(session_service.sessions)}")
    
    # Show teacher preferences
    teacher_profile = memory_bank.get_or_create_profile(teacher_id)
    print(f"\n👨‍🏫 Профіль вчителя '{teacher_id}':")
    print(f"   - Стиль викладання: {teacher_profile.teaching_style}")
    print(f"   - Розмір класу: {teacher_profile.class_size}")
    print(f"   - Згенеровано планів: {teacher_profile.lesson_plan_count}")
    print(f"   - Улюблені предмети: {teacher_profile.preferred_subjects}")
    
    print("\n" + "="*80)
    print("✨ Pedagogue AI завершено успішно!")
    print("="*80 + "\n")
    
    logger.info("pedagogue_ai_completed_successfully")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Програму зупинено користувачем")
    except Exception as e:
        logger.error("main_failed", error=str(e))
        print(f"\n❌ Помилка: {e}")
