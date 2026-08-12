"""Self-contained browser UI for the optional SpecForge Gate API."""

from __future__ import annotations

WEB_UI_HEADERS = {
    "Cache-Control": "no-store",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "style-src 'unsafe-inline'; "
        "script-src 'unsafe-inline'; "
        "connect-src 'self'; "
        "img-src 'none'; "
        "font-src 'none'; "
        "object-src 'none'; "
        "base-uri 'none'; "
        "form-action 'none'; "
        "frame-ancestors 'none'"
    ),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}

WEB_UI_HTML = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SpecForge Gate — Requirements check</title>
  <style>
    :root {
      color-scheme: light;
      --paper: #fcf4ea;
      --paper-strong: #fffaf4;
      --graphite: #192228;
      --muted: #657077;
      --line: #d9d2c9;
      --orange: #fe7101;
      --orange-soft: #ffe2ca;
      --green: #2f6f45;
      --green-soft: #edf6ed;
      --error: #b3261e;
      --warning: #9a5b00;
      --info: #315c72;
      --shadow: 0 22px 60px rgb(25 34 40 / 10%);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at 82% 8%, rgb(254 113 1 / 10%), transparent 27rem),
        var(--paper);
      color: var(--graphite);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system,
        BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    button, textarea { font: inherit; }

    code, pre {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }

    .shell {
      width: min(1240px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 44px;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      margin-bottom: 26px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 800;
      letter-spacing: -0.03em;
    }

    .brand-mark {
      width: 14px;
      height: 14px;
      background: var(--orange);
      border-radius: 3px;
      box-shadow: 0 0 0 5px rgb(254 113 1 / 12%);
    }

    .mode-row {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 8px;
    }

    .mode {
      border: 1px solid var(--graphite);
      border-radius: 999px;
      padding: 7px 11px;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      background: var(--graphite);
      color: var(--paper-strong);
    }

    .mode.ai {
      border-color: var(--orange);
      background: transparent;
      color: var(--graphite);
    }

    .hero {
      display: grid;
      gap: 10px;
      margin-bottom: 24px;
      max-width: 820px;
    }

    .eyebrow {
      color: var(--orange);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    h1 {
      margin: 0;
      font-size: clamp(34px, 5vw, 64px);
      line-height: 0.98;
      letter-spacing: -0.055em;
    }

    .hero p {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.55;
      max-width: 760px;
    }

    .workspace {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(360px, 0.9fr);
      gap: 18px;
      align-items: start;
    }

    .panel {
      background: rgb(255 250 244 / 82%);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
      overflow: hidden;
      backdrop-filter: blur(12px);
    }

    .panel-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
    }

    .panel-title {
      margin: 0;
      font-size: 15px;
      letter-spacing: -0.02em;
    }

    .tiny {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }

    .editor-wrap { padding: 18px; }

    textarea {
      width: 100%;
      min-height: 500px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fffdf9;
      color: var(--graphite);
      padding: 18px;
      line-height: 1.55;
      outline: none;
      transition: border-color 120ms ease, box-shadow 120ms ease;
    }

    textarea:focus {
      border-color: var(--orange);
      box-shadow: 0 0 0 4px rgb(254 113 1 / 12%);
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }

    .button {
      appearance: none;
      border: 1px solid var(--graphite);
      border-radius: 11px;
      padding: 10px 14px;
      cursor: pointer;
      background: transparent;
      color: var(--graphite);
      font-weight: 750;
      transition: transform 120ms ease, opacity 120ms ease, background 120ms ease;
    }

    .button:hover:not(:disabled) { transform: translateY(-1px); }

    .button.primary {
      background: var(--graphite);
      color: white;
    }

    .button.accent {
      border-color: var(--orange);
      background: var(--orange);
      color: #1a120c;
    }

    .button:disabled {
      cursor: not-allowed;
      opacity: 0.42;
    }

    .notice {
      min-height: 22px;
      margin-top: 12px;
      color: var(--muted);
      font-size: 13px;
    }

    .summary {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 9px;
      padding: 18px;
    }

    .metric {
      padding: 13px 12px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: rgb(255 255 255 / 48%);
    }

    .metric strong {
      display: block;
      font-size: 22px;
      letter-spacing: -0.04em;
    }

    .metric span {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .status-line {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 0 18px 16px;
      flex-wrap: wrap;
    }

    .status-chip {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 7px 10px;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.06em;
    }

    .status-chip.pass,
    .status-chip.enabled {
      border-color: #6f8b70;
      background: var(--green-soft);
      color: #25452a;
    }

    .status-chip.needs-work {
      border-color: var(--orange);
      background: var(--orange-soft);
      color: #6f3400;
    }

    .status-chip.disabled {
      border-color: var(--line);
      background: #f1ede8;
      color: var(--muted);
    }

    .filters {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 0 18px 16px;
    }

    .filter {
      border: 1px solid var(--line);
      border-radius: 999px;
      background: transparent;
      color: var(--muted);
      padding: 7px 10px;
      font-size: 12px;
      cursor: pointer;
    }

    .filter[aria-pressed="true"] {
      border-color: var(--graphite);
      background: var(--graphite);
      color: white;
    }

    .findings,
    .contradictions {
      display: grid;
      gap: 10px;
      padding: 0 18px 18px;
    }

    .finding,
    .contradiction {
      border: 1px solid var(--line);
      border-left-width: 4px;
      border-radius: 12px;
      padding: 13px 14px;
      background: rgb(255 255 255 / 55%);
    }

    .finding.error { border-left-color: var(--error); }
    .finding.warning { border-left-color: var(--warning); }
    .finding.info { border-left-color: var(--info); }
    .contradiction { border-left-color: var(--orange); }

    .finding-top,
    .contradiction-top {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 7px;
    }

    .finding-id,
    .contradiction-id { font-weight: 850; }
    .finding-meta { color: var(--muted); font-size: 12px; }
    .finding-message { margin: 0; line-height: 1.45; }
    .finding-fix,
    .contradiction-copy {
      margin: 7px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }

    .empty {
      padding: 30px 18px 36px;
      text-align: center;
      color: var(--muted);
      line-height: 1.5;
    }

    .privacy {
      display: flex;
      gap: 8px;
      align-items: flex-start;
      margin-top: 16px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }

    .privacy-dot {
      width: 7px;
      height: 7px;
      flex: 0 0 7px;
      margin-top: 5px;
      border-radius: 50%;
      background: var(--orange);
    }

    .ai-panel {
      margin-top: 18px;
    }

    .ai-status-row {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
      padding: 16px 18px 0;
    }

    .ai-grid {
      display: grid;
      grid-template-columns: minmax(300px, 0.72fr) minmax(0, 1.28fr);
      gap: 18px;
      padding: 18px;
    }

    .ai-column {
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: rgb(255 255 255 / 42%);
      overflow: hidden;
    }

    .ai-column-head {
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
    }

    .ai-column-head h3 {
      margin: 0;
      font-size: 14px;
    }

    .draft-output {
      min-height: 260px;
      max-height: 620px;
      overflow: auto;
      margin: 0;
      padding: 16px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      background: transparent;
      color: var(--graphite);
      font-size: 13px;
      line-height: 1.55;
    }

    .ai-empty {
      padding: 24px 16px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }

    @media (max-width: 900px) {
      .workspace,
      .ai-grid { grid-template-columns: 1fr; }
      textarea { min-height: 390px; }
    }

    @media (max-width: 560px) {
      .shell { width: min(100% - 20px, 1240px); padding-top: 18px; }
      .topbar { align-items: flex-start; }
      .summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .panel-head { align-items: flex-start; flex-direction: column; }
      .mode-row { justify-content: flex-start; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <div class="topbar">
      <div class="brand"><span class="brand-mark" aria-hidden="true"></span>SpecForge Gate</div>
      <div class="mode-row">
        <div class="mode">Deterministic</div>
        <div class="mode ai">Advisory AI</div>
      </div>
    </div>

    <section class="hero" aria-labelledby="page-title">
      <div class="eyebrow">Requirements quality gate</div>
      <h1 id="page-title">Find the gaps before implementation starts.</h1>
      <p>
        Run the deterministic gate first, or explicitly request an advisory AI review that adds
        contradiction analysis and a conservative improved-spec draft without changing gate status.
      </p>
    </section>

    <section class="workspace">
      <article class="panel">
        <div class="panel-head">
          <div>
            <h2 class="panel-title">Specification</h2>
            <div class="tiny">Ctrl / ⌘ + Enter runs the deterministic gate</div>
          </div>
          <button class="button" id="load-example" type="button">Load example</button>
        </div>
        <div class="editor-wrap">
          <label class="tiny" for="spec-input">Markdown or plain text</label>
          <textarea
            id="spec-input"
            spellcheck="false"
            placeholder="# Goal&#10;Describe the intended outcome..."
            aria-describedby="analysis-notice"
          ></textarea>
          <div class="actions">
            <button class="button accent" id="run-check" type="button">Analyze requirements</button>
            <button
              class="button primary" id="run-ai-review" type="button" disabled>AI Review</button>
            <button class="button" id="clear-input" type="button">Clear</button>
          </div>
          <div class="notice" id="analysis-notice" role="status" aria-live="polite">Ready.</div>
          <div class="privacy">
            <span class="privacy-dot" aria-hidden="true"></span>
            <span>
              Analyze requirements never calls AI. AI Review sends the current text only after an
              explicit click and only through the server-configured provider.
            </span>
          </div>
        </div>
      </article>

      <article class="panel" aria-labelledby="results-title">
        <div class="panel-head">
          <div>
            <h2 class="panel-title" id="results-title">Deterministic analysis</h2>
            <div class="tiny">Structured findings from <code>/v1/check</code></div>
          </div>
          <button class="button primary" id="copy-markdown" type="button" disabled>
            Copy Markdown
          </button>
        </div>

        <div class="summary" aria-label="Finding summary">
          <div class="metric"><strong id="metric-total">0</strong><span>Total</span></div>
          <div class="metric"><strong id="metric-errors">0</strong><span>Errors</span></div>
          <div class="metric"><strong id="metric-warnings">0</strong><span>Warnings</span></div>
          <div class="metric"><strong id="metric-info">0</strong><span>Info</span></div>
        </div>

        <div class="status-line">
          <span class="status-chip" id="report-status">Not analyzed</span>
          <span class="tiny" id="report-source">Source: web-ui</span>
        </div>

        <div class="filters" id="finding-filters" aria-label="Filter findings">
          <button class="filter" type="button" data-filter="all" aria-pressed="true">All</button>
          <button class="filter" type="button" data-filter="error" aria-pressed="false">
            Errors
          </button>
          <button class="filter" type="button" data-filter="warning" aria-pressed="false">
            Warnings
          </button>
          <button class="filter" type="button" data-filter="info" aria-pressed="false">Info</button>
        </div>

        <div class="findings" id="findings-list">
          <div class="empty">Run an analysis to see findings here.</div>
        </div>
      </article>
    </section>

    <section class="panel ai-panel" id="ai-review-section" aria-labelledby="ai-review-title">
      <div class="panel-head">
        <div>
          <h2 class="panel-title" id="ai-review-title">AI Review</h2>
          <div class="tiny">Advisory only · deterministic PASS/NEEDS WORK never changes</div>
        </div>
        <button class="button" id="refresh-ai-status" type="button">Refresh provider</button>
      </div>

      <div class="ai-status-row">
        <span class="status-chip disabled" id="ai-provider-status">Checking provider…</span>
        <span class="tiny" id="ai-provider-detail">Server configuration is being inspected.</span>
      </div>

      <div class="ai-grid">
        <section class="ai-column" aria-labelledby="contradictions-title">
          <div class="ai-column-head">
            <h3 id="contradictions-title">Contradictions</h3>
          </div>
          <div class="contradictions" id="contradictions-list">
            <div class="ai-empty">Run AI Review to inspect direct contradictions.</div>
          </div>
        </section>

        <section class="ai-column" aria-labelledby="improved-title">
          <div class="panel-head">
            <div>
              <h3 class="panel-title" id="improved-title">Improved specification draft</h3>
              <div class="tiny">Review before use. The model is not an authority.</div>
            </div>
            <div class="actions">
              <button class="button" id="copy-improved" type="button" disabled>Copy draft</button>
              <button class="button primary" id="use-improved" type="button" disabled>
                Use as input
              </button>
            </div>
          </div>
          <pre
            class="draft-output" id="improved-spec-output">Run AI Review to generate a draft.</pre>
        </section>
      </div>
    </section>
  </main>

  <script>
    "use strict";

    const input = document.getElementById("spec-input");
    const runButton = document.getElementById("run-check");
    const aiReviewButton = document.getElementById("run-ai-review");
    const clearButton = document.getElementById("clear-input");
    const loadExampleButton = document.getElementById("load-example");
    const copyButton = document.getElementById("copy-markdown");
    const copyImprovedButton = document.getElementById("copy-improved");
    const useImprovedButton = document.getElementById("use-improved");
    const refreshAIStatusButton = document.getElementById("refresh-ai-status");
    const notice = document.getElementById("analysis-notice");
    const findingsList = document.getElementById("findings-list");
    const statusChip = document.getElementById("report-status");
    const sourceLabel = document.getElementById("report-source");
    const aiProviderStatus = document.getElementById("ai-provider-status");
    const aiProviderDetail = document.getElementById("ai-provider-detail");
    const contradictionsList = document.getElementById("contradictions-list");
    const improvedSpecOutput = document.getElementById("improved-spec-output");
    const filters = Array.from(document.querySelectorAll("[data-filter]"));

    const metrics = {
      total: document.getElementById("metric-total"),
      errors: document.getElementById("metric-errors"),
      warnings: document.getElementById("metric-warnings"),
      info: document.getElementById("metric-info"),
    };

    const example = `# Goal
Allow an operator to export filtered orders to CSV.

# Expected result
A UTF-8 CSV file contains the same rows shown by the active filters.

# Acceptance criteria
- Export should work fast and correctly.

# Out of scope
- PDF export.

# Errors and edge cases
- Empty result sets return headers with no data rows.`;

    let activeFilter = "all";
    let report = null;
    let aiReview = null;
    let aiEnabled = false;
    let isBusy = false;

    function setNotice(message) {
      notice.textContent = message;
    }

    function setBusy(busy, mode) {
      isBusy = busy;
      runButton.disabled = busy;
      aiReviewButton.disabled = busy || !aiEnabled;
      refreshAIStatusButton.disabled = busy;
      runButton.textContent = busy && mode === "deterministic"
        ? "Analyzing…"
        : "Analyze requirements";
      aiReviewButton.textContent = busy && mode === "ai"
        ? "AI reviewing…"
        : "AI Review";
    }

    function resetReport() {
      report = null;
      copyButton.disabled = true;
      metrics.total.textContent = "0";
      metrics.errors.textContent = "0";
      metrics.warnings.textContent = "0";
      metrics.info.textContent = "0";
      statusChip.textContent = "Not analyzed";
      statusChip.className = "status-chip";
      sourceLabel.textContent = "Source: web-ui";
      renderFindings();
    }

    function resetAIReview() {
      aiReview = null;
      copyImprovedButton.disabled = true;
      useImprovedButton.disabled = true;
      improvedSpecOutput.textContent = "Run AI Review to generate a draft.";
      renderContradictions();
    }

    function renderSummary() {
      if (!report) {
        return;
      }
      metrics.total.textContent = String(report.summary.total);
      metrics.errors.textContent = String(report.summary.errors);
      metrics.warnings.textContent = String(report.summary.warnings);
      metrics.info.textContent = String(report.summary.info);
      statusChip.textContent = report.status;
      statusChip.className = "status-chip " + (report.status === "PASS" ? "pass" : "needs-work");
      sourceLabel.textContent = "Source: " + report.source;
    }

    function findingCard(finding) {
      const card = document.createElement("article");
      card.className = "finding " + finding.severity;

      const top = document.createElement("div");
      top.className = "finding-top";

      const rule = document.createElement("span");
      rule.className = "finding-id";
      rule.textContent = finding.rule_id;

      const meta = document.createElement("span");
      meta.className = "finding-meta";
      const location = finding.line === null ? "" : " · line " + finding.line;
      meta.textContent = finding.severity.toUpperCase() + location;

      const message = document.createElement("p");
      message.className = "finding-message";
      message.textContent = finding.message;

      const fix = document.createElement("p");
      fix.className = "finding-fix";
      fix.textContent = "Suggested fix: " + finding.suggestion;

      top.append(rule, meta);
      card.append(top, message, fix);

      if (finding.excerpt) {
        const excerpt = document.createElement("p");
        excerpt.className = "finding-fix";
        excerpt.textContent = "Excerpt: " + finding.excerpt;
        card.append(excerpt);
      }

      return card;
    }

    function renderFindings() {
      findingsList.replaceChildren();
      if (!report) {
        const empty = document.createElement("div");
        empty.className = "empty";
        empty.textContent = "Run an analysis to see findings here.";
        findingsList.append(empty);
        return;
      }

      const visible = report.findings.filter(
        (finding) => activeFilter === "all" || finding.severity === activeFilter,
      );

      if (visible.length === 0) {
        const empty = document.createElement("div");
        empty.className = "empty";
        empty.textContent = report.findings.length === 0
          ? "No findings. The deterministic gate passed."
          : "No findings match this filter.";
        findingsList.append(empty);
        return;
      }

      for (const finding of visible) {
        findingsList.append(findingCard(finding));
      }
    }

    function contradictionCard(item, index) {
      const card = document.createElement("article");
      card.className = "contradiction";

      const top = document.createElement("div");
      top.className = "contradiction-top";

      const label = document.createElement("span");
      label.className = "contradiction-id";
      label.textContent = "Contradiction " + String(index + 1);
      top.append(label);

      const statementA = document.createElement("p");
      statementA.className = "contradiction-copy";
      statementA.textContent = "A: “" + item.statement_a + "”";

      const statementB = document.createElement("p");
      statementB.className = "contradiction-copy";
      statementB.textContent = "B: “" + item.statement_b + "”";

      const explanation = document.createElement("p");
      explanation.className = "finding-message";
      explanation.textContent = item.explanation;

      card.append(top, statementA, statementB, explanation);
      return card;
    }

    function renderContradictions() {
      contradictionsList.replaceChildren();
      if (!aiReview) {
        const empty = document.createElement("div");
        empty.className = "ai-empty";
        empty.textContent = "Run AI Review to inspect direct contradictions.";
        contradictionsList.append(empty);
        return;
      }

      if (aiReview.contradictions.length === 0) {
        const empty = document.createElement("div");
        empty.className = "ai-empty";
        empty.textContent = "No direct contradictions were returned.";
        contradictionsList.append(empty);
        return;
      }

      aiReview.contradictions.forEach((item, index) => {
        contradictionsList.append(contradictionCard(item, index));
      });
    }

    function markdownReport(value) {
      const lines = [
        "# SpecForge Gate: " + value.status,
        "",
        "| Severity | Count |",
        "|---|---:|",
        "| Error | " + value.summary.errors + " |",
        "| Warning | " + value.summary.warnings + " |",
        "| Info | " + value.summary.info + " |",
      ];

      if (value.findings.length > 0) {
        lines.push("", "## Findings", "");
        for (const finding of value.findings) {
          const location = finding.line === null ? "" : " (line " + finding.line + ")";
          lines.push(
            "### `" + finding.rule_id + "` · " + finding.severity + location,
            "",
            finding.message,
            "",
            "**Suggested fix:** " + finding.suggestion,
            "",
          );
        }
      }
      return lines.join("\n").trimEnd() + "\n";
    }

    function apiError(payload, status) {
      if (payload && payload.detail && typeof payload.detail === "object") {
        const detail = payload.detail;
        if (detail.message) {
          return detail.message + (detail.line ? " (line " + detail.line + ")" : "");
        }
        if (detail.code === "text_too_large") {
          return "Input exceeds the configured limit of " + detail.max_chars + " characters.";
        }
        if (detail.code === "ai_not_configured") {
          return "AI Review is not configured on this server.";
        }
        if (detail.code) {
          return "AI Review failed: " + detail.code + ".";
        }
      }
      return "Request failed with HTTP " + status + ".";
    }

    async function refreshAIStatus() {
      if (isBusy) {
        return;
      }
      aiProviderStatus.textContent = "Checking provider…";
      aiProviderStatus.className = "status-chip disabled";
      aiProviderDetail.textContent = "Server configuration is being inspected.";
      aiEnabled = false;
      aiReviewButton.disabled = true;

      try {
        const response = await fetch("/v1/ai/status", {method: "GET"});
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(apiError(payload, response.status));
        }

        aiEnabled = payload.enabled === true;
        if (aiEnabled) {
          aiProviderStatus.textContent = "AI enabled";
          aiProviderStatus.className = "status-chip enabled";
          aiProviderDetail.textContent = (
            "Provider: " + payload.provider + " \u00b7 Model: " + payload.model
          );
        } else {
          aiProviderStatus.textContent = "AI disabled";
          aiProviderStatus.className = "status-chip disabled";
          aiProviderDetail.textContent = "Configure a server-side provider to enable AI Review.";
        }
      } catch (error) {
        aiProviderStatus.textContent = "AI unavailable";
        aiProviderStatus.className = "status-chip disabled";
        aiProviderDetail.textContent = error instanceof Error
          ? error.message
          : "Could not read AI provider status.";
      } finally {
        aiReviewButton.disabled = !aiEnabled || isBusy;
      }
    }

    async function runAnalysis() {
      const text = input.value;
      if (!text.trim()) {
        setNotice("Paste a specification before running the gate.");
        input.focus();
        return;
      }

      setBusy(true, "deterministic");
      setNotice("Running deterministic checks…");
      try {
        const response = await fetch("/v1/check", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({text, source: "web-ui"}),
        });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(apiError(payload, response.status));
        }
        report = payload;
        copyButton.disabled = false;
        renderSummary();
        renderFindings();
        setNotice("Analysis complete: " + report.summary.total + " finding(s).");
      } catch (error) {
        setNotice(error instanceof Error ? error.message : "Analysis failed.");
      } finally {
        setBusy(false, "deterministic");
      }
    }

    async function runAIReview() {
      const text = input.value;
      if (!text.trim()) {
        setNotice("Paste a specification before requesting AI Review.");
        input.focus();
        return;
      }
      if (!aiEnabled) {
        setNotice("AI Review is not configured on this server.");
        return;
      }

      setBusy(true, "ai");
      setNotice("Running deterministic checks and advisory AI review…");
      try {
        const response = await fetch("/v1/ai/review", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({text, source: "web-ui"}),
        });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(apiError(payload, response.status));
        }

        report = payload.deterministic;
        aiReview = payload;
        copyButton.disabled = false;
        copyImprovedButton.disabled = false;
        useImprovedButton.disabled = false;
        renderSummary();
        renderFindings();
        renderContradictions();
        improvedSpecOutput.textContent = aiReview.improved_spec;
        aiProviderStatus.textContent = "AI enabled";
        aiProviderStatus.className = "status-chip enabled";
        aiProviderDetail.textContent = (
          "Provider: " + aiReview.provider + " \u00b7 Model: " + aiReview.model
        );
        setNotice(
          "AI review complete: "
          + String(aiReview.contradictions.length)
          + " contradiction(s), draft ready for review.",
        );
      } catch (error) {
        setNotice(error instanceof Error ? error.message : "AI Review failed.");
      } finally {
        setBusy(false, "ai");
      }
    }

    runButton.addEventListener("click", runAnalysis);
    aiReviewButton.addEventListener("click", runAIReview);
    refreshAIStatusButton.addEventListener("click", refreshAIStatus);

    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        runAnalysis();
      }
    });

    input.addEventListener("input", () => {
      if (report || aiReview) {
        resetReport();
        resetAIReview();
        setNotice("Input changed. Previous results were cleared.");
      }
    });

    clearButton.addEventListener("click", () => {
      input.value = "";
      resetReport();
      resetAIReview();
      input.focus();
      setNotice("Input cleared.");
    });

    loadExampleButton.addEventListener("click", () => {
      input.value = example;
      resetReport();
      resetAIReview();
      input.focus();
      setNotice("Example loaded. Analyze it or request AI Review.");
    });

    for (const filterButton of filters) {
      filterButton.addEventListener("click", () => {
        activeFilter = filterButton.dataset.filter || "all";
        for (const item of filters) {
          item.setAttribute("aria-pressed", String(item === filterButton));
        }
        renderFindings();
      });
    }

    copyButton.addEventListener("click", async () => {
      if (!report) {
        return;
      }
      try {
        await navigator.clipboard.writeText(markdownReport(report));
        setNotice("Markdown report copied to clipboard.");
      } catch (_error) {
        setNotice("Clipboard access was denied by the browser.");
      }
    });

    copyImprovedButton.addEventListener("click", async () => {
      if (!aiReview) {
        return;
      }
      try {
        await navigator.clipboard.writeText(aiReview.improved_spec);
        setNotice("Improved specification draft copied to clipboard.");
      } catch (_error) {
        setNotice("Clipboard access was denied by the browser.");
      }
    });

    useImprovedButton.addEventListener("click", () => {
      if (!aiReview) {
        return;
      }
      const draft = aiReview.improved_spec;
      input.value = draft;
      resetReport();
      resetAIReview();
      input.focus();
      setNotice("Improved draft loaded as input. Review it, then run the gate again.");
    });

    refreshAIStatus();
  </script>
</body>
</html>
'''
