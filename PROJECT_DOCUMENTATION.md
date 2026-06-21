# Research Writer Agent - Project Documentation

## 📋 Project Overview

This is an **AI-powered Research & Content Generation System** that automates the process of creating well-researched, professionally written, and quality-checked articles. The system uses a multi-agent pipeline powered by LangGraph and ChatGroq LLM.

### Key Features:
- ✅ Automated research gathering
- ✅ Article writing with structure
- ✅ Professional editing & refinement
- ✅ Quality evaluation & scoring
- ✅ REST API for integration
- ✅ Web UI with Streamlit

---

## 🏗️ Project Architecture

```
User Input (Topic)
       ↓
   API/Streamlit
       ↓
   Workflow Graph
       ↓
┌─────────────────────────────────┐
│  AGENT PIPELINE (Sequential)    │
├─────────────────────────────────┤
│ 1. Researcher Agent             │
│    └→ Gathers facts/stats       │
│       ↓                         │
│ 2. Writer Agent                 │
│    └→ Creates article           │
│       ↓                         │
│ 3. Editor Agent                 │
│    └→ Improves quality          │
│       ↓                         │
│ 4. Evaluator Module             │
│    └→ Scores content            │
│       ↓                         │
│  Final Output                   │
└─────────────────────────────────┘
```

---

## 📂 File Structure & Descriptions

### Root Level Files

#### `app.py` - FastAPI Backend
**Purpose:** REST API server that receives requests and executes the workflow

**What it does:**
```python
- Creates a FastAPI app instance
- Defines POST endpoint: /generate
- Takes topic as parameter
- Invokes the LangGraph workflow
- Returns complete workflow result (research, article, edited, evaluation)
```

**Key Points:**
- Listens on `http://localhost:8000`
- Used by Streamlit frontend to submit requests
- Single endpoint for all generation requests

---

#### `streamlit_app.py` - Web Interface
**Purpose:** User-friendly web interface for the system

**What it does:**
```python
- Creates title: "Research Writer Agent"
- Text input field for topic entry
- Generate button to submit
- Makes HTTP POST request to API
- Displays final edited article
- Shows evaluation metrics (word count, score)
```

**Key Points:**
- Runs on `http://localhost:8501`
- Client-side application
- Communicates with FastAPI backend
- Shows results from API response

---

#### `requirements.txt` - Project Dependencies
**What it contains:**
```
langgraph          → Agentic workflow framework
langchain          → LLM integration framework
langchain-core     → Core LangChain utilities
langchain-groq     → Groq LLM integration
fastapi            → Web framework for API
uvicorn            → ASGI server for FastAPI
streamlit          → Web app framework
python-dotenv      → Load environment variables
pydantic           → Data validation
```

---

### `graph/` Package - Workflow Orchestration

#### `graph/workflow.py` - LangGraph Pipeline
**Purpose:** Defines and orchestrates the entire agent workflow

**Key Components:**

1. **AgentState (TypedDict)** - Shared state across agents
```python
topic: str              # Input from user
research: str          # Output from researcher
article: str           # Output from writer
edited: str            # Output from editor
evaluation: dict       # Output from evaluator
```

2. **Node Functions** - Each represents a stage:
- `research_node()` → Calls researcher_agent
- `writer_node()` → Calls writer_agent
- `editor_node()` → Calls editor_agent
- `evaluation_node()` → Calls evaluate

3. **StateGraph Builder** - Chains nodes in sequence:
```
research → writer → editor → evaluation → END
```

**Workflow Flow:**
1. User inputs topic
2. Researcher gathers information
3. Writer creates article from research
4. Editor improves the article
5. Evaluator scores final product
6. Complete result returned to user

---

### `agents/` Package - Individual Agents

#### `agents/researcher.py` - Research Agent
**Role:** Gathers factual information and research about the topic

**How it Works:**
```python
Input:  topic (string)
Process: Uses ChatGroq LLM with prompt
Output: Research content (facts, statistics, important points)
```

**System Prompt:**
```
Research the topic: {topic}

Provide:
1. Key Facts
2. Statistics
3. Important Points
```

**What it does:**
- Takes user topic
- Sends to Groq LLM (llama3-70b-8192)
- LLM returns comprehensive research data
- Returns raw text content

**Example Flow:**
```
Input:  "Artificial Intelligence in Healthcare"
↓
Output: "Key Facts about AI in Healthcare:
         - AI can diagnose diseases 40% faster than humans
         - 75% of hospitals are implementing AI solutions
         - Statistics: Market expected to reach $X billion by 2030
         - Important Points: Privacy concerns, Data quality..."
```

---

#### `agents/writer.py` - Writer Agent
**Role:** Creates a well-structured, professional article

**How it Works:**
```python
Input:  research (text from researcher)
Process: Uses ChatGroq LLM with structured prompt
Output: Complete article with structure
```

**System Prompt:**
```
Write a detailed article from: {research}

Include:
- Introduction
- Main Content
- Conclusion
```

**What it does:**
- Takes research content from previous agent
- Structures it into article format
- Ensures proper flow and readability
- Returns formatted article

**Example Flow:**
```
Input:  Research data about AI in Healthcare
↓
Output: "AI in Healthcare: A Comprehensive Guide
         
         Introduction:
         Healthcare industry is transforming...
         
         Main Content:
         1. Diagnostic Capabilities...
         2. Treatment Planning...
         3. Administrative Efficiency...
         
         Conclusion:
         AI represents a paradigm shift..."
```

---

#### `agents/editor.py` - Editor Agent
**Role:** Refines and improves article quality

**How it Works:**
```python
Input:  article (from writer)
Process: Uses ChatGroq LLM to enhance quality
Output: Polished, professional article
```

**System Prompt:**
```
Improve the article.

Fix:
- Grammar
- Structure
- Readability

Article: {article}
```

**What it does:**
- Takes written article
- Corrects grammar and spelling
- Improves sentence structure
- Enhances readability
- Ensures professional quality

**Example Flow:**
```
Input:  Raw article with grammar issues
↓
Output: "Healthcare industry is transforming..." (corrected)
        Better sentence flow, professional tone
```

---

### `evaluation/` Package - Quality Assessment

#### `evaluation/evaluator.py` - Evaluator Module
**Role:** Scores and assesses final content quality

**How it Works:**
```python
Input:  content (final edited article)
Process: Calculates metrics
Output: Evaluation dictionary
```

**Scoring Logic:**
```python
word_count = count words in content

score = 0 points

IF word_count > 300:
    score += 50 points
    
IF word_count > 600:
    score += 50 points

Return: {
    "word_count": number,
    "score": 0-100 (max 100)
}
```

**What it does:**
- Counts total words in final article
- Awards points based on length thresholds
- Ensures minimum quality standards
- Returns evaluation metrics

**Scoring Examples:**
```
Article with 200 words   → score: 0
Article with 400 words   → score: 50
Article with 700 words   → score: 100
```

---

## 🤖 How Each Agent Works - Technical Deep Dive

### Agent Architecture

All agents follow the same pattern:

```python
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()  # Load API keys from .env

llm = ChatGroq(
    model="openai/gpt-oss-120b"  # Groq's GPT-OSS 120B model (current recommended)
)

def agent_function(input_data):
    prompt = f"System instruction...\n{input_data}"
    result = llm.invoke(prompt)
    return result.content  # Extract text output
```

### LLM Details

- **Provider:** Groq (Fast AI inference)
- **Model:** OpenAI GPT-OSS 120B (131,072 token context)
- **Authentication:** API key from .env file
- **Response Type:** Text content
- **Token Speed:** ~500 tokens per second
- **Context Window:** 131,072 tokens input, 65,536 tokens output

---

## ❓ Key Prompts to Understand Each Agent

### Questions to Ask About Researcher Agent

1. **"How does the researcher gather current information?"**
   - Answer: Uses Groq's Llama 3 LLM knowledge (trained data cutoff)
   - Limitation: Cannot browse real-time internet

2. **"What format should research output be in?"**
   - Answer: Structured with facts, statistics, important points
   - Can be customized in prompt

3. **"Can I modify what facts the researcher gathers?"**
   - Answer: Yes! Edit the prompt in researcher.py
   - Example: Add "Include recent studies" or "Focus on X aspect"

4. **"How does it handle niche/specialized topics?"**
   - Answer: Depends on Llama 3's training data
   - May need more specific prompts for technical topics

---

### Questions to Ask About Writer Agent

1. **"How does the writer structure the article?"**
   - Answer: Follows prompt template: Intro + Main Content + Conclusion
   - Currently hardcoded - can be customized

2. **"Can I control article length or tone?"**
   - Answer: Yes! Modify the system prompt
   - Example: Add "Write in academic tone" or "Keep under 1000 words"

3. **"Does writer add citations or sources?"**
   - Answer: Not currently - this would require enhancement
   - Could be added: "Include citations for all claims"

4. **"What style of writing does it produce?"**
   - Answer: Professional, structured, balanced
   - Dependent on Llama 3 training and prompt quality

---

### Questions to Ask About Editor Agent

1. **"What specific improvements does the editor make?"**
   - Answer: Grammar, structure, readability (as per prompt)
   - Current focus: Technical writing quality

2. **"Does it change the meaning of content?"**
   - Answer: Should only refine, not alter core message
   - Potential issue: Verify output matches original intent

3. **"Can I customize what the editor focuses on?"**
   - Answer: Yes! Modify the improvement criteria
   - Example: Add "Simplify technical jargon" or "Add more examples"

4. **"Is there a before/after comparison?"**
   - Answer: Not currently tracked
   - Could add: Save both versions for comparison

---

### Questions to Ask About Evaluator

1. **"How is the quality score calculated?"**
   - Answer: Word count based (0-100 points)
   - 300+ words = 50 points, 600+ words = 50 more points

2. **"Is word count the only quality metric?"**
   - Answer: Currently yes
   - Could enhance with: Readability scores, keyword density, fact-checking

3. **"What's a good score?"**
   - Answer: 
     - 0-50: Too short/needs expansion
     - 50-99: Acceptable but could be longer
     - 100: Excellent length and content

4. **"How can I improve the scoring system?"**
   - Answer: Add metrics like:
     - Readability grade level
     - Sentence complexity
     - Keyword relevance
     - Fact verification

---

## 🔄 End-to-End Workflow Example

**User Input:** "Quantum Computing"

```
STEP 1: RESEARCHER
Input: "Quantum Computing"
↓
Prompt: "Research the topic: Quantum Computing
         Provide: 1. Key Facts 2. Statistics 3. Important Points"
↓
Output: "Key Facts:
         - Quantum computers process data using quantum bits (qubits)
         - Superposition allows qubits to be 0 and 1 simultaneously
         - Entanglement links qubits for complex calculations
         
         Statistics:
         - Quantum computing market: $X billion by 2030
         - 60% of enterprises exploring quantum tech
         
         Important Points:
         - Still in research/early commercialization
         - Applications: Drug discovery, optimization, cryptography"

STEP 2: WRITER
Input: Research content above
↓
Prompt: "Write a detailed article from: [research content]
         Include: - Introduction - Main Content - Conclusion"
↓
Output: "Quantum Computing: The Next Frontier in Technology
         
         Introduction:
         Technology is advancing at unprecedented rates...
         
         Main Content:
         [Structured article with examples]
         
         Conclusion:
         Quantum computing represents..."

STEP 3: EDITOR
Input: Article from Writer
↓
Prompt: "Improve the article. Fix: - Grammar - Structure - Readability"
↓
Output: "[Same article but with:
          - Fixed grammar/typos
          - Better sentence flow
          - Improved clarity
          - Professional tone]"

STEP 4: EVALUATOR
Input: Edited article (let's say 750 words)
↓
Calculation:
- word_count = 750
- score = 0
- Is 750 > 300? YES → score += 50
- Is 750 > 600? YES → score += 50
- Final score = 100
↓
Output: {
    "word_count": 750,
    "score": 100
}

FINAL RESULT TO USER:
{
    "topic": "Quantum Computing",
    "research": "[research content]",
    "article": "[original article]",
    "edited": "[final polished article]",
    "evaluation": {
        "word_count": 750,
        "score": 100
    }
}
```

---

## 🚀 How to Use the System

### Running the API
```bash
# Terminal 1: Start API server
cd capstoneproject
uvicorn app:app --reload
# API runs on http://localhost:8000
```

### Running Streamlit UI
```bash
# Terminal 2: Start web interface
cd capstoneproject
streamlit run streamlit_app.py
# UI runs on http://localhost:8501
```

### Testing via API
```bash
# Terminal 3: Test endpoint
curl -X POST "http://localhost:8000/generate?topic=Artificial%20Intelligence"
```

---

## 🔧 How to Enhance Each Agent

### Enhance Researcher Agent
```python
# Current
prompt = f"""Research the topic: {topic}
             Provide: 1. Key Facts 2. Statistics 3. Important Points"""

# Enhanced
prompt = f"""Research the topic: {topic}
             Provide comprehensive information including:
             1. Key Facts (5-7 recent developments)
             2. Statistics (quantifiable data)
             3. Important Points (critical insights)
             4. Expert Perspectives
             5. Future Outlook
             
             Focus on: Recent trends and innovations
             Tone: Balanced and analytical"""
```

### Enhance Writer Agent
```python
# Current
prompt = f"""Write a detailed article from: {research}
             Include: - Introduction - Main Content - Conclusion"""

# Enhanced
prompt = f"""Write a professional article (800-1200 words) from: {research}
             
             Structure:
             - Hook (engaging opening)
             - Introduction (context and significance)
             - Body (3-5 main sections with examples)
             - Expert insights
             - Counterarguments
             - Conclusion (summary and future implications)
             
             Tone: Professional, accessible, data-driven"""
```

### Enhance Editor Agent
```python
# Current
prompt = f"""Improve the article. Fix: - Grammar - Structure - Readability"""

# Enhanced
prompt = f"""Professionally edit the article ensuring:
             - Perfect grammar and spelling
             - Logical flow and transitions
             - Clear, concise language
             - Active voice where possible
             - Varied sentence structure
             - Removal of redundancy
             - Professional tone throughout
             - Fact consistency
             
             Article: {article}"""
```

### Enhance Evaluator
```python
# Current
if words > 300:
    score += 50
if words > 600:
    score += 50

# Enhanced
def enhanced_evaluate(content):
    words = len(content.split())
    sentences = len(content.split('.'))
    
    score = 0
    
    # Length metric
    if words > 300: score += 25
    if words > 600: score += 25
    
    # Readability metric
    avg_word_length = sum(len(w) for w in content.split()) / len(content.split())
    if 4 < avg_word_length < 6: score += 15
    
    # Structure metric
    if content.count('\n') > 3: score += 15
    
    # Professional language metric
    if any(word in content.lower() for word in ['however', 'moreover', 'therefore']):
        score += 10
    if any(word in content.lower() for word in ['very', 'really', 'basically']):
        score -= 5
    
    return {
        "word_count": words,
        "avg_sentence_length": words / sentences if sentences > 0 else 0,
        "score": min(100, max(0, score))
    }
```

---

## 📊 Data Flow Diagram

```
User Browser (Streamlit)
    ↓ [text input: topic]
    ↓ [POST /generate?topic=X]
    ↓
FastAPI Server (app.py)
    ↓ [invoke workflow]
    ↓
LangGraph Workflow
    ├→ research_node()
    │   ├→ Researcher Agent (ChatGroq)
    │   └→ returns research: str
    │
    ├→ writer_node()
    │   ├→ Writer Agent (ChatGroq)
    │   └→ returns article: str
    │
    ├→ editor_node()
    │   ├→ Editor Agent (ChatGroq)
    │   └→ returns edited: str
    │
    ├→ evaluation_node()
    │   ├→ Evaluator Module
    │   └→ returns evaluation: dict
    │
    └→ EndNode
        └→ returns complete state
    ↓
API Response (JSON)
    ↓
Browser Display (Streamlit)
    └→ Shows edited article + evaluation
```

---

## ⚠️ Important Notes

1. **API Key Required:** Set GROQ_API_KEY in .env file
2. **Sequential Processing:** Agents run one after another (not parallel)
3. **Token Limitations:** Llama 3 has 8192 token context window
4. **No Internet Access:** Researchers cannot browse real-time web
5. **Stateless:** No conversation memory between requests

---

## 🎯 Next Steps for Enhancement

1. Add error handling and logging
2. Implement caching to avoid duplicate requests
3. Add streaming responses for real-time feedback
4. Implement parallel agent execution
5. Add database to store article history
6. Implement user authentication
7. Add feedback loop for continuous improvement
8. Create admin dashboard for monitoring

