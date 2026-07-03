"""agency-kit — the meta-orchestrator for the AI Agency.

Unifies nine optional departments:
  • product-kit   — discovery, strategy, prioritisation, design, delivery, measurement
  • marketing-kit — research, positioning, content, campaigns, analytics
  • solve-kit     — problem-solving, root-cause, decision intelligence
  • finance-kit   — business case, pricing, pipeline, commercial closing, reporting
  • comms-kit     — corporate comms, PR/media, crisis, public affairs, ESG, events
  • data-kit      — data strategy, engineering, analytics/BI, ML/LLMOps, data products
  • ops-kit       — process, PMO, compliance (NIS2, AI Act), risk, operational excellence
  • people-kit    — org design, talent, L&D, performance, culture, people analytics
  • tech-kit      — architecture, DevOps, security, engineering excellence, build-vs-buy

Missions run through a local agent CLI engine (Claude Code / Codex / Gemini) —
no API key, no SDK. See `agency_cli/engines/cli_engine.py`.
"""
__version__ = "0.2.0"
