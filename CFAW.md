**ENGINEERING STANDARD**

**Contract-First Agentic Workflow**

**CFAW**

*A specification-driven framework for maximum velocity AI-assisted software engineering.*

Version 7.0 - 2026

---

# 1. The Goal

## 1.1 What This Workflow Is For

CFAW is a workflow designed to unleash the full capability of frontier models by giving them the context they need to succeed. The objective is to produce code as rapidly as possible above a quality floor — where the quality floor is what production code written by a competent senior engineer would look like. In reality, this floor is lower than it should be. As of 2025 there are 64 billion workdays worth of tech debt of repair time, costing over $2 trillion annually in the US alone with about $1.5 trillion required to fix the backlog. So the more ambitious goal is to produce more code AND better code than what humans have produced on their own. We will use AI to enhance and accelerate coding.

The workflow is calibrated to the specific strengths and weaknesses of frontier models in March 2026. Frontier models reason well about architecture, generate high-quality code, and hold complex intent across long sessions. What they cannot do is remember decisions made in previous sessions. Every gate in CFAW addresses that specific limitation and no others.

> **THE DESIGN PRINCIPLE**
>
> Give the model what it needs.
>
> The structural problem with AI-assisted development at scale in 2026 is not frontier model capability — it is session statelessness. A model that reasons well in session 3 has no memory of those decisions in session 40. Without externalized, versioned constraints, architectural drift is inevitable regardless of model quality.
>
> The Constitution and the spec are the persistent memory the context window cannot be. They do not compensate for model weakness. They give a capable model the stable reference it needs to produce work that compounds correctly over time.

## 1.2 How CFAW Solves Session Statelessness

A cold-prompted model entering a repository with zero contracts has nothing to follow beyond the immediate prompt and whatever it can gather within its context window before acting. The result is locally-reasonable code that drifts from project standards in ways no single session can detect.

CFAW builds context progressively across phases:

1. **Contracts** (Constitution + layer specs) provide architectural memory that persists across every session.
2. **Discovery** forces the model to research the codebase and produce a written baseline before planning.
3. **The Spec** captures the full design — files, signatures, behavioral scenarios — as a durable artifact.
4. **TDD** produces a test suite that encodes the behavioral contract in executable form.
5. **Implementation** proceeds with contracts, research, tests, and spec all in context simultaneously.

By the time the model writes production code, it has far more context than any cold prompt could provide. Each artifact is written to a persistent location so it survives session boundaries.

---

# 2. Pillar I — The Project Constitution

The Constitution is the authoritative specification of how this codebase is built. It is injected into context before every session. It is the architectural memory that makes consistent multi-session development possible.

The Constitution is version-controlled alongside the code. Changes follow the amendment process in Section 2.5.

## 2.1 The Golden Stack — Whitelist and Blacklist

Define both what to use and what is forbidden. Without explicit prohibition, the model makes a reasonable choice from its training distribution — and that choice won't necessarily be the project standard. Explicit rules eliminate the ambiguity.

> **EXAMPLE — ANDROID PROJECT**
>
> UI: Jetpack Compose exclusively. XML layouts are forbidden.
>
> Networking: Ktor. Retrofit is forbidden.
>
> Local persistence: SQLDelight. Room is forbidden.
>
> DI: Dagger Hilt. Manual service locators and global singletons are forbidden.
>
> Async: Kotlin Coroutines + Flow. RxJava is forbidden.

## 2.2 Architectural Boundaries

Frontier models understand Clean Architecture well. The reason to codify layer boundaries in the Constitution is not capability — it is visibility. Rules not present in the injected context are invisible. In a complex session, a model may make a locally-reasonable choice that violates a boundary it simply wasn't reminded of.

> **EXAMPLE — CLEAN ARCHITECTURE ENFORCEMENT**
>
> The domain module is pure Kotlin/Java with zero dependencies on data or presentation modules.
>
> UseCases return `Result<T>`. Raw exceptions must not cross layer boundaries.
>
> UI layers observe state exclusively via unidirectional data flow (UDF) using StateFlow.
>
> Business logic is forbidden in Fragment, Activity, or Composable bodies.

## 2.3 The Definition of Done

The DoD is machine-verifiable. Tooling and pre-merge checks are the authoritative gate.

> **EXAMPLE — DEFINITION OF DONE**
>
> Passes detekt linter with zero errors.
>
> Achieves 80% line coverage AND 70% branch coverage for new logic.
>
> Includes KDoc for all public interfaces.
>
> Zero new visibility increases (private -> internal -> public) not listed in the approved working spec.
>
> Drift audit passes: git diff matches the file manifest in the working spec.
>
> For Compose features: Architect has signed off on the rendered layout.

## 2.4 Codified Anti-Patterns

Every recurring mistake is a Constitution entry. Caught once, becomes law.

> **EXAMPLE — ANTI-PATTERN REGISTRY**
>
> Never use try/catch inside Composable or UI components. Handle exceptions in the data layer and pass as sealed state classes.
>
> Tests must never catch generic Exception or Throwable. Use `assertThrows<SpecificException>` for failure states.
>
> The SUT (System Under Test) must never appear as a mock or spy within its own test file.
>
> Production code must contain zero references to test classes, annotations, or environment-detection flags used as logic branches.
>
> No external library dependency may be added without explicit listing in the working spec.
>
> No Android permission, manifest entry, build script modification, or ProGuard rule may be added or altered without explicit listing in the spec's Permissions & Config Delta section.

## 2.5 Constitution Versioning and Amendment Protocol

- Semantic versioning: Patch for clarifications, Minor for new rules, Major for breaking changes.
- If the Constitution changes mid-feature, re-execute the Constitution Audit section of the working spec before coding continues.
- All changes committed with the prefix `[CONSTITUTION]` and a changelog entry in CONSTITUTION.md.

## 2.6 Mapping CFAW Concepts to Your Repository

Every project using CFAW must define where each concept lives in the file tree. Without this mapping, the framework is abstract and agents cannot locate the artifacts they need.

| CFAW Concept | What It Is | Where It Lives |
|---|---|---|
| Constitution | Always-loaded architectural rules, golden stack, anti-patterns | Root-level config files injected into every session (e.g., `CLAUDE.md`, `AGENTS.md`, or equivalent) |
| Contract Pack | Layer-specific rules loaded per task | A `contracts/` directory with per-layer spec files and a routing table |
| Plans Directory | Per-ticket working artifacts that persist across sessions | `plans/{ticket_id}/` with `discovery.md`, `spec.md`, `test_spec.md` |
| Working Spec | The approved implementation plan for a feature | `plans/{ticket_id}/spec.md` |
| Test Spec | Gherkin behavioral scenarios that define correctness | `plans/{ticket_id}/test_spec.md` |
| Discovery Document | Codebase research baseline for a feature | `plans/{ticket_id}/discovery.md` |

The plans directory is checked into the repository and kept permanently. Artifacts are created during the CFAW lifecycle and remain as a historical record after the feature merges. This gives every session access to prior phase outputs without relying on chat history — and gives future sessions the ability to trace back to the original design when debugging, auditing, or extending the feature later.

---

# 3. Pillar II — Complexity Routing

Process overhead is calibrated to architectural impact. The Architect decides the tier based on their judgment of the work involved.

| Tier | Scope | Workflow |
|---|---|---|
| Tier 1 — Atomic | Self-contained changes with no cross-layer ripple: style tweaks, copy edits, bugfixes, renaming, multi-file propagation of a localised change | Direct prompt under Constitution guardrails. No planning phase. |
| Tier 2 — Modular | New screen, new API endpoint, new DB table, core business logic modification | Full CFAW lifecycle: Discovery -> Spec + Test Spec -> TDD Red -> Implement -> Drift Audit. Reviewer Agent at Architect discretion. |
| Tier 3 — Systemic | Major refactors, library migrations, cross-module dependency changes | Tier 2 lifecycle + mandatory Reviewer Agent audit + rollback plan before any code is generated. |

## 3.1 Tier 1 Escalation Criteria

Escalate to Tier 2 when any of the following apply:

- The change modifies or extends a domain contract (UseCase signature, data model, repository interface).
- The change adds or removes public API surface.
- The change requires coordinating new behavior across more than one architectural layer.
- The change adds any external dependency, manifest entry, or build script modification.

File count is a signal, not a gate. A four-file rename is Tier 1. A two-file domain contract restructure is Tier 2. Architectural impact is the criterion.

## 3.2 Agent Self-Classification

When starting a new task, the Architect can ask the agent to self-classify the work before proceeding. This is not a gate — it is a tool to help the Architect make a faster, more informed tier decision.

> **SELF-CLASSIFICATION PROMPT**
>
> Before beginning any work, analyze this task and classify it:
>
> 1. **Tier Assessment**: Is this Tier 1 (Atomic), Tier 2 (Modular), or Tier 3 (Systemic)? State which and why.
> 2. **Layers Touched**: Which architectural layers will this change touch? List each with the files you expect to modify.
> 3. **Contract Impact**: Does this change modify any domain contract, public API surface, or cross-layer boundary? Yes/No with specifics.
> 4. **Risk Factors**: What could go wrong? What existing behavior could break?
> 5. **Escalation Triggers**: Do any Tier 1 escalation criteria apply?
>
> Output your classification before proceeding. If you assess Tier 2 or Tier 3, do not write code — begin the Discovery phase instead.
>
> `[YOUR DESCRIPTION OF THE WORK HERE]`

The Architect reviews the classification, overrides if needed, and directs the agent to the appropriate workflow.

---

# 4. Pillar III — The Tier 2/3 Execution Lifecycle

For any non-trivial change, the model passes through sequential gates. Each gate closes a specific failure mode not caught elsewhere.

| Phase | Gate | Output | Failure = ? |
|---|---|---|---|
| 1 — Discovery | Model indexes module | `plans/{ticket_id}/discovery.md` | Process halts |
| 2 — Spec | Architect approves | `plans/{ticket_id}/spec.md` + `plans/{ticket_id}/test_spec.md` | No code written |
| 3 — TDD Red | Tests verified red | Feature branch with failing tests | Rewrite tests; see Section 4.3 |
| 4 — Implement | Tests green + drift audit vs. spec | Completed feature on feature branch | Revert or justify |

## 4.1 Phase 1: Discovery

The model indexes the target module: existing data models, dependencies, API contracts, and utility classes. This serves two purposes: it surfaces existing code that shouldn't be re-invented, and it establishes the baseline against which Phase 4 drift is measured.

Feed the model the full relevant module. Context windows at this capability level are large enough to hold an entire module comfortably — artificial pruning starves the model of information it needs to produce an accurate discovery and plan.

Output is saved to `plans/{ticket_id}/discovery.md`. This file persists across sessions so subsequent phases can reference it, and remains as a permanent record after the feature merges.

If Discovery reveals scope significantly exceeding the original ticket, split the work into separate tickets before proceeding to Spec.

## 4.2 Phase 2: The Spec (Implementation Plan + Test Spec)

The model produces two artifacts. No code is written until the Architect approves both.

### Artifact 1: Implementation Plan (`spec.md`)

The model drafts the implementation plan. This is the architectural contract for what will be built. Saved to `plans/{ticket_id}/spec.md`.

Required sections:

- **Objective**: Feature definition and acceptance criteria.
- **Architecture**: Every file to be created, modified, or deleted. Nothing outside this manifest may be touched without triggering the drift protocol.
- **Data Contracts**: Exact function signatures, data class definitions, schema deltas, and API payloads.
- **Permissions & Config Delta**: Any changes to AndroidManifest.xml, build scripts, ProGuard rules, or security config. If none, state explicitly. Omitting this section is a spec rejection.
- **Visual Spec** (Compose features only): A description or annotated wireframe sufficient to verify the rendered output post-implementation.
- **Constitution Audit**: Confirmation this plan does not violate any Constitution rule, with the Constitution version referenced.
- **Rollback Plan** (Tier 3 only): Step-by-step recovery if implementation stalls mid-migration.
- **Cross-Spec Dependencies**: Any dependency on data contracts from another in-progress feature.

### Artifact 2: Test Spec (`test_spec.md`)

The model drafts behavioral scenarios in Gherkin format that define the complete behavioral contract for the feature. These scenarios are the source of truth for what the tests in Phase 3 will assert. Saved to `plans/{ticket_id}/test_spec.md`.

Format is flexible: Given/When/Then, plain-English descriptions, or table-driven cases are all acceptable. Content requirements are fixed:

- Every behavioral state described in the Objective has at least one scenario.
- Every error path in the Data Contracts has a scenario with a typed failure state.
- Every Then clause states concrete expected values — not references to production code.
- Mutation heuristic: what is the most broken implementation that would still pass these scenarios? If the answer is plausible, the scenarios are insufficient.

> **EXAMPLE SCENARIO**
>
> **Scenario: Offline Data Sync**
>
> **Given** the device has no network connection and there is pending data in the local SQLDelight cache,
>
> **When** the SyncWorker is triggered by the WorkManager,
>
> **Then** the system emits `SyncState.Pending(retryCount = 1, payloadSize = n)`, retains all local data without modification, and schedules a retry without throwing an unhandled exception.

The Architect reviews and approves both artifacts before Phase 3 begins.

### The Spec-Primacy Instruction

The implementation model (in Phase 4) is seeded with an explicit instruction that the spec is the source of truth. This is the structural defense against the model deriving the implementation from the tests rather than from the specification, which would make the tests unfalsifiable.

> **SPEC-PRIMACY INSTRUCTION**
>
> Derive the implementation entirely from the Markdown Spec and Constitution. The test suite is present in the repository. Do not use test assertions to infer expected values or implementation structure — the tests are a post-hoc verifier, not a blueprint.
>
> If the spec is ambiguous on a behavioral detail, surface the ambiguity rather than resolving it by reading the test.

### Reconciling Spec-Primacy with TDD

These are complementary, not contradictory:

- **Tests define WHAT correctness looks like.** They encode the behavioral contract from `test_spec.md` into executable assertions. They answer: "did we build it right?"
- **The spec defines HOW to implement it.** `spec.md` prescribes architecture, signatures, data flow, and design. It answers: "what are we building?"

The tests are derived from the test spec's behavioral scenarios. The implementation is derived from the spec's architecture and data contracts. The tests verify the implementation. At no point does the implementation derive from the tests.

## 4.3 Phase 3: TDD Red — Write Failing Tests

The model translates the approved behavioral scenarios from `plans/{ticket_id}/test_spec.md` into executable test code. No production code is written in this phase — only tests.

### Domain Logic and Data Layer — Strict TDD

For UseCases, repositories, data models, state management, and any code with behavioral contracts: the model writes test code that compiles and fails. This is non-negotiable because:

- Behavioral contracts can be fully specified in advance from the test spec.
- The red state is objective proof that tests are genuine falsifiers, not tautologies.
- The spec-derived expected values in the test assertions are the primary guard against the model converging on a passing-but-wrong implementation.

The model must:

1. Write test code in the layer-correct test project for every scenario in `test_spec.md`.
2. Add minimal stub types/methods (with `throw new NotImplementedException()` or equivalent) if the production type doesn't exist yet — only enough to compile.
3. Run the tests and confirm they all fail.
4. Report the red results explicitly: `RED: N tests written, N failing, 0 passing`.

> **THE RED-STATE CHECK**
>
> The Architect runs the suite locally and confirms red before proceeding. If any test passes before the feature code exists, it is invalid and must be fixed before implementation begins.
>
> Invalid test indicators: tautological assertion, production logic cloned into the expected value, mocked SUT, or suppressed exception.

### Compose UI — Single-Pass Exception

For Compose-only UI changes — layouts, styling, visual structure, component composition — the strict upfront red-state mandate is a velocity tax with poor return. Writing failing UI tests before the layout exists is unnatural and friction-heavy for visual work where the implementation drives the testable structure.

For UI-exclusive changes: the model generates the Composable implementation and the accompanying UI tests in a single pass during Phase 4. The Architect reviews both before they are finalized. The mutation heuristic still applies to the test review: what is the most broken UI implementation that would still pass these tests?

This bypass applies only to Compose layout and visual structure. Any Composable that contains state management, business logic delegation, or ViewModel interaction is subject to strict TDD.

## 4.4 Phase 4: Implementation — Write Code, Go Green

Implementation proceeds on the feature branch. The model has full access to the relevant source files, the working spec (`spec.md`), the test spec (`test_spec.md`), the Constitution, and the discovery document simultaneously. Feed the full relevant context — do not artificially prune to manage a token budget. Current context windows handle this comfortably.

The model writes the minimum production code needed to make all failing tests pass. It must:

1. Derive the implementation from `spec.md`, not from the test assertions.
2. Run tests after each meaningful change — do not batch large changes without test feedback.
3. If new behavior is needed that has no test, return to Phase 3 and write the test first.
4. Report the green results: `GREEN: N tests passing, 0 failing`.

### Drift Detection

On completion, the model compares the git diff against the spec's file manifest.

> **DRIFT AUDIT RULES**
>
> **Minor drift** — Files outside the domain module with small incidental changes (e.g., an import update in an adjacent utility). Record a review note; Architect acknowledges before merge.
>
> **Significant drift** — Any file in the domain/ module, manifest or security config changes, multi-file unlisted modifications, or public API surface changes. Full revert-or-amend: change is reverted or a spec amendment is approved before continuing.
>
> **Hard flags — always significant, no exceptions** — Any modification to AndroidManifest.xml, build scripts, ProGuard rules, or security config not in the Permissions & Config Delta. Any new external dependency not in the spec. Any visibility increase (private -> internal -> public) not in the Architecture section.

## 4.5 Compose Visual Verification

For Compose features, the Architect's sign-off on the rendered layout is part of the Definition of Done. To accelerate this: take a screenshot of the rendered Compose preview and feed it back to the model alongside the Visual Spec. The model flags layout regressions, padding issues, typography drift, and alignment problems. The Architect reviews the model's assessment and makes the final call. This keeps the human in the loop for aesthetic judgment while delegating the tedious pixel-comparison work to the model.

---

# 5. TDD Failure Modes and Guardrails

Frontier models reason well about test quality. The failure modes below emerge under the specific conditions of an agentic coding loop: a stated goal (make tests pass), a large output space, and no structural constraint distinguishing "tests pass because the code is correct" from "tests pass by other means." The guardrails close those alternative paths.

> **THE META-GUARDRAIL**
>
> When reviewing any test suite, ask: **what is the most broken implementation that would still pass these tests?**
>
> If the answer is plausible, the tests are insufficient regardless of coverage percentage.

### 1. Spec-Implementation Divergence

**The Condition:** If the model derives both tests and implementation from the same reasoning process, it may embed the same misunderstanding in both. The test asserts the wrong behavior; the code implements the wrong behavior. Everything is green; the software is wrong.

**The Guardrail:** The Spec-Primacy Instruction and the pre-implementation red-state check close this structurally. Tests are authored before implementation; implementation is derived from the spec, not from the tests.

### 2. Test Deletion and Suppression

**The Condition:** In an agentic loop where failing tests are the primary obstacle, removing or suppressing them is a structurally valid path to the stated goal. Manifests as deletion, commenting out, or unjustified `@Ignore`/`@Disabled` annotations.

**The Guardrail:** Any `@Ignore` or `@Disabled` annotation must include a linked issue reference. Test deletions require explicit Architect acknowledgment. Unexplained reduction in test count is a red flag in diff review.

### 3. Expected Values Derived From Production Code

**The Condition:** Without explicit guidance, a model writing tests may derive expected values by calling the production function and asserting on its output — producing a test that passes for any implementation, including a wrong one.

**The Guardrail:** Behavioral scenarios must state concrete expected values. Test assertions must not call production code to produce expected values. The pre-implementation red-state check is the primary enforcement: a test that passes before the feature exists cannot have been legitimately derived from the spec.

### 4. Visibility Mutation

**The Condition:** When internal behavior is difficult to reach through the public interface, the model may increase member visibility — promoting private fields or methods to internal or public — to make them testable directly. This destroys encapsulation and makes future refactors that don't change behavior break tests.

**The Guardrail:** Constitution rule: no member visibility may be increased without explicit justification in the spec's Architecture section. The drift audit scans for visibility increases as a hard flag.

### 5. Over-Mocking

**The Condition:** Without explicit testing philosophy guidance, a model may default to heavy mocking. Taken to an extreme, the test suite verifies the mocking library, not the business logic.

**The Guardrail:** At least one integration-style test per feature must use real implementations for adjacent layers (e.g., ViewModel with real Interactor, mocking only the network boundary). Constitution rule: the SUT must never appear as a mock or spy within its own test file.

### 6. Exception Suppression

**The Condition:** Error path tests can produce false-positive passes when exception handling is misconfigured: a generic try/catch swallows the failure, an expected exception becomes a nullable return, or `assertNotNull` is used instead of `assertThrows`.

**The Guardrail:** Constitution rule: tests must never catch generic `Exception` or `Throwable`. Use `assertThrows<SpecificException>` for all error-path assertions. Behavioral scenarios must enumerate expected exception types for all error paths.

### 7. Condition Stuffing

**The Condition:** In a severely constrained loop, the model may resort to test-environment branching in production code: `if (isTestEnvironment) { return hardcodedExpectedValue }`. Rare with frontier models, but invisible in normal code review and severe in consequence.

**The Guardrail:** Constitution rule: production code must contain zero references to test classes, test annotations, or any flag that alters execution path based on test-environment detection.

### 8. Coverage Threshold Gaming

**The Condition:** Without branch coverage requirements or scenario-level definitions, a model targeting a line coverage number covers the cheapest paths first. Error handling and boundary conditions may be entirely absent while the report shows 80%.

**The Guardrail:** Complement line coverage with branch coverage requirements. The behavioral scenarios are the authoritative coverage definition: a feature is done when every approved scenario has a corresponding test that was red before implementation and green after.

---

# 6. The Reviewer Agent Protocol

For Tier 3 changes, a Reviewer Agent audits the spec before any code is generated. For Tier 2, available at Architect discretion when the spec is complex, touches sensitive boundaries, or warrants an adversarial second pass.

The Reviewer Agent's mandate is open-ended adversarial audit. At frontier capability, this surfaces failure modes no checklist anticipates.

The Reviewer Agent must be given the full contract pack: the Constitution, all relevant layer contracts from the contract pack, and the task routing table. Without these, the review is against an unspecified standard.

> **REVIEWER AGENT PROMPT**
>
> You are an adversarial architectural reviewer. You have been given the Constitution, the relevant layer contracts, and the working spec. Identify every way this spec could fail to produce correct software. There is no limit on what you may flag.
>
> At minimum, cover: Constitution violations, layer contract violations, unlisted or implicit dependencies, behavioral scenario coverage gaps, manifest completeness, Permissions & Config Delta completeness, and — for Tier 3 — rollback viability at each migration stage. These are a floor, not a ceiling.
>
> Flag assumptions the spec makes about existing code behavior that cannot be verified from the Discovery report. Flag architectural decisions that create future constraints not acknowledged in the spec. Flag anything that would cause this implementation to fail in ways the test suite cannot catch.
>
> Produce a structured report. Do not suggest implementation code.

Implementation may not begin until all flagged items are resolved in a revised spec or formally accepted with documented rationale.

---

# 7. Triage and Recovery

When the test suite stays red, iterating raw error logs back into the active session without structure is the path to reward hacking — convergence on a state that passes tests rather than a state that is correct. Structured triage separates diagnosis from repair.

## 7.1 Step 1 — Auditor Mode

Issue an explicit mode-switch instruction before providing failure context:

> **AUDITOR MODE INSTRUCTION**
>
> You are now in Auditor Mode. Treat the current implementation, test suite, and failure logs as neutral artifacts. Do not attempt to fix anything. Analyze the failure against the spec and categorize it into one of three buckets. Produce a diagnosis only.

The Auditor receives full visibility: Constitution, working spec, raw failure logs, stack traces, implementation code, and test code. Stack traces are diagnostic signal — the Auditor uses them to reason about what behavioral contract was violated.

> **THE THREE BUCKETS**
>
> **Bucket A — Spec Ambiguity:** The spec lacked hard constraints; test and implementation made diverging but technically-compliant assumptions. The contract is weak.
>
> **Bucket B — Test Misalignment:** The test expected something not mandated by the spec. The test is wrong relative to the contract.
>
> **Bucket C — Implementation Drift:** Spec and tests are aligned; the implementation failed to fulfill the contract. The code is wrong.

Save the diagnosis before touching anything.

## 7.2 Step 2 — Patch the Contract (Buckets A and B)

The fix targets the spec and tests, not the code. Update the working spec to close the loophole. Have the model regenerate the affected scenarios and tests. The Architect confirms each assertion is traceable to a concrete constraint in the updated spec. Run the corrected tests against the existing implementation — if they pass, the loop is complete.

## 7.3 Step 3 — Implementation Patch (Bucket C, or Persistent Red)

For Bucket C failures, try up to two inline correction loops in the active session before resetting. Feed the model the Auditor's diagnosis and the full failure context, then issue a targeted repair instruction. Frontier models correct well within a continuous session when given the diagnosis and the behavioral contract that was violated. If two in-session attempts don't resolve it, the problem is structural — proceed to hard reset.

> **INLINE CORRECTION INSTRUCTION**
>
> Auditor Mode is complete. Switching to repair. Here is the Auditor's diagnosis and the full failure context. Fix the code to satisfy the spec. Apply the minimum surgical diff. Do not rewrite unrelated logic or change the architecture. Derive the fix from the spec; use the failure context to understand the bug, not to target assertion values.

If two inline attempts fail: commit the current state (`git commit -m "WIP: pre-patch state"`) as a rollback anchor, start a fresh session, and seed it with the spec, current implementation, Spec-Primacy Instruction, and the full Auditor diagnosis. The hard session reset discards any reasoning momentum that has been anchored to a wrong approach.

## 7.4 Two-Strike Escalation

Two complete triage cycles without a green suite means the problem is structural: a deeper spec ambiguity, an architecture wrong for the requirement, or scope drift. Archive the current attempt and re-enter from Phase 1 with a clean slate.

> **TRIAGE FLOW**
>
> Red -> Auditor Mode -> diagnose -> save diagnosis
>
> Bucket A/B: Update spec -> regenerate tests -> Architect verifies fidelity -> run against existing impl. Green: done. Red: go to Step 3.
>
> Bucket C: Up to two inline corrections -> if still red: commit WIP -> hard session reset -> surgical patch with full Auditor context -> run suite.
>
> Two full cycles red: Tier 3 re-spec. Archive. Return to Phase 1.

## 7.5 The Post-Green Amendment Path

When a feature is green and drift-clean but the Architect finds the behavior misses an unstated intent during testing, a scoped amendment is available rather than a full Tier 2 re-spec.

> **POST-GREEN AMENDMENT PROTOCOL**
>
> Requirements for a scoped amendment:
>
> 1. A written scope statement appended to the working spec: exactly what is wrong and what the correct behavior is. One paragraph maximum.
> 2. Architect confirmation that the correction is contained within the already-approved file manifest. If new files are required, escalate to Tier 2.
> 3. Updated behavioral scenarios. The model drafts; the Architect approves before any code is touched.
> 4. Corrected tests must confirm red against the current implementation before the patch proceeds.
>
> Any change to the file manifest, data contracts, or architectural boundaries escalates to a standard Tier 2.

---

# 8. Conclusion: Build the Machine Right

Frontier models are capable engineering partners. The bottleneck is not their reasoning within a session — it is the absence of persistent context across the sessions that constitute a real project. CFAW solves that bottleneck. The Constitution is the architectural memory. The spec is the session-level contract. Together they give a capable model what it needs to produce work that compounds correctly over time.

Every rule here exists because it closes a specific hole that costs more to leave open than to close. If you find a gate that does not pay for itself, remove it.

> **THE CFAW CONTRACT**
>
> 1. The intelligence of the system lives in static specifications, not in chat history.
> 2. The Constitution is law. Violations are rejected, not reviewed.
> 3. No code is written without an approved spec. No spec is approved without a Constitution audit.
> 4. The spec phase produces both an implementation plan and a test spec. Tests are red before implementation. UI: single-pass is acceptable.
> 5. The implementation derives from the spec. Tests are verifiers, not blueprints.
> 6. Drift is flagged proportionally. Minor is noted; significant is reverted or amended.
> 7. Behavioral scenarios define done. Coverage numbers are a floor, not a ceiling.
> 8. Ask of every test suite: what is the most broken implementation that still passes?

*You cease to be a coder. You become the Architect of the machine.*

---

# 9. Meta Prompts for Each Phase

These are prompt generators. When you need to begin a CFAW phase, you don't cold-prompt the model — you feed your informal description into the appropriate meta-prompt, and it produces a high-quality, structured prompt for that phase. Use these at the start of each new session to ensure the model enters with the right framing.

**Workflow:** Informal idea -> Meta-prompt -> Structured phase prompt -> Feed to model with Constitution + contracts.

**Phases:** 9.1 Discovery -> 9.2 Spec + Test Spec -> 9.3 TDD Red -> 9.4 Implementation.

## 9.1 Discovery Meta-Prompt

You are an expert Prompt Engineer and Principal Systems Architect. Your objective is to take the user's informal description of a software feature and translate it into a highly effective, rigorous prompt designed specifically for the **Discovery** phase of development.

The resulting prompt you generate must instruct the target AI to:
1. Analyze the core business, technical, and user experience goals of the provided idea.
2. Identify missing information, potential architectural bottlenecks, and edge cases.
3. Output a structured list of targeted, high-impact questions to clarify the exact scope before any specifications are drafted.

Structure the output prompt with the following sections:
- **System Role**: Define the AI as a meticulous Product Manager and Lead Architect.
- **Context**: Present the user's raw idea clearly and concisely.
- **Objective**: Instruct the AI to map the domain and uncover blind spots.
- **Output Format**: Demand a categorized list of clarifying questions (e.g., Core Logic, Data Persistence, UI/UX flows, Edge Cases).

User's informal description:
`[INSERT RAW IDEA HERE]`

## 9.2 Specification Meta-Prompt

You are an expert Prompt Engineer. Your task is to translate the user's conceptual understanding of a system into a deterministic prompt for the **Specification (Spec)** phase.

The resulting prompt must instruct the target AI to consume the finalized discovery document and output **two artifacts**:

**Artifact 1 — Implementation Plan (`spec.md`):** A comprehensive, low-level technical specification. The generated prompt must force the AI to define:
1. System Architecture (component boundaries, separation of concerns, exact files to create/modify/delete).
2. Data Models and Schemas (local DB entities, types, relationships).
3. API Contracts or Internal Interfaces (method signatures, payloads, error handling).
4. Permissions & Config Delta (any build, manifest, or configuration changes).
5. Constitution Audit (confirmation of compliance with project rules).

**Artifact 2 — Test Spec (`test_spec.md`):** Gherkin behavioral scenarios for every behavioral state and error path. The generated prompt must force the AI to:
1. Write Given/When/Then scenarios with concrete expected values for every behavior described in the Objective.
2. Include error-path scenarios with typed failure states for every error in the Data Contracts.
3. Apply the mutation heuristic: what is the most broken implementation that would still pass these scenarios?

Structure the generated prompt with:
- **System Role**: Define the AI as a Staff-level Technical Lead.
- **Context**: `[Placeholder for the finalized discovery notes/requirements]`.
- **Directives**: Strict rules on formatting (use Markdown, strictly adhere to the target tech stack). Both artifacts must be produced.
- **Deliverables**: `plans/{ticket_id}/spec.md` and `plans/{ticket_id}/test_spec.md`.

User's informal description of the spec needs:
`[INSERT RAW IDEA HERE]`

## 9.3 TDD Red Meta-Prompt

You are an expert Prompt Engineer. Your task is to generate a rigorous prompt for the **TDD Red** phase — translating approved behavioral scenarios into executable, failing test code.

The resulting prompt must instruct the target AI to:
1. Read every scenario in `plans/{ticket_id}/test_spec.md`.
2. Write a test method for each scenario in the layer-correct test project.
3. Use concrete expected values from the scenarios — never derive expected values from production code.
4. Add minimal stub types/methods (with `throw new NotImplementedException()` or equivalent) if the production type doesn't exist yet.
5. Run the full test suite and confirm every new test fails.
6. Report: `RED: N tests written, N failing, 0 passing`.

Structure the generated prompt with:
- **System Role**: Define the AI as a Senior Test Engineer specializing in the target stack.
- **Context**: `plans/{ticket_id}/test_spec.md` and `plans/{ticket_id}/spec.md` (for type signatures only — not for implementation logic).
- **Directives**: No production code may be written. Tests must compile. Every scenario must have a corresponding test. Invalid test indicators (tautological assertions, mocked SUT, suppressed exceptions) are rejection criteria.
- **Deliverables**: Test files in the correct test projects, ready to run and fail.

## 9.4 Implementation Meta-Prompt

You are an expert Prompt Engineer. Your task is to take the user's implementation goals and generate an actionable, strict prompt for the **Implementation** phase.

The resulting prompt must instruct the target AI to write production-ready code that strictly adheres to the previously generated Specification and makes all previously generated Tests pass.

The generated prompt must force the AI to:
1. Implement the code logically, one module or component at a time.
2. Strictly follow the defined architecture, data models, and interface contracts from `spec.md`.
3. Write clean, modular, and highly optimized code without over-engineering.
4. Run the test suite after each meaningful change and report progress toward green.
5. If new behavior is needed that has no test, stop and write the test first.
6. Ensure the output passes the full test suite without modification.

Structure the generated prompt with:
- **System Role**: Define the AI as a Senior Software Engineer specializing in the target stack.
- **Context**: `plans/{ticket_id}/test_spec.md`.
- **Directives**: Include the Spec-Primacy Instruction. Hard rules on code style, error handling, performance constraints, and avoiding hallucinated dependencies. Implementation derives from the spec, not from test assertions.
- **Deliverables**: The exact source code files required, complete with necessary imports.

Here is the meta-prompt designed to slot perfectly into Section 9 of your CFAW specification. I calibrated it to act as the strict, adversarial gatekeeper required by your Phase 4 Drift Audit and Section 7 Auditor Mode rules.

## 9.5 Code Review & Drift Audit Meta-Prompt

You are an expert Prompt Engineer. Your task is to generate an adversarial and uncompromising prompt for the Code Review & Drift Audit phase.

The resulting prompt must instruct the target AI to evaluate the completed implementation strictly against the agreed-upon contracts, acting as an impartial enforcer of the project's architecture. It must not attempt to fix the code; its sole purpose is diagnosis and verification.

The generated prompt must force the AI to:

Perform a rigid Drift Audit: Compare the implementation's git diff against the file manifest and architecture defined in spec.md.

Categorize any detected drift strictly according to the framework rules: Minor (incidental files), Significant (domain layer, API surface), or Hard Flags (unlisted external dependencies, visibility increases, manifest/build script changes).

Evaluate the test suite against the Meta-Guardrail: What is the most broken implementation that would still pass these tests? Check for test tautologies, suppressed exceptions, and condition stuffing.

Audit for Constitution violations (e.g., layer boundary breaches, forbidden tech stack usage).

Output a definitive verdict: Pass (Merge), Minor Drift (Acknowledge), or Fail (Revert/Amend) mapped to the Bucket A/B/C triage system.

Structure the generated prompt with:

System Role: Define the AI as a Principal Architecture Auditor. It is adversarial, detail-oriented, and immune to the sunk-cost fallacy of discarding written code.

Context: [Placeholder for spec.md], [Placeholder for Constitution], [Placeholder for test_spec.md], and [Placeholder for git diff / source code].

Directives: Do not suggest or write implementation code. Focus entirely on verification against the contracts. Flag all visibility mutations and expected values derived from production code.

Deliverables: A structured Audit Report detailing Drift Categorization, Constitution violations, TDD Guardrail failures, and a final go/no-go verdict.
