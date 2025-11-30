"""
Interactive Teacher Assistant - Pedagogue AI
Allows teachers to input their own lesson requests and generate plans.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from google import genai
from agents.orchestrator_agent import OrchestratorAgent
from utils.session_manager import InMemorySessionService
from utils.memory_bank import MemoryBank
from utils.observability import setup_logging

# Load environment
load_dotenv()
setup_logging("INFO")


def print_header():
    """Print welcome header."""
    print("\n" + "="*70)
    print("   PEDAGOGUE AI - Interactive Teacher Assistant")
    print("   Система підтримки українських вчителів")
    print("="*70)


def print_lesson_plan(result):
    """Pretty print the generated lesson plan."""
    if not result.get('success'):
        print(f"\n[X] Error: {result.get('message', result.get('error'))}")
        return
    
    lesson = result['lesson_plan']
    metadata = lesson['metadata']
    qa_review = lesson.get('qa_review', {})
    
    print("\n" + "="*70)
    print("[SUCCESS] Lesson Plan Generated!")
    print("="*70)
    
    # Metadata
    print("\n[METADATA]")
    print(f"   Grade:    {metadata.get('grade')}")
    print(f"   Subject:  {metadata.get('subject')}")
    print(f"   Topic:    {metadata.get('topic')}")
    print(f"   Duration: {metadata.get('duration')} minutes")
    
    # Quality Score
    if qa_review.get('success'):
        avg_score = qa_review.get('scores', {}).get('average', 0)
        status = qa_review.get('overall_status', 'unknown')
        print(f"\n[QUALITY SCORE]")
        print(f"   Score:  {avg_score:.1f}/10")
        print(f"   Status: {status}")
    
    # Components Status
    print("\n[COMPONENTS]")
    components = [
        ('Standards', lesson.get('standards', {}).get('success', False)),
        ('Learning Strategies', lesson.get('learning_strategies', {}).get('success', False)),
        ('Objectives', lesson.get('objectives', {}).get('success', False)),
        ('Warm-up', lesson.get('warmup', {}).get('success', False)),
        ('Instruction', lesson.get('instruction', {}).get('success', False)),
        ('Guided Practice', lesson.get('guided_practice', {}).get('success', False)),
        ('Differentiation', lesson.get('differentiation', {}).get('success', False)),
        ('Independent Practice', lesson.get('independent_practice', {}).get('success', False)),
        ('Formative Assessment', lesson.get('formative_assessment', {}).get('success', False)),
        ('Summative Assessment', lesson.get('summative_assessment', {}).get('success', False)),
        ('QA Review', qa_review.get('success', False))
    ]
    
    for name, success in components:
        status = "[OK]" if success else "[X]"
        print(f"   {status} {name}")
    
    # Sample content
    print("\n[PREVIEW: Learning Objectives]")
    if lesson.get('objectives', {}).get('success'):
        obj_text = lesson['objectives'].get('objectives', '')
        preview = obj_text[:400] + "..." if len(obj_text) > 400 else obj_text
        print(preview)
    
    print("\n[PREVIEW: Warm-up Activity]")
    if lesson.get('warmup', {}).get('success'):
        warmup_text = lesson['warmup'].get('warmup', '')
        preview = warmup_text[:400] + "..." if len(warmup_text) > 400 else warmup_text
        print(preview)
    
    print("\n" + "="*70)


def save_lesson_plan(result, format='txt'):
    """Save lesson plan to teacher-friendly file (TXT or DOCX)."""
    if not result.get('success'):
        return
    
    from utils.export_formats import export_to_txt, export_to_docx
    
    if format.lower() == 'docx':
        filename = export_to_docx(result['lesson_plan'])
    else:
        filename = export_to_txt(result['lesson_plan'])
    
    print(f"\n[SAVED] Lesson plan saved to: {filename}")


async def interactive_session():
    """Run interactive session with user input."""
    
    # Initialize system
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("\n[X] ERROR: GOOGLE_API_KEY not found in .env file")
        print("[!] Please create .env file with your API key")
        return
    
    print("\n[INITIALIZING] Setting up Pedagogue AI...")
    client = genai.Client(api_key=api_key)
    session_service = InMemorySessionService()
    memory_bank = MemoryBank()
    
    orchestrator = OrchestratorAgent(
        client=client,
        model_name="gemini-2.0-flash-exp",
        session_service=session_service,
        memory_bank=memory_bank
    )
    
    print("[OK] All 5 agents initialized successfully")
    print("   - Orchestrator Agent")
    print("   - Standards Agent")
    print("   - Learning Science Agent")
    print("   - Content Generator Agent")
    print("   - Quality Assurance Agent")
    
    # Session tracking
    session_count = 0
    
    print("\n" + "="*70)
    print("READY! You can now request lesson plans.")
    print("="*70)
    print("\nExamples of requests:")
    print("   - Створи урок математики для 5 класу про дроби")
    print("   - Зроби план уроку з фізики для 8 класу про електричний струм")
    print("   - Урок української мови для 3 класу про іменники, 40 хвилин")
    print("\nType 'quit' or 'exit' to stop.")
    print("="*70)
    
    while True:
        print("\n")
        # Get user input
        try:
            user_request = input("👩‍🏫 Your lesson request: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n[EXIT] Goodbye!")
            break
        
        # Check for exit commands
        if user_request.lower() in ['quit', 'exit', 'q', 'вихід']:
            print("\n[EXIT] Thank you for using Pedagogue AI! До побачення! 👋")
            break
        
        if not user_request:
            print("[!] Please enter a lesson request.")
            continue
        
        # Generate lesson plan
        session_count += 1
        teacher_id = "interactive_user"
        session_id = f"interactive_session_{session_count}"
        
        print(f"\n[PROCESSING] Generating lesson plan...")
        print("[WAIT] This may take 30-90 seconds...\n")
        
        try:
            result = await orchestrator.handle_teacher_request(
                request=user_request,
                teacher_id=teacher_id,
                session_id=session_id
            )
            
            # Display results
            print_lesson_plan(result)
            
            # Ask if user wants to save
            if result.get('success'):
                print("\n💾 Save lesson plan?")
                print("   1 - TXT (readable text file)")
                print("   2 - DOCX (Microsoft Word document)")
                print("   n - Don't save")
                
                save_choice = input("\nChoice (1/2/n): ").strip().lower()
                
                if save_choice in ['1', 'txt']:
                    save_lesson_plan(result, format='txt')
                elif save_choice in ['2', 'docx', 'word']:
                    save_lesson_plan(result, format='docx')
                
                # Show teacher stats
                profile = memory_bank.get_or_create_profile(teacher_id)
                print(f"\n[STATS] Total lesson plans generated: {profile.lesson_plan_count}")
        
        except Exception as e:
            print(f"\n[ERROR] An error occurred: {str(e)}")
            print("[!] Please try again with a different request.")
        
        print("\n" + "-"*70)
    
    # Final summary
    print("\n" + "="*70)
    print("SESSION SUMMARY")
    print("="*70)
    print(f"Total requests processed: {session_count}")
    
    # Export traces
    from utils.observability import tracer
    trace_file = f"traces_interactive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    tracer.export_traces(trace_file)
    print(f"Traces exported to: {trace_file}")
    
    print("\n✨ Thank you for using Pedagogue AI! ✨\n")


def main():
    """Main entry point."""
    print_header()
    
    print("\n[INFO] Interactive mode allows you to:")
    print("   ✓ Type your own lesson requests in Ukrainian")
    print("   ✓ Generate complete lesson plans with all components")
    print("   ✓ Save generated plans to JSON files")
    print("   ✓ Build your teacher profile with preferences")
    
    try:
        asyncio.run(interactive_session())
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Session cancelled by user.")
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
