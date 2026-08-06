# Security policy

SpecForge Gate is a pre-release project. Security reports are welcome, but there is no promised service-level agreement or guaranteed response time.

## Supported state

The active `main` branch and open release-preparation work are the supported security review targets. Older commits, local forks, and unpublished experiments are not supported as maintained release lines.

## What to report

Please report suspected vulnerabilities such as:

- unsafe handling of local files or paths;
- command execution risks;
- dependency-related vulnerabilities;
- workflow or release-process weaknesses;
- disclosure of sensitive data through logs or reports.

## How to report

Do not publicly disclose a suspected vulnerability before it has been reviewed.

If GitHub private vulnerability reporting is available for this repository, use it. If it is not available, open a GitHub Issue with a minimal, non-exploitative description and ask for a maintainer-preferred private follow-up path. Do not include exploit details, secrets, tokens, or sensitive files in a public Issue.

## Scope boundaries

The current deterministic CLI runs locally and does not require an API key or upload documents. Planned REST API, web UI, Docker, GitHub Action, and optional AI-provider integrations are not implemented yet and should not be reported as available attack surfaces in the current codebase.
