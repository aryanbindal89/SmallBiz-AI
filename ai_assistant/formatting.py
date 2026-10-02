import re


HEADING_RE = re.compile(r'^\s{0,3}#{1,4}\s+(.+?)\s*#*\s*$')
BOLD_HEADING_RE = re.compile(r'^\s*\*\*(.+?)\*\*:?\s*$')
LIST_ITEM_RE = re.compile(r'^\s*(?:[-*•]\s+|\d+[.)]\s+)(.+)$')
BOLD_TERM_RE = re.compile(r'\*\*(.+?)\*\*|__(.+?)__')


def _clean_inline_markup(value):
    value = re.sub(r'\*\*(.+?)\*\*|__(.+?)__', lambda match: match.group(1) or match.group(2), value)
    value = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', value)
    return value.replace('`', '').strip()


def parse_assistant_response(response):
    raw_sections = []
    title = 'Overview'
    lines = []

    def save_raw_section():
        if lines:
            raw_sections.append((title, list(lines)))
            lines.clear()

    for raw_line in response.splitlines():
        heading_match = HEADING_RE.match(raw_line) or BOLD_HEADING_RE.match(raw_line)
        if heading_match:
            save_raw_section()
            title = _clean_inline_markup(heading_match.group(1))
        else:
            lines.append(raw_line)
    save_raw_section()

    keywords = []
    sections = []
    for section_title, section_lines in raw_sections:
        if section_title.casefold() in {'key terms', 'keywords', 'terms to know'}:
            for match in BOLD_TERM_RE.finditer('\n'.join(section_lines)):
                term = _clean_inline_markup(match.group(1) or match.group(2))
                if 1 <= len(term.split()) <= 5 and len(term) <= 40 and term.casefold() not in {item.casefold() for item in keywords}:
                    keywords.append(term)
                if len(keywords) == 8:
                    break
            continue

        blocks = []
        paragraph_lines = []

        def flush_paragraph():
            if paragraph_lines:
                text = _clean_inline_markup(' '.join(paragraph_lines))
                if text:
                    blocks.append({'type': 'paragraph', 'text': text})
                paragraph_lines.clear()

        for raw_line in section_lines:
            line = raw_line.strip()
            if not line or re.fullmatch(r'[-*_]{3,}', line):
                flush_paragraph()
                continue

            list_match = LIST_ITEM_RE.match(line)
            if list_match:
                flush_paragraph()
                if not blocks or blocks[-1]['type'] != 'list':
                    blocks.append({'type': 'list', 'items': []})
                blocks[-1]['items'].append(_clean_inline_markup(list_match.group(1)))
                continue

            paragraph_lines.append(line)

        flush_paragraph()
        if blocks:
            sections.append({'title': section_title, 'blocks': blocks})

    return sections, keywords