# -*- coding: utf-8 -*-
"""Збирає пояснювальну записку курсової роботи у форматі .docx."""
import io
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest.mock import patch

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import content as C  # noqa: E402
from poultry_farm.farm import Farm  # noqa: E402
from poultry_farm.storage import JsonStorage  # noqa: E402
from poultry_farm.ui import App  # noqa: E402

FONT = "Times New Roman"
IMG = Path(__file__).parent / "img"
OUT = ROOT / "Курсова_робота_ООП_Птахоферма.docx"
STUDENT = "Павло Павлишин"
GROUP = "Кн-31"
SUPERVISOR = "А. Татомир"
TEXT_WIDTH = 16.5
REPO_PLACEHOLDER = "[ПОСИЛАННЯ НА РЕПОЗИТОРІЙ]"


# --------------------------------------------------------------- допоміжне
def run_font(run, size=14, bold=None, italic=None, name=FONT):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    run.font.color.rgb = RGBColor(0, 0, 0)


def clear_theme_fonts(style):
    """Прибирає шрифти теми, щоб заголовки не підхоплювали Calibri."""
    rpr = style.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    for a in list(rf.attrib):
        if a.endswith("Theme"):
            del rf.attrib[a]
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), FONT)


def set_style(doc):
    st = doc.styles["Normal"]
    st.font.size = Pt(14)
    pf = st.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(0)
    pf.space_before = Pt(0)
    clear_theme_fonts(st)
    for name, align in (("Heading 1", WD_ALIGN_PARAGRAPH.CENTER), ("Heading 2", WD_ALIGN_PARAGRAPH.LEFT)):
        h = doc.styles[name]
        h.font.size = Pt(14)
        h.font.bold = True
        h.font.italic = False
        h.font.color.rgb = RGBColor(0, 0, 0)
        hp = h.paragraph_format
        hp.alignment = align
        hp.space_before = Pt(12 if name == "Heading 2" else 0)
        hp.space_after = Pt(12)
        hp.line_spacing = 1.5
        hp.keep_with_next = True
        clear_theme_fonts(h)
    doc.styles["Heading 2"].paragraph_format.first_line_indent = Cm(1.25)


def add_text(p, text, size=14, bold=False, italic=False):
    """Додає текст; позначку {REPO} замінює посиланням або жовтим нагадуванням."""
    parts = text.split("{REPO}")
    for i, part in enumerate(parts):
        if part:
            run_font(p.add_run(part), size, bold, italic)
        if i < len(parts) - 1:
            r = p.add_run(C.REPO_URL or REPO_PLACEHOLDER)
            run_font(r, size, bold, italic)
            if not C.REPO_URL:
                r.font.highlight_color = WD_COLOR_INDEX.YELLOW


def para(doc, text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=True, size=14, bold=False,
         italic=False, spacing=1.5, after=0, before=0, keep=False):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing = spacing
    pf.space_after = Pt(after)
    pf.space_before = Pt(before)
    pf.first_line_indent = Cm(1.25) if indent else None
    pf.keep_with_next = keep
    if text:
        add_text(p, text, size, bold, italic)
    return p


def center(doc, text, size=14, bold=False, after=0, before=0):
    return para(doc, text, WD_ALIGN_PARAGRAPH.CENTER, False, size, bold, spacing=1.0,
                after=after, before=before)


def heading(doc, text, level, new_page=False):
    p = doc.add_heading("", level=level)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        r = p.add_run(line)
        if i < len(lines) - 1:
            r.add_break()
    p.paragraph_format.page_break_before = new_page
    return p


def plain_title(doc, text):
    """Заголовок структурного елемента, який не входить до змісту."""
    p = para(doc, text, WD_ALIGN_PARAGRAPH.CENTER, False, bold=True, after=12)
    p.paragraph_format.page_break_before = True
    p.paragraph_format.keep_with_next = True
    return p


def add_field(paragraph, instr, placeholder, size=14):
    r = paragraph.add_run()
    run_font(r, size)
    for kind, txt in (("begin", None), ("instr", instr), ("separate", None),
                      ("text", placeholder), ("end", None)):
        if kind in ("begin", "separate", "end"):
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        elif kind == "instr":
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = txt
        else:
            el = OxmlElement("w:t")
            el.text = txt
        r._r.append(el)


def shade(paragraph, fill="F2F2F2"):
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pPr.append(shd)
    bdr = OxmlElement("w:pBdr")
    for side in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:space"), "4")
        e.set(qn("w:color"), "808080")
        bdr.append(e)
    pPr.append(bdr)


def code_block(doc, text, size=10):
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pf = p.paragraph_format
        pf.line_spacing = 1.0
        pf.space_after = Pt(0)
        pf.left_indent = Cm(0.3)
        pf.right_indent = Cm(0.3)
        if i < len(lines) - 1:
            pf.keep_with_next = len(lines) < 30
        run_font(p.add_run(line if line else " "), size, name="Courier New")
        shade(p)


def caption(doc, text):
    """Підпис рисунка (під рисунком, по центру)."""
    return para(doc, text, WD_ALIGN_PARAGRAPH.CENTER, False, spacing=1.0, after=12, before=6)


def fix_table_width(t, widths_cm):
    """Фіксована ширина таблиці та колонок (інакше Word стискає таблицю)."""
    tblPr = t._tbl.tblPr
    for tag in ("w:tblW", "w:tblLayout"):
        old = tblPr.find(qn(tag))
        if old is not None:
            tblPr.remove(old)
    tw = OxmlElement("w:tblW")
    tw.set(qn("w:w"), str(int(sum(widths_cm) * 567)))
    tw.set(qn("w:type"), "dxa")
    tblPr.append(tw)
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths_cm):
        gc.set(qn("w:w"), str(int(w * 567)))
    for row in t.rows:
        for cell, w in zip(row.cells, widths_cm):
            cell.width = Cm(w)


def table(doc, cap, header, rows, widths):
    """Звичайна таблиця без декоративного оформлення; назва над таблицею."""
    k = TEXT_WIDTH / sum(widths)
    widths = [w * k for w in widths]
    para(doc, cap, WD_ALIGN_PARAGRAPH.LEFT, False, spacing=1.0, after=6, before=12, keep=True)
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, h in enumerate(header):
        cp = t.rows[0].cells[i].paragraphs[0]
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.paragraph_format.line_spacing = 1.0
        run_font(cp.add_run(h), 12, True)
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    t.rows[0]._tr.get_or_add_trPr().append(th)
    for row in rows:
        cells = t.add_row().cells
        t.rows[-1]._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for i, val in enumerate(row):
            cp = cells[i].paragraphs[0]
            cp.alignment = WD_ALIGN_PARAGRAPH.LEFT
            cp.paragraph_format.line_spacing = 1.0
            run_font(cp.add_run(val), 12)
    fix_table_width(t, widths)
    para(doc, "", spacing=1.0, indent=False, after=6)


def figure(doc, name, cap, width_cm):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(6)
    p.add_run().add_picture(str(IMG / name), width=Cm(width_cm))
    caption(doc, cap)


# -------------------------------------------------------- дані для рисунків
def capture_outputs():
    """Виконує реальні дії програми над тестовими даними й повертає їхній вивід."""
    farm = Farm()
    farm.add_employee("Veterinarian", "Олена Мельник", 15000)
    farm.add_employee("Manager", "Марія Шевчук", 18000)
    farm.add_employee("Worker", "Іван Коваль", 12000)
    farm.add_bird("LayingHen", "UA-001", date(2026, 3, 1), 1750, 1)
    farm.add_bird("Broiler", "BR-001", date(2026, 9, 1), 950, 1)
    farm.add_bird("Duck", "DK-001", date(2026, 4, 10), 2100, 2)
    farm.add_bird("LayingHen", "UA-002", date(2026, 3, 5), 1700, 3)
    for bid, day, v in [(1, 1, 0.82), (1, 2, 0.9), (2, 1, 58), (2, 2, 61), (3, 1, 0.5),
                        (4, 1, 0.8), (4, 2, 0.88)]:
        farm.add_record(bid, date(2026, 10, day), v)
    app = App(farm, JsonStorage(Path(tempfile.mkdtemp()) / "f.json"))

    def grab(fn):
        buf = io.StringIO()
        with redirect_stdout(buf):
            fn()
        return buf.getvalue().rstrip()

    out = {"@FARM_REPORT": grab(app.farm_report), "@STAFF_REPORT": grab(app.staff_report)}
    res = subprocess.run([sys.executable, "-I", "-m", "unittest", "-v"], cwd=ROOT,
                         capture_output=True, text=True, encoding="utf-8",
                         env={"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1",
                              "SYSTEMROOT": "C:\\Windows"})
    text = (res.stderr or res.stdout).strip()
    short = []
    for ln in text.splitlines():
        if ln.startswith("test_"):
            name, _, _ = ln.partition(" (")
            short.append(f"{name} ... {ln.rsplit('...', 1)[-1].strip()}")
        else:
            short.append(ln)
    out["@TEST_OUTPUT"] = "\n".join(short)
    if "OK" not in text or "Ran 18 tests" not in text:
        raise SystemExit("Тести не пройшли — записку не збираю:\n" + text)
    return out


# ------------------------------------------------------------------ збірка
def title_page(doc):
    center(doc, "МІНІСТЕРСТВО ОСВІТИ І НАУКИ УКРАЇНИ", bold=True, after=6)
    center(doc, "Львівський національний університет ветеринарної медицини")
    center(doc, "та біотехнологій імені С. З. Ґжицького", after=6)
    center(doc, "Кафедра інформаційних технологій", after=110)
    center(doc, "КУРСОВА РОБОТА", size=16, bold=True, after=10)
    center(doc, "з дисципліни «Об'єктно-орієнтоване програмування»", after=10)
    center(doc, "на тему: «" + C.TOPIC + "»", bold=True, after=80)
    for text, gap in ((f"Студент групи {GROUP}", 0), (STUDENT, 12), (f"Керівник роботи: {SUPERVISOR}", 12),
                      ("Національна шкала: ______________", 0), ("Кількість балів: ______", 0),
                      ("Оцінка ECTS: ______", 12), ("Члени комісії:", 0),
                      ("__________  ______________", 0), ("__________  ______________", 0),
                      ("__________  ______________", 0)):
        p = para(doc, text, WD_ALIGN_PARAGRAPH.LEFT, False, spacing=1.15, after=gap)
        p.paragraph_format.left_indent = Cm(8)
    center(doc, "Львів – 2026", before=70)


FORMULA_NO = [0, 0]
LISTING_NO = [""]


def render_items(doc, items, outputs, appendix=None):
    listing = 0
    for it in items:
        kind = it[0]
        if kind == "p":
            para(doc, it[1])
        elif kind == "formula":
            FORMULA_NO[1] += 1
            p = para(doc, "", WD_ALIGN_PARAGRAPH.LEFT, False, before=3, after=3)
            stops = p.paragraph_format.tab_stops
            stops.add_tab_stop(Cm(TEXT_WIDTH / 2), WD_TAB_ALIGNMENT.CENTER)
            stops.add_tab_stop(Cm(TEXT_WIDTH), WD_TAB_ALIGNMENT.RIGHT)
            run_font(p.add_run("\t" + it[1].rstrip(",.") + "\t"), 14, italic=True)
            run_font(p.add_run(f"({FORMULA_NO[0]}.{FORMULA_NO[1]})"), 14)
        elif kind == "fig":
            figure(doc, it[1], it[2], it[3])
        elif kind == "fig_code":
            code_block(doc, outputs.get(it[2], it[2]))
            caption(doc, it[1])
        elif kind == "table":
            table(doc, it[1], it[2], it[3], it[4])
        elif kind == "code":
            code_block(doc, it[1])
            para(doc, "", spacing=1.0, indent=False, after=6)
        elif kind == "code_file":
            listing += 1
            para(doc, f"Лістинг {appendix}.{listing} — {it[1]} (файл {it[2]})",
                 WD_ALIGN_PARAGRAPH.LEFT, False, spacing=1.0, before=12, after=6, keep=True)
            code_block(doc, (ROOT / it[2]).read_text(encoding="utf-8").rstrip(), size=9)


def count_items():
    figs = tabs = 0
    groups = [items for ch in (C.CH1, C.CH2, C.CH3, C.CH4) for _, items in ch["sections"]]
    groups += [items for _, _, items in C.APPENDICES]
    for items in groups:
        for it in items:
            if it[0] in ("fig", "fig_code"):
                figs += 1
            elif it[0] == "table":
                tabs += 1
    return figs, tabs


def appendix_word(n):
    return "додаток" if n == 1 else ("додатки" if 2 <= n <= 4 else "додатків")


def build(pages=0):
    outputs = capture_outputs()
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin, sec.right_margin = Cm(3), Cm(1.5)
    sec.top_margin = sec.bottom_margin = Cm(2)
    sec.different_first_page_header_footer = True
    set_style(doc)

    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_field(fp, "PAGE", "1", 12)

    title_page(doc)

    # --- реферат
    figs, tabs = count_items()
    n_app = len(C.APPENDICES)
    plain_title(doc, "РЕФЕРАТ")
    para(doc, f"Пояснювальна записка до курсової роботи: {pages if pages else '__'} с., {figs} рис., "
              f"{tabs} табл., {len(C.REFERENCES)} джерел, {n_app} {appendix_word(n_app)}.")
    for t in C.REFERAT:
        para(doc, t)
    para(doc, "КЛЮЧОВІ СЛОВА: " + C.ABSTRACT_KEYWORDS + ".")

    # --- зміст
    plain_title(doc, "ЗМІСТ")
    add_field(doc.add_paragraph(), r'TOC \o "1-2" \h \z \u',
              "Щоб оновити зміст: правий клік → «Оновити поле».")

    # --- вступ і розділи
    heading(doc, "ВСТУП", 1, new_page=True)
    for t in C.INTRO:
        para(doc, t)

    for n, ch in enumerate((C.CH1, C.CH2, C.CH3, C.CH4), 1):
        FORMULA_NO[:] = [n, 0]
        heading(doc, f"РОЗДІЛ {n}\n{ch['title']}", 1, new_page=True)
        for title, items in ch["sections"]:
            heading(doc, title, 2)
            render_items(doc, items, outputs)

    heading(doc, "ВИСНОВКИ", 1, new_page=True)
    for t in C.CONCLUSIONS:
        para(doc, t)

    heading(doc, "БІБЛІОГРАФІЧНИЙ СПИСОК", 1, new_page=True)
    for i, ref in enumerate(C.REFERENCES, 1):
        para(doc, f"{i}. {ref}")

    # --- додатки: окрема титульна сторінка «ДОДАТКИ», далі кожен додаток з нової сторінки
    p = heading(doc, "ДОДАТКИ", 1, new_page=True)
    p.paragraph_format.space_before = Cm(10)
    for letter, title, items in C.APPENDICES:
        h = heading(doc, f"ДОДАТОК {letter}\n{title}", 2, new_page=True)
        h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        h.paragraph_format.first_line_indent = None
        h.paragraph_format.space_before = Pt(0)
        render_items(doc, items, outputs, appendix=letter)

    doc.core_properties.title = C.TOPIC
    doc.core_properties.author = STUDENT
    doc.save(OUT)
    return OUT


if __name__ == "__main__":
    pg = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    print(build(pg))
