"""Generate independent SmallDocs themes and a Bootstrap-free Quarto overlay.

Only src/foundations.json owns role colors, typography, spacing and shape.
The pinned vendor trees remain unmodified.
"""
import json
import re
import shutil
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def resolve(mode):
    """Resolve semantic references without treating legacy aliases as colors."""
    return {role: mode["swatches"][ref] for role, ref in mode["roles"].items()}


def aliases(mode):
    roles = resolve(mode)
    values = dict(roles)
    values.update(link=roles["accent-text"], button=roles["primary-fill"])
    values["on-button"] = roles["button-ink"]
    values["button-hover"] = roles["primary-hover-fill"]
    values["focus-rgb"] = ", ".join(str(int(roles["focus"][i:i+2], 16)) for i in (1, 3, 5))
    for state, triple in mode["states"].items():
        for legacy, current in (("bg", "fill"), ("ink", "ink"), ("line", "boundary")):
            values[state + "-" + legacy] = triple[current]
    ink = roles["selected-ink"].replace("#", "%23")
    control_ink = roles["ink"].replace("#", "%23")
    values["check-image"] = 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 16 16\'%3E%3Cpath fill=\'none\' stroke=\'' + ink + '\' stroke-width=\'3\' d=\'m3 8 3 3 7-7\'/%3E%3C/svg%3E")'
    values["radio-image"] = 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 16 16\'%3E%3Ccircle fill=\'' + ink + '\' cx=\'8\' cy=\'8\' r=\'4\'/%3E%3C/svg%3E")'
    values["select-image"] = 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 16 16\'%3E%3Cpath fill=\'none\' stroke=\'' + control_ink + '\' stroke-width=\'2\' d=\'m3 6 5 5 5-5\'/%3E%3C/svg%3E")'
    values["menu-image"] = 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 30 30\'%3E%3Cpath fill=\'none\' stroke=\'' + control_ink + '\' stroke-width=\'2\' stroke-linecap=\'round\' d=\'M4 7h22M4 15h22M4 23h22\'/%3E%3C/svg%3E")'
    return values


def rem(value):
    return f"{value / 16:g}rem"


def variables(foundation, mode):
    values = {"r-" + key: value for key, value in aliases(foundation["modes"][mode]).items()}
    typography = foundation["typography"]
    values.update({"r-font-" + key: value for key, value in typography["fonts"].items()})
    values.update({"r-size-" + key: rem(value) for key, value in typography["profiles"]["reading"].items()})
    values.update({"r-space-" + key: rem(value) for key, value in foundation["spacing"]["profiles"]["reading"].items()})
    values.update({"r-line-" + key: str(value) for key, value in typography["lineHeights"].items()})
    values["r-radius"] = rem(foundation["shape"]["radius"])
    weights = typography["availableWeights"]["heading"]
    values["r-heading-weight"] = str(600 if 600 in weights else 700 if 700 in weights else 400)
    values["r-bold-weight"] = str(max(typography["availableWeights"]["body"]))
    declarations = "\n".join(f"  --{key}: {value};" for key, value in values.items())
    return f":root {{\n{declarations}\n  color-scheme: {mode};\n}}\n"


def build():
    source = ROOT / "src"
    foundation = json.loads((source / "foundations.json").read_text())
    theme = json.loads((source / "theme.json").read_text())
    name = theme["name"]
    if foundation["schemaVersion"] != 1 or foundation["theme"] != name:
        raise ValueError("Unsupported or mismatched foundation")
    # Compatibility metadata is generated; it is never an independent palette.
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    theme["version"] = version
    theme["palette"] = aliases(foundation["modes"][foundation["nativeMode"]])
    (source / "theme.json").write_text(json.dumps(theme, indent=2) + "\n")
    output = ROOT / "_extensions" / name
    output.mkdir(parents=True, exist_ok=True)
    upstream = (ROOT / "vendor/bootswatch/bootstrap.min.css").read_text()
    upstream = re.sub(r"@import\s+url\([^)]*\)\s*;", "", upstream)
    upstream = re.sub(r"/\*# sourceMappingURL=.*?\*/", "", upstream)
    reading = (source / "reading.css").read_text()
    design = (source / "design.css").read_text()
    fonts = (source / "fonts.css").read_text()
    for mode in ("light", "dark"):
        overlay = variables(foundation, mode) + reading + design
        (output / f"{name}-{mode}.css").write_text(upstream + "\n" + fonts + "\n" + overlay)
        # Quarto compiles its own native Bootstrap/Bootswatch base. This file
        # contains only owned font declarations, tokens and component rules.
        roles = resolve(foundation["modes"][mode])
        defaults = {
            "body-bg": roles["paper"], "body-color": roles["ink"],
            "headings-color": roles["ink"], "link-color": roles["accent-text"],
            "navbar-bg": roles["paper"], "navbar-fg": roles["ink"],
            "navbar-hl": roles["accent-text"], "grid-body-width": "640px",
            "link-hover-color": roles["link-hover"], "code-block-bg": roles["code"],
            "font-family-sans-serif": foundation["typography"]["fonts"]["ui"],
            "font-family-monospace": foundation["typography"]["fonts"]["code"],
            "web-font-path": "false", "enable-shadows": "false",
        }
        for kind, state in (("note", "info"), ("tip", "success"), ("warning", "warning"), ("important", "danger"), ("caution", "danger")):
            defaults["callout-color-" + kind] = foundation["modes"][mode]["states"][state]["ink"]
        scss = "/*-- scss:defaults --*/\n" + "".join(f"${key}: {value};\n" for key, value in defaults.items())
        (output / f"{name}-{mode}.scss").write_text(scss + "/*-- scss:rules --*/\n" + overlay)
    shutil.copy2(output / f"{name}-{foundation['nativeMode']}.css", output / f"{name}.css")
    shutil.copytree(ROOT / "vendor/fonts", output / "fonts", dirs_exist_ok=True)
    for origin, destination in (("vendor/bootswatch/LICENSE", "BOOTSWATCH-LICENSE"),
                                ("vendor/bootstrap/LICENSE", "BOOTSTRAP-LICENSE"),
                                ("LICENSE", "READING-LICENSE")):
        shutil.copy2(ROOT / origin, output / destination)
    shutil.copy2(source / "fonts.css", output / "fonts.css")
    shutil.copy2(source / "foundations.json", output / "foundations.json")
    shutil.copy2(source / "smalldocs.yml", output / "smalldocs.yml")
    extension, count = re.subn(r"^version: .*$", "version: " + version,
                               (source / "_extension.yml").read_text(), flags=re.MULTILINE)
    if count != 1:
        raise ValueError("Expected one Quarto extension version")
    (source / "_extension.yml").write_text(extension)
    (output / "_extension.yml").write_text(extension)
    print("Built " + name + " (paired SmallDocs and Quarto)")


if __name__ == "__main__":
    build()
