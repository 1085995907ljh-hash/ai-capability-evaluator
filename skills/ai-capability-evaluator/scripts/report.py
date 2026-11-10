#!/usr/bin/env python3
"""Validate and render evidence-backed AI capability reviews using only stdlib.

This validates structural consistency, not the truth of evidence, the fairness of
judgment, or actual context isolation. Agent IDs/fresh flags are provenance claims
that the orchestrator must substantiate with real runtime records.
"""
import argparse
import html
import hashlib
import os
import json
import sys
from pathlib import Path

LEVELS = {"Assisted", "L1", "L2", "L3", "L4"}
def fail(path, message):
    raise ValueError(f"{path}: {message}")


def obj(value, path):
    if not isinstance(value, dict):
        fail(path, "expected object")
    return value


def arr(value, path, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value):
        fail(path, "expected " + ("non-empty " if nonempty else "") + "array")
    return value


def string(value, path):
    if not isinstance(value, str) or not value.strip():
        fail(path, "expected non-empty string")
    return value


def strings(value, path):
    for index, item in enumerate(arr(value, path)):
        string(item, f"{path}[{index}]")
    return value


def choice(value, choices, path):
    if not isinstance(value, str) or value not in choices:
        fail(path, "unknown value")


def validate(data):
    """Validate structure, not the truth of evidence or model judgment."""
    obj(data, "report")
    for key, version in (("schema_version", "2.0"), ("rubric_version", "1.1")):
        if data.get(key) != version:
            fail(key, "expected " + version)
    for obsolete in ("audit", "rounds"):
        if obsolete in data:
            fail(obsolete, "obsolete audit fields; fresh scoring migration required")
    if type(data.get("demo")) is not bool:
        fail("demo", "expected boolean")
    candidate = obj(data.get("candidate"), "candidate")
    for key in ("id", "name"):
        string(candidate.get(key), "candidate." + key)
    material_ids = set()
    for i, material in enumerate(arr(data.get("materials"), "materials")):
        path = f"materials[{i}]"
        obj(material, path)
        for key in ("id", "label", "format", "coverage"):
            string(material.get(key), path + "." + key)
        if material["id"] in material_ids:
            fail(path, "duplicate material ID")
        material_ids.add(material["id"])
        strings(material.get("limitations"), path + ".limitations")
    evidence_by_id = {}
    for i, item in enumerate(arr(data.get("evidence"), "evidence")):
        path = f"evidence[{i}]"
        obj(item, path)
        for key in ("id", "material_id", "locator", "observation"):
            string(item.get(key), path + "." + key)
        if item["id"] in evidence_by_id:
            fail(path, "duplicate evidence ID")
        if item["material_id"] not in material_ids:
            fail(path, "unknown material ID")
        evidence_by_id[item["id"]] = item
        choice(item.get("kind"), {"artifact", "self_report", "inference"}, path + ".kind")
        for key in ("supports", "limits"):
            strings(item.get(key), path + "." + key)
    understanding = obj(data.get("understanding"), "understanding")
    for key in ("work_summary", "contribution"):
        string(understanding.get(key), "understanding." + key)
    strings(understanding.get("limitations"), "understanding.limitations")

    def refs(value, path):
        strings(value, path)
        if len(set(value)) != len(value):
            fail(path, "duplicate evidence reference")
        if any(eid not in evidence_by_id for eid in value):
            fail(path, "unknown evidence ID")

    assessment = obj(data.get("assessment"), "assessment")
    choice(assessment.get("proposed_level"), LEVELS, "assessment.proposed_level")
    choice(assessment.get("rating_status"), {"supported", "provisional"}, "assessment.rating_status")
    choice(assessment.get("confidence"), {"high", "medium", "low"}, "assessment.confidence")
    strings(assessment.get("evidence_gaps"), "assessment.evidence_gaps")
    reason = string(assessment.get("reason"), "assessment.reason")
    if not 160 <= sum(not c.isspace() for c in reason) <= 260:
        fail("assessment.reason", "expected 160–260 non-whitespace characters")
    for key in ("level_explanation", "higher_level_explanation"):
        string(assessment.get(key), "assessment." + key)
    if "dimensions" in assessment:
        fail("assessment.dimensions", "obsolete dimension fields")
    provisional = assessment["rating_status"] == "provisional"
    if provisional:
        if assessment["proposed_level"] != "Assisted" or assessment["confidence"] != "low":
            fail("assessment", "provisional floor requires Assisted and low confidence")
        if not assessment["evidence_gaps"]:
            fail("assessment.evidence_gaps", "provisional floor requires explicit gaps")
        for key in ("reason", "level_explanation"):
            if "暂定" not in assessment[key] and "provisional" not in assessment[key].lower():
                fail("assessment." + key, "provisional disclosure required")
    reviewed = []
    for i, review in enumerate(arr(assessment.get("material_reviews"), "assessment.material_reviews")):
        path = f"assessment.material_reviews[{i}]"
        obj(review, path)
        mid = string(review.get("material_id"), path + ".material_id")
        if mid not in material_ids or mid in reviewed:
            fail(path, "unknown or duplicate material review")
        reviewed.append(mid)
        for key in ("summary", "interpretation", "limitation"):
            string(review.get(key), path + "." + key)
        refs(review.get("evidence_ids"), path + ".evidence_ids")
        if any(evidence_by_id[eid]["material_id"] != mid for eid in review["evidence_ids"]):
            fail(path, "citation belongs to another material")
    if reviewed != [m["id"] for m in data["materials"]]:
        fail("assessment.material_reviews", "every material needs its own review in input order")
    basis = arr(assessment.get("level_basis"), "assessment.level_basis")
    if not provisional and not basis:
        fail("assessment.level_basis", "supported grade requires level basis")
    for i, item in enumerate(basis):
        path = f"assessment.level_basis[{i}]"
        obj(item, path)
        for key in ("criterion", "finding"):
            string(item.get(key), path + "." + key)
        refs(item.get("evidence_ids"), path + ".evidence_ids")
        if not provisional and not item["evidence_ids"]:
            fail(path, "supported criterion requires evidence")
    evaluation = obj(data.get("evaluation"), "evaluation")
    for key in ("scorer_id", "context_mode", "packet_version"):
        string(evaluation.get(key), "evaluation." + key)
    if evaluation.get("scorer_fresh") is not True:
        fail("evaluation.scorer_fresh", "fresh scorer context required")
    return data


def esc(value):
    return html.escape(str(value), quote=True)


def bullets(items, empty="无"):
    return "<ul>" + "".join("<li>" + esc(item) + "</li>" for item in items) + "</ul>" if items else "<p class=muted>" + esc(empty) + "</p>"


def candidate_name(data):
    name = data["candidate"]["name"]
    if data["demo"] and "虚构" not in name:
        return "演示·虚构样例：" + name
    return name


def summary_text(data):
    validate(data)
    return f"候选人：{candidate_name(data)}\n等级：{data['assessment']['proposed_level']}\n理由：{data['assessment']['reason']}"


def report_fingerprint(data):
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


STYLE = """
:root{color-scheme:light;--ink:#202c2b;--muted:#63716f;--line:#dce4df;--accent:#245b4a;--paper:#fff;--bg:#f2f5f2}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.75 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
main{max-width:1060px;margin:40px auto;padding:0 28px 56px}header{border-bottom:2px solid var(--ink);padding-bottom:20px;margin-bottom:32px}h1{font-size:30px;line-height:1.35;margin:6px 0 12px;font-weight:650}h2{font-size:23px;line-height:1.4;margin:0 0 24px}h3{font-size:17px;margin:26px 0 10px}p{margin:8px 0 14px;overflow-wrap:anywhere}section{background:var(--paper);border:1px solid var(--line);padding:30px;margin:0 0 24px;border-radius:6px}.eyebrow,.muted{color:var(--muted);font-size:13px}.eyebrow{letter-spacing:.1em}.section-number{color:var(--accent);margin-right:12px;font-size:15px}button{font:inherit;background:var(--accent);color:white;border:0;padding:8px 17px;border-radius:4px;cursor:pointer}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #c38d32;outline-offset:3px}.copy-row{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:22px}.summary{border-left:3px solid var(--accent);padding-left:20px}.summary p{margin-bottom:12px}.label{font-weight:650}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;vertical-align:top;border-bottom:1px solid var(--line);padding:13px 12px}th{background:#f4f7f4;font-weight:600}td:first-child{min-width:110px}.table-wrap{overflow-x:auto}.pill{display:inline-block;background:#edf3ef;color:var(--accent);padding:2px 9px;border-radius:3px;font-size:12px;white-space:nowrap}.pill.warn{background:#fff4dc;color:#7c5719}a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:3px}.evidence{border-top:1px solid var(--line);padding:18px 0}.evidence:first-of-type{margin-top:8px}.evidence:target{background:#f4f8e9;outline:3px solid #e1e9bd}.evidence blockquote{margin:10px 0;padding:8px 16px;border-left:2px solid #bdcfc4;background:#f7f9f6;white-space:pre-wrap;overflow-wrap:anywhere}.evidence-meta{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.evidence ul{font-size:14px}ul{padding-left:22px;margin:8px 0 14px}li{overflow-wrap:anywhere}details{border-top:1px solid var(--line);margin-top:22px;padding-top:16px}summary{cursor:pointer;font-weight:600}.round{padding:12px 0;border-bottom:1px solid var(--line)}.demo{background:#fff3d8;color:#684b16;border:1px solid #ead5a3;padding:12px 18px;margin:0 0 20px}.audit-grid{display:grid;grid-template-columns:140px 1fr;gap:14px 20px}.audit-grid dt{font-weight:600}.audit-grid dd{margin:0;min-width:0}.audit-grid dd p,.audit-grid dd ul{margin-top:0}.copy-source{display:none}footer{font-size:12px;color:var(--muted)}
@media(max-width:640px){main{margin:20px auto;padding:0 12px 30px}section{padding:22px 18px}h1{font-size:25px}h2{font-size:21px}.audit-grid{grid-template-columns:1fr;gap:4px}.audit-grid dd{margin-bottom:14px}th,td{padding:10px 8px}}
@media print{body{background:white}main{max-width:none;margin:0;padding:0}section{border:0;border-top:1px solid #aaa;padding:20px 0;margin:0}button,.copy-row,footer{display:none}.table-wrap{overflow:visible}details{display:block}details>*{display:block}a{color:inherit}h2,h3{break-after:avoid}.evidence{break-inside:avoid}}
"""

COPY_SCRIPT = """
document.getElementById('copy-summary').addEventListener('click',async function(){
 const text=document.getElementById('copy-source').textContent;
 const message=document.getElementById('copy-status');
 try{if(!navigator.clipboard||!window.isSecureContext)throw new Error('fallback');await navigator.clipboard.writeText(text);message.textContent='已复制，可直接发送给面试官';}
 catch(error){const field=document.createElement('textarea');field.value=text;field.setAttribute('readonly','');field.style.position='fixed';field.style.top='0';field.style.left='-9999px';document.body.appendChild(field);field.select();try{const ok=document.execCommand('copy');if(!ok)throw new Error('copy');message.textContent='已复制，可直接发送给面试官';field.remove();}catch(e){field.style.position='static';field.style.width='100%';field.style.height='180px';message.textContent='请手动复制下方已选中的文字';field.focus();field.select();}}
});
"""


def render(data):
    validate(data)
    assessment = data["assessment"]
    level = assessment["proposed_level"]
    reviews = {item["material_id"]: item for item in assessment["material_reviews"]}
    evidence = {item["id"]: item for item in data["evidence"]}

    parts = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             '<meta name="report-sha256" content="' + report_fingerprint(data) + '"><meta name="referrer" content="no-referrer"><title>' + esc(data["candidate"]["name"]) + ' · AI 能力评审</title><style>' + STYLE + '</style><body><main>',
             '<header><div class=eyebrow>AI CAPABILITY</div><h1>' + esc(data['candidate']['name']) + ' · AI 能力评级</h1><div class=muted>候选人编号 ' + esc(data["candidate"]["id"]) + ' · 评分标准 v' + esc(data["rubric_version"]) + '</div></header>']
    badge = "暂定等级 · 资料不足" if assessment["rating_status"] == "provisional" else "基于提交材料定级"
    parts.append('<p class=muted>' + esc(badge) + ' · 证据置信度：' + esc({"high": "高", "medium": "中", "low": "低"}[assessment["confidence"]]) + '</p>')
    if data["demo"]:
        parts.append('<aside class=demo>演示报告 · 使用虚构样例，不代表真实候选人评价。</aside>')
    parts += ['<section id=summary><h2><span class=section-number>01</span>总结</h2><div class=copy-row><button id=copy-summary type=button>一键复制总结</button><span id=copy-status class=muted role=status aria-live=polite>仅复制候选人、等级、理由</span></div><div class=summary>',
              '<p><span class=label>候选人：</span>' + esc(candidate_name(data)) + '</p>',
              '<p><span class=label>等级：</span>' + esc(level) + '</p>',
              '<p><span class=label>理由：</span>' + esc(assessment["reason"]) + '</p></div>',
              '<pre id=copy-source class=copy-source>' + esc(summary_text(data)) + '</pre></section>',
              '<section id=process><h2><span class=section-number>02</span>具体评判过程</h2>']
    for index, material in enumerate(data["materials"], 1):
        review = reviews[material["id"]]
        parts += ['<article class=material-review><h3>' + str(index) + '. ' + esc(material["label"]) + '</h3>',
                  '<p>' + esc(review["summary"]) + '</p>',
                  '<p>' + esc(review["interpretation"]) + '</p>',
                  '<p>' + esc(review["limitation"]) + '</p>']
        if review["evidence_ids"]:
            locators = dict.fromkeys(evidence[eid]["locator"] for eid in review["evidence_ids"])
            parts.append('<p class=muted>依据：' + '；'.join(esc(value) for value in locators) + '</p>')
        if material["limitations"]:
            parts.append('<p class=muted>读取限制：' + '；'.join(esc(value) for value in material["limitations"]) + '</p>')
        parts.append('</article>')
    parts += ['<h3>为什么是这个等级</h3><p>' + esc(assessment["level_explanation"]) + '</p>',
              '<h3>为什么还达不到更高等级</h3><p>' + esc(assessment["higher_level_explanation"]) + '</p>',
              '</section><footer>本报告仅依据当前所列材料定级，未进行独立审核；自述、演示或暂定等级不等于已核实的能力。读取限制见逐份材料说明。</footer></main><script>' + COPY_SCRIPT + '</script></body></html>']
    return "\n".join(parts)


def render_index(inputs, output):
    """Link actual distinct pages; do not publish stale or placeholder reports."""
    output = output.resolve()
    rows, identities, pages = [], set(), set()
    for source in inputs:
        source = source.resolve()
        data = validate(json.loads(source.read_text(encoding="utf-8")))
        page = source.with_suffix(".html")
        if output in {source, page}:
            fail("index.output", "index must not overwrite an input or candidate page")
        if data["candidate"]["id"] in identities or page in pages:
            fail("index.inputs", "duplicate candidate or page")
        identities.add(data["candidate"]["id"])
        pages.add(page)
        marker = '<meta name="report-sha256" content="' + report_fingerprint(data) + '">'
        if not page.is_file() or marker not in page.read_text(encoding="utf-8"):
            fail(str(page), "missing or stale candidate page; render current JSON first")
        from urllib.parse import quote
        href = quote(os.path.relpath(page, output.parent).replace(os.sep, "/"), safe="/")
        label = candidate_name(data)
        suffix = "（暂定）" if data["assessment"]["rating_status"] == "provisional" else ""
        rows.append('<li><a href="' + esc(href) + '">' + esc(label) + '</a> · ' + esc(data["assessment"]["proposed_level"] + suffix) + '</li>')
    return ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>候选人 AI 评级目录</title><style>' + STYLE + '</style><body><main><header><h1>候选人 AI 评级</h1>'
            '<p class=muted>点击姓名查看独立页面。这里只列已完成的人，按处理顺序展示。</p></header><section><ul>'
            + "".join(rows) + '</ul></section></main></body></html>')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate").add_argument("input", type=Path)
    renderer = commands.add_parser("render")
    renderer.add_argument("input", type=Path)
    renderer.add_argument("--output", type=Path, required=True)
    indexer = commands.add_parser("index")
    indexer.add_argument("inputs", type=Path, nargs="+")
    indexer.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "index":
            content = render_index(args.inputs, args.output)
        else:
            data = validate(json.loads(args.input.read_text(encoding="utf-8")))
            if args.command == "validate":
                print("Valid report contract")
                return 0
            if args.output.resolve() == args.input.resolve():
                raise ValueError("output must differ from input")
            content = render(data)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
        print(f"Rendered: {args.output}")
        return 0
    except (ValueError, OSError) as error:
        print(f"Invalid report: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
