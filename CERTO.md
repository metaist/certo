# Certo

Certo is a tool that turns conversations about intent into living specifications (blueprints) that can be verified against code.

## Vision

Software verification is fundamentally an attention allocation problem. Humans can't review everything, so certo's job is to surface the right things at the right time.

The core insight: when the same agent writes code and tests, we lose independent verification. Certo bridges the semantic gap between intent and implementation by capturing intent through conversation, expanding it into testable implications, and checking code against those implications using multiple verification strategies.

## Core Concepts

**Blueprint**: A structured representation of everything between natural language intent and code. Contains business needs, requirements, decisions, concerns (with testable statements), and contexts. Stored in version control alongside code.

**Concern**: A category of quality (functional, performance, security, etc.) with statements that must be true. All concerns follow the same structure: claim, conditions, verification strategies, failure response, provenance.

**Decision**: An explicit choice made during specification, with alternatives considered, rationale, and history. Decisions can evolve; implications update accordingly.

**Context**: Where different rules apply. Exemptions, modifications, environment-specific overrides. Contexts have expiration dates.

**Zoom**: Semantic zoom—view specifications at any level of detail, from one-line summary to formal proof. Edit at any level.

## Verification Strategies

Certo tries all applicable strategies for each statement:

- Static analysis (AST, patterns, data flow)
- Behavioral tests (generated, then verified)
- Property-based tests
- Contracts (via wrappers, non-invasive)
- Benchmarks and profiling
- Runtime monitoring
- LLM-based review (adversarial, semantic)

Strategies provide different kinds of evidence. Agreement increases confidence. Disagreement is the most valuable signal.

## Layered Execution

1. Static (fast, every commit)
2. ML models (moderate cost, PR/merge)
3. Test execution (slow but concrete)
4. LLM review (expensive, selective)
5. Human review (decision points only)

## Non-Functional Coverage

Beyond functional correctness: performance, efficiency, resource bounds, UX, security, observability, failure modes, data integrity, compliance, accessibility, maintainability, dependencies, deployment, human factors.

## Language Strategy

LLM-powered language-agnostic core first. Python adapter fast-follow. Framework plugins later.

## Bootstrapping Certo

Certo should be built using certo. The blueprint for certo itself should be the first blueprint created.

### First Actions

1. Propose a native blueprint format (YAML or similar)
2. Begin the requirements interview for certo itself
3. Produce a v0 blueprint for certo
4. Identify the first verifiable implications
5. Build the minimal checker that can verify those implications

### Interview Protocol

When conducting a requirements interview:

- Ask one question at a time
- Distinguish between statements (exploratory), decisions (commitments), and deferrals (acknowledged open questions)
- Surface implications from common sense, but mark them as proposed until confirmed
- When you encounter a fork (multiple valid paths), identify it explicitly and ask for a decision
- Track provenance: who decided, when, based on what
- Periodically summarize and confirm understanding
- Propose zoom levels: "Here's the one-liner. Want me to expand?"

### Blueprint Format Requirements

The native format should:

- Be human-readable and editable
- Support the full structure (business needs, requirements, decisions, concerns, contexts)
- Track provenance inline
- Support history/evolution without losing current-state readability
- Be diffable in git
- Be parseable for the checker

## Success Criteria

Certo succeeds if:

- Someone can rebuild a system from its blueprint (not the exact code, but one that passes all checks)
- The checker catches real mismatches between intent and implementation
- Decisions are traceable from failing check back to business need
- Humans only see what requires their judgment
- The tool is usable enough that people actually use it

## Open Questions (Deferred)

- Exact CLI interface
- Web UI / TUI design
- Collaboration features
- Knowledge base curation and sharing
- Pricing/distribution model
- Offline operation capability

These will be addressed through the requirements interview process.
