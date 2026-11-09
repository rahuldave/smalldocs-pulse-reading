"""Public consumers use a temporary committed snapshot of current build outputs."""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("theme_build", ROOT / "scripts/build.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def command(args, cwd):
    return subprocess.run(args, cwd=cwd, check=True, text=True)


@pytest.fixture(scope="session")
def foundation():
    return json.loads((ROOT / "src/foundations.json").read_text())


def test_schema_and_published_manifest(foundation):
    jsonschema.validate(foundation, json.loads((ROOT / "src/foundations-contract.schema.json").read_text()))
    builder.build()
    output = ROOT / "_extensions" / foundation["theme"]
    assert (output / "foundations.json").read_bytes() == (ROOT / "src/foundations.json").read_bytes()
    metadata = json.loads((ROOT / "src/theme.json").read_text())
    assert metadata["palette"] == builder.aliases(foundation["modes"][foundation["nativeMode"]])
    before = {p.name: p.read_bytes() for p in output.glob("*.*")}
    builder.build()
    assert before == {p.name: p.read_bytes() for p in output.glob("*.*")}


def luminance(color):
    channels = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    channels = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
    return sum(v * w for v, w in zip(channels, (.2126, .7152, .0722)))


def contrast(first, second):
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + .05) / (low + .05)


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_semantic_pairs_and_overlay(foundation, mode):
    mapping = foundation["modes"][mode]
    roles = builder.resolve(mapping)
    for foreground in ("ink", "muted", "accent-text", "secondary-text", "code-ink"):
        for surface in ("paper", "panel", "code"):
            assert contrast(roles[foreground], roles[surface]) >= 5, (mode, foreground, surface)
    for fill, ink in (("primary-fill", "button-ink"), ("primary-hover-fill", "primary-hover-ink"), ("selected-fill", "selected-ink"), ("disabled-fill", "disabled-ink")):
        assert contrast(roles[fill], roles[ink]) >= 4.5, (mode, fill)
    for state in mapping["states"].values():
        assert contrast(state["fill"], state["ink"]) >= 5
        assert contrast(state["fill"], state["boundary"]) >= 3
    for boundary in ("focus", "control-boundary"):
        for surface in ("paper", "panel", "code"):
            assert contrast(roles[boundary], roles[surface]) >= 3
    overlay = (ROOT / "_extensions" / foundation["theme"] / f"{foundation['theme']}-{mode}.scss").read_text()
    assert ".container{" not in overlay and "Bootstrap v" not in overlay
    for role, value in builder.aliases(mapping).items():
        assert f"--r-{role}: {value};" in overlay
    assert "--r-size-title: 2.25rem" in overlay
    assert "--r-size-display: 3rem" in overlay


def snapshot(tmp_path, foundation):
    builder.build()
    published = tmp_path / "published"
    shutil.copytree(ROOT / "_extensions", published / "_extensions")
    command(["git", "init", "-q", str(published)], tmp_path)
    command(["git", "add", "."], published)
    command(["git", "-c", "user.name=Theme test", "-c", "user.email=test@example.org", "commit", "-qm", "Published extension"], published)
    return published


def test_smalldocs_consumer(tmp_path, foundation):
    published = snapshot(tmp_path, foundation)
    consumer = tmp_path / "smalldocs"
    consumer.mkdir()
    name = foundation["theme"]
    (consumer / "_smalldocs.yml").write_text(f"project:\n  type: website\ntheme: {name}\nwebsite:\n  title: Reading QA\n  navbar:\n    left:\n      - href: index.qmd\n        text: Components\n")
    shutil.copy2(ROOT / "tests/fixtures/components.qmd", consumer / "index.qmd")
    command([sys.executable, "-m", "smalldocs.cli", "add", str(published)], consumer)
    command([sys.executable, "-m", "smalldocs.cli", "render", str(consumer), "--strict"], consumer)
    out = consumer / "_site"
    html = (out / "index.html").read_text()
    assert 'id="invalid"' in html and 'aria-describedby="invalid-message"' in html
    for mode in ("light", "dark"):
        css = out / "site_libs/themes" / name / f"{name}-{mode}.css"
        assert css.is_file()
        for ref in re.findall(r"url\(fonts/([^)]*)\)", css.read_text()):
            assert (css.parent / "fonts" / ref).is_file(), ref
        assert "@import" not in css.read_text()
    assert next((consumer / "_extensions").rglob("foundations.json")).read_bytes() == (ROOT / "src/foundations.json").read_bytes()
    save = ROOT / ".build/qa/smalldocs"
    shutil.copytree(out, save, dirs_exist_ok=True)


def test_quarto_consumer(tmp_path, foundation):
    if not shutil.which("quarto"):
        pytest.skip("Quarto is required for the separate Quarto consumer check")
    published = snapshot(tmp_path, foundation)
    consumer = tmp_path / "quarto"
    consumer.mkdir()
    name = foundation["theme"]
    command(["quarto", "add", str(published), "--no-prompt"], consumer)
    (consumer / "_quarto.yml").write_text(f"project:\n  type: website\nformat: {name}-html\nwebsite:\n  title: Reading QA\n  navbar:\n    left:\n      - href: index.qmd\n        text: Components\n")
    shutil.copy2(ROOT / "tests/fixtures/components.qmd", consumer / "index.qmd")
    command(["quarto", "render"], consumer)
    out = consumer / "_site"
    html = (out / "index.html").read_text()
    assert 'id="invalid"' in html and "quarto-bootstrap" in html
    styles = [p for p in out.rglob("bootstrap*.css") if "icons" not in p.name]
    assert len(styles) >= 2
    for mode in ("light", "dark"):
        assert re.search(r'id="quarto-bootstrap" data-mode="' + mode + '"', html)

    for path in [*styles, *out.rglob("fonts.css")]:
        css = path.read_text()
        assert "fonts.googleapis.com" not in css
        if path.name != "fonts.css":
            assert "--r-primary-hover-ink" in css
        for ref in re.findall(r"url\([\"']?([^)'\"]+\.ttf)[\"']?\)", css):
            assert (path.parent / ref).resolve().is_file(), (path, ref)
    save = ROOT / ".build/qa/quarto"
    shutil.copytree(out, save, dirs_exist_ok=True)
    shutil.copy2(ROOT / "tests/fixtures/narrow.html", ROOT / ".build/qa/narrow.html")


def test_profiles_drive_generated_values(foundation):
    import copy
    changed = copy.deepcopy(foundation)
    changed["typography"]["profiles"]["reading"]["body"] = 24
    changed["typography"]["lineHeights"]["reading"] = 1.75
    changed["spacing"]["profiles"]["reading"]["panel"] = 32
    output = builder.variables(changed, "light")
    assert "--r-size-body: 1.5rem;" in output
    assert "--r-line-reading: 1.75;" in output
    assert "--r-space-panel: 2rem;" in output
    css = (ROOT / "src/reading.css").read_text()
    assert "font-size: var(--r-size-body)" in css
    assert "line-height: var(--r-line-reading)" in css
    assert "padding: var(--r-space-panel)" in css
    for mode in changed["modes"].values():
        values = builder.aliases(mode)
        assert mode["swatches"][mode["roles"]["selected-ink"]].replace("#", "%23") in values["check-image"]


def test_semantic_callouts_cover_all_types(foundation):
    css = (ROOT / "src/reading.css").read_text()
    fixture = (ROOT / "tests/fixtures/components.qmd").read_text()
    for kind, state in (("tip", "success"), ("warning", "warning"), ("important", "danger"), ("caution", "danger"), ("note", "info")):
        assert f".callout-{kind}" in fixture
        assert f".callout-{kind} > .callout-header {{ background: var(--r-{state}-bg); color: var(--r-{state}-ink); border-color: var(--r-{state}-line); }}" in css
        assert f".callout-{kind} :is(.callout-title-container,.callout-icon-container,.callout-icon) {{ color: var(--r-{state}-ink); }}" in css
