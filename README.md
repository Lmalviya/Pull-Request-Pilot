# 🚀 Pull Request Pilot

**Pull Request Pilot** is an AI-powered automated code review system that integrates directly into your GitHub workflow via webhooks. It acts as an intelligent co-pilot, providing granular, line-by-line feedback on Pull Requests using state-of-the-art LLMs (OpenAI, Anthropic, or local Ollama instances).

---

## ✨ Key Features & Functionality

### 1. **High-Focus AI Reviews**
Instead of dumping an entire file into the AI, PR Pilot uses a **"Tiny Chunking" strategy**. It breaks down git diffs into small, manageable 10-line blocks. This prevents "context overload," reduces hallucinations, and ensures the AI provides highly accurate feedback on specific logic changes.

### 2. **Multi-Model Support**
Deploy with your choice of LLM provider:
- **OpenAI**: GPT-4, GPT-4-turbo, etc.
- **Anthropic**: Claude 3.5 Sonnet, etc.
- **Ollama**: Run models like `llama3.1` or `mistral` locally for privacy and zero cost.

### 3. **Advanced Semantic Filtering**
Powered by **Tree-sitter ASTs**, the system detects if changes are purely non-semantic (e.g., updating comments, docstrings, or fixing indentation). If no logic change is detected, it skips the LLM review entirely, saving significant API costs and reducing noise.
- **Includes**: Traditional ignore lists for `.lock`, `.json`, `.md`.
- **Logic**: Deep AST comparison for Python, JS, Go, Java, and more.

### 4. **Flexible Execution Modes**
- **Sequential**: Processes one chunk at a time (safe for local hardware or strict API limits).
- **Parallel**: Uses `asyncio` to process multiple blocks simultaneously for high-speed reviews.

### 5. **Universal Code Parser**
Powered by **Tree-sitter**, the pilot understands the structure (classes, functions, methods) of your code across 9+ languages including **Python, JavaScript, TypeScript, Go, Java, Rust, C, C++, and Ruby**. This allows the AI to stay aware of the semantic context of every change.

### 6. **Containerized Architecture**
Ready for deployment with **Docker** and **Docker Compose**, featuring a multi-stage `Dockerfile` and automated dependency management via **PDM**.

---

## 🛠️ Getting Started

### Prerequisites
- Docker & Docker Compose
- A GitHub Personal Access Token (with `repo` access)
- (Optional) [Ollama](https://ollama.com/) installed if running models locally.

### Installation & Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Lmalviya/Pull-Request-Pilot.git
    cd Pull-Request-Pilot
    ```

2.  **Configure Environment**:
    Copy the example env file and fill in your keys:
    ```bash
    cp .env.example .env
    ```

3.  **Run with Docker**:
    ```bash
    docker-compose up --build
    ```
    The application will start on `http://localhost:8000`.

4.  **Expose for Webhooks**:
    Use a tool like `ngrok` to expose your local port for GitHub Webhooks:
    ```bash
    ngrok http 8000
    ```
    Add the generated URL + `/webhook/github` to your GitHub Repository settings.

---

## 🗺️ Roadmap & Future Enhancements

### 🚧 Currently Supported
- [x] GitHub Webhook Integration (Push & PR events)
- [x] Multi-stage Tiny Chunking for diffs
- [x] **Universal Multi-language Parser** (Tree-sitter integration)
- [x] Configurable ignore lists (extensions/files)
- [x] OpenAI, Anthropic, and Ollama providers
- [x] Sequential & Parallel review execution
- [x] Inline commenting on GitHub PRs
- [x] **Advanced Semantic Filtering** (AST-based logic change detection)

### 🚀 Planned Features (To Be Implemented Later)
- [ ] **GitLab & Bitbucket Support**: Expand SCM services to support other major platforms.
- [ ] **Review Memory**: Allow the agent to remember previous comments to avoid repetitive feedback.
- [ ] **Custom System Prompts**: Web UI or per-repo configuration for specialized review rules (e.g., security-first, performance-first).
- [ ] **Support for PR Summary**: Generate a high-level summary of the entire PR in addition to inline comments.
- [ ] **Test Coverage Analysis**: Automatically check if new code has corresponding test changes.

---

## 📝 Project Structure
- `src/api`: FastAPI webhook endpoints.
- `src/services/scm`: logic for interacting with GitHub/GitLab.
- `src/services/llm`: Clients for different AI providers.
- `src/utils`: Hunk processing and filtering utilities.
- `notes/`: Architectural notes and setup guides.

---

## ⚖️ License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.