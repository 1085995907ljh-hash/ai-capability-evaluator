"""Meaningful schema, publication and multi-page navigation regressions."""
import copy
import importlib.util
import json
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("report", ROOT / "scripts/report.py")
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)


def fixture():
    return json.loads((ROOT / "assets/example-report.json").read_text())


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sections = []
        self.links = []
        self.events = []
        self.scripts = 0
        self.in_copy = False
        self.copy = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section":
            self.sections.append(attrs.get("id"))
        if tag == "a":
            self.links.append(attrs.get("href"))
        if tag == "script":
            self.scripts += 1
        self.events.extend(k for k in attrs if k.lower().startswith("on"))
        if attrs.get("id") == "copy-source":
            self.in_copy = True

    def handle_endtag(self, tag):
        if tag == "pre":
            self.in_copy = False

    def handle_data(self, text):
        if self.in_copy:
            self.copy += text


class ReportTests(unittest.TestCase):
    def test_separate_page_without_audit_and_exact_hr_copy(self):
        data = fixture()
        parser = Elements()
        source = report.render(data)
        parser.feed(source)
        self.assertEqual(parser.sections, ["summary", "process"])
        self.assertEqual(parser.copy, report.summary_text(data))
        self.assertTrue(parser.copy.startswith("候选人：候选人 A（虚构演示）\n等级：L2\n理由："))
        self.assertNotIn("审核通过", source)
        self.assertNotIn("共评审", source)
        self.assertNotIn("Delegation", source)
        self.assertIn("未进行独立审核", source)

    def test_no_caught_error_is_not_a_publication_veto(self):
        data = fixture()
        # Main L1 conditions can be supported without a caught-error incident.
        data["assessment"].update(proposed_level="L1", evidence_gaps=["未展示实际AI抓错案例"])
        data["assessment"]["level_basis"] = [{"criterion": "完整委派并检查", "finding": "情境中有记录", "evidence_ids": ["E-001"]}]
        report.validate(data)
        self.assertIn("等级：L1", report.summary_text(data))
        self.assertIn("id=summary", report.render(data))

    def test_no_evidence_still_has_explicit_provisional_floor(self):
        data = fixture()
        data["materials"], data["evidence"] = [], []
        a = data["assessment"]
        a.update(proposed_level="Assisted", rating_status="provisional", confidence="low",
                 evidence_gaps=["材料未能读取，尚无可用于确认AI使用的证据"], level_basis=[], material_reviews=[],
                 reason="暂定为Assisted，当前材料无法读取，缺少能够确认实际AI使用方式的内容。本结论采用五级体系中的最低暂定位置，仅用于本次材料评价，并不表示已经证明候选人具备基础能力，也不能据此认定其能力不足。现阶段无法核实本人承担的任务、AI承接范围、结果检查方式或实际产物，因此没有依据支持完整委派、持续自动运行、团队系统建设或公司职能重构。后续可依据可读的项目说明、任务输入输出及个人贡献记录重新评级；当前结论的证据置信度为低。",
                 level_explanation="Assisted是资料不足时的最低暂定等级，不是已证明的能力。")
        report.validate(data)
        self.assertIn("暂定等级", report.render(data))
        self.assertIn("暂定", report.summary_text(data))

    def test_provisional_cannot_hide_uncertainty_or_inflate_level(self):
        for change in [
            {"proposed_level": "L1"}, {"confidence": "high"}, {"evidence_gaps": []},
            {"reason": fixture()["assessment"]["reason"]},
            {"level_explanation": "已经证明能力"},
        ]:
            data = fixture()
            data["assessment"].update(proposed_level="Assisted", rating_status="provisional", confidence="low",
                                      evidence_gaps=["无法确认"], reason="暂定：" + data["assessment"]["reason"],
                                      level_explanation="最低暂定等级。")
            data["assessment"].update(change)
            with self.assertRaises(ValueError):
                report.validate(data)

    def test_null_obsolete_audit_and_unfresh_context_are_rejected(self):
        changes = [
            lambda d: d["assessment"].update(proposed_level=None),
            lambda d: d.update(audit={"status": "pass"}),
            lambda d: d.update(rounds=[]),
            lambda d: d["evaluation"].update(scorer_fresh=False),
            lambda d: d["evaluation"].update(scorer_id=""),
            lambda d: d.update(schema_version="1.1"),
            lambda d: d["assessment"].update(reason="太短"),
        ]
        for change in changes:
            data = fixture()
            change(data)
            with self.assertRaises(ValueError):
                report.validate(data)

    def test_material_coverage_order_and_own_file_citations(self):
        data = fixture()
        data["materials"].append({"id": "M2", "label": "截图.jpg", "format": "JPG", "coverage": "全文", "limitations": []})
        with self.assertRaisesRegex(ValueError, "every material"):
            report.validate(data)
        data["assessment"]["material_reviews"].append({"material_id": "M2", "summary": "截图", "interpretation": "演示", "limitation": "无运行历史", "evidence_ids": []})
        report.validate(data)
        data["assessment"]["material_reviews"][1]["evidence_ids"] = ["E-001"]
        with self.assertRaisesRegex(ValueError, "another material"):
            report.validate(data)
        data["assessment"]["material_reviews"][1]["evidence_ids"] = []
        data["assessment"]["material_reviews"].reverse()
        with self.assertRaisesRegex(ValueError, "input order"):
            report.validate(data)

    def test_missing_broken_or_duplicate_evidence_is_rejected(self):
        for change in [
            lambda d: d["assessment"]["level_basis"][0].update(evidence_ids=[]),
            lambda d: d["assessment"]["level_basis"][0].update(evidence_ids=["missing"]),
            lambda d: d["evidence"].append(copy.deepcopy(d["evidence"][0])),
            lambda d: d["evidence"][0].update(material_id="missing"),
        ]:
            data = fixture()
            change(data)
            with self.assertRaises(ValueError):
                report.validate(data)

    def test_candidate_html_injection_is_escaped(self):
        data = fixture()
        payload = '</script><img src=x onerror="alert(1)"><script>alert(2)</script>'
        data["candidate"]["name"] = payload
        data["materials"][0]["label"] = payload
        data["assessment"]["material_reviews"][0]["summary"] = payload
        source = report.render(data)
        parser = Elements()
        parser.feed(source)
        self.assertNotIn(payload, source)
        self.assertEqual(parser.events, [])
        self.assertEqual(parser.scripts, 1)
        self.assertIn(payload, parser.copy)

    def test_directory_links_distinct_current_pages_and_preserves_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = []
            for i in range(2):
                data = fixture()
                data["candidate"] = {"id": f"c{i}", "name": f"虚构候选人{i}"}
                folder = root / f"person {i}"
                folder.mkdir()
                path = folder / "report.json"
                path.write_text(json.dumps(data))
                path.with_suffix(".html").write_text(report.render(data))
                sources.append(path)
            output = root / "index.html"
            parser = Elements()
            parser.feed(report.render_index(sources, output))
            self.assertEqual(len(set(parser.links)), 2)
            for i, href in enumerate(parser.links):
                page = root / unquote(href)
                self.assertTrue(page.is_file())
                self.assertIn(f"虚构候选人{i}", page.read_text())
                self.assertNotIn(f"虚构候选人{1-i}", page.read_text())

    def test_directory_rejects_missing_stale_duplicate_pages_and_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "report.json"
            data = fixture()
            source.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "missing or stale"):
                report.render_index([source], root / "index.html")
            source.with_suffix(".html").write_text(report.render(data))
            data["candidate"]["name"] = "虚构修改后"
            source.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "missing or stale"):
                report.render_index([source], root / "index.html")
            source.with_suffix(".html").write_text(report.render(data))
            with self.assertRaisesRegex(ValueError, "duplicate"):
                report.render_index([source, source], root / "index.html")
            for target in [source, source.with_suffix(".html")]:
                with self.assertRaisesRegex(ValueError, "overwrite"):
                    report.render_index([source], target)

    def test_invalid_cli_creates_no_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / "in.json", Path(tmp) / "out.html"
            data = fixture()
            data["assessment"]["proposed_level"] = None
            source.write_text(json.dumps(data))
            self.assertEqual(report.main(["render", str(source), "--output", str(output)]), 2)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
