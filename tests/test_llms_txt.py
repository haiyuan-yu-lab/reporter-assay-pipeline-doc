"""MkDocs copies a curated llms.txt index to the published site root."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = ROOT / "site"
LLMS_TXT = SITE_ROOT / "llms.txt"
SITE_PREFIX = "https://haiyuan-yu-lab.github.io/reporter-assay-pipeline-doc"
SITE_HOST = "haiyuan-yu-lab.github.io"
SITE_PATH_PREFIX = "/reporter-assay-pipeline-doc/"

# Independent of the index file: representative published destinations from
# the approved assay-oriented navigation.
REQUIRED_DOC_PATHS = (
    "/",
    "/quickstart/",
    "/assay-model/",
    "/reporter-assay-concepts/",
    "/reporter-assay-normalization/",
    "/cap-assay-concepts/",
    "/glossary/",
    "/workflow/",
    "/input-preparation/",
    "/complete-command-paths/",
    "/steps-1-2/",
    "/steps-3-5/",
    "/steps-6-8/",
    "/steps-9/",
    "/reporter/troubleshooting/",
    "/cap-selection/workflow/",
    "/cap-selection/migrating-to-0.2.0b5/",
    "/cap-selection/prepare-inputs/",
    "/cap-selection/steps-1-3/",
    "/cap-selection/complete-run/",
    "/cap-selection/step4/",
    "/cap-selection/troubleshooting/",
    "/cli/pipe/",
    "/cli/qc/",
    "/cli/export/",
    "/cli/cap-assay/",
    "/reporter/formats/",
    "/reporter/resource-guidance/",
    "/reporter/known-limitations/",
    "/cap-selection/formats/",
    "/cap-selection/resource-guidance/",
    "/cap-selection/known-limitations/",
)
CODE_REPO = "https://github.com/DignoMor/reporter-assay-pipeline"
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


class RenderedPage(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        for name in ("id", "name"):
            if attributes.get(name):
                self.ids.add(attributes[name])
        if tag == "a" and attributes.get("href"):
            self.hrefs.append(attributes["href"])


def rendered_pages() -> dict[Path, RenderedPage]:
    pages: dict[Path, RenderedPage] = {}
    for path in SITE_ROOT.rglob("*.html"):
        page = RenderedPage()
        page.feed(path.read_text(encoding="utf-8"))
        pages[path.resolve()] = page
    return pages


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
        self.assertLess(len(text), 5000)
        self.assertRegex(text, r"^# .+", text)
        self.assertIn(CODE_REPO, text)
        hrefs = {href for _label, href in LINK_RE.findall(text)}
        for path in REQUIRED_DOC_PATHS:
            self.assertIn(f"{SITE_PREFIX}{path}", hrefs)

    def test_every_indexed_site_url_resolves_in_the_built_site(self) -> None:
        text = LLMS_TXT.read_text(encoding="utf-8")
        pages = rendered_pages()
        checked = 0
        for _label, href in LINK_RE.findall(text):
            url = urlsplit(href)
            if url.scheme not in {"http", "https"} or url.netloc != SITE_HOST:
                continue
            if not url.path.startswith(SITE_PATH_PREFIX):
                continue
            relative = unquote(url.path[len(SITE_PATH_PREFIX) :])
            target = (SITE_ROOT / relative).resolve()
            if target.is_dir():
                target /= "index.html"
            self.assertTrue(target.is_file(), f"llms.txt: missing {href}")
            if url.fragment and target.resolve() in pages:
                self.assertIn(
                    unquote(url.fragment),
                    pages[target.resolve()].ids,
                    f"llms.txt: missing anchor {href}",
                )
            checked += 1
        self.assertGreater(checked, 0, "expected indexed site URLs in llms.txt")

    def test_documentation_links_resolve_in_the_built_site(self) -> None:
        pages = rendered_pages()
        checked = 0
        for source, page in pages.items():
            for href in page.hrefs:
                url = urlsplit(href)
                if url.scheme or url.netloc:
                    continue
                relative = unquote(url.path)
                if relative.startswith(SITE_PATH_PREFIX):
                    target = SITE_ROOT / relative[len(SITE_PATH_PREFIX) :]
                elif relative.startswith("/"):
                    target = SITE_ROOT / relative.lstrip("/")
                elif relative:
                    target = source.parent / relative
                else:
                    target = source
                target = target.resolve()
                if target.is_dir():
                    target /= "index.html"
                self.assertTrue(
                    target.is_file(),
                    f"{source.relative_to(SITE_ROOT)}: missing {href}",
                )
                if url.fragment and target.resolve() in pages:
                    self.assertIn(
                        unquote(url.fragment),
                        pages[target.resolve()].ids,
                        f"{source.relative_to(SITE_ROOT)}: missing anchor {href}",
                    )
                checked += 1
        self.assertGreater(checked, 0)

    def test_superseded_shared_reference_pages_are_not_published(self) -> None:
        for path in ("formats", "resource-allocation", "known-limitations"):
            with self.subTest(path=path):
                self.assertFalse((SITE_ROOT / path / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
