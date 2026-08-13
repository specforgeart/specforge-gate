# Improved-spec draft

SpecForge Gate provides an optional provider-neutral `draft_improved_specification()` feature that produces an advisory Markdown rewrite of a supplied specification. It is intentionally separate from deterministic checks and does not change SG rule findings, PASS/NEEDS WORK, report formats, or exit codes.

## Contract

The feature accepts the source specification, one explicit `AIProvider`, optional validated `Contradiction` context, and optional deterministic `Finding` context. It asks the provider for text output and returns an immutable `ImprovedSpecDraft(text, provider, model)`.

The prompt is conservative and gate-aware: it asks the model to improve structure, clarity, testability, acceptance criteria, scope boundaries, and edge cases without inventing unsupported business facts. Deterministic findings are supplied as authoritative quality feedback. Missing required sections must be restored; when their facts are unknown, the section remains with an explicit TODO/open question instead of being silently omitted. Missing facts and unresolved contradictions remain explicit rather than being guessed.

## Prompt-injection boundary

The source specification and contradiction context are JSON-encoded into the user message and explicitly described to the model as untrusted data. Instructions embedded inside the specification are not application instructions.

This reduces prompt-confusion risk but is not a security proof. Callers must continue to treat model output as untrusted advisory text.

## Contradiction context

Callers may pass contradiction results from `analyze_contradictions()`. The drafting feature re-validates that each supplied contradiction:

- is a `Contradiction` value;
- contains two distinct bounded statements;
- quotes verbatim substrings of the same source specification;
- is not duplicated, including reversed pairs;
- has a bounded non-empty explanation.

This prevents manually constructed or stale contradiction evidence from being silently injected as trusted context.

## Output validation and deterministic recheck

The provider output must be non-empty direct Markdown, contain at least one Markdown heading, fit within the configured size bound, contain no NUL byte, and not wrap the entire draft in a Markdown code fence. Provider transport errors are propagated through the existing `AIProviderError` contract.

Product AI review flows immediately run the generated draft through the same deterministic core and configuration used for the source. REST and CLI therefore expose both the original deterministic report and `draft_deterministic`. The Web UI shows the original-to-draft finding count and draft gate status before the operator chooses whether to use the draft.

These checks still do not establish semantic truth. The draft remains advisory and requires human review.

## Security and privacy

Invoking the feature sends the specification and optional contradiction context to the explicitly configured provider. The feature does not choose a provider, discover credentials, persist prompts or responses, log document contents, or make additional network calls outside `provider.generate()`.

For sensitive specifications, use a provider and endpoint whose data-handling policy is acceptable for the document. A local Ollama endpoint can keep the provider call local when configured that way.

## Example

```python
from specforge_gate.ai import OllamaProvider, draft_improved_specification

provider = OllamaProvider(model="qwen3:8b")
result = draft_improved_specification(
    "# Goal\nMake export fast and convenient.",
    provider,
)
print(result.text)
```

In v0.3.0 the function is consumed only inside explicit AI review flows: `specgate ai-review FILE`, `POST /v1/ai/review`, and the Web UI **AI Review** action. It is never invoked by deterministic `specgate check`, `POST /v1/check`, or the reusable GitHub Action, and no product surface applies the draft automatically.
