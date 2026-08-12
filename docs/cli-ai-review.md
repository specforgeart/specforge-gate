# CLI AI review

`specgate ai-review` is the explicit command-line entry point for the optional AI product flow.
It keeps deterministic analysis first, then asks one environment-configured provider for advisory
contradictions and a conservative improved-specification draft.

The existing `specgate check` command is unchanged and performs no provider call.

## Configure a provider

The CLI uses the same runtime environment contract as the REST AI review flow.

### Ollama

```bash
export SPECFORGE_AI_PROVIDER=ollama
export SPECFORGE_AI_MODEL=llama3.2
```

Ollama defaults to `http://127.0.0.1:11434`. Override it only when the operator intentionally
chooses another Ollama endpoint:

```bash
export SPECFORGE_AI_BASE_URL=http://127.0.0.1:11434
```

PowerShell:

```powershell
$env:SPECFORGE_AI_PROVIDER = "ollama"
$env:SPECFORGE_AI_MODEL = "llama3.2"
```

### OpenAI-compatible endpoint

```bash
export SPECFORGE_AI_PROVIDER=openai-compatible
export SPECFORGE_AI_MODEL=my-model
export SPECFORGE_AI_BASE_URL=https://example.invalid/v1
export SPECFORGE_AI_API_KEY=replace-me
```

`SPECFORGE_AI_API_KEY` is optional for endpoints that do not require Bearer authentication.
`SPECFORGE_AI_TIMEOUT_SECONDS` may be set to a positive finite number; the default is 60 seconds.

## Run

The command intentionally accepts one explicit file, not a directory:

```bash
specgate ai-review requirements.md
specgate ai-review requirements.md --format json --fail-on none
specgate ai-review requirements.md --format markdown --fail-on none
```

The single-file boundary prevents an accidental directory command from sending many documents to
an external provider.

## Output contract

A successful AI review always contains:

- the unchanged deterministic report;
- configured provider and model identifiers;
- validated contradiction items whose quoted statements are verbatim source substrings;
- one bounded conservative improved-specification Markdown draft.

JSON output follows the same product shape as the REST AI review response:

```json
{
  "deterministic": {},
  "provider": "ollama",
  "model": "llama3.2",
  "contradictions": [],
  "improved_spec": "# Goal\n..."
}
```

Text and Markdown formats are human-reviewable presentations of the same result.

## Exit codes

`ai-review` preserves deterministic `--fail-on` behavior after a successful AI review:

- `0`: review completed and the configured deterministic threshold did not fail;
- `1`: review completed, but deterministic findings reached the `--fail-on` threshold;
- `2`: configuration, file input, suppression syntax, provider, or AI-output validation failed.

Use `--fail-on none` when the command is being used only to obtain the advisory review.

## Security and privacy boundary

The command reads one explicit local file and sends its specification text to the provider selected
by environment variables. Provider URLs, model names, and API keys are not command-line arguments,
so they are not echoed in normal CLI output. The command does not persist prompts or responses.

Text and Markdown output escape terminal control characters before printing model-derived content.
JSON output uses normal JSON escaping.

AI output is advisory and untrusted. Contradiction evidence is validated against the source, and the
improved draft still requires human review. Neither AI result changes SG rule IDs, deterministic
findings, PASS/NEEDS WORK semantics, or the behavior of `specgate check`.

## End-to-end local demo

For a reproducible Ollama workflow covering deterministic CLI, explicit AI review, REST API, and
Web UI, see [End-to-end local AI demo](local-ai-demo.md).
