# Pull-Request-Pilot: A Technical Deep-Dive & Roadmap

Pull-Request-Pilot is an agentic AI system designed to solve the critical friction points in modern code reviews. This document is split into two sections: **Part 1** explores the existing architecture and where to find the implementation in the codebase. **Part 2** outlines the strategic roadmap for scaling, cost management, and observability.

---

## Part 1: What We Have Built (Current Architecture)

We have built a stateful, context-aware reviewer that moves beyond simple prompt-wrapping. Below is the technical breakdown of the core components and their locations in the project.

### 1. Semantic Filtering (The "Noise" Gate)
**Concept:** Not every change needs an LLM. Docstring updates, lock-file changes, or whitespace adjustments shouldn't waste tokens. 
- **Mechanism:** We use **Tree-sitter** to parse the Abstract Syntax Tree (AST). By comparing the "Semantic Fingerprint" (stripping comments and extras) of the old vs. new code, we determine if logical changes occurred.
- **Where to find it:** 
    - `src/utils/filter_utils.py`: Contains the `should_review_file()` logic.
    - `notes/sementic_filtering.txt`: Detailed theory on AST walk vs. raw diff.

### 2. Tiny Chunking & Precision Line Tracking
**Concept:** Large diffs cause "Attention Drift." We force the model to focus on 10-line windows.
- **Mechanism:** The `HunkProcessor` segments a patch into 10-line blocks. It maintains a `current_new_line` counter that tracks the actual line numbers in the *destination* file, ensuring that inline comments never "drift" to the wrong location.
- **Where to find it:** 
    - `src/utils/hunk_processor.py`: The core chunking and line-counting engine.
    - `notes/chunking.txt`: Logic for handling additions (+) vs context lines.

### 3. Contextual Tooling (Agentic Pull)
**Concept:** Diff context is often too small to understand complex bugs. Instead of sending the whole file (expensive), we give the agent "Hands."
- **Mechanism:** The agent is equipped with tools like `get_file_structure` and `get_function_content`. When the agent identifies a risky change, it pauses, pulls the full body of the surrounding function, and then resumes with a "Deep" understanding.
- **Where to find it:** 
    - `src/services/llm/tools/`: Tool definitions for the Agent.
    - `notes/contextual_tooling.txt`: Philosophy on why "Pull" is better than "Pushing" full files.

### 4. Review Memory (Stateful Collaboration)
**Concept:** Avoid the "Robotic Repeat" problem where the bot posts the same advice on every commit.
- **Mechanism:** The system fetches existing PR comments before starting. It calculates a hash/normalized version of proposed comments. If a comment already exists at that line, it is suppressed.
- **Where to find it:** 
    - `src/services/scm/github.py`: Logic for fetching existing PR comments.
    - `notes/review_memory.txt`: The deduplication roadmap and completed matches.

### 5. Multi-Language Parsing (Universal Semantic Walker)
**Concept:** Unified support for Python, Go, Rust, JS/TS, and Java without writing 5 different parsers.
- **Mechanism:** A language-agnostic tree-walker that uses a `NODE_TYPES` map to identify declarations (classes, functions, methods) regardless of the language syntax.
- **Where to find it:** 
    - `src/code_parser/parser.py`: The dispatcher for language extensions.
    - `src/code_parser/language.py`: The configuration mapping Tree-sitter nodes to logical types.
    - `notes/multi-language-support.txt`: Instructions on adding new languages.

---

## Part 2: The Future Horizon (Improvements & Strategy)

As the system scales, we move from "Building a tool" to "Running a Platform." Below are the strategic pillars for future development.

### 1. Handling "Monster" PRs (>1,000 Lines)
Current chunking handles files well, but extremely large PRs pose a different challenge.
- **Priority Scoring:** Implement a weighting system. Prioritize files in `/core`, `/logic`, or `/security` over `/ui` or `/tests`.
- **Sampling:** For massive refactors (e.g., renaming a variable project-wide), the agent should detect the pattern after 5 chunks and "summarize" the rest rather than reviewing 500 instances.
- **Concurrency Control:** Use a distributed task queue (like Celery/Redis) instead of simple `asyncio` to prevent the SCM service from timing out on long-running reviews.

### 2. Cost & Token Economics (FinOps)
When running in production with models like GPT-4o or Claude 3.5, costs can skyrocket.
- **Monitoring Cost per PR:** 
    - Wrap the LLM client to track `prompt_tokens` and `completion_tokens` per `PR_ID`.
    - Log these metrics to a database to generate "Monthly Cost per Developer" reports.
- **Budgeting:** Implement a "Soft Limit" in the `.env` (e.g., `MAX_TOKENS_PER_PR=50000`). If a PR exceeds this, the agent switches to a cheaper model (e.g., Llama 3 on Ollama) or skips low-priority files.

### 3. Observability & Performance Metrics
To improve the "Trust" of the developers, we must monitor the bot's performance.

| Metric | Target | Detection Method |
| :--- | :--- | :--- |
| **Acceptance Rate** | >30% | Track GitHub reactions (🚀/👍) or if code was changed following a comment. |
| **Hallucination Rate** | <2% | Monitor "Invalid Line Number" errors returned by the SCM API. |
| **Latency** | <2 min | Measure time from `PullRequestEvent` to `LastCommentPosted`. |
| **Tool Usage Utility** | N/A | Log how often `get_function_content` actually leads to a change in the final review comment. |

### 4. Advanced AI Patterns
- **RAG for Codebase (Cross-File Analysis):** Currently, the agent is file-scoped. By indexing the codebase into a Vector DB, the agent could detect if a change in `Module A` breaks an undocumented assumption in `Module B`.
- **Automated Fix Generation (Patch/Diff):** Instead of just saying "This is broken," provide a one-click `Apply Suggestion` block. This requires high-precision formatting to ensure the suggested code matches the project's linter.
- **Commit History Context:** Understanding *who* wrote the code and *why* (via commit messages) can help the AI avoid suggesting changes that were previously rejected in other PRs.

## Part 3: Implementation Deep Dives (Roadmap & Advanced Engineering)

To transition this from a prototype to a production-grade platform, we need to solve deep engineering challenges in validation, cost, and scale.

### 1. Cost Engineering: The "FinOps" Monitoring Logic
In a production environment, you need an automated gatekeeper to prevent runaway API costs. We propose a `CostMonitor` class that decorates the LLM service.

**Conceptual Implementation:**
```python
class CostMonitor:
    def __init__(self, daily_budget=10.0, pr_limit=1.0):
        self.daily_budget = daily_budget
        self.pr_limit = pr_limit
        self.current_pr_cost = 0.0

    def track_call(self, model, prompt_tokens, completion_tokens):
        # Pricing logic (e.g., $0.015 per 1k tokens)
        cost = (prompt_tokens * pricing[model]['input']) + (completion_tokens * pricing[model]['output'])
        self.current_pr_cost += cost
        
        if self.current_pr_cost > self.pr_limit:
            # Fallback to local Ollama (Free) for remaining chunks
            return "SWITCH_TO_LOCAL"
        return "STAY_ON_CLOUD"
```
- **Strategic Value:** This prevents a single 5,000-line "monster" PR from burning your entire weekly budget while still providing a basic review via local models.

### 2. Algorithmic Handling of Large PRs: The "Sampling Strategy"
A senior developer doesn't review every single line of a 500-file refactor where only a variable name changed. The system should mimic this intuition.

- **Phase A: Hunk Hashing:** Calculate a hash of the *logical change* in each hunk.
- **Phase B: Redundancy Detection:** If 10 patches in a row have identical logical changes (e.g., renaming `old_val` to `new_val`), the system enters **"Summary Mode."**
- **Phase C: Pattern Notification:** Instead of 100 comments, it posts one: *"Detected a bulk rename pattern. I've spot-checked 5 instances and they look correct; skipping the remaining 95 instances to save tokens."*

### 3. Anti-Hallucination: The Multi-Stage Validation Pipeline
LLMs occasionally hallucinate line numbers or suggest syntactically broken code. We build "Unit Tests" for the AI's output.

1.  **Line Validity Check:** Before posting, the `ScmService` verifies if the `line_number` returned by the AI actually exists in the PR's `head` commit. If it doesn't, the comment is dropped or re-anchored to the nearest hunk.
2.  **Self-Correction Loop:** If a comment fails validation, we send a "Correction Prompt": *"You suggested a comment on line 45, but that line doesn't exist. Here is the correct hunk context. Please retry."*
3.  **Static Analysis on Suggestions:** Run a lightweight parser (like `flake8` or `eslint`) on the AI's suggested code snippets. If the suggestion itself has syntax errors, discard it to maintain high developer trust.

### 4. ROI & Performance Metrics: Quantifying Success
How do we prove this tool is worth it? We track the "Developer Trust Score."

- **Time to Merge (TTM):** Does using PR-Pilot reduce the total time a PR stays open?
- **Re-Open Rate:** Do PRs reviewed by the agent have fewer "Fix-up" commits later than those reviewed only by humans?
- **Developer Sentiment (Direct Feedback):**
    - `Acceptance Rate`: Counting how many AI suggestions were actually implemented by the dev.
    - `Rejection Rate`: Tracking which files the AI is "noisiest" in, helping us tune the Semantic Filter.
- **Cost vs. Value:** If a senior engineer costs $100/hr, and the bot saves 15 minutes of leur time per review at a cost of $0.50, the ROI is ~50x.

*Last Updated: January 31, 2026*
