# Solution Design: Narrative Transformation System

## Overview

This document describes the architecture and design decisions of an AI-powered system that transforms classic stories (like Ramayana) into new settings (like Tech Startups) while preserving their narrative essence.

---

## System Architecture

### High-Level Pipeline

```
Input (Story Name + Target World)
        ↓
[1] Story Extraction → Load metadata from JSON
        ↓
[2] World Building → Generate new setting via LLM
        ↓
[3] Character Mapping → Map characters to new roles
        ↓
[4] Plot Transformation → Adapt plot events to new world
        ↓
[5] Consistency Validation → Check coherence (⭐ clever addition)
        ↓
[6] Output Assembly → Generate final markdown document
        ↓
Output (reimagined_story.md)
```

---

## Component Design

### 1. Story Extractor (`utils/extractor.py`)

**Purpose:** Parse source story metadata into structured format

**Input:**

- JSON file with story data (characters, themes, plot structure)

**Output:**

- Pydantic models: `StoryElements`, `Character`, `PlotAct`

**Key Features:**

- Type-safe data models using Pydantic
- Helper functions for formatting (character summaries, plot summaries)
- Validation of required fields

**Design Decision:**

- Why Pydantic? Type safety, automatic validation, easy serialization
- Why JSON? Simple, human-readable, easy to extend

---

### 2. World Builder (`utils/transformer.py` - Part 1)

**Purpose:** Generate vivid new world setting that supports original themes

**Input:**

- Story elements (themes, setting type)
- Target world description (e.g., "Silicon Valley tech startup")

**Output:**

- `WorldSetting` with overview, details, theme translation

**Process:**

1. Load prompt template from `prompts/world_building.txt`
2. Replace placeholders with story data
3. Send to Gemini LLM (4096 tokens, temp 0.8)
4. Clean incomplete sentences from response
5. Parse into structured sections

**Design Decisions:**

- **Separate prompt files:** Easy iteration without code changes
- **Higher temperature (0.8):** More creative world-building
- **Token limit 4096:** Balance detail vs cost
- **Sentence cleaning:** Ensures complete, polished output

---

### 3. Character Mapper (`utils/transformer.py` - Part 2)

**Purpose:** Map original characters to new world equivalents

**Input:**

- Story elements (original characters)
- World setting (for context)

**Output:**

- List of `CharacterMapping` with names, roles, traits, rationales

**Process:**

1. Format character and world data for context
2. Request JSON output from LLM
3. Parse JSON, validate structure
4. Retry with lower temperature (0.5) if parsing fails

**Design Decisions:**

- **JSON output:** Structured, parsable, type-safe
- **Retry logic:** Handles LLM inconsistency (2 attempts)
- **Temperature adjustment:** Start creative (0.7), fallback structured (0.5)
- **Manual string replacement:** Avoids Python format conflicts with JSON

**Challenges & Solutions:**

- _Challenge:_ LLM returns markdown-wrapped JSON
- _Solution:_ Strip `json` markers before parsing
- _Challenge:_ Incomplete JSON due to token limits
- _Solution:_ Increased max_tokens to 6000, added validation

---

### 4. Plot Transformer (`utils/transformer.py` - Part 3)

**Purpose:** Adapt original plot structure to new setting

**Input:**

- Story elements (original plot)
- World setting
- Character mappings

**Output:**

- List of `TransformedPlotAct` (3 acts with events, themes)

**Process:**

1. Format all context (world, characters, original plot)
2. Explicit instruction to follow 3-act structure
3. LLM generates adapted plot with events
4. Regex parsing to extract acts, events, themes
5. Validate completeness (retry if 0 acts found)

**Design Decisions:**

- **Regex parsing:** More robust than line-by-line parsing
- **Explicit format in prompt:** Reduces LLM hallucination
- **Validation check:** Ensures "## Act" pattern exists before accepting
- **Lower temp on retry (0.5):** More instruction-following

**Challenges & Solutions:**

- _Challenge:_ LLM ignoring task, generating random stories
- _Solution:_ Directive prompt emphasizing "Transform EXISTING plot"
- _Challenge:_ Incomplete responses (cut mid-sentence)
- _Solution:_ Sentence cleaning, higher token limit (6000)
- _Challenge:_ 0 acts parsed
- _Solution:_ Improved regex patterns, retry logic

---

### 5. Consistency Validator (`utils/validator.py`) ⭐

**Purpose:** Validate coherence across generated content (clever addition)

**Input:**

- All generated components (world, characters, plot)
- Original story elements

**Output:**

- `ConsistencyReport` with issues categorized by severity

**Validation Checks:**

1. **Character Consistency:** Ensures new names used in plot, not original
2. **Theme Preservation:** Validates themes mentioned in plot
3. **World Consistency:** Checks plot events align with world setting
4. **Narrative Structure:** Validates 3-act structure, complete events

**Severity Levels:**

- **Critical:** Blocks quality (e.g., missing acts)
- **Warning:** Needs review (e.g., brief theme mentions)
- **Info:** Minor suggestions

**Design Decision:**

- Why add this? Shows systematic thinking, production-ready approach
- Pattern matching for detection (not LLM-based for speed)
- Reports don't block output, just inform user

---

### 6. Output Assembler (`utils/assembler.py`)

**Purpose:** Combine all components into final markdown document

**Input:**

- All generated components
- Consistency report

**Output:**

- Complete markdown file with:
  - World-building section
  - Character mapping table
  - Plot structure (3 acts)
  - Creative rationale
  - Validation results
  - Metadata

**Design Decisions:**

- **Markdown format:** Universal, readable, version-controllable
- **Tabulate for tables:** Clean, aligned formatting
- **UTF-8 encoding:** Handles special characters
- **Timestamp metadata:** Reproducibility tracking

---

## Prompt Engineering Strategy

### Key Principles

1. **Structured Output Requirements**
   - Explicit format instructions in prompts
   - Examples of expected structure
   - "CRITICAL" markers for non-negotiable rules

2. **Context Management**
   - Provide relevant context (themes, characters)
   - Limit context length (truncate world description to 400 chars in plot)
   - Prioritize essential information

3. **Instruction Clarity**
   - Use directive language ("Transform EXISTING plot")
   - Add completion instructions ("Do not stop mid-sentence")
   - Specify format explicitly ("Start with [ and end with ]")

4. **Error Prevention**
   - Request JSON for structured data
   - Add validation checks post-generation
   - Implement retry logic with adjusted parameters

---

## Technology Stack

| Component        | Technology              | Rationale                          |
| ---------------- | ----------------------- | ---------------------------------- |
| Language         | Python 3.10+            | Rich ecosystem, AI/ML libraries    |
| Package Manager  | uv                      | Fast, modern, reliable             |
| LLM              | Google Gemini 2.0 Flash | Cost-effective, fast, good quality |
| Framework        | LangChain               | Prompt management, LLM abstraction |
| Data Models      | Pydantic                | Type safety, validation            |
| Output Format    | Markdown                | Universal, readable, portable      |
| Console UI       | Rich                    | Beautiful terminal output          |
| Table Formatting | Tabulate                | Clean markdown tables              |

---

## Design Trade-offs

### 1. LLM vs Rule-Based Transformation

**Decision:** LLM-based generation

**Trade-offs:**

- ✅ Pros: Creative, flexible, handles nuance
- ❌ Cons: Non-deterministic, requires validation, costs tokens
- **Why chosen:** Creativity essential for narrative transformation

### 2. Single Mega-Prompt vs Chained Prompts

**Decision:** Chained prompts (modular pipeline)

**Trade-offs:**

- ✅ Pros: Debuggable, controllable, reusable components
- ❌ Cons: More API calls, slightly slower
- **Why chosen:** Better control, easier to iterate, clearer failures

### 3. JSON vs Natural Language Output

**Decision:** JSON for structured data (characters), text for creative content (world, plot)

**Trade-offs:**

- JSON: Parsable, structured, but less natural
- Text: Creative, flowing, but harder to parse
- **Why chosen:** Hybrid approach - structure where needed, creativity where valued

### 4. Validation: LLM vs Rule-Based

**Decision:** Rule-based validation

**Trade-offs:**

- ✅ Pros: Fast, deterministic, no API cost
- ❌ Cons: Limited to pattern matching
- **Why chosen:** Speed and reliability for quality checks

---

## Error Handling Strategy

### 1. LLM Response Failures

**Approach:**

- Retry logic (max 2 attempts)
- Temperature adjustment on retry (lower = more structured)
- Explicit validation of output format

### 2. Incomplete Responses

**Approach:**

- Token limit increase (4096 → 6000)
- Sentence completion cleaning
- Length validation with regeneration

### 3. JSON Parsing Errors

**Approach:**

- Strip markdown formatting
- Validate JSON structure before parsing
- Provide clear error messages with debug output

### 4. Missing Data

**Approach:**

- Default values in Pydantic models
- Graceful degradation (empty lists vs exceptions)
- Clear error messages to user

---

## Scalability Considerations

### Current Limitations

1. **Single story at a time:** No batch processing
2. **No caching:** Regenerates everything each run
3. **Fixed story format:** Requires specific JSON structure
4. **No user interaction:** One-shot generation

### Future Improvements

1. **Batch Processing**
   - Process multiple stories/worlds in parallel
   - Queue system for API rate limiting

2. **Caching Layer**
   - Cache world descriptions by (story, target_world) key
   - Redis for distributed caching
   - Reduce redundant API calls

3. **Interactive Refinement**
   - User feedback loop for regeneration
   - Selective component regeneration (re-do just characters)
   - A/B testing different temperatures/prompts

4. **API Endpoint**
   - REST API for programmatic access
   - Async processing for long-running tasks
   - Webhook notifications on completion

5. **Multi-Model Support**
   - Abstract LLM interface (support GPT, Claude, Gemini)
   - Cost optimization by model selection
   - Quality comparison across models

6. **Enhanced Validation**
   - LLM-based coherence checking
   - User-defined validation rules
   - Automated quality scoring

---

## Performance Metrics

### Generation Time (Ramayana → Tech Startup)

| Component           | Time     | API Calls        |
| ------------------- | -------- | ---------------- |
| Extraction          | <1s      | 0                |
| World Building      | 10-15s   | 1                |
| Character Mapping   | 15-20s   | 1-2 (with retry) |
| Plot Transformation | 20-30s   | 1-2 (with retry) |
| Validation          | <1s      | 0                |
| Assembly            | <1s      | 0                |
| **Total**           | **~60s** | **3-5**          |

### Token Usage (Approximate)

| Component           | Input Tokens | Output Tokens | Cost (Gemini) |
| ------------------- | ------------ | ------------- | ------------- |
| World Building      | ~800         | ~1200         | $0.002        |
| Character Mapping   | ~1000        | ~800          | $0.002        |
| Plot Transformation | ~1200        | ~2000         | $0.003        |
| **Total**           | **~3000**    | **~4000**     | **~$0.007**   |

_Cost per story transformation: Less than 1 cent_

---

## Security & Privacy

### Current Implementation

- ✅ API keys in `.env` (not committed)
- ✅ No user data collection
- ✅ Local file storage only
- ✅ No external data transmission (except to Gemini API)

### Production Considerations

1. **API Key Management:** Use secrets manager (AWS Secrets, Vault)
2. **Rate Limiting:** Implement per-user API quotas
3. **Input Sanitization:** Validate user-provided story data
4. **Output Filtering:** Check for PII, sensitive content before saving
5. **Audit Logging:** Track all generations for debugging/monitoring

---

## Testing Strategy

### Current Approach

- **Manual testing:** Run each component with test data
- **Visual inspection:** Check output quality in markdown
- **Consistency validation:** Automated checks for coherence

### Production Testing

1. **Unit Tests**
   - Test each function with mock LLM responses
   - Validate Pydantic model constraints
   - Test edge cases (empty data, malformed JSON)

2. **Integration Tests**
   - Full pipeline execution
   - Multiple story/world combinations
   - Regression testing (saved outputs as baselines)

3. **Quality Tests**
   - Theme preservation metrics
   - Character consistency scoring
   - Narrative coherence evaluation (LLM-based)

---

## Conclusion

This system demonstrates:

1. **Modular Design:** Clear separation of concerns, reusable components
2. **Prompt Engineering:** Structured, directive, validated outputs
3. **Error Resilience:** Retry logic, validation, graceful degradation
4. **Production Thinking:** Consistency checking, metadata, reproducibility

The architecture balances creativity (LLM generation) with reliability (validation, structure), creating a system that's both powerful and dependable.

---
