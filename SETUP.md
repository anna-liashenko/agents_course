# Setup Instructions for Reviewers

## Quick Start (For Reviewers)

This submission uses **Google ADK (Agent Development Kit)** to create a multi-agent system for Ukrainian teachers.

### Prerequisites

- Python 3.11 or higher
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### Step 1: Clone and Setup

```bash
git clone https://github.com/anna-liashenko/agents_course/
cd agents_course
```

### Step 2: Configure API Key

**🚨 IMPORTANT: Add Your API Key**

Create a `.env` file in the project root:

Then edit `.env` and replace `your_api_key_here` with your actual Google Gemini API key:

```
GOOGLE_API_KEY=AIzaSy...your_actual_key_here
DEFAULT_MODEL=gemini-2.0-flash-exp
LOG_LEVEL=INFO
```

### Step 4: Run the Interactive Demo

```bash
python interactive_teacher.py
```

This will start an interactive session where you can request lesson plans in Ukrainian!

**Example requests to try:**
- `Створи урок математики для 5 класу про дроби`
- `Зроби план уроку з біології для 8 класу про клітини`
- `Урок української мови для 3 класу про іменники`

### Alternative: Run Pre-configured Examples

```bash
python main.py
```

This runs 2 pre-configured lesson plan examples.

## What to Expect

The system will:
1. Parse your Ukrainian language request using AI
2. Extract grade, subject, topic, and duration
3. Coordinate 5 specialized agents in parallel and sequential workflows
4. Generate a complete lesson plan with:
   - НУШ curriculum standards (from local files)
   - Learning objectives (SMART format)
   - Warm-up activity
   - Direct instruction
   - Guided practice
   - 3-tier differentiation
   - Independent practice
   - Formative and summative assessments
   - Quality assurance review
5. Offer to save the plan as TXT or DOCX file

Generation takes **30-90 seconds** (multiple AI calls).

## Understanding the Output

After generation, you'll see:
- Metadata (grade, subject, topic, duration)
- Quality score (out of 10)
- Component status ([OK] or [X])
- Sample content preview

You can then save the lesson plan in teacher-friendly formats:
- **TXT**: Plain text file readable in any editor
- **DOCX**: Microsoft Word document with formatting

## Architecture Highlights (3+ ADK Concepts)

This project demonstrates:

1. **Multi-Agent Coordination** - 5 specialized agents work together
2. **Parallel Execution** - Standards + Learning Science agents run concurrently
3. **Sequential Pipeline** - Content generation flows through stages
4. **Agent-as-Tool Pattern** - Sub-agents exposed as tools to Orchestrator
5. **Session Management** - Conversation context tracking
6. **Memory Bank** - Long-term teacher preference storage
7. **Observability** - Structured logging and tracing throughout

## Offline Mode Note

⚠️ This submission uses **pre-downloaded** НУШ curriculum files due to the Ministry of Education website blocking automated access (HTTP 403).

In a **production system**, the Standards Agent would:
- Search mon.gov.ua for curriculum PDFs
- Download and process them automatically
- Cache results for future use

For this demo, standards are loaded from the `standards/` folder containing 9 pre-downloaded curriculum documents covering grades 1-11 for Math, Ukrainian, and Biology.

## Troubleshooting

**Import errors?**
```bash
pip install -r requirements.txt
```

**API errors?**
- Check your API key is correct in `.env`
- Verify internet connection
- Check API quota at https://ai.dev/usage

**No standards found?**
- This is expected for subjects/grades not in the `standards/` folder
- The system will still generate a complete 9.6/10 quality lesson plan
- Standards are optional but valuable

## Project Structure

```
agents_course/
├── agents/              # 5 specialized agents
├── tools/               # Custom tools (PDF processing, web search)
├── utils/               # Session, memory, observability, export
├── mcp_server/          # Model Context Protocol server
├── standards/           # Pre-downloaded НУШ curriculum (PDFs/DOCX)
├── examples/            # Usage examples
├── interactive_teacher.py  # Main interactive interface
└── main.py             # Pre-configured examples
```

## Questions?

See the full [README.md](README.md) for detailed architecture, design decisions, and ADK concept explanations.
