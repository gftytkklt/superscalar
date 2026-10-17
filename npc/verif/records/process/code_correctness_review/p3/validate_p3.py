#!/usr/bin/env python3
"""Structural Final Gate for CCR-P3; does not execute guest/device behavior."""
import gzip
import hashlib
import json
import os
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
CCR = ROOT / "npc/verif/records/process/code_correctness_review"
OUT = CCR / "p3"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check(name, condition, checks):
    checks.append({"check": name, "pass": bool(condition)})


def main():
    checks = []
    source = json.loads((OUT / "source-evidence.json").read_text())
    with gzip.open(OUT / "coverage.before.jsonl.gz", "rb") as stream:
        before_digest = hashlib.sha256(stream.read()).hexdigest()
    check("original matrix digest", before_digest == source["coverage_before_sha256"], checks)
    check("current matrix digest", digest(CCR / "coverage.jsonl") == source["coverage_after_sha256"], checks)
    check("source identity drift empty", not source["source_identity_drift"], checks)

    p3_file = p3_branch = n02 = total = 0
    out_file = list(map(json.loads, (OUT / "file-review.jsonl").open()))
    out_branch = list(map(json.loads, (OUT / "branch-review.jsonl").open()))
    out_n02 = list(map(json.loads, (OUT / "n02-loader-supplement.jsonl").open()))
    file_ids, branch_ids = set(), set()
    module_counts = Counter()
    scope_corrected = 0
    with gzip.open(OUT / "coverage.before.jsonl.gz", "rt") as old, (CCR / "coverage.jsonl").open() as new:
        for prior_line, after_line in zip(old, new):
            prior, after = json.loads(prior_line), json.loads(after_line)
            total += 1
            check_fields = ("row_id", "row_kind", "module_id", "path", "source_sha256")
            if any(prior.get(k) != after.get(k) for k in check_fields):
                raise AssertionError(f"identity/phase changed: {prior['row_id']}")
            if prior["path"] != "nemu/resource/mips-elf/README.md":
                assert prior.get("effective_phase") == after.get("effective_phase")
            if prior["effective_phase"] == "CCR-P3" and prior["review_status"] != "Excluded":
                review = after.get("p3_review", {})
                assert review.get("disposition") and review.get("validation") == "NotRun; static review only"
                module_counts[(after["module_id"], review["disposition"])] += 1
                if after["row_kind"] == "file":
                    p3_file += 1
                    file_ids.add(after["row_id"])
                    path = ROOT / after["path"]
                    actual = (hashlib.sha256(os.readlink(path).encode()).hexdigest() if path.is_symlink()
                              else digest(path) if path.is_file() else "unavailable")
                    assert actual == review["source_identity"]
                    if review["disposition"] == "S06ExcludedIdentity":
                        scope_corrected += 1
                        assert after["review_status"] == "Excluded"
                        assert after["effective_phase"] is None and not after["review_profiles"]
                        assert review["prior_scope"]["effective_phase"] == "CCR-P3"
                    else:
                        assert after["review_status"] == "Reviewed"
                else:
                    p3_branch += 1
                    branch_ids.add(after["row_id"])
            elif prior["module_id"] == "N02" and prior["row_kind"] == "file" and prior["path"] in (
                    "nemu/src/am-bin.S", "nemu/src/nemu-main.c"):
                n02 += 1
                assert after.get("p3_loader_supplement", {}).get("disposition") == "ReviewedStatic"
                assert prior["review_status"] == after["review_status"]
            else:
                assert prior == after, f"outside P3 changed: {prior['row_id']}"
        assert next(old, None) is None and next(new, None) is None
    check("matrix identity and allowed change only", total == 40010, checks)
    check("P3 file and conditional denominator", (p3_file, p3_branch) == (2612, 1183), checks)
    check("N02 loader supplement, no phase reassignment", n02 == 2 and len(out_n02) == 2, checks)
    check("individual P3 file/condition evidence", file_ids == {x["row_id"] for x in out_file}
          and branch_ids == {x["row_id"] for x in out_branch}, checks)
    check("one approved S06 correction", scope_corrected == 1, checks)
    check("module dispositions", module_counts == Counter({(m, d): n for m, ds in
          source["module_dispositions"].items() for d, n in ds.items()}), checks)

    issues = json.loads((CCR / "findings.json").read_text())
    p3_issues = json.loads((OUT / "findings.json").read_text())
    check("stable finding IDs and counts", len(issues) == 22 and len(p3_issues) == 14
          and [v["id"] for v in issues] == [f"CCR-F{i:04d}" for i in range(1, 23)]
          and issues[8:] == p3_issues, checks)
    for issue in p3_issues:
        for location in issue["locations"]:
            assert digest(ROOT / location["path"]) == location["sha256"]
            assert all(1 <= line <= sum(1 for _ in (ROOT / location["path"]).open(errors="replace"))
                       for line in location["lines"])
    check("finding source hashes and line bounds", True, checks)

    head = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).strip()
    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True)
    changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines()
    check("P2 commit remains HEAD and P3 unstaged", head == "9918989" and not staged, checks)
    check("tracked edits only navigation docs", set(changed) <= {
        "README.md", "npc/README.md", "npc/verif/README.md", "npc/verif/records/README.md",
        "npc/verif/records/process/README.md"}, checks)
    check("tracked whitespace", diff_check.returncode == 0, checks)
    check("no P4 start", "P4 仍未获执行授权" in (CCR / "P3.md").read_text()
          and "CCR-P4 | Next/Planned，未Start" in (ROOT / ".agent/TASK_QUEUE.md").read_text(), checks)
    links = ("P3.md", "COVERAGE.md", "FINDINGS.md", "p3/README.md",
             "p3/source-evidence.json", "p3/file-review.jsonl", "p3/branch-review.jsonl",
             "p3/n02-loader-supplement.jsonl", "p3/findings.json", "p3/coverage.before.jsonl.gz")
    check("P3 primary evidence present", all((CCR / path).exists() for path in links), checks)
    result = {"date": "2026-10-17", "phase": "CCR-P3", "head": head,
              "status": "PASS" if all(x["pass"] for x in checks) else "FAIL",
              "checks": checks, "counts": {"matrix_rows": total, "p3_files": p3_file,
              "p3_conditional_rows": p3_branch, "n02_loader_supplement": n02,
              "s06_corrected": scope_corrected, "p3_findings": len(p3_issues)},
              "dynamic_tests": 0, "production_edits": 0, "installs": 0, "p3_commits": 0,
              "limits": "Structural/source-identity gate only; static correctness conclusions in P3.md, no device/guest/REF dynamic result."}
    (OUT / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "checks": len(checks), **result["counts"]}))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
