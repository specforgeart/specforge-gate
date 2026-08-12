# Advisory contradiction analysis

SpecForge Gate provides an optional provider-neutral contradiction-analysis feature on top of the existing `AIProvider` contract. It is deliberately separate from the deterministic quality gate.

## Status and boundary

`analyze_contradictions(specification, provider)` sends one explicitly supplied specification to one explicitly configured provider and returns a validated `ContradictionAnalysis` result.

The feature is **advisory**:

- it does not create or modify `SGxxx` rule findings;
- it does not change `PASS` / `NEEDS WORK`;
- it does not change CLI exit codes or deterministic JSON/Markdown report contracts;
- product surfaces invoke it only through explicit AI review actions; the GitHub Action and deterministic engine do not invoke it;
- provider failures remain provider failures and are not converted into deterministic findings.

## Result contract

A successful analysis returns:

- `ContradictionAnalysis.contradictions` — immutable tuple of zero or more `Contradiction` objects;
- `Contradiction.statement_a` — exact verbatim substring from the source specification;
- `Contradiction.statement_b` — a different exact verbatim substring from the source specification;
- `Contradiction.explanation` — short advisory explanation;
- `provider` and `model` — normalized provider identity from the provider response.

An empty contradiction tuple is a valid result. It means the configured model did not return any direct contradictions under the feature prompt; it is not a proof that the specification is contradiction-free.

## Hallucination guardrail

The model is instructed to quote both conflicting statements verbatim. SpecForge then verifies that both strings are actual substrings of the submitted specification before accepting the result.

If a model invents or paraphrases either quote, returns duplicate pairs, returns malformed JSON, adds unexpected fields, or exceeds bounded result sizes, the feature raises `ContradictionAnalysisError(code="invalid_output")` rather than surfacing the untrusted result.

This does not make model judgment deterministic. It makes the accepted evidence auditable against the source text.

## Prompt-injection boundary

The specification is JSON-encoded inside the provider-neutral user prompt. The fixed system prompt explicitly treats the specification value as untrusted data and instructs the model not to follow instructions embedded in it.

Prompt injection cannot be eliminated by prompting alone. Therefore the feature also:

- accepts only the narrow contradiction JSON shape;
- rejects non-verbatim evidence;
- keeps the result advisory;
- does not allow the model to invoke tools, URLs, files, commands, or deterministic rule controls.

## Bounds

The first implementation intentionally bounds the surface:

- maximum specification length: 200,000 characters;
- maximum accepted contradictions: 20;
- maximum statement quote length: 2,000 characters;
- maximum explanation length: 4,000 characters.

These are feature validation bounds, not provider token limits.

## Errors

Feature-level validation uses `ContradictionAnalysisError`:

- `invalid_input` — blank or oversized specification;
- `invalid_output` — provider text cannot be accepted as the contradiction result contract.

`AIProviderError` from Ollama or OpenAI-compatible transports propagates unchanged so callers retain normalized authentication, timeout, rate-limit, unavailable, and retryable metadata.

## Example

```python
from specforge_gate.ai import OllamaProvider, analyze_contradictions

provider = OllamaProvider(model="qwen3:8b")
result = analyze_contradictions(
    "The export must complete within 2 seconds.\n"
    "The export may take up to 30 seconds for the same request.",
    provider,
)

for contradiction in result.contradictions:
    print(contradiction.statement_a)
    print(contradiction.statement_b)
    print(contradiction.explanation)
```

The provider call occurs only when `analyze_contradictions()` is invoked.

## Product surfaces

In v0.3.0 contradiction analysis is consumed only by explicit AI review orchestration:

- `specgate ai-review FILE`;
- `POST /v1/ai/review`;
- the same-origin Web UI **AI Review** action.

`specgate check`, `POST /v1/check`, the reusable GitHub Action, and the deterministic engine remain
provider-free. Provider routing/fallback, persistence, telemetry, and automatic draft application
remain out of scope.
