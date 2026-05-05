"""
Parse extracted PDF text into clean English markdown files for docs-en/.
Run from the repo root: python parse_handbook.py
"""
import re
import os

SECTIONS = [
    (1,  "Welcome",                                "01-welcome.md",                5,  5),
    (2,  "Absence Management (Sickness)",          "02-absence-management.md",     6,  16),
    (3,  "Adoption Leave",                         "03-adoption-leave.md",         17, 21),
    (4,  "Anti-Bribery",                           "04-anti-bribery.md",           22, 22),
    (5,  "Bullying and Harassment",                "05-bullying-harassment.md",    23, 27),
    (6,  "Capability & Performance",               "06-capability-performance.md", 28, 32),
    (7,  "Carers Leave",                           "07-carers-leave.md",           33, 34),
    (8,  "Company Vehicle Drivers",                "08-company-vehicles.md",       35, 40),
    (9,  "Compassionate Leave",                    "09-compassionate-leave.md",    41, 42),
    (10, "Cycle to Work Scheme",                   "10-cycle-to-work.md",          43, 44),
    (11, "Data Protection at Work",                "11-data-protection.md",        45, 48),
    (12, "Dependency and Emergency Leave",         "12-dependency-emergency.md",   49, 50),
    (13, "Disciplinary",                           "13-disciplinary.md",           51, 55),
    (14, "Drugs and Alcohol Abuse",                "14-drugs-alcohol.md",          56, 59),
    (15, "Equal Opportunities & Diversity",        "15-equal-opportunities.md",    60, 61),
    (16, "Electric Vehicle Lease Scheme",          "16-electric-vehicle.md",       62, 63),
    (17, "Expenses",                               "17-expenses.md",               64, 66),
    (18, "Eyesight Test",                          "18-eyesight-test.md",          67, 68),
    (19, "Flexi Time",                             "19-flexi-time.md",             69, 71),
    (20, "Food in the Workplace",                  "20-food-workplace.md",         72, 72),
    (21, "Grievance",                              "21-grievance.md",              73, 75),
    (22, "Health & Safety",                        "22-health-safety.md",          76, 77),
    (23, "Holiday",                                "23-holiday.md",                78, 79),
    (24, "IT Systems Use",                         "24-it-systems.md",             80, 85),
    (25, "Key Holder",                             "25-key-holder.md",             86, 87),
    (26, "Leave for Public & Civic Duties",        "26-public-civic-duties.md",    88, 90),
    (27, "Lieu Day",                               "27-lieu-day.md",               91, 92),
    (28, "Maternity & Pregnancy",                  "28-maternity-pregnancy.md",    93, 100),
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

# Patterns for repeated section header lines at the top of each page, e.g.
# "SECTION 2:  ABSENCE MANAGEMENT POLICY & PROCEDURE"
# "SECTION 8:  COMPANY VEHICLE DRIVERS POLICY & PROCEDURE"
SECTION_HEADER_RE = re.compile(r'^SECTION\s+\d+[:.]\s+', re.IGNORECASE)
# Standalone page number (1-3 digits on a line by themselves)
PAGE_NUM_RE = re.compile(r'^\d{1,3}$')
# Subsection heading: starts with "X.Y" or "X.Y.Z" followed by text or tab
SUBSEC_HEADING_RE = re.compile(r'^(\d+\.\d+(?:\.\d+)*(?:\.\d+)?)\s+(.*)')
# Bullet point
BULLET_RE = re.compile(r'^[•·]\s*(.*)')
# Lettered item: "a.", "b.", etc.
LETTER_ITEM_RE = re.compile(r'^([a-z])\.\s+(.*)')
# Form field lines (contain patterns like ".........." or are very short labels)
FORM_DOTS_RE = re.compile(r'\.{10,}')
# Yes/No labels that appear in forms
YES_NO_RE = re.compile(r'^(Yes|No)\s*$')


def load_pages(path):
    """Return a dict mapping page_number -> page_text."""
    pages = {}
    current_page = None
    current_lines = []
    page_re = re.compile(r'^---\s*PAGE\s+(\d+)\s*---')
    with open(path, encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.rstrip('\n')
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


def is_noise_line(line):
    """Return True for lines that should be dropped (page nos, repeated headers, form artefacts)."""
    stripped = line.strip()
    if not stripped:
        return False
    if PAGE_NUM_RE.match(stripped):
        return True
    if SECTION_HEADER_RE.match(stripped):
        return True
    if FORM_DOTS_RE.search(stripped):
        return True
    if YES_NO_RE.match(stripped):
        return True
    # Drop lines that look like form field labels without content
    # e.g. "Employee Name", "Department", "Date:" standing alone with no useful context
    # We keep these when they appear inside policy text but the form blocks are mostly
    # flagged by the dots pattern above.
    return False


def lines_to_markdown(sec_num, sec_title, raw_lines):
    """Convert a list of raw text lines to markdown."""
    out = []
    out.append(f'---')
    out.append(f'title: "{sec_title}"')
    out.append(f'---')
    out.append(f'')
    out.append(f'# Section {sec_num}: {sec_title}')
    out.append(f'')

    prev_blank = True

    for line in raw_lines:
        if is_noise_line(line):
            continue

        stripped = line.strip()

        if not stripped:
            if not prev_blank:
                out.append('')
                prev_blank = True
            continue

        prev_blank = False

        # Subsection heading (e.g. "2.1  About this Policy")
        m = SUBSEC_HEADING_RE.match(stripped)
        if m:
            num = m.group(1)
            title = m.group(2).strip()
            depth = num.count('.')
            if depth == 1 and title:
                out.append(f'')
                out.append(f'## {num} {title}')
                out.append(f'')
            elif title:
                out.append(f'')
                out.append(f'**{num}** {title}')
                out.append(f'')
            elif num:
                # numbered clause with content on next line
                out.append(f'')
                out.append(f'**{num}**')
            prev_blank = False
            continue

        # Bullet points
        m = BULLET_RE.match(stripped)
        if m:
            out.append(f'- {m.group(1).strip()}')
            prev_blank = False
            continue

        # Lettered list items
        m = LETTER_ITEM_RE.match(stripped)
        if m:
            out.append(f'- **{m.group(1)})** {m.group(2).strip()}')
            prev_blank = False
            continue

        # ALL-CAPS lines (likely subsection headers without numbers)
        if stripped == stripped.upper() and len(stripped) > 4 and stripped.isalpha() is False:
            # Could be a titled block like "COMPANY DRIVING HOURS GUIDELINES"
            # Emit as a subheading if it looks substantial
            if len(stripped.split()) >= 2 and not stripped.startswith('N.B'):
                out.append(f'')
                out.append(f'### {stripped.title()}')
                out.append(f'')
                prev_blank = False
                continue

        out.append(stripped)
        prev_blank = False

    # Collapse runs of 3+ blank lines into 2
    result = []
    blank_count = 0
    for line in out:
        if line == '':
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)

    return '\n'.join(result)


def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(repo_root, '_extracted_text.txt')
    output_dir = os.path.join(repo_root, 'docs-en')
    css_src = os.path.join(repo_root, 'docs', 'stylesheets', 'extra.css')
    css_dst_dir = os.path.join(output_dir, 'stylesheets')
    img_dst_dir = os.path.join(output_dir, 'img')

    print("Loading pages...")
    pages = load_pages(input_file)
    max_page = max(pages.keys())
    print(f"  Found {len(pages)} pages (up to page {max_page})")

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(css_dst_dir, exist_ok=True)
    os.makedirs(img_dst_dir, exist_ok=True)

    # Copy extra.css
    import shutil
    shutil.copy2(css_src, os.path.join(css_dst_dir, 'extra.css'))
    print("  Copied extra.css")

    # Copy logo
    logo_src = os.path.join(repo_root, 'Stovax_Gazco_Logo.png')
    if os.path.exists(logo_src):
        shutil.copy2(logo_src, os.path.join(img_dst_dir, 'logo.png'))
        # Also copy to docs/img for the French site
        fr_img_dir = os.path.join(repo_root, 'docs', 'img')
        os.makedirs(fr_img_dir, exist_ok=True)
        shutil.copy2(logo_src, os.path.join(fr_img_dir, 'logo.png'))
        print("  Copied logo to docs-en/img/ and docs/img/")

    print("\nGenerating section files...")
    for sec_num, sec_title, filename, page_start, page_end in SECTIONS:
        # Gather raw lines for this section
        raw_lines = []
        for p in range(page_start, min(page_end + 1, max_page + 1)):
            if p in pages:
                raw_lines.extend(pages[p].split('\n'))
                raw_lines.append('')  # blank between pages

        md = lines_to_markdown(sec_num, sec_title, raw_lines)
        out_path = os.path.join(output_dir, filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"  {filename}  ({len(md)} chars)")

    # Generate index.md
    index_md = generate_index()
    with open(os.path.join(output_dir, 'index.md'), 'w', encoding='utf-8') as f:
        f.write(index_md)
    print("  index.md")

    print(f"\nDone. {len(SECTIONS) + 1} files written to {output_dir}/")


def generate_index():
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


if __name__ == '__main__':
    main()
