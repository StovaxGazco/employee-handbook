"""
Handbook parser — generates clean English markdown from extracted PDF text.
Run from the repo root: python3 parse_handbook.py
"""
import re
import os
import shutil

# ---------------------------------------------------------------------------
# Section definitions: (number, title, filename, page_start, page_end)
# ---------------------------------------------------------------------------
SECTIONS = [
    (1,  "Welcome",                                "01-welcome.md",                5,   5),
    (2,  "Absence Management (Sickness)",          "02-absence-management.md",     6,   16),
    (3,  "Adoption Leave",                         "03-adoption-leave.md",         17,  21),
    (4,  "Anti-Bribery",                           "04-anti-bribery.md",           22,  22),
    (5,  "Bullying and Harassment",                "05-bullying-harassment.md",    23,  27),
    (6,  "Capability & Performance",               "06-capability-performance.md", 28,  32),
    (7,  "Carers Leave",                           "07-carers-leave.md",           33,  34),
    (8,  "Company Vehicle Drivers",                "08-company-vehicles.md",       35,  40),
    (9,  "Compassionate Leave",                    "09-compassionate-leave.md",    41,  42),
    (10, "Cycle to Work Scheme",                   "10-cycle-to-work.md",          43,  44),
    (11, "Data Protection at Work",                "11-data-protection.md",        45,  48),
    (12, "Dependency and Emergency Leave",         "12-dependency-emergency.md",   49,  50),
    (13, "Disciplinary",                           "13-disciplinary.md",           51,  55),
    (14, "Drugs and Alcohol Abuse",                "14-drugs-alcohol.md",          56,  59),
    (15, "Equal Opportunities & Diversity",        "15-equal-opportunities.md",    60,  61),
    (16, "Electric Vehicle Lease Scheme",          "16-electric-vehicle.md",       62,  63),
    (17, "Expenses",                               "17-expenses.md",               64,  66),
    (18, "Eyesight Test",                          "18-eyesight-test.md",          67,  68),
    (19, "Flexi Time",                             "19-flexi-time.md",             69,  71),
    (20, "Food in the Workplace",                  "20-food-workplace.md",         72,  72),
    (21, "Grievance",                              "21-grievance.md",              73,  75),
    (22, "Health & Safety",                        "22-health-safety.md",          76,  77),
    (23, "Holiday",                                "23-holiday.md",                78,  79),
    (24, "IT Systems Use",                         "24-it-systems.md",             80,  85),
    (25, "Key Holder",                             "25-key-holder.md",             86,  87),
    (26, "Leave for Public & Civic Duties",        "26-public-civic-duties.md",    88,  90),
    (27, "Lieu Day",                               "27-lieu-day.md",               91,  92),
    (28, "Maternity & Pregnancy",                  "28-maternity-pregnancy.md",    93,  100),
    (29, "Mental Health & Wellbeing",              "29-mental-health.md",          101, 104),
    (30, "Mobile Phone",                           "30-mobile-phone.md",           105, 105),
    (31, "Pandemic Management at Work",            "31-pandemic.md",               106, 109),
    (32, "Parental Leave (Statutory)",             "32-parental-leave.md",         110, 112),
    (33, "Parental Bereavement",                   "33-parental-bereavement.md",   113, 115),
    (34, "Paternity",                              "34-paternity.md",              116, 118),
    (35, "Probationary Period",                    "35-probationary-period.md",    119, 125),
    (36, "Right to Request Flexible Working",      "36-flexible-working.md",       126, 130),
    (37, "Right to Request Time off to Train",     "37-time-off-to-train.md",      131, 134),
    (38, "Shared Parental Leave",                  "38-shared-parental-leave.md",  135, 139),
    (39, "Smoking",                                "39-smoking.md",                140, 140),
    (40, "Social Media",                           "40-social-media.md",           141, 142),
    (41, "Special Leave",                          "41-special-leave.md",          143, 145),
    (42, "Staff Purchase",                         "42-staff-purchase.md",         146, 147),
    (43, "Staff Suggestion Scheme",                "43-suggestion-scheme.md",      148, 149),
    (44, "Stress",                                 "44-stress.md",                 150, 153),
    (45, "Travel",                                 "45-travel.md",                 154, 155),
    (46, "Uniform Dress Code",                     "46-uniform-dress-code.md",     156, 157),
    (47, "Weather — Adverse Conditions",           "47-adverse-weather.md",        158, 158),
    (48, "Whistle Blowing",                        "48-whistle-blowing.md",        159, 160),
    (49, "Working from Home",                      "49-working-from-home.md",      161, 163),
    (50, "Working Time Regulations",               "50-working-time-regulations.md", 164, 168),
    (51, "Work Related Functions & Events",        "51-work-related-functions.md", 169, 9999),
]

# Map section number → (filename, display title)
SECTION_MAP = {n: (fn, title) for n, title, fn, _, _ in SECTIONS}

# ---------------------------------------------------------------------------
# Cross-link rules: (regex_pattern, replacement)
# Longest/most-specific patterns first to avoid partial replacements.
# Each tuple: (compiled_re, link_text, filename)
# We do NOT auto-link when the section is currently being rendered (avoids
# self-referential links); the formatter handles that.
# ---------------------------------------------------------------------------
# Build "(Section X)" / "Section X" numeric patterns
def _section_link_re(n):
    fn, title = SECTION_MAP[n]
    # matches "Section 34" or "(Section 34)" — case-sensitive
    return (
        re.compile(r'(?<!\[)\bSection ' + str(n) + r'\b(?!\])'),
        f'Section {n}',
        fn,
    )

SECTION_NUM_LINKS = [_section_link_re(n) for n in range(1, 52)]

# Named policy cross-links (longer phrases first)
_NAMED = [
    ("Whistle Blowing Policy and Procedure",           "48-whistle-blowing.md"),
    ("Whistle Blowing Policy",                         "48-whistle-blowing.md"),
    ("Whistle Blowing",                                "48-whistle-blowing.md"),
    ("Right to Request Flexible Working Policy",       "36-flexible-working.md"),
    ("Right to Request Flexible Working",              "36-flexible-working.md"),
    ("Flexible Working Policy and Procedure",          "36-flexible-working.md"),
    ("Flexible Working Policy",                        "36-flexible-working.md"),
    ("Shared Parental Leave Policy and Procedure",     "38-shared-parental-leave.md"),
    ("Shared Parental Leave Policy",                   "38-shared-parental-leave.md"),
    ("Shared Parental Leave",                          "38-shared-parental-leave.md"),
    ("Disciplinary Policy and Procedure",              "13-disciplinary.md"),
    ("Disciplinary Procedure",                         "13-disciplinary.md"),
    ("Disciplinary Policy",                            "13-disciplinary.md"),
    ("Grievance Policy and Procedure",                 "21-grievance.md"),
    ("Grievance Procedure",                            "21-grievance.md"),
    ("Grievance Policy",                               "21-grievance.md"),
    ("Absence Management Policy and Procedure",        "02-absence-management.md"),
    ("Absence Management Policy",                      "02-absence-management.md"),
    ("Sickness Absence Policy",                        "02-absence-management.md"),
    ("Adoption Leave Policy and Procedure",            "03-adoption-leave.md"),
    ("Adoption Leave Policy",                          "03-adoption-leave.md"),
    ("Anti-Bribery Policy and Procedure",              "04-anti-bribery.md"),
    ("Anti-Bribery Policy",                            "04-anti-bribery.md"),
    ("Bullying and Harassment Policy and Procedure",   "05-bullying-harassment.md"),
    ("Bullying and Harassment Policy",                 "05-bullying-harassment.md"),
    ("Capability & Performance Policy and Procedure",  "06-capability-performance.md"),
    ("Capability and Performance Policy",              "06-capability-performance.md"),
    ("Carers Leave Policy",                            "07-carers-leave.md"),
    ("Carers Leave",                                   "07-carers-leave.md"),
    ("Company Vehicle Drivers Policy",                 "08-company-vehicles.md"),
    ("Compassionate Leave Policy",                     "09-compassionate-leave.md"),
    ("Cycle to Work Scheme",                           "10-cycle-to-work.md"),
    ("Data Protection Policy",                         "11-data-protection.md"),
    ("Dependency and Emergency Leave Policy",          "12-dependency-emergency.md"),
    ("Drugs and Alcohol Policy",                       "14-drugs-alcohol.md"),
    ("Equal Opportunities Policy",                     "15-equal-opportunities.md"),
    ("Electric Vehicle Lease Scheme",                  "16-electric-vehicle.md"),
    ("Expenses Policy",                                "17-expenses.md"),
    ("Eyesight Test Policy",                           "18-eyesight-test.md"),
    ("Flexi Time Policy",                              "19-flexi-time.md"),
    ("Flexi Time",                                     "19-flexi-time.md"),
    ("Health and Safety Policy",                       "22-health-safety.md"),
    ("Health & Safety",                                "22-health-safety.md"),
    ("IT Systems Use Policy",                          "24-it-systems.md"),
    ("Maternity Policy and Procedure",                 "28-maternity-pregnancy.md"),
    ("Maternity Policy",                               "28-maternity-pregnancy.md"),
    ("Maternity and Pregnancy Policy",                 "28-maternity-pregnancy.md"),
    ("Maternity Leave",                                "28-maternity-pregnancy.md"),
    ("Mental Health Policy",                           "29-mental-health.md"),
    ("Pandemic Management Policy",                     "31-pandemic.md"),
    ("Parental Bereavement Policy",                    "33-parental-bereavement.md"),
    ("Parental Bereavement",                           "33-parental-bereavement.md"),
    ("Paternity Policy and Procedure",                 "34-paternity.md"),
    ("Paternity Policy",                               "34-paternity.md"),
    ("Paternity Leave",                                "34-paternity.md"),
    ("Probationary Period Policy",                     "35-probationary-period.md"),
    ("Social Media Policy",                            "40-social-media.md"),
    ("Special Leave Policy",                           "41-special-leave.md"),
    ("Staff Suggestion Scheme",                        "43-suggestion-scheme.md"),
    ("Stress Policy",                                  "44-stress.md"),
    ("Working from Home Policy",                       "49-working-from-home.md"),
    ("Working Time Regulations",                       "50-working-time-regulations.md"),
]

NAMED_LINKS = [
    (re.compile(r'(?<!\[)\b' + re.escape(phrase) + r'\b(?!\])'), phrase, fn)
    for phrase, fn in _NAMED
]

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

# Matches a line that is ONLY a subsection number (e.g. "2.1", "2.1.1", "8.3.")
# with optional trailing whitespace / tab
NUM_ONLY_RE = re.compile(r'^(\d+\.[\d.]*)\s*$')

# Matches a line that starts with a subsection number then a tab or 1+ spaces then text
# e.g. "2.18\tLong Term Absence"  or  "32.1.1  The Company wishes..."  or  "34.4.4. Employees..."
NUM_INLINE_RE = re.compile(r'^(\d+\.[\d.]*)(?:\t| +)(.+)$')

# Repeated section header at top of each page
SECTION_HEADER_RE = re.compile(r'^SECTION\s+\d+[:.]\s+', re.IGNORECASE)

# Standalone page number
PAGE_NUM_RE = re.compile(r'^\d{1,3}$')

# Bullet point
BULLET_RE = re.compile(r'^[•·]\s*(.*)')

# Lettered list item
LETTER_ITEM_RE = re.compile(r'^([a-z])\.\s+(.*)')

# Pure dot/underscore filler lines (no meaningful label)
FORM_DOTS_RE = re.compile(r'^[._\s]{8,}$')

# Any line containing 5+ consecutive dots/underscores — treat as form field(s)
FORM_HAS_DOTS_RE = re.compile(r'[._]{5,}')

# Known sentence-starter words that mean the next line is body text, not a heading title
_BODY_STARTS = (
    'The ', 'This ', 'If ', 'Where ', 'In ', 'An ', 'A ', 'Each ', 'For ',
    'When ', 'Upon ', 'As ', 'At ', 'Employees ', 'Employee ', 'Company ',
    'All ', 'No ', 'Any ', 'Once ', 'During ', 'Following ', 'Unless ',
    'Should ', 'Subject ', 'Under ', 'It ', 'Please ', 'Note ',
)


def looks_like_heading_title(line: str) -> bool:
    """True if `line` looks like a section heading title rather than body text."""
    s = line.strip()
    if not s or len(s) > 90:
        return False
    if s.endswith(('.', ',', ';', ':')):
        return False
    if any(s.startswith(w) for w in _BODY_STARTS):
        return False
    return True


def is_noise(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if PAGE_NUM_RE.match(s):
        return True
    if SECTION_HEADER_RE.match(s):
        return True
    if FORM_DOTS_RE.search(s):
        return True
    return False


def num_depth(num_str: str) -> int:
    """Return the nesting depth: '2.1' → 1, '2.1.1' → 2, '2.1.1.1' → 3"""
    return num_str.rstrip('.').count('.')


def apply_crosslinks(text: str, current_file: str) -> str:
    """Apply section cross-links to a line of text."""
    # Named links first (more specific)
    for pattern, phrase, fn in NAMED_LINKS:
        if fn == current_file:
            continue  # don't self-link
        text = pattern.sub(f'[{phrase}]({fn})', text)
    # Numeric Section X links
    for pattern, label, fn in SECTION_NUM_LINKS:
        if fn == current_file:
            continue
        text = pattern.sub(f'[{label}]({fn})', text)
    return text


# ---------------------------------------------------------------------------
# Main converter
# ---------------------------------------------------------------------------

def load_pages(path: str) -> dict:
    pages = {}
    current_page = None
    current_lines = []
    page_re = re.compile(r'^---\s*PAGE\s+(\d+)\s*---')
    with open(path, encoding='utf-8') as f:
        for raw in f:
            line = raw.rstrip('\n')
            m = page_re.match(line.strip())
            if m:
                if current_page is not None:
                    pages[current_page] = '\n'.join(current_lines)
                current_page = int(m.group(1))
                current_lines = []
            else:
                current_lines.append(line)
    if current_page is not None:
        pages[current_page] = '\n'.join(current_lines)
    return pages


def convert_section(sec_num: int, sec_title: str, filename: str, raw_lines: list) -> str:
    """Convert raw lines for one section into clean markdown."""

    out = [
        '---',
        f'title: "{sec_title}"',
        '---',
        '',
        f'# Section {sec_num}: {sec_title}',
        '',
    ]

    lines = raw_lines
    n = len(lines)
    i = 0
    in_form_table = False  # track whether we're inside a markdown table block

    def peek_next_content(start):
        """Return (index, stripped_line) of the next non-empty, non-noise line."""
        j = start
        while j < n:
            s = lines[j].strip()
            if s and not is_noise(lines[j]):
                return j, s
            j += 1
        return n, ''

    def collect_body(start):
        """Collect contiguous body-text continuation lines from `start`.
        Stops at blank lines, noise, or any structural marker.
        Returns (end_index, joined_text).
        """
        parts = []
        k = start
        while k < n:
            cs = lines[k].strip()
            if not cs:
                break
            if is_noise(lines[k]):
                k += 1
                continue
            if (NUM_ONLY_RE.match(cs) or NUM_INLINE_RE.match(cs) or
                    BULLET_RE.match(cs) or LETTER_ITEM_RE.match(cs)):
                break
            if cs == cs.upper() and len(cs.split()) >= 2 and not cs.startswith('N.B') and len(cs) > 6:
                break
            parts.append(cs)
            k += 1
        return k, ' '.join(parts)

    # Skip any leading top-level section number (e.g. "2.") and its title.
    while i < n:
        s = lines[i].strip()
        if re.match(r'^\d+\.\s*$', s):
            i += 1
            j, ns = peek_next_content(i)
            if ns and looks_like_heading_title(ns):
                i = j + 1
            continue
        break

    while i < n:
        raw = lines[i]
        s = raw.strip()

        # --- Skip noise lines ---
        if not s:
            if in_form_table:
                in_form_table = False
            out.append('')
            i += 1
            continue
        if is_noise(raw):
            i += 1
            continue

        # --- Number-only line? ---
        m = NUM_ONLY_RE.match(s)
        if m:
            num = m.group(1).rstrip('.')
            depth = num_depth(num + '.')  # treat "2.1" as depth 1
            # Peek at next non-empty line to decide if it's a heading title
            j, next_s = peek_next_content(i + 1)

            if depth == 0:
                # Top-level section number (e.g. "2.") — skip it and its title
                if next_s and looks_like_heading_title(next_s):
                    i = j + 1
                else:
                    i += 1
                continue

            if depth == 1:
                # X.Y → H2 heading; next line is the heading title if it looks like one
                if next_s and looks_like_heading_title(next_s):
                    title_text = apply_crosslinks(next_s, filename)
                    out.append('')
                    out.append(f'## {num} {title_text}')
                    out.append('')
                    i = j + 1  # consume the title line
                else:
                    out.append('')
                    out.append(f'## {num}')
                    out.append('')
                    i += 1
            else:
                # X.Y.Z → bold clause number, body text inline
                if next_s and looks_like_heading_title(next_s):
                    # Short descriptive title; body text may follow after
                    title_text = apply_crosslinks(next_s, filename)
                    out.append(f'\n**{num}** {title_text}')
                    i = j + 1
                else:
                    # Body text on next line(s) — collect and join continuations
                    k, body_text = collect_body(j)
                    if body_text:
                        body_text = apply_crosslinks(body_text, filename)
                        out.append(f'\n**{num}** {body_text}')
                        i = k
                    else:
                        out.append(f'\n**{num}**')
                        i += 1
            continue

        # --- Number + tab/spaces + inline text on same line? ---
        m = NUM_INLINE_RE.match(s)
        if m:
            num = m.group(1).rstrip('.')
            first_text = m.group(2).strip()
            depth = num_depth(num + '.')
            # Collect any continuation lines
            k, cont_text = collect_body(i + 1)
            full_text = (first_text + ' ' + cont_text).strip() if cont_text else first_text
            full_text = apply_crosslinks(full_text, filename)
            if depth == 1:
                out.append('')
                out.append(f'## {num} {full_text}')
                out.append('')
            else:
                out.append(f'\n**{num}** {full_text}')
            i = k
            continue

        # --- Bullet point ---
        m = BULLET_RE.match(s)
        if m:
            content = m.group(1).strip()
            k, cont_text = collect_body(i + 1)
            if cont_text:
                content = content + ' ' + cont_text
            content = apply_crosslinks(content, filename)
            out.append(f'- {content}')
            i = k
            continue

        # --- Lettered list item ---
        m = LETTER_ITEM_RE.match(s)
        if m:
            content = m.group(2).strip()
            k, cont_text = collect_body(i + 1)
            if cont_text:
                content = content + ' ' + cont_text
            content = apply_crosslinks(content, filename)
            out.append(f'- **{m.group(1)})** {content}')
            i = k
            continue

        # --- ALL-CAPS subsection label (e.g. "COMPANY DRIVING HOURS GUIDELINES") ---
        if s == s.upper() and len(s.split()) >= 2 and not s.startswith('N.B') and len(s) > 6:
            if in_form_table:
                in_form_table = False
            out.append('')
            out.append(f'### {s.title()}')
            out.append('')
            i += 1
            continue

        # --- Form field line: any line with 5+ consecutive dots → table row(s) ---
        if FORM_HAS_DOTS_RE.search(s):
            # Split on dot runs to extract all field labels from the line
            parts = re.split(r'\s*[._]{5,}\s*', s)
            labels = [p.strip().rstrip(':').strip() for p in parts
                      if p.strip() and p.strip() not in ('or', 'and', '*', '')]
            if labels:
                if not in_form_table:
                    out.append('')
                    out.append('| Field | Details |')
                    out.append('|---|---|')
                    in_form_table = True
                for label in labels:
                    out.append(f'| {label} | |')
            i += 1
            continue

        # --- Regular paragraph line ---
        if in_form_table:
            in_form_table = False
        linked = apply_crosslinks(s, filename)
        out.append(linked)
        i += 1

    # Collapse 3+ consecutive blank lines to 2
    result = []
    blanks = 0
    for line in out:
        if line == '':
            blanks += 1
            if blanks <= 2:
                result.append(line)
        else:
            blanks = 0
            result.append(line)

    return '\n'.join(result)


# ---------------------------------------------------------------------------
# Index page
# ---------------------------------------------------------------------------

def generate_index() -> str:
    rows = '\n'.join(
        f'| [Section {n}]({fn}) | {title} |'
        for n, title, fn, _, _ in SECTIONS
    )
    return f'''---
title: "Home"
---

# Employee Handbook

**Stovax Group — Stovax Limited and Gazco Limited**

---

Welcome to the Stovax Group Employee Handbook. Together with your Contract of Employment, this handbook contains important information about what we expect from you and what you can expect from us. It also sets out the policies and procedures that will be followed in a variety of different circumstances.

The sections are organised in alphabetical order. Click a section below to go directly to it.

---

## Contents

| Section | Title |
|---------|-------|
{rows}

---

*The Human Resources Team is always available to provide guidance and help. Please do not hesitate to contact us.*
'''


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    input_file  = os.path.join(repo_root, '_extracted_text.txt')
    output_dir  = os.path.join(repo_root, 'docs-en')
    css_src     = os.path.join(repo_root, 'docs', 'stylesheets', 'extra.css')
    css_dst_dir = os.path.join(output_dir, 'stylesheets')
    img_dst_dir = os.path.join(output_dir, 'img')
    fr_img_dir  = os.path.join(repo_root, 'docs', 'img')

    os.makedirs(output_dir,  exist_ok=True)
    os.makedirs(css_dst_dir, exist_ok=True)
    os.makedirs(img_dst_dir, exist_ok=True)
    os.makedirs(fr_img_dir,  exist_ok=True)

    shutil.copy2(css_src, os.path.join(css_dst_dir, 'extra.css'))

    # Logo handling
    dark_logo  = os.path.join(repo_root, 'Stovax_Gazco_Logo-dark.png')
    light_logo = os.path.join(repo_root, 'Stovax_Gazco_Logo.png')
    logo_to_use = dark_logo if os.path.exists(dark_logo) else light_logo
    shutil.copy2(logo_to_use, os.path.join(img_dst_dir, 'logo.png'))
    shutil.copy2(logo_to_use, os.path.join(fr_img_dir,  'logo.png'))
    print(f'  Logo: {os.path.basename(logo_to_use)}')

    print('Loading pages...')
    pages = load_pages(input_file)
    max_page = max(pages.keys())
    print(f'  {len(pages)} pages (up to {max_page})')

    print('Generating section files...')
    for sec_num, sec_title, filename, page_start, page_end in SECTIONS:
        raw_lines = []
        for p in range(page_start, min(page_end + 1, max_page + 1)):
            if p in pages:
                raw_lines.extend(pages[p].split('\n'))
                raw_lines.append('')

        md = convert_section(sec_num, sec_title, filename, raw_lines)
        out_path = os.path.join(output_dir, filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(md)

        # Count headings as a quality check
        h2 = md.count('\n## ')
        h3 = md.count('\n### ')
        bold = md.count('\n**')
        print(f'  {filename:<45}  H2={h2:2d}  H3={h3:2d}  bold={bold:2d}')

    with open(os.path.join(output_dir, 'index.md'), 'w', encoding='utf-8') as f:
        f.write(generate_index())
    print('  index.md')
    print(f'\nDone. Written to {output_dir}/')


if __name__ == '__main__':
    main()
