#!/usr/bin/env python3
"""Annotate the frozen P1/P2 matrix with P3 RV64 and S01/S03 dispositions."""
import gzip
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
CCR = ROOT / "npc/verif/records/process/code_correctness_review"
OUT = CCR / "p3"
MATRIX = CCR / "coverage.jsonl"
BEFORE = OUT / "coverage.before.jsonl.gz"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def digest_row(path, row):
    if row["source_status"] != "present":
        return "unavailable"
    if path.is_symlink():
        return hashlib.sha256(os.readlink(path).encode()).hexdigest()
    return sha(path)


def disposition(row):
    path, module = row["path"], row["module_id"]
    if path == "nemu/resource/mips-elf/README.md":
        return "S06ExcludedIdentity", "MIPS专属资源说明；S06仅RV64，原P1保留行在P3更正为批准排除。"
    if module == "N14":
        cls = row.get("classification")
        if path == "nemu/tools/spike-diff/repo/spike_dasm/spike_dasm_option_parser.cc":
            return "S01DeletedSymlink", "本地删除是可见差异；仅属独立spike_dasm，不参与NEMU→Spike共享库链；原HEAD链接目标仍可查，未把缺失当已审函数。"
        if cls == "upstream_or_mixed_source":
            return "S01UpstreamBoundary", "固定Spike/kconfig/fixdep来源和工作树差异；NEMU实际调用的adapter/API已单独审。无关上游函数按S01不逐函数审。"
        if cls == "generated_or_build_artifact":
            return "S03ArtifactBoundary", "身份/哈希及声明的生成与消费链已核；历史产物与当前源码/config/flags精确配对Unknown，P9/P10复核。"
        if cls == "git_metadata":
            return "S01GitMetadata", "仅导航嵌套仓库身份；不把objects/index/config当可执行源码。"
        return "S01S03Navigation", "说明、配置或资源身份已登记，相关RV64源码/生成消费链在对应行审阅。"
    if module == "N01":
        return "ReviewedStatic", "Kconfig选择RV64 native/AM/shared、DEVICE和REF条件；Make/filelist及生成头入口与副作用已核。"
    if module == "N08":
        return "ReviewedStatic", "new_space/MMIO映射、范围、更新/中断、native/AM分支和重复初始化责任已核。"
    if module == "N09":
        return "ReviewedStatic", "serial/RTC/mtime/keyboard/VGA/audio/disk/SD卡的地址、宽度、回调、长度、状态与错误路径已核。"
    if module == "N10":
        return "ReviewedStatic", "native/AM装载、参数、表达式、watchpoint、trace/snapshot、exit/quit调用链已核。"
    if module == "N11":
        return "ReviewedStatic", "NEMU DUT、NPC REF、Spike golden及可选QEMU适配的ABI/PC/内存/skip/attach限制已核。"
    if module == "N12":
        return "ReviewedStatic", "宿主log/时钟/随机/LLVM反汇编与gen-expr判据已核；CPU/类型旧责任沿P2。"
    if module == "N13":
        return "ReviewedStatic", "RV64测试实际oracle/skip/退出；SD卡驱动MMIO接线与资源来源已核，历史PASS未复用为本次结果。"
    if module == "X02":
        return "InterfaceReviewed", "仅NPC REF loader/33字寄存器/内存/skip及配置接口；完整NPC RTL留P9或业务范围。"
    raise AssertionError((module, path))


def main():
    OUT.mkdir(exist_ok=True)
    if not BEFORE.exists():
        with MATRIX.open("rb") as src, gzip.open(BEFORE, "wb", compresslevel=6) as dst:
            for chunk in iter(lambda: src.read(1 << 20), b""):
                dst.write(chunk)
    with gzip.open(BEFORE, "rb") as source:
        h = hashlib.sha256()
        for chunk in iter(lambda: source.read(1 << 20), b""):
            h.update(chunk)
        before_sha = h.hexdigest()
    findings = json.loads((OUT / "findings.json").read_text())
    bypath = defaultdict(list)
    for issue in findings:
        for location in issue["locations"]:
            bypath[location["path"]].append(issue["id"])

    tmp = MATRIX.with_suffix(".p3.tmp")
    file_review = OUT / "file-review.jsonl"
    branch_review = OUT / "branch-review.jsonl"
    loader_supplement = OUT / "n02-loader-supplement.jsonl"
    counts = Counter()
    module_counts = defaultdict(Counter)
    drift = []
    file_sha = {}
    with gzip.open(BEFORE, "rt") as src, tmp.open("w") as dst, file_review.open("w") as files, branch_review.open("w") as branches, loader_supplement.open("w") as loader_rows:
        for line in src:
            row = json.loads(line)
            if row["module_id"] == "N02" and row["row_kind"] == "file" and row["path"] in (
                    "nemu/src/am-bin.S", "nemu/src/nemu-main.c"):
                actual = digest_row(ROOT / row["path"], row)
                if actual != row.get("source_sha256"):
                    drift.append({"path": row["path"], "expected": row.get("source_sha256"), "actual": actual})
                row["p3_loader_supplement"] = {
                    "responsibility": "NEMU host AM embedded image symbol/entry and native monitor handoff only; CPU execution remains P2",
                    "disposition": "ReviewedStatic", "source_identity": actual,
                    "validation": "NotRun", "evidence": "P3.md / p3/n02-loader-supplement.jsonl"}
                loader_rows.write(json.dumps({"row_id": row["row_id"], "path": row["path"],
                                             **row["p3_loader_supplement"]}, ensure_ascii=False) + "\n")
                dst.write(json.dumps(row, ensure_ascii=False) + "\n")
                continue
            if row.get("effective_phase") != "CCR-P3" or row.get("review_status") == "Excluded":
                dst.write(line)
                continue
            status, rationale = disposition(row)
            path = row["path"]
            if row["row_kind"] == "file":
                actual = digest_row(ROOT / path, row)
                expected = row.get("source_sha256")
                if actual != expected and not (actual == "unavailable" and row["source_status"] != "present"):
                    drift.append({"path": path, "expected": expected, "actual": actual})
                file_sha[path] = actual
            else:
                actual = file_sha.get(path, row.get("source_sha256"))
            if status == "S06ExcludedIdentity":
                prior_scope = {k: row.get(k) for k in ("effective_phase", "effective_phase_responsibilities",
                             "review_config", "review_profiles", "scope_reason")}
                row["review_status"] = "Excluded"
                row["effective_phase"] = None
                row["effective_phase_responsibilities"] = {}
                row["review_config"] = []
                row["review_profiles"] = []
                row["scope_reason"] = "MIPS-only resource description; Excluded under approved S06 RV64 scope"
                row["scope_approval"]["p3_correction"] = "SCOPE_RV64.md#s06-clarification-20261017"
                row["scope_approval"]["current_depth"] = "Historical identity only; outside current RV64 review denominator"
            else:
                row["review_status"] = "Reviewed"
            ids = sorted(set(bypath.get(path, [])))
            row["issue_ids"] = sorted(set(row.get("issue_ids", []) + ids))
            row["evidence_ids"] = sorted(set(row.get("evidence_ids", []) + ["CCR-E-P3-static", "CCR-E-P3-matrix"]))
            row["p3_review"] = {"disposition": status, "rationale": rationale,
                                "source_identity": actual, "issue_ids": ids,
                                "validation": "NotRun; static review only", "evidence": "P3.md / p3/source-evidence.json"}
            if status == "S06ExcludedIdentity":
                row["p3_review"]["prior_scope"] = prior_scope
            if row["row_kind"] == "conditional_path":
                row["p3_review"]["condition"] = row["function_or_path"]
                row["p3_review"]["condition_note"] = (
                    "结构/endif无独立行为；相关RV64 native/AM/shared分支按P3.md判定"
                    if row["function_or_path"].strip().startswith("#endif") else
                    "仅RV64有效臂/本阶段宿主支撑；当前配置与候选变体分开，其他ISA分支不计已审")
                branches.write(json.dumps({"row_id": row["row_id"], "module_id": row["module_id"],
                                           "path": path, "line_range": row["line_range"],
                                           "condition": row["function_or_path"],
                                           "disposition": status, "rationale": row["p3_review"]["condition_note"],
                                           "evidence": "P3.md"}, ensure_ascii=False) + "\n")
            else:
                row["normal"] = f"CCR-P3: {rationale}"
                row["boundary_zero_empty_invalid"] = f"CCR-P3: {rationale}"
                row["failure_state_return_cleanup"] = f"CCR-P3: {rationale}"
                row["integer_alignment_lifetime"] = f"CCR-P3: {rationale}"
                row["init_repeat"] = f"CCR-P3: {rationale}"
                row["conditional_upstream_downstream"] = f"CCR-P3: {rationale}"
                row["limits"] = list(dict.fromkeys(row.get("limits", []) + [
                    "P3仅静态审阅；历史build/REF/GUI/音频的源码配置配对及动态行为未获本轮证明"] ))
                files.write(json.dumps({"row_id": row["row_id"], "module_id": row["module_id"],
                                        "path": path, "source_sha256": actual,
                                        "disposition": status, "rationale": rationale,
                                        "issue_ids": ids, "validation": "NotRun",
                                        "evidence": "P3.md"}, ensure_ascii=False) + "\n")
            counts[row["row_kind"]] += 1
            module_counts[row["module_id"]][status] += 1
            dst.write(json.dumps(row, ensure_ascii=False) + "\n")
    if drift:
        tmp.unlink()
        raise RuntimeError(f"P1 source identity drift: {len(drift)}; first={drift[:4]}")
    os.replace(tmp, MATRIX)
    result = {"date": "2026-10-17", "head": "9918989", "coverage_before_sha256": before_sha,
              "coverage_after_sha256": sha(MATRIX), "file_rows": counts["file"],
              "conditional_rows": counts["conditional_path"],
              "module_dispositions": {k: dict(v) for k, v in module_counts.items()},
              "source_identity_drift": drift, "dynamic_validation": "NotRun",
              "scope_correction": "N13 mips-elf README Excluded under S06; no other scope changes",
              "n02_loader_supplement_rows": 2}
    (OUT / "source-evidence.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"file_rows": result["file_rows"], "conditional_rows": result["conditional_rows"],
                      "drift": len(drift), "status": "P3 static annotated"}))


if __name__ == "__main__":
    main()
