# JalMitra: files by team member

The code files stay where they are, because the app imports them by name from the main folder. Moving them would break JalMitra. This map shows each member which files are "theirs" to explain and to commit to on GitHub.

Team (Section DC): Naveen Khatri, Rohit Sharma, Aryan Jangir, Himanshu Yadav, Aryan Sharma and Garvit Khandal.

| Member | Part | Main files | Supporting files and results |
|---|---|---|---|
| 1 · Naveen Khatri (25BCON0699) | Problem, data collection and cleaning | `extract_data.py`, `build_dataset.py`, `build_database.py`, `validate_database.py`, `gwra_enrich.py` | `data/groundwater.db`, `data/groundwater.csv`, `data/processed/`, `data/extracted/`, `data/duplicate_records.csv`, `data/category_conflicts.csv`, `data/quality_report.csv`, `DATA_SOURCES.md`, `DATA_REQUIREMENTS.md`, `JALMITRA4_GROUNDWATER_DATA_REPORT.md`, `ingest/` |
| 2 · Rohit Sharma (25BCON0627) | Database, place-name search and RAG retrieval | `database.py`, `retrieval.py`, `entity_resolver.py`, `intent_parser.py`, `rag.py`, `build_rag_index.py`, `gwra_blocks_retrieval.py`, `monitoring_retrieval.py` | `data/place_aliases.csv`, `data/monitoring/gwra_blocks_2025.db`, `engine.py` (the pipeline), `test_gwra_blocks.py`, `test_monitoring.py` |
| 3 · Aryan Jangir (25BCON0767) | Prompt engineering and model selection | `jalmitra_ai.py` (system prompt `SYSTEM`, task prompts `TASK`, `STYLE`, `LENGTH`, `SCRIPT_HINT`, `build_messages`), `llm_compose.py`, `llm_provider.py` | `LLM_ARCHITECTURE.md`, `eval/model_selection.py`, `eval/compare_models.py`, `eval/comparison_2026-11-23.md`, `eval/phase6_screen_*.md` (Qwen vs Gemma), `requirements-llm.txt` |
| 4 · Himanshu Yadav (25BCON0718) | Verification, guardrails and prompt-injection safety | `answer_verifier.py`, `semantic_gate.py`, `security.py`, the `check()` and retry part of `jalmitra_ai.py` | `eval/security_live.py`, `eval/security_live_2026-11-23.md`, `eval/semantic_factuality.py`, `eval/semantic_v5*.md`, `test_v4_semantic.py`, `test_v4_llm.py` |
| 5 · Aryan Sharma (25BCON0771) | Six languages and the chat website | `language.py`, `conversation.py`, `conversation_state.py`, `templates_v3.py`, `templates_app.py`, `templates_kn.py`, `app_info.py`, `app.py`, `ui_chat_v4.py`, `ui_theme.py`, `ui_settings.py`, `ui_components.py`, `chat_store.py`, `voice.py` | `voice_component/`, `assets/`, `.streamlit/config.toml`, `docs/screenshots/`, `docs/language_review_template.csv`, `eval/lang_eval.py`, `eval/lang_*.tsv`, `test_conversation.py`, `test_app_info.py`, `test_v4_ui.py` |
| 6 · Garvit Khandal (25BCON0784) | Testing, results, GitHub, limitations and future scope | `test_local_engine.py`, `test_v3.py`, `test_v3_domains.py`, `test_v5.py`, `test_v6.py`, `test_300q.py`, `fake_ai_for_tests.py`, `eval/phase6_eval.py` | `TEST_STATUS.md`, `KNOWN_LIMITATIONS.md`, `ROADMAP.md`, `CHANGELOG.md`, `README.md`, `eval/PHASE6_REPORT.md`, `eval/phase6_full_*.md`, `tests_data/`, `.gitignore` |

Each member's own notes file is in `docs/members/` (uploaded by that member; see Part 10 of the GitHub guide).

Shared: `START_JALMITRA.bat` and `STOP_JALMITRA.bat` start and stop the app (the demo).

## Not part of the current app (kept for history)

- `ai.py`, `gemini_test.py`, `test_chatbot.py`: the first Gemini (cloud AI) version, before the move to a local model.
- `ui_pages.py`, `ui_pages_v3.py`, `ui_text.py`, `ui_text_v3.py`, `knowledge.py`, `knowledge_answer.py`, `soil_card.py`, `soil_interpret.py`, `water_quality.py`, `report_builders.py`, `reports_pdf.py`, `import_dataset.py`, `build_knowledge_db.py`, `ui_coming_soon.py`: the 3.0 soil, land, crop and report pages. They still load as hidden pages and are listed as "coming soon".
- `backup/`: earlier versions. GitHub history replaces it, so it is not uploaded.
