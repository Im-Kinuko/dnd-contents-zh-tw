"""Preserve block structure while allowing complete inline phrases to move.

No third-party parser is needed. Raw tags, attributes and entities survive round
trips. Unsupported or malformed markup is rejected rather than repaired silently.
"""
from collections import Counter
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
import re

INLINE = set("a abbr b bdi bdo br cite code del em i img ins kbd mark q ruby rp rt s samp small span strong sub sup time u var wbr".split())
VOID = set("area base br col embed hr img input link meta param source track wbr".split())
PROTECTED = {"script", "style", "pre"}
ATOM = re.compile(r"@[A-Za-z][A-Za-z0-9]*\[[^\]]*\]|&(?:amp;)?Reference\[[^\]]*\]|\[\[.*?\]\]", re.S)
LABEL = re.compile(r"(@[A-Za-z][A-Za-z0-9]*\[[^\]]*\]|&(?:amp;)?Reference\[[^\]]*\]|\[\[.*?\]\])(?:\{([^}]*)\})?", re.S)


@dataclass
class Node:
    tag: str
    opening: str
    children: list = field(default_factory=list)
    closing: str = ""

    def render(self):
        return self.opening + render(self.children) + self.closing


def render(children):
    return "".join(child.render() if isinstance(child, Node) else child for child in children)


class Parser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.offsets = [0]
        for match in re.finditer("\n", source):
            self.offsets.append(match.end())
        self.root = Node("root", "")
        self.stack = [self.root]
        self.feed(source)
        self.close()
        if len(self.stack) != 1:
            raise ValueError("HTML 標籤未閉合：" + self.stack[-1].tag)
        if self.root.render() != source:
            raise ValueError("HTML 無法原樣解析，需人工檢查")

    def append(self, value):
        self.stack[-1].children.append(value)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, self.get_starttag_text())
        self.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.append(Node(tag, self.get_starttag_text()))

    def handle_endtag(self, tag):
        if len(self.stack) == 1 or self.stack[-1].tag != tag:
            raise ValueError("HTML 閉合順序錯誤：" + tag)
        line, column = self.getpos()
        start = self.offsets[line - 1] + column
        end = self.source.index(">", start) + 1
        self.stack.pop().closing = self.source[start:end]

    def handle_data(self, data):
        self.append(data)

    def entity(self, prefix, name):
        line, column = self.getpos()
        start = self.offsets[line - 1] + column
        value = prefix + name
        if self.source[start + len(value):].startswith(";"):
            value += ";"
        self.append(value)

    def handle_entityref(self, name):
        self.entity("&", name)

    def handle_charref(self, name):
        self.entity("&#", name)

    def handle_comment(self, data):
        self.append(Node("#protected", "<!--" + data + "-->"))

    def handle_decl(self, decl):
        self.append(Node("#protected", "<!" + decl + ">"))


@dataclass
class Block:
    id: str
    html: str
    children: list


class Plan:
    def __init__(self, html):
        self.root = Parser(html).root
        self.parts = []
        self.blocks = []
        self.walk(self.root.children)

    def walk(self, children):
        pending = []

        def flush():
            if not pending:
                return
            content = render(pending)
            if content.strip():
                block = Block("b%04d" % (len(self.blocks) + 1), content, list(pending))
                self.blocks.append(block)
                self.parts.append(block)
            else:
                self.parts.append(content)
            pending.clear()

        for child in children:
            if isinstance(child, str) or child.tag in INLINE:
                pending.append(child)
                continue
            flush()
            if child.tag in PROTECTED or child.tag == "#protected":
                self.parts.append(child.render())
            else:
                self.parts.append(child.opening)
                self.walk(child.children)
                self.parts.append(child.closing)
        flush()

    def structure(self):
        return tuple("BLOCK" if isinstance(part, Block) else part
                     for part in self.parts if isinstance(part, Block) or part.strip())

    def build(self, replacements):
        return "".join(replacements.get(part.id, part.html) if isinstance(part, Block) else part
                       for part in self.parts)


def inline_shape(node):
    children = sorted((inline_shape(child) for child in node.children if isinstance(child, Node)), key=repr)
    # Code and comments carry literal technical content, not translated prose.
    literal = render(node.children) if node.tag in {"code", "#protected"} else ""
    return (node.opening, node.closing, tuple(children), literal)


def annotation_profile(children, ancestors=()):
    result = Counter()
    pending = []

    def flush():
        text = "".join(pending)
        for atom in ATOM.findall(text):
            result[(ancestors, atom)] += 1
        if "{}" in text:
            result[(ancestors, "{} placeholder")] += text.count("{}")
        pending.clear()

    for child in children:
        if isinstance(child, str):
            pending.append(child)
        else:
            flush()
            result.update(annotation_profile(child.children, ancestors + (child.opening,)))
    flush()
    return result


def compare_html(en_html, zh_html):
    """Return structural errors; inline order may differ within each block."""
    try:
        en, zh = Plan(en_html), Plan(zh_html)
    except ValueError as exc:
        return [str(exc)]
    if en.structure() != zh.structure():
        return ["段落／表格／區塊結構或屬性與 EN 不同"]
    problems = []
    for a, b in zip(en.blocks, zh.blocks):
        en_inline = Counter(inline_shape(c) for c in a.children if isinstance(c, Node))
        zh_inline = Counter(inline_shape(c) for c in b.children if isinstance(c, Node))
        if en_inline != zh_inline:
            problems.append(a.id + " 句內標籤、屬性、巢狀關係或技術內容不同")
        if annotation_profile(a.children) != annotation_profile(b.children):
            problems.append(a.id + " UUID／Reference／巨集／佔位符或其格式歸屬不同")
    return problems


def visible_text(html):
    root = Parser(html).root

    def text(children):
        result = []
        for child in children:
            if isinstance(child, str):
                result.append(child)
            elif child.tag not in PROTECTED | {"code", "#protected"}:
                result.append(text(child.children))
        return "".join(result)

    value = LABEL.sub(lambda match: match.group(2) or "", text(root.children))
    return unescape(value)
