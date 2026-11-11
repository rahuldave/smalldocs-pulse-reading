"""Check the winning compiled color declarations on real component selectors.

This deliberately small CSS cascade probe is limited to opaque colors and the
normal/selected/disabled states below; browser QA covers rendered interactions.
Dynamic pseudo-classes map to fixture classes so every authored state rule is
matched through the same CSS selector parser, including its specificity.
"""
import re
from xml.etree import ElementTree

import cssselect2
import tinycss2


def effective_colors(css, fragment):
    for pseudo in ("hover", "active", "focus-visible"):
        css = css.replace(":" + pseudo, ".probe-" + pseudo)
    matcher = cssselect2.Matcher()
    for rule in tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True):
        if rule.type != "qualified-rule":
            continue
        declarations = [d for d in tinycss2.parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True) if d.type == "declaration"]
        try:
            selectors = cssselect2.compile_selector_list(tinycss2.serialize(rule.prelude))
        except cssselect2.SelectorError:
            continue
        for selector in selectors:
            matcher.add_selector(selector, declarations)
    tree = ElementTree.fromstring('<html><body><div id="quarto-content">' + fragment + '</div></body></html>')
    root = cssselect2.ElementWrapper.from_html_root(tree)
    by_element = {}
    for element in root.iter_subtree():
        inherited = by_element.get(element.parent.etree_element, {}) if element.parent else {}
        values = {k: v for k, v in inherited.items() if k.startswith("--")}
        winners = {}
        for specificity, order, pseudo, declarations in matcher.match(element):
            if pseudo:
                continue
            for index, declaration in enumerate(declarations):
                key = (declaration.important, specificity, order, index)
                names = ("background-color",) if declaration.name == "background" else (declaration.name,)
                for name in names:
                    if name not in winners or key >= winners[name][0]:
                        winners[name] = (key, tinycss2.serialize(declaration.value).strip())
        values.update({name: value for name, (_, value) in winners.items()})
        by_element[element.etree_element] = values
        if element.etree_element.get("id") == "probe":
            def resolve(value):
                for _ in range(12):
                    changed = re.sub(r"var\((--[\w-]+)(?:,[^)]*)?\)", lambda m: values.get(m[1], m[0]), value)
                    if changed == value:
                        return value
                    value = changed
                raise AssertionError("Cyclic color reference")
            return {name: resolve(values.get(name, "")) for name in ("color", "background-color", "border-color", "text-decoration", "outline")}
    raise AssertionError("Missing probe component")
