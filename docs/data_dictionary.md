# Data Dictionary — LLM System Ops Telemetry (Synthetic)

This document defines the schema, column semantics, and relationships for the dataset CSV files.

**Synthetic dataset notice:** All records are synthetic and designed for LLMOps analytics (cost/latency/failures/tools/feedback). Token counts and costs are **estimated** and do not represent real billing data.

## Dataset overview

- **Time coverage (UTC):** 2025-02-01 → 2025-04-30
- **Core grain:** one row = one **interaction** (request → response)
- **Joinable multi-table layout:** interactions ↔ sessions ↔ users, plus prompt lookup and aligned SFT samples.

## Table map

```text
users (user_id)
  └── sessions (session_id, user_id)
        └── interactions (interaction_id, session_id, user_id)
              └── sft_samples (sample_id, interaction_id)

prompts_lookup (prompt_id)  # dimension table (joinable from interactions via prompt_id)
```

## Global conventions

### Timestamps
- All timestamps are **UTC** and use ISO 8601 with `Z` suffix (e.g., `2025-03-25T11:14:35Z`).
- Derived time fields in `llm_system_interactions.csv` use UTC (`date_utc`, `hour_of_day_utc`, `day_of_week`).

### Splits
- `split` is a deterministic, group-safe train/val/test assignment derived from `session_id` hashing.
- Use `split` for modeling/evaluation. Avoid random row-level splits to prevent session leakage.

### Feedback fields
- `user_feedback_score` / `csat_mean` / `avg_csat` use a discrete scale: **-2, -1, 0, 1, 2**.
- Missing feedback is encoded as **NaN**, and the boolean `user_feedback_observed` indicates whether feedback is present.

### Cost and token accounting (synthetic)
- `prompt_tokens`, `completion_tokens`, and all token-derived metrics are **synthetic/estimated**.
- `cost_usd` is an **estimated** cost derived from token counts and a synthetic pricing heuristic (see README).

### Modeling leakage note
For predictive modeling, do not use direct outcome/label fields as features (e.g., `failure_type`, `is_failure`, explicit failure flags, resolution fields) when the target is derived from them.

### Synthetic data boundaries
- Latency and throughput fields are synthetic approximations and may not match real production distributions.
- Tool usage is represented as a small controlled vocabulary and simple combinations.

## `llm_system_interactions.csv`

**Grain:** 1 row = 1 interaction (request → response)

**Primary key:** `interaction_id`  
**Foreign keys:** `session_id`, `user_id`, `prompt_id`

| Column | Type | Description | Notes / Values |
|---|---:|---|---|
| `interaction_id` | string | Unique interaction identifier (one request → one response). |  |
| `session_id` | string | Session identifier (FK to sessions summary). |  |
| `user_id` | string | User identifier (FK to users summary). |  |
| `prompt_id` | string | Prompt configuration identifier (FK to prompts lookup). | Mirrors the aligned interaction prompt configuration. |
| `timestamp_utc` | string | Event timestamp in UTC (ISO 8601, `Z`). | Example format: `YYYY-MM-DDTHH:MM:SSZ`. |
| `channel` | string | Client channel where the request originated. | One of: api, internal_tool, mobile_app, slack, web_app. |
| `use_case` | string | High-level use-case label for the interaction. | One of: brainstorming, coding_assistant, content_writing, customer_support, data_analysis, internal_qa. |
| `country_code` | string | User country code. | ISO 3166-1 alpha-2. Observed: AE, AU, BR, CA, DE, EG, FR, GB, IN, US. |
| `region` | string | Coarse region derived from country. | Coarse region derived from country. One of: AMER, APAC, EMEA. |
| `account_tier` | string | Account tier at interaction time. | One of: enterprise, free, pro. |
| `segment` | string | Customer segment at interaction time. | One of: enterprise_team, individual, team. |
| `instruction_template` | string | Instruction profile/template name used to guide the assistant. | One of: analytics_helper, code_assistant_secure, creative_writer, general_assistant, internal_policy_qa, support_strict. |
| `model_provider` | string | Model provider family. | One of: anthropic, google, local, meta, mistral, openai. |
| `model_name` | string | Model name used to serve the request. | One of: claude-3.5-sonnet, custom-local-8b, gemini-1.5-pro, gpt-4.1, gpt-4o-mini, llama-3.1-70b, llama-3.1-8b, mistral-large. |
| `temperature` | float | Sampling temperature used for generation. | Typical range [0.1, 1.0]. |
| `top_p` | float | Nucleus sampling parameter. | Typical range [0.8, 1.0]. |
| `max_tokens` | int | Maximum allowed completion tokens for the request. |  |
| `prompt_tokens` | int | Estimated input token count for the request. | Synthetic/estimated; not from a real billing system. |
| `completion_tokens` | int | Estimated output token count for the response. | Synthetic/estimated; not from a real billing system. |
| `total_tokens` | int | Estimated total token count (`prompt_tokens + completion_tokens`). | Synthetic/estimated. |
| `latency_ms` | int | End-to-end latency for the interaction, in milliseconds. | Unit: ms. |
| `cost_usd` | float | Estimated cost in USD for the interaction. | Synthetic estimate derived from token counts and a pricing heuristic. |
| `response_quality_score` | float | Synthetic response quality score in [0, 1] (higher is better). |  |
| `is_failure` | bool | Whether the interaction was marked as a failure. |  |
| `failure_type` | string | Failure category (or `none` if not a failure). | One of: formatting_error, hallucination, latency_timeout, none, safety_block, tool_error, toxicity. |
| `hallucination_flag` | bool | True when the failure is hallucination-related. | Redundant with `failure_type` by design. |
| `toxicity_flag` | bool | True when the failure is toxicity-related. | Redundant with `failure_type` by design. |
| `safety_block_flag` | bool | True when output was blocked by safety policy. | Redundant with `failure_type` by design. |
| `formatting_error_flag` | bool | True when response violated a required format/output contract. | Redundant with `failure_type` by design. |
| `tool_error_flag` | bool | True when a tool call failed or tool output was invalid. | Redundant with `failure_type` by design. |
| `latency_timeout_flag` | bool | True when the interaction was labeled as a timeout. | Redundant with `failure_type` by design. |
| `tool_calls_count` | int | Number of tool calls executed. | Integer in [0, 3]. |
| `tools_used` | string | Tools used in the interaction. | Pipe-separated list. Base tool tokens: code_run, email_send, http_request, knowledge_lookup, sql_query, tool_invocation_failed, vector_search, workflow_orchestrator. Use `none` when no tools were used. `tool_invocation_failed` denotes a tool call attempt that failed. |
| `user_feedback_score` | float | User feedback score when provided. | Values: -2, -1, 0, 1, 2. Missing as NaN when not observed. |
| `user_feedback_label` | string | Categorical label derived from `user_feedback_score`. | One of: negative, neutral, no_feedback, positive. |
| `user_reported_issue` | bool | Whether the user explicitly reported an issue in feedback. |  |
| `retry_index` | int | Retry attempt index (0 = first attempt). | Higher values indicate retries for the same request. |
| `repair_strategy` | string | Mitigation/repair strategy applied after an issue. | One of: add_constraints_to_prompt, decompose_task, enable_tools, manual_post_edit, none, regenerate_with_lower_temp, switch_model_family. |
| `final_resolution_state` | string | Final resolution outcome for the interaction. | One of: abandoned, auto_resolved, escalated_to_human. |
| `split` | string | Group-safe dataset split derived from `session_id` hash. | One of: train, val, test. Deterministic: sha1(session_id) % 100 with thresholds 80/90. |
| `business_impact_tag` | string | Business impact category assigned to the interaction. | One of: critical, high, low, medium. |
| `request_text` | string | Synthetic user request text (raw). | Free-form text. |
| `response_text_snippet` | string | Truncated assistant response preview (snippet). | For full response text, use `llm_system_instruction_tuning_samples.csv` → `raw_response_text` / `sft_assistant_response`. |
| `response_text_snippet_len_chars` | int | Character length of `response_text_snippet`. | Derived. |
| `response_text_snippet_is_truncated` | bool | Whether `response_text_snippet` is truncated (contains `...`). | In this dataset, always true. |
| `tokens_per_second` | float | Derived throughput: `total_tokens / (latency_ms / 1000)`. | Derived metric; synthetic token counts and latency. |
| `date_utc` | string | UTC date derived from `timestamp_utc`. | Format: `YYYY-MM-DD`. |
| `hour_of_day_utc` | int | UTC hour derived from `timestamp_utc`. | Integer 0–23. |
| `day_of_week` | int | Day of week derived from `timestamp_utc`. | Integer 0=Mon … 6=Sun. |
| `is_weekend` | bool | True if `day_of_week` is Saturday (5) or Sunday (6). |  |
| `is_peak_hour` | bool | True if `hour_of_day_utc` is within peak hours. | Peak hours: 09–18 UTC (inclusive). |
| `prompt_to_completion_ratio` | float | Derived ratio: `prompt_tokens / completion_tokens`. | Only meaningful when `completion_tokens > 0`. |
| `request_text_template` | string | Canonical request template used to generate `request_text`. | Useful for clustering / template-level analysis. |
| `instruction_text` | string | Full instruction text corresponding to `instruction_template`. | Synthetic instruction content. |
| `user_feedback_observed` | bool | True if feedback was observed (`user_feedback_score` not NaN). |  |

## `llm_system_sessions_summary.csv`

**Grain:** 1 row = 1 session (aggregated over its interactions)

**Primary key:** `session_id`  
**Foreign keys:** `user_id`

| Column | Type | Description | Notes / Values |
|---|---:|---|---|
| `session_id` | string | Unique session identifier (one conversation session). |  |
| `user_id` | string | User identifier (FK to users summary). |  |
| `use_case` | string | Primary use-case label for the session. | One of: brainstorming, coding_assistant, content_writing, customer_support, data_analysis, internal_qa. |
| `channel` | string | Primary channel for the session. | One of: api, internal_tool, mobile_app, slack, web_app. |
| `country_code` | string | User country code for the session. | ISO 3166-1 alpha-2. Observed: AE, AU, BR, CA, DE, EG, FR, GB, IN, US. |
| `region` | string | Coarse region derived from country. | One of: AMER, APAC, EMEA. |
| `account_tier` | string | Account tier for the session. | One of: enterprise, free, pro. |
| `segment` | string | Customer segment for the session. | One of: enterprise_team, individual, team. |
| `total_requests` | int | Total number of interactions in the session. |  |
| `failed_requests` | int | Number of interactions where `is_failure=True`. |  |
| `failure_rate` | float | `failed_requests / total_requests`. |  |
| `avg_latency_ms` | float | Mean `latency_ms` across interactions in the session. | Unit: ms. |
| `median_latency_ms` | float | Median `latency_ms` across interactions in the session. | Unit: ms. |
| `avg_response_quality_score` | float | Mean `response_quality_score` across interactions. |  |
| `avg_tokens_per_request` | float | Mean `total_tokens` across interactions. | Synthetic/estimated token counts. |
| `requests_with_tools` | int | Count of interactions with `tool_calls_count > 0`. |  |
| `share_requests_with_tools` | float | `requests_with_tools / total_requests`. |  |
| `n_retry_requests` | int | Count of interactions with `retry_index > 0`. |  |
| `escalations_to_human` | int | Count of interactions where `final_resolution_state = escalated_to_human`. |  |
| `csat_mean` | float | Mean `user_feedback_score` over interactions with observed feedback. | NaN if no feedback was observed in the session. |
| `csat_response_rate` | float | Share of interactions with observed feedback. | Computed as mean of `user_feedback_observed`. |
| `risk_session_flag` | bool | Synthetic triage label indicating a session likely needs operator review. | Derived from session signals (e.g., high failure_rate and/or many escalations and/or low feedback/quality). |
| `total_cost_usd` | float | Sum of `cost_usd` across interactions in the session. | Synthetic estimate. |
| `total_tokens` | int | Sum of `total_tokens` across interactions in the session. | Synthetic/estimated token counts. |
| `avg_cost_per_request` | float | `total_cost_usd / total_requests`. | Synthetic estimate. |
| `cost_per_1k_tokens` | float | `total_cost_usd / (total_tokens / 1000)`. | Synthetic estimate. |
| `avg_tokens_per_second` | float | Mean `tokens_per_second` across interactions. | Derived metric; synthetic token counts and latency. |
| `start_timestamp_utc` | string | Timestamp of first interaction in the session (UTC). | ISO 8601 with `Z`. |
| `end_timestamp_utc` | string | Timestamp of last interaction in the session (UTC). | ISO 8601 with `Z`. |
| `session_duration_seconds` | float | `end_timestamp_utc - start_timestamp_utc` in seconds. |  |
| `session_duration_minutes` | float | `session_duration_seconds / 60`. |  |
| `requests_per_minute` | float | `total_requests / session_duration_minutes`. | NaN when `session_duration_minutes == 0`. |
| `total_latency_ms` | int | Sum of `latency_ms` across interactions in the session. | Unit: ms. |
| `zero_duration_session_flag` | bool | True when `session_duration_seconds == 0`. | Can happen when all interactions share the same timestamp. |
| `total_latency_seconds` | float | `total_latency_ms / 1000`. |  |
| `effective_session_duration_seconds` | float | `max(session_duration_seconds, total_latency_seconds)`. | Avoids zero-duration sessions for rate calculations. |
| `requests_per_minute_effective` | float | `total_requests / (effective_session_duration_seconds / 60)`. | Preferred requests-per-minute metric when zero-duration sessions exist. |

## `llm_system_users_summary.csv`

**Grain:** 1 row = 1 user (aggregated over the user's sessions/interactions)

**Primary key:** `user_id`

| Column | Type | Description | Notes / Values |
|---|---:|---|---|
| `user_id` | string | Unique user identifier. |  |
| `total_sessions` | int | Number of distinct sessions for the user. |  |
| `total_requests` | int | Total number of interactions across all sessions. |  |
| `total_failed_requests` | int | Total number of interactions where `is_failure=True`. |  |
| `overall_failure_rate` | float | `total_failed_requests / total_requests`. |  |
| `avg_csat` | float | Mean `user_feedback_score` over interactions with observed feedback. | NaN if the user never provided feedback. |
| `risk_sessions_share` | float | `high_risk_sessions_count / total_sessions`. |  |
| `escalations_per_100_sessions` | float | `total_escalations / total_sessions * 100`. |  |
| `total_cost_usd` | float | Sum of `cost_usd` across all interactions for the user. | Synthetic estimate. |
| `total_tokens` | int | Sum of `total_tokens` across all interactions for the user. | Synthetic/estimated token counts. |
| `avg_tokens_per_request` | float | Mean `total_tokens` across interactions for the user. | Synthetic/estimated token counts. |
| `avg_requests_per_session` | float | `total_requests / total_sessions`. |  |
| `primary_use_case` | string | Most frequent `use_case` across a user's sessions (mode). | Tie-break: alphabetical. One of: brainstorming, coding_assistant, content_writing, customer_support, data_analysis, internal_qa. |
| `primary_channel` | string | Most frequent `channel` across a user's sessions (mode). | Tie-break: alphabetical. One of: api, internal_tool, mobile_app, slack, web_app. |
| `dominant_segment` | string | Most frequent `segment` for the user. | Most frequent segment for the user. One of: enterprise_team, individual, team. |
| `dominant_account_tier` | string | Most frequent `account_tier` for the user. | Most frequent account_tier for the user. One of: enterprise, free, pro. |
| `dominant_country_code` | string | Most frequent `country_code` for the user. | Most frequent country_code for the user. Observed: AE, AU, BR, CA, DE, EG, FR, GB, IN, US. |
| `dominant_region` | string | Most frequent `region` for the user. | Most frequent region for the user. One of: AMER, APAC, EMEA. |
| `high_risk_user_flag` | bool | Synthetic triage label indicating unusually high risky-session activity. | Derived from `risk_sessions_share`, escalations, and failure rate heuristics. |
| `high_risk_sessions_count` | int | Number of sessions for the user where `risk_session_flag=True`. |  |
| `total_escalations` | int | Total escalations to human across the user's sessions. |  |

## `llm_system_prompts_lookup.csv`

**Grain:** 1 row = 1 prompt/instruction configuration (lookup)

**Primary key:** `prompt_id`


**Join:** `llm_system_interactions.csv`.`prompt_id` → `llm_system_prompts_lookup.csv`.`prompt_id`

| Column | Type | Description | Notes / Values |
|---|---:|---|---|
| `prompt_id` | string | Opaque identifier for the full prompt configuration (hash-like). |  |
| `prompt_sha1` | string | SHA1 checksum of the prompt payload (integrity/dedup). |  |
| `prompt_len` | int | Prompt payload length in characters. |  |
| `instruction_template` | string | Instruction profile/template associated with this prompt. | One of: analytics_helper, code_assistant_secure, creative_writer, general_assistant, internal_policy_qa, support_strict. |
| `use_case` | string | Use-case associated with this prompt configuration. | One of: brainstorming, coding_assistant, content_writing, customer_support, data_analysis, internal_qa. |
| `n_interactions` | int | Number of interactions using this prompt configuration. |  |
| `share_within_template` | float | `n_interactions` normalized within `instruction_template`. | Sum to 1.0 within each template. |
| `n_sessions` | int | Number of distinct sessions where this prompt appears. |  |
| `n_users` | int | Number of distinct users where this prompt appears. |  |
| `use_case_mismatch_count` | int | Count of interactions where the observed use_case differs from this prompt's use_case. | Synthetic consistency check. |
| `instruction_text` | string | Instruction text associated with this prompt configuration. |  |
| `instruction_id` | string | Opaque identifier for the instruction text (hash-like). |  |
| `instruction_sha1` | string | SHA1 checksum of the instruction text. |  |
| `instruction_len` | int | Instruction text length in characters. |  |

## `llm_system_instruction_tuning_samples.csv`

**Grain:** 1 row = 1 SFT training sample (aligned to an interaction)

**Primary key:** `sample_id`  
**Foreign keys:** `interaction_id`, `session_id`, `user_id`, `prompt_id`
**Alignment:** 1:1 with `llm_system_interactions.csv` on `interaction_id`.

| Column | Type | Description | Notes / Values |
|---|---:|---|---|
| `interaction_id` | string | Foreign key to interactions (1:1 alignment). |  |
| `session_id` | string | Session identifier (FK). |  |
| `user_id` | string | User identifier (FK). |  |
| `prompt_id` | string | Prompt configuration identifier (FK to prompts lookup). | Join to `llm_system_prompts_lookup.csv` on `prompt_id`. |
| `split` | string | Group-safe dataset split derived from `session_id` hash. | One of: train, val, test. Deterministic: sha1(session_id) % 100 with thresholds 80/90. |
| `use_case` | string | Use-case label for the sample. | One of: brainstorming, coding_assistant, content_writing, customer_support, data_analysis, internal_qa. |
| `account_tier` | string | Account tier at sample time. | One of: enterprise, free, pro. |
| `country_code` | string | User country code. | ISO 3166-1 alpha-2. Observed: AE, AU, BR, CA, DE, EG, FR, GB, IN, US. |
| `segment` | string | Customer segment at sample time. | One of: enterprise_team, individual, team. |
| `raw_request_text` | string | Raw user request text (copy of `request_text` from interactions). |  |
| `raw_response_text` | string | Raw assistant response text (copy of `response_text` from interactions). |  |
| `sft_user_prompt` | string | SFT-ready user prompt (cleaned/structured). | Intended as the training input. |
| `sft_assistant_response` | string | SFT-ready assistant response (cleaned/structured). | Intended as the training target. |
| `sample_id` | int | Unique SFT sample identifier. |  |
| `business_impact_tag` | string | Business impact category aligned with the interaction. | One of: critical, high, low, medium. |
| `instruction_text` | string | Instruction text used as the system/instruction context for the sample. | Aligned with interactions. |