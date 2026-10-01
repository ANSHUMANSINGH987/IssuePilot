# IssuePilot Model Harness

The `harness/` directory provides an extensible runtime abstraction for executing open-weight code models (e.g., Qwen 2.5 Coder, Llama 3.1) alongside OpenAI-compatible endpoints (Ollama, vLLM, SGLang).

## Planned Modules:
- `client.py`: Async client connection to OpenAI-compatible inference servers with streaming support.
- `prompts.py`: Contributor profiling, issue triage, and dossier synthesis prompt templates.
- `schemas.py`: Pydantic models for structured output extraction (issue suitability scores, setup blueprints).
