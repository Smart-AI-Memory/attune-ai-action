#!/usr/bin/env python3
"""
Attune AI GitHub Action runner.
Executes Attune workflows in CI mode and generates reports.
"""

import argparse
import json
import os
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Attune AI workflows in CI")
    parser.add_argument(
        "--workflow",
        required=True,
        choices=["code-review", "release-prep"],
        help="Attune workflow to execute",
    )
    parser.add_argument(
        "--config",
        default="",
        help="Path to attune config file",
    )
    parser.add_argument(
        "--fail-on-critical",
        default="true",
        help="Fail if critical issues found",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for output reports",
    )
    return parser.parse_args()


def run_code_review(output_dir: Path, config: str) -> dict:
    """Run the code-review workflow in CI mode."""
    from attune.workflows import WorkflowEngine
    from attune.workflows.registry import get_workflow

    engine = WorkflowEngine(ci_mode=True)
    workflow = get_workflow("code-review")

    # Get changed files from git
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1"],
        capture_output=True,
        text=True,
    )
    changed_files = [f for f in result.stdout.strip().split("\n") if f]

    if not changed_files:
        return {
            "summary": "No changed files detected.",
            "issues_found": 0,
            "cost_saved": "N/A",
        }

    # Run review on changed files
    report = engine.run(
        workflow,
        files=changed_files,
        output_format="markdown",
    )

    # Write report
    report_path = output_dir / "code-review-report.md"
    report_path.write_text(report.to_markdown())

    # Write summary for GitHub step summary
    summary_path = output_dir / "summary.md"
    summary_path.write_text(
        f"## Attune AI Code Review\n\n"
        f"**Files reviewed:** {len(changed_files)}\n\n"
        f"**Issues found:** {report.issue_count}\n\n"
        f"**Critical:** {report.critical_count} | "
        f"**Warning:** {report.warning_count} | "
        f"**Info:** {report.info_count}\n\n"
        f"**Cost tier used:** {report.tier_used}\n\n"
        f"**Estimated savings:** {report.cost_savings}\n\n"
        f"See full report in artifacts.\n"
    )

    return {
        "summary": f"{report.issue_count} issues found in {len(changed_files)} files",
        "issues_found": report.issue_count,
        "critical_count": report.critical_count,
        "cost_saved": report.cost_savings,
    }


def run_release_prep(output_dir: Path, config: str) -> dict:
    """Run the release-prep workflow in CI mode."""
    from attune.workflows import WorkflowEngine
    from attune.workflows.registry import get_workflow

    engine = WorkflowEngine(ci_mode=True)
    workflow = get_workflow("release-prep")

    report = engine.run(
        workflow,
        output_format="markdown",
    )

    # Write report
    report_path = output_dir / "release-prep-report.md"
    report_path.write_text(report.to_markdown())

    # Write summary
    summary_path = output_dir / "summary.md"
    summary_path.write_text(
        f"## Attune AI Release Prep\n\n"
        f"**Security audit:** {report.security_status}\n\n"
        f"**Test coverage:** {report.test_coverage}\n\n"
        f"**Changelog generated:** {'Yes' if report.changelog else 'No'}\n\n"
        f"**Quality gates passed:** {report.gates_passed}/{report.gates_total}\n\n"
        f"**Cost tier used:** {report.tier_used}\n\n"
        f"**Estimated savings:** {report.cost_savings}\n\n"
        f"See full report in artifacts.\n"
    )

    return {
        "summary": f"Release prep complete: {report.gates_passed}/{report.gates_total} gates passed",
        "issues_found": report.gates_total - report.gates_passed,
        "cost_saved": report.cost_savings,
    }


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workflow_runners = {
        "code-review": run_code_review,
        "release-prep": run_release_prep,
    }

    runner = workflow_runners[args.workflow]

    try:
        result = runner(output_dir, args.config)
    except Exception as e:
        # Write error summary
        summary_path = output_dir / "summary.md"
        summary_path.write_text(
            f"## Attune AI - Error\n\n"
            f"Workflow `{args.workflow}` failed:\n\n"
            f"```\n{e}\n```\n"
        )
        print(f"::error::Attune workflow failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Set outputs via GitHub Actions output mechanism
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"report={output_dir}\n")
            f.write(f"summary={result['summary']}\n")
            f.write(f"issues_found={result['issues_found']}\n")
            f.write(f"cost_saved={result.get('cost_saved', 'N/A')}\n")

    # Fail if critical issues and fail_on_critical is set
    if args.fail_on_critical == "true" and result.get("critical_count", 0) > 0:
        print(
            f"::error::Found {result['critical_count']} critical issues. "
            f"Set fail_on_critical to false to ignore.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Attune workflow completed: {result['summary']}")


if __name__ == "__main__":
    main()
