"""MkDocs copies a curated llms.txt index to the published site root."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = ROOT / "site"
LLMS_TXT = SITE_ROOT / "llms.txt"
SITE_PREFIX = "https://haiyuan-yu-lab.github.io/reporter-assay-pipeline-doc"

# Independent of the index file: published HTML paths required by issue #4.
REQUIRED_DOC_PATHS = (
    "/",
    "/quickstart/",
    "/tasks/",
    "/workflow/",
    "/cli/",
    "/cli/pipe/",
    "/cli/qc/",
    "/cli/export/",
    "/formats/",
    "/faq/",
    "/known-limitations/",
    "/glossary/",
)
CODE_REPO = "https://github.com/haiyuan-yu-lab/reporter-assay-pipeline"
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


class LlmsTxtPublishingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        mkdocs = ROOT / ".venv" / "bin" / "mkdocs"
        command = str(mkdocs) if mkdocs.is_file() else shutil.which("mkdocs")
        if command is None:
            raise unittest.SkipTest("mkdocs is not installed")
        env = os.environ.copy()
        env["PATH"] = str(ROOT / ".venv" / "bin") + os.pathsep + env.get("PATH", "")
        subprocess.run(
            [command, "build", "--strict"],
            cwd=ROOT,
            check=True,
            env=env,
        )

    def test_production_build_places_llms_txt_at_site_root(self) -> None:
        self.assertTrue(LLMS_TXT.is_file(), "expected site/llms.txt after mkdocs build")

    def test_index_links_code_repo_and_required_rendered_pages(self) -> None:
        text = LLMS_TXT.read_text(encoding="utf-8")
        self.assertLess(len(text), 4000)
        self.assertRegex(text, r"^# .+", text)
        self.assertIn(CODE_REPO, text)
        hrefs = {href for _label, href in LINK_RE.findall(text)}
        for path in REQUIRED_DOC_PATHS:
            self.assertIn(f"{SITE_PREFIX}{path}", hrefs)

    def test_documentation_links_resolve_in_the_built_site(self) -> None:
        text = LLMS_TXT.read_text(encoding="utf-8")
        for _label, href in LINK_RE.findall(text):
            if not href.startswith(SITE_PREFIX):
                continue
            relative = href[len(SITE_PREFIX) :].lstrip("/")
            target = SITE_ROOT / relative / "index.html" if relative else SITE_ROOT / "index.html"
            self.assertTrue(target.is_file(), f"{href} should exist at {target}")


if __name__ == "__main__":
    unittest.main()
