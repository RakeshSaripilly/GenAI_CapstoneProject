---
title: RAG Knowledge Assistant
emoji: 📚
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.35.0
app_file: streamlit_app.py
pinned: false
---

# Research Writer Agent - Complete Project Guide

## 📚 Project Overview

This is now an **AI-powered Retrieval-Augmented Generation (RAG) system** that indexes project documents and answers questions grounded in retrieved context.

### 🎯 What This System Does

1. **Takes documents** from the repo or uploads
2. **Chunks and embeds** the content into a vector store
3. **Retrieves relevant context** for each question
4. **Generates grounded answers** with the LLM
5. **Returns sources and answer text** through the API or web interface

---

## 📂 Complete Project Structure (Step-by-Step)

```
capstoneproject/
│
├── 📄 app.py                          ← FastAPI backend server for ingest / ask
├── 📄 streamlit_app.py                ← Streamlit RAG interface
├── 📄 rag.py                          ← Indexing, retrieval, and answer generation
├── 📄 llm_config.py                   ← LLM configuration with retry logic
├── 📄 requirements.txt                ← Python dependencies
├── 📄 .env                            ← Environment variables (not tracked)
│
├── 📁 agents/                         ← Legacy agent files from the original workflow
│   ├── __init__.py
│   ├── researcher.py                  ← Research/information gathering agent
│   ├── writer.py                      ← Article writing agent
│   └── editor.py                      ← Content refinement agent
│
├── 📁 graph/                          ← Legacy workflow orchestration files
│   ├── __init__.py
│   └── workflow.py                    ← LangGraph pipeline definition
│
├── 📁 evaluation/                     ← Legacy quality assessment module
│   ├── __init__.py
│   └── evaluator.py                   ← Content scoring module
│
├── 📄 PROJECT_DOCUMENTATION.md        ← Original documentation
└── 📄 README.md                       ← This file
```

---

## 🔍 Detailed File Explanations

### **Root Level Files**

#### 1️⃣ **app.py** - FastAPI Backend Server

**What it is:** The main API server that receives requests from the web interface

**What it does:**
```python
# Creates a web server that listens for requests
# When a topic is submitted, it runs the entire workflow
# Returns the complete results (research, article, evaluation)
```

**Key Features:**
- 🟢 **Endpoint:** `POST /generate?topic=YOUR_TOPIC`
- 🟢 **Also accepts:** JSON body `{"topic": "YOUR_TOPIC"}`
- 🟢 **Returns:** JSON with all workflow results
- 🟢 **Error handling:** Catches and reports any issues

**How it works in detail:**
```python
@app.post("/generate")
def generate(topic: str = None, request: GenerateRequest = None):
    # Step 1: Get the topic from user
    actual_topic = topic or request.topic
    
    # Step 2: Run the entire workflow
    result = graph.invoke({"topic": actual_topic})
    
    # Step 3: Return structured response
    return {"status": "success", "result": result}
```

**What happens inside:**
1. User submits a topic
2. FastAPI receives the request
3. Calls `graph.invoke()` which runs all agents in sequence
4. Returns all outputs in JSON format

**Example Request/Response:**

Request:
```
POST http://localhost:8000/generate?topic=artificial%20intelligence
```

Response:
```json
{
  "status": "success",
  "result": {
    "topic": "artificial intelligence",
    "research": "Key Facts: AI can process data 40% faster...",
    "article": "Artificial Intelligence: A Comprehensive Guide...",
    "edited": "Artificial Intelligence: A Comprehensive Guide... [improved version]",
    "evaluation": {
      "word_count": 750,
      "score": 100
    }
  }
}
```

---

#### 2️⃣ **streamlit_app.py** - Web User Interface

**What it is:** A web application that provides a friendly user interface

**What it does:**
- Creates a text box for users to enter topics
- Submits requests to the FastAPI backend
- Displays the final article and evaluation scores
- Shows any errors in a user-friendly way

**Interface Features:**
```
┌─────────────────────────────────┐
│  Research Writer Agent          │  ← Title
├─────────────────────────────────┤
│ Enter Topic:                    │
│ [___________________________]   │  ← Input field
│                                 │
│    [ Generate ]                 │  ← Submit button
│                                 │
│ ─────────────────────────────── │
│ Final Article                   │  ← Results section
│ [Full article content...]       │
│                                 │
│ Evaluation                      │  ← Scores
│ {                               │
│   "word_count": 750,            │
│   "score": 100                  │
│ }                               │
└─────────────────────────────────┘
```

**How it works in detail:**
```python
# 1. Create input box
topic = st.text_input("Enter Topic")

# 2. When user clicks Generate button
if st.button("Generate"):
    # 3. Send request to FastAPI
    response = requests.post(
        "http://localhost:8000/generate",
        params={"topic": topic}
    )
    
    # 4. Get results from response
    data = response.json()
    result = data["result"]
    
    # 5. Display the edited article
    st.write(result["edited"])
    
    # 6. Display evaluation scores
    st.json(result["evaluation"])
```

**Error Handling:**
- If API server is down: Shows error message
- If topic is empty: User can't click Generate
- If API returns error: Displays the error details

---

#### 3️⃣ **llm_config.py** - LLM Configuration & Retry Logic

**What it is:** Central configuration for connecting to Groq's LLM with reliability features

**What it does:**
- Sets up the ChatGroq client with proper settings
- Configures HTTP timeouts and connection pooling
- Implements automatic retry logic (tries 3 times if connection fails)
- Provides a single reusable LLM instance

**Why it's important:**
- **Reliability:** If API call fails, automatically retries
- **Speed:** Uses connection pooling for faster requests
- **Timeout:** Prevents hanging if Groq API is slow
- **Centralization:** All agents use the same LLM instance

**How the retry logic works:**
```
First attempt fails (connection error)
    ↓ (wait 2 seconds)
Second attempt fails
    ↓ (wait 4 seconds)
Third attempt fails
    ↓
Raise exception to user
```

**Configuration details:**
```python
llm = ChatGroq(
    model="openai/gpt-oss-120b",      # Model being used
    temperature=0.7,                   # Creativity level (0-1)
    max_tokens=2048,                   # Max response length
    timeout=60.0,                      # Wait max 60 seconds
)
```

---

#### 4️⃣ **requirements.txt** - Project Dependencies

**What it is:** A list of all Python libraries needed to run this project

**What each library does:**

| Library | Purpose |
|---------|---------|
| `langgraph` | Framework for building agent workflows |
| `langchain` | LLM integration toolkit |
| `langchain-core` | Core utilities for LangChain |
| `langchain-groq` | Groq LLM integration for LangChain |
| `fastapi` | Web framework for creating APIs |
| `uvicorn` | Server to run FastAPI applications |
| `streamlit` | Framework for creating web interfaces |
| `python-dotenv` | Load environment variables from `.env` file |
| `pydantic` | Data validation and serialization |
| `tenacity` | Retry logic with exponential backoff |
| `httpx` | Advanced HTTP client with timeout support |

**How to install:**
```bash
pip install -r requirements.txt
```

---

### **agents/ Package - Individual AI Agents**

These are the specialized agents that perform different tasks in the workflow.

#### 1️⃣ **agents/researcher.py** - Research Agent

**What it does:** Gathers factual information and research about a topic

**The Process:**

```
Input: User's topic (e.g., "Quantum Computing")
    ↓
[Researcher creates a prompt with the topic]
    ↓
[Sends to Groq LLM for processing]
    ↓
[LLM thinks about the topic and generates facts]
    ↓
Output: Research content (facts, statistics, important points)
```

**System Prompt (instructions given to LLM):**
```
Research the topic: {user's topic}

Provide:
1. Key Facts
2. Statistics
3. Important Points
```

**Example:**

Input Topic:
```
"Quantum Computing"
```

Output Research:
```
Key Facts:
- Quantum computers use quantum bits (qubits) instead of regular bits
- Qubits can be 0, 1, or both at the same time (superposition)
- This allows massive parallel processing

Statistics:
- Quantum computing market will reach $65 billion by 2030
- 60% of enterprises are exploring quantum technology
- Google's quantum chip is 1 million times faster than regular computers

Important Points:
- Still in early research stage
- Applications: Drug discovery, optimization, cryptography
- Major players: Google, IBM, Microsoft
```

**Code explanation:**
```python
from llm_config import llm, with_retry

@with_retry  # If fails, automatically retry up to 3 times
def research_agent(topic):
    # Create the prompt for the LLM
    prompt = f"""
    Research the topic: {topic}
    
    Provide:
    1. Key Facts
    2. Statistics
    3. Important Points
    """
    
    # Send to LLM and get response
    result = llm.invoke(prompt)
    
    # Extract just the text (not metadata)
    return result.content
```

**What the `@with_retry` decorator does:**
- If the first attempt fails (network error, timeout), wait 2 seconds and try again
- If second attempt fails, wait 4 seconds and try again
- If third attempt fails, give up and raise an error
- This makes the system resilient to temporary network issues

---

#### 2️⃣ **agents/writer.py** - Writer Agent

**What it does:** Creates a well-structured, professional article from the research

**The Process:**

```
Input: Research content from researcher agent
    ↓
[Writer creates a structured prompt]
    ↓
[Sends research + instructions to Groq LLM]
    ↓
[LLM structures the content into an article]
    ↓
Output: Complete article with introduction, body, and conclusion
```

**System Prompt:**
```
Write a detailed article from: {research content}

Include:
- Introduction
- Main Content
- Conclusion
```

**Example:**

Input (Research from previous step):
```
"Key Facts: Quantum computing uses qubits...
 Statistics: Market will reach $65 billion...
 Important Points: Early research stage..."
```

Output Article:
```
Quantum Computing: The Next Frontier in Technology

Introduction:
Quantum computing represents a revolutionary shift in computational power. 
Unlike classical computers that use bits (0 or 1), quantum computers harness 
the power of quantum mechanics to process information exponentially faster.

Main Content:
1. How Quantum Computers Work
   Quantum computers operate on three key principles:
   - Superposition: Qubits exist in multiple states simultaneously
   - Entanglement: Qubits are interconnected across the system
   - Interference: Algorithms amplify correct answers and cancel wrong ones

2. Current Applications
   - Drug Discovery: Modeling molecular interactions
   - Optimization: Solving complex logistics problems
   - Cryptography: Breaking current encryption standards

3. The Market Opportunity
   The quantum computing market is expected to reach $65 billion by 2030,
   with 60% of enterprises already exploring implementations.

Conclusion:
While quantum computing is still in its early research phase, the potential 
applications are transformative. Organizations that invest now will gain 
competitive advantages in the next decade.
```

**Code explanation:**
```python
@with_retry
def writer_agent(research):
    # Create prompt with research content
    prompt = f"""
    Write a detailed article from: {research}
    
    Include:
    - Introduction
    - Main Content
    - Conclusion
    """
    
    # Send to LLM
    result = llm.invoke(prompt)
    
    # Return the article
    return result.content
```

**Key point:** The writer takes unstructured research and transforms it into a professionally formatted article.

---

#### 3️⃣ **agents/editor.py** - Editor Agent

**What it does:** Refines the article by fixing grammar, improving structure, and enhancing readability

**The Process:**

```
Input: Raw article from writer agent
    ↓
[Editor creates a prompt asking for improvements]
    ↓
[Sends article + instructions to Groq LLM]
    ↓
[LLM reviews and improves the article]
    ↓
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

**Example of improvements:**

Before (Writer output):
```
"Quantum computing is a new technology. It use qubits. Qubits is different 
from bits because they can be 0 and 1 at same time. This makes them faster. 
The market for quantum computing is big. It will reach 65 billion dollars."
```

After (Editor output):
```
"Quantum computing represents a paradigm shift in computational technology. 
Unlike classical computers that rely on bits, quantum systems harness quantum 
mechanics through qubits. These quantum bits possess a unique property called 
superposition, allowing them to exist in multiple states simultaneously—a 
characteristic that enables exponential computational advantages. The global 
quantum computing market is projected to reach $65 billion by 2030, reflecting 
growing enterprise investment in this transformative technology."
```

**Improvements made:**
- Fixed grammar: "use" → "harness", "is" → "represent"
- Better structure: Clearer flow and transitions
- Enhanced readability: Varied sentence length, professional vocabulary
- Removed redundancy: Combined related ideas

**Code explanation:**
```python
@with_retry
def editor_agent(article):
    # Create prompt asking for improvements
    prompt = f"""
    Improve the article.
    
    Fix:
    - Grammar
    - Structure
    - Readability
    
    Article: {article}
    """
    
    # Send to LLM for refinement
    result = llm.invoke(prompt)
    
    # Return improved article
    return result.content
```

---

### **graph/ Package - Workflow Orchestration**

#### 📊 **graph/workflow.py** - LangGraph Pipeline

**What it is:** The master coordinator that orchestrates all agents in sequence

**What it does:**
- Defines the state/data passed between agents
- Creates nodes (processing steps) for each agent
- Chains nodes together in the correct order
- Manages error handling for each step

**The Workflow Structure:**

```
┌─────────────────────────────────────────────────┐
│              STATE MACHINE                      │
├─────────────────────────────────────────────────┤
│                                                 │
│  topic: str           ← Input from user        │
│  research: str        ← Output from researcher │
│  article: str         ← Output from writer     │
│  edited: str          ← Output from editor     │
│  evaluation: dict     ← Output from evaluator  │
│                                                 │
└─────────────────────────────────────────────────┘
```

**The Pipeline Flow:**

```
START
  ↓
[research_node] → Calls researcher_agent → Gets research
  ↓
[writer_node] → Calls writer_agent → Gets article
  ↓
[editor_node] → Calls editor_agent → Gets edited article
  ↓
[evaluation_node] → Calls evaluator → Gets score
  ↓
END
```

**Code breakdown:**

```python
# Step 1: Define the shared state
class AgentState(TypedDict):
    topic: str              # What user asked for
    research: str           # What researcher found
    article: str            # What writer created
    edited: str             # What editor refined
    evaluation: dict        # What evaluator scored

# Step 2: Create processing nodes (each node calls an agent)
def research_node(state):
    # Take topic from state
    # Call researcher agent
    # Add research to state
    research = research_agent(state["topic"])
    return {"research": research}

def writer_node(state):
    # Take research from state
    # Call writer agent
    # Add article to state
    article = writer_agent(state["research"])
    return {"article": article}

def editor_node(state):
    # Take article from state
    # Call editor agent
    # Add edited version to state
    edited = editor_agent(state["article"])
    return {"edited": edited}

def evaluation_node(state):
    # Take edited article from state
    # Call evaluator
    # Add evaluation to state
    evaluation = evaluate(state["edited"])
    return {"evaluation": evaluation}

# Step 3: Connect the nodes in sequence
builder = StateGraph(AgentState)

builder.add_node("research", research_node)
builder.add_node("writer", writer_node)
builder.add_node("editor", editor_node)
builder.add_node("evaluation", evaluation_node)

# Step 4: Define the flow
builder.set_entry_point("research")  # Start here

builder.add_edge("research", "writer")    # research → writer
builder.add_edge("writer", "editor")      # writer → editor
builder.add_edge("editor", "evaluation")  # editor → evaluation
builder.add_edge("evaluation", END)       # evaluation → finish

# Step 5: Compile into executable graph
graph = builder.compile()
```

**How it executes:**

When `graph.invoke({"topic": "AI"})` is called:

```
1. Initialize state: {topic: "AI"}
2. Run research_node:
   - Calls research_agent("AI")
   - Updates state with research
   - State: {topic: "AI", research: "...facts..."}
3. Run writer_node:
   - Calls writer_agent("...facts...")
   - Updates state with article
   - State: {...previous..., article: "...article..."}
4. Run editor_node:
   - Calls editor_agent("...article...")
   - Updates state with edited version
   - State: {...previous..., edited: "...refined..."}
5. Run evaluation_node:
   - Calls evaluate("...refined...")
   - Updates state with score
   - State: {...previous..., evaluation: {word_count: X, score: Y}}
6. Return final state with everything
```

**Error handling in nodes:**
```python
def writer_node(state):
    try:
        article = writer_agent(state["research"])
        return {"article": article}
    except Exception as e:
        raise Exception(f"Writer node failed: {str(e)}")
```

If any node fails, the error is caught and reported with context about which step failed.

---

### **evaluation/ Package - Quality Assessment**

#### 🎯 **evaluation/evaluator.py** - Content Scorer

**What it does:** Scores the final article quality based on objective metrics

**The Scoring Logic:**

```python
def evaluate(content):
    # Step 1: Count words in the article
    words = len(content.split())
    
    # Step 2: Initialize score
    score = 0
    
    # Step 3: Award points based on length
    if words > 300:
        score += 50  # Award 50 points if over 300 words
    
    if words > 600:
        score += 50  # Award 50 more points if over 600 words
    
    # Step 4: Return results
    return {
        "word_count": words,
        "score": score  # Max score: 100
    }
```

**Scoring Breakdown:**

| Word Count | Points Earned | Total Score |
|-----------|---------------|-------------|
| 0-299     | 0             | 0 (Poor)    |
| 300-599   | 50            | 50 (Fair)   |
| 600+      | 50 + 50       | 100 (Good)  |

**Example:**

Article with 750 words:
```
word_count = 750
score = 0

Is 750 > 300? YES → score = 50
Is 750 > 600? YES → score = 50 + 50 = 100

Result: {
    "word_count": 750,
    "score": 100
}
```

**Why this matters:**
- Ensures minimum quality standards
- Encourages thorough, detailed articles
- Provides objective feedback to users
- Can be extended with more metrics

---

## 🔄 Complete End-to-End Example

Let's trace what happens when a user submits a topic:

**User Input:** "Machine Learning Basics"

### Step 1: User Submits via Streamlit
```
User types: "Machine Learning Basics"
User clicks: "Generate"
Streamlit sends to API: POST /generate?topic=Machine%20Learning%20Basics
```

### Step 2: FastAPI Receives Request
```python
# In app.py
@app.post("/generate")
def generate(topic: str):
    result = graph.invoke({"topic": "Machine Learning Basics"})
    return {"status": "success", "result": result}
```

### Step 3: Workflow Begins - Research Node
```
research_node is called with state:
{
  "topic": "Machine Learning Basics"
}

↓

Calls researcher_agent("Machine Learning Basics")

↓

LLM receives prompt:
"Research the topic: Machine Learning Basics
 Provide:
 1. Key Facts
 2. Statistics
 3. Important Points"

↓

LLM returns research like:
"Key Facts:
 - Machine learning is a subset of AI
 - Computers learn patterns from data without explicit programming
 - Three main types: supervised, unsupervised, reinforcement learning
 
 Statistics:
 - ML market reached $45 billion in 2024
 - 75% of enterprises use ML solutions
 
 Important Points:
 - Requires large labeled datasets
 - Can find patterns humans miss
 - Powers recommendation systems, fraud detection, etc."

↓

State updated:
{
  "topic": "Machine Learning Basics",
  "research": "Key Facts: Machine learning is..."
}
```

### Step 4: Workflow Continues - Writer Node
```
writer_node is called with state from previous step

↓

Calls writer_agent(research_content)

↓

LLM receives prompt:
"Write a detailed article from: Key Facts: Machine learning is...
 Include:
 - Introduction
 - Main Content
 - Conclusion"

↓

LLM returns structured article:
"Machine Learning Basics: A Comprehensive Guide

Introduction:
Machine learning represents a fundamental shift in how we build software...

Main Content:
1. What is Machine Learning?
   Machine learning is a subset of artificial intelligence...
   
2. Types of Machine Learning
   - Supervised Learning: Learning with labeled examples
   - Unsupervised Learning: Finding patterns in unlabeled data
   - Reinforcement Learning: Learning through rewards and penalties

3. Real-World Applications
   - Recommendation Systems: Netflix, Amazon
   - Fraud Detection: Banks and payment systems
   - Image Recognition: Google Photos, facial recognition

Conclusion:
Machine learning is transforming industries..."

↓

State updated:
{
  "topic": "Machine Learning Basics",
  "research": "Key Facts: Machine learning is...",
  "article": "Machine Learning Basics: A Comprehensive Guide..."
}
```

### Step 5: Workflow Continues - Editor Node
```
editor_node is called with state from previous step

↓

Calls editor_agent(article)

↓

LLM receives prompt:
"Improve the article.
 Fix:
 - Grammar
 - Structure
 - Readability
 Article: Machine Learning Basics..."

↓

LLM improves article:
- Fixes any grammatical errors
- Improves sentence flow
- Makes technical terms clearer
- Enhances overall professionalism

Returns: Same article but polished version

↓

State updated:
{
  "topic": "Machine Learning Basics",
  "research": "Key Facts...",
  "article": "Original article",
  "edited": "Polished article..."
}
```

### Step 6: Workflow Continues - Evaluation Node
```
evaluation_node is called with state from previous step

↓

Calls evaluate(edited_article)

↓

Evaluator counts words:
Let's say the edited article is 820 words

word_count = 820
score = 0

Is 820 > 300? YES → score = 50
Is 820 > 600? YES → score = 50 + 50 = 100

Returns: {
  "word_count": 820,
  "score": 100
}

↓

State updated:
{
  "topic": "Machine Learning Basics",
  "research": "Key Facts...",
  "article": "Original article",
  "edited": "Polished article...",
  "evaluation": {"word_count": 820, "score": 100}
}
```

### Step 7: Final Result
```
FastAPI returns to Streamlit:
{
  "status": "success",
  "result": {
    "topic": "Machine Learning Basics",
    "research": "Key Facts: Machine learning is...",
    "article": "Machine Learning Basics: A Comprehensive Guide...",
    "edited": "Machine Learning Basics: A Comprehensive Guide... (improved)",
    "evaluation": {
      "word_count": 820,
      "score": 100
    }
  }
}
```

### Step 8: Streamlit Displays Results
```
Streamlit receives the response and displays:
┌─────────────────────────────────────────┐
│ Final Article                           │
├─────────────────────────────────────────┤
│ Machine Learning Basics:                │
│ A Comprehensive Guide                   │
│                                         │
│ [Full article content displayed...]     │
│                                         │
│ Evaluation                              │
│ {                                       │
│   "word_count": 820,                    │
│   "score": 100                          │
│ }                                       │
└─────────────────────────────────────────┘
```

---

## 🚀 How to Run the System

### Prerequisites
- Python 3.8+
- Groq API key (from https://console.groq.com)

### Step 1: Set Up Environment
```bash
# Navigate to project directory
cd capstoneproject

# Create .env file with your API key
echo GROQ_API_KEY=your_api_key_here > .env

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Start the FastAPI Backend
```bash
# Terminal 1
uvicorn app:app --reload

# Output should show:
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 3: Start Streamlit Frontend (Optional)
```bash
# Terminal 2
streamlit run streamlit_app.py

# Output should show:
# Local URL: http://localhost:8501
```

### Step 4: Use the System

**Option A - Via Swagger Docs:**
```
1. Open http://localhost:8000/docs
2. Click on "POST /ask" or "POST /ingest"
3. Click "Try it out"
4. Enter a question in the JSON body for `/ask`
5. Upload files as multipart form data for `/ingest`
6. Click "Execute"
7. View the response
```

**Option B - Via Streamlit Web UI:**
```
1. Open http://localhost:8501
2. Upload documents in the sidebar if needed
3. Enter a question in the text input
4. Click "Ask"
5. View the answer and retrieved sources
```

**Option C - Via cURL:**
```bash
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"What does the documentation say about the workflow?\",\"top_k\":5}"
```

### Optional Knowledge Base Folder

Create a `knowledge_base/` folder in the project root and drop `.pdf`, `.md`, or `.txt` files there. The app will index those files automatically when it starts or when you call `/reindex`.

---

## 📊 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INPUT LAYER                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Streamlit Web UI        │  API Docs (Swagger)            │
│  (Port 8501)             │  (Port 8000/docs)              │
│                                                             │
└────────────────┬──────────────────────────────────────────┘
                 │ HTTP Request
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                  API LAYER (FastAPI)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  app.py                                                    │
│  - POST /generate                                          │
│  - GET /health                                             │
│                                                             │
└────────────────┬──────────────────────────────────────────┘
                 │ invoke()
                 ↓
┌─────────────────────────────────────────────────────────────┐
│              ORCHESTRATION LAYER (LangGraph)               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  workflow.py (State Machine)                               │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │ AgentState                                   │          │
│  │ - topic: str                                 │          │
│  │ - research: str                              │          │
│  │ - article: str                               │          │
│  │ - edited: str                                │          │
│  │ - evaluation: dict                           │          │
│  └──────────────────────────────────────────────┘          │
│                                                             │
│  research_node → writer_node → editor_node → eval_node    │
│                                                             │
└────────────────┬──────────────────────────────────────────┘
                 │
        ┌────────┼────────┐
        ↓        ↓        ↓
┌──────────────────────────────────────────────────────────┐
│            AGENT LAYER (Individual Agents)              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ researcher.py    writer.py      editor.py               │
│ Gathers facts    Structures     Improves quality        │
│ and stats        into article   and readability         │
│                                                          │
└────────┬─────────────┬──────────────────┬──────────────┘
         │             │                  │
         └──────────┬──┴──────────────────┘
                    │
                    ↓
┌──────────────────────────────────────────────────────────┐
│         LLM LAYER (Groq API with Retry Logic)           │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  llm_config.py (Groq ChatGPT 120B)                      │
│  - Timeout: 60 seconds                                  │
│  - Retry: Up to 3 attempts with backoff                │
│  - Temperature: 0.7 (balanced creativity)               │
│                                                          │
└────────┬──────────────────────────────────────────────┘
         │
         ↓
    Groq API
    (External Service)
    
         │
         ↓
    ┌────────────────────────────┐
    │ LLM Response (Text)        │
    └────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────────────────────┐
│         EVALUATION LAYER (Quality Scoring)              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  evaluator.py                                           │
│  - Counts words                                         │
│  - Awards points based on length                        │
│  - Returns score (0-100)                                │
│                                                          │
└────────────────┬─────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│              RESPONSE LAYER (JSON Output)              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  {                                                      │
│    "status": "success",                                │
│    "result": {                                         │
│      "topic": "...",                                   │
│      "research": "...",                                │
│      "article": "...",                                 │
│      "edited": "...",                                  │
│      "evaluation": {...}                               │
│    }                                                    │
│  }                                                      │
│                                                         │
└────────────────┬──────────────────────────────────────┘
                 │ JSON Response
                 ↓
         Browser / App
```

---

## 🎓 Key Learning Outcomes

After understanding this project, students will learn:

### 1. **AI & LLM Integration**
- How to use LLMs (Large Language Models) for text processing
- Prompting techniques (system instructions, formatting, examples)
- Error handling and retry logic for API calls

### 2. **Agent-Based Architecture**
- Building specialized agents for specific tasks
- Orchestrating agents in a workflow
- State management across agents
- Sequential vs parallel processing

### 3. **Web Development**
- Building REST APIs with FastAPI
- Creating web interfaces with Streamlit
- HTTP request/response handling
- Error handling and status codes

### 4. **Software Engineering**
- Project structure and organization
- Separation of concerns (agents, workflow, API)
- Dependency management (requirements.txt)
- Configuration management (.env files)
- Logging and debugging

### 5. **Data Flow**
- Understanding how data flows through a pipeline
- State transformations at each step
- Data validation and error propagation

---

## 🔧 Customization Guide

### How to Modify Research Agent
```python
# In agents/researcher.py, change the prompt:
prompt = f"""
Research the topic: {topic}

Provide ONLY:
1. Latest scientific findings
2. Quantifiable statistics
3. Expert opinions from recent publications

Focus on peer-reviewed sources only.
Ignore opinion-based content.
"""
```

### How to Modify Writer Agent
```python
# In agents/writer.py, change the prompt:
prompt = f"""
Write a technical article (1000-1500 words) from: {research}

Structure as:
- Abstract (100 words)
- Introduction with context
- Problem statement
- Solution/Approach
- Benefits and implications
- Limitations
- Conclusion

Use academic tone. Include citations where possible.
"""
```

### How to Modify Evaluator
```python
# In evaluation/evaluator.py, enhance scoring:
def evaluate(content):
    words = len(content.split())
    sentences = len(content.split('.'))
    
    score = 0
    
    # Length scoring
    if words > 400: score += 25
    if words > 800: score += 25
    
    # Readability scoring
    avg_word_len = sum(len(w) for w in content.split()) / len(content.split())
    if 4 < avg_word_len < 6: score += 20  # Good word length
    
    # Structure scoring
    if '\n' in content: score += 15  # Has sections
    
    # Professional language
    pro_words = ['moreover', 'therefore', 'consequently', 'furthermore']
    if any(w in content.lower() for w in pro_words): score += 15
    
    return {
        "word_count": words,
        "avg_word_length": avg_word_len,
        "sentence_count": sentences,
        "score": min(100, max(0, score))
    }
```

---

## ⚠️ Important Notes

1. **API Key Required:** Must set `GROQ_API_KEY` in `.env` file
2. **Internet Connection:** Requires connection to Groq API
3. **Rate Limits:** Groq API may have rate limits on free tier
4. **Sequential Processing:** Agents run one after another (not in parallel)
5. **Token Limits:** Each LLM call has a maximum token limit
6. **Cost:** Using Groq API may incur costs depending on your plan

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `GROQ_API_KEY not found` | Create `.env` file with your API key |
| `Connection refused` on port 8000 | Start FastAPI: `uvicorn app:app --reload` |
| `Connection refused` on Streamlit | Start Streamlit: `streamlit run streamlit_app.py` |
| 500 error from API | Check if Groq API is responding, check API key validity |
| Timeout errors | Increase timeout in `llm_config.py` |
| Out of memory | Process shorter topics or reduce model size |

---

## 📚 Further Learning

### Concepts to Explore
- **LangGraph:** Advanced workflow patterns, parallel execution
- **LangChain:** Chain composition, memory management
- **Prompt Engineering:** Few-shot learning, chain-of-thought
- **FastAPI:** Middleware, authentication, database integration
- **Streamlit:** Custom components, state management
- **Groq API:** Different models, token counting

### Enhancement Ideas
1. Add database to store article history
2. Implement user authentication
3. Add article caching to avoid duplicate processing
4. Create admin dashboard for monitoring
5. Implement streaming responses for real-time feedback
6. Add fact-checking agent
7. Implement parallel agent execution
8. Add feedback loop for continuous improvement
9. Create article templates for different genres
10. Add multi-language support

---

## 📝 Summary

This Research Writer Agent project demonstrates:
- **Multi-agent systems:** Specialized agents working together
- **LLM integration:** Using large language models effectively
- **Workflow orchestration:** Coordinating complex pipelines
- **Full-stack development:** Backend API + Frontend UI
- **Error handling:** Robust, production-ready code

The system takes a simple topic and transforms it through research, writing, editing, and evaluation to produce a professional article—all automatically!

---

**Happy Learning! 🎉**
