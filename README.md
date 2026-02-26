# Attune AI Action

AI-powered code review and release prep for your CI/CD pipeline, powered by [Attune AI](https://github.com/Smart-AI-Memory/attune-ai) and Claude.

Smart tier routing automatically optimizes LLM costs (34-86% savings) while maintaining quality.

## Quick Start

### Code Review on PRs

```yaml
name: Attune Code Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - uses: Smart-AI-Memory/attune-ai-action@v1
        with:
          workflow: code-review
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Release Prep on Tags

```yaml
name: Attune Release Prep
on:
  push:
    tags: ['v*']

jobs:
  release-prep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: Smart-AI-Memory/attune-ai-action@v1
        with:
          workflow: release-prep
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          fail_on_critical: 'true'
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `workflow` | Yes | - | `code-review` or `release-prep` |
| `anthropic_api_key` | Yes | - | Your Anthropic API key |
| `python_version` | No | `3.12` | Python version |
| `attune_version` | No | `latest` | Attune AI version |
| `tier_strategy` | No | `auto` | Cost tier: `auto`, `cheap`, `capable`, `premium` |
| `fail_on_critical` | No | `true` | Fail action on critical issues |
| `config` | No | - | Path to attune config file |

## Outputs

| Output | Description |
|--------|-------------|
| `report` | Path to generated report |
| `summary` | Brief summary of findings |
| `issues_found` | Number of issues found |
| `cost_saved` | Estimated cost savings from tier routing |

## Cost Optimization

Attune AI routes prompts through smart tiers (CHEAP -> CAPABLE -> PREMIUM), only escalating when complexity requires it. In CI, this means routine reviews use cheaper models while critical security findings get premium attention — saving 34-86% vs. using the most expensive model for everything.

Set `tier_strategy` to control this:
- `auto` (default) — Attune decides based on complexity
- `cheap` — minimize cost, good for quick checks
- `capable` — balanced quality and cost
- `premium` — maximum quality, use for release-critical reviews

## License

Apache 2.0 — same as [Attune AI](https://github.com/Smart-AI-Memory/attune-ai).
