"""Генерація UML-діаграм (клас, варіанти використання, архітектура) для пояснювальної записки."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT = Path(__file__).parent / "img"
OUT.mkdir(exist_ok=True)
F = "C:/Windows/Fonts/"
REG, BOLD, ITAL = F + "arial.ttf", F + "arialbd.ttf", F + "ariali.ttf"
MONO = F + "consola.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


INK = (30, 30, 30)
FILL_C = (255, 250, 225)
FILL_A = (232, 240, 255)
GREY = (90, 90, 90)


class Canvas:
    def __init__(self, w, h):
        self.img = Image.new("RGB", (w, h), "white")
        self.d = ImageDraw.Draw(self.img)

    def save(self, name):
        self.img.save(OUT / name, dpi=(200, 200))

    # --- текст
    def text(self, xy, s, f, fill=INK, anchor="la"):
        self.d.text(xy, s, font=f, fill=fill, anchor=anchor, align="center")

    # --- UML-клас
    def cls(self, x, y, w, title, attrs, methods, abstract=False, fill=FILL_C):
        ft = font(BOLD, 30)
        fta = font(ITAL, 30) if abstract else ft
        fb = font(MONO, 22)
        row = 30
        head = 78 if abstract else 56
        ha = 16 + row * len(attrs) if attrs else 16
        hm = 16 + row * len(methods) if methods else 16
        h = head + ha + hm
        d = self.d
        d.rectangle([x, y, x + w, y + h], fill=fill, outline=INK, width=3)
        d.line([x, y + head, x + w, y + head], fill=INK, width=2)
        d.line([x, y + head + ha, x + w, y + head + ha], fill=INK, width=2)
        cy = y + 28 if not abstract else y + 24
        if abstract:
            self.text((x + w / 2, y + 22), "«abstract»", font(REG, 20), GREY, "mm")
            cy = y + 54
        self.text((x + w / 2, cy), title, fta, INK, "mm")
        for i, a in enumerate(attrs):
            self.text((x + 12, y + head + 8 + i * row), a, fb)
        for i, m in enumerate(methods):
            self.text((x + 12, y + head + ha + 8 + i * row), m, fb)
        return (x, y, x + w, y + h)

    # --- лінії
    def line(self, pts, dash=False, width=3):
        if not dash:
            self.d.line(pts, fill=INK, width=width, joint="curve")
            return
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            length = max(abs(x2 - x1), abs(y2 - y1))
            n = int(length // 16)
            for i in range(0, n, 2):
                a, b = i / max(n, 1), min(i + 1, n) / max(n, 1)
                self.d.line([x1 + (x2 - x1) * a, y1 + (y2 - y1) * a,
                             x1 + (x2 - x1) * b, y1 + (y2 - y1) * b], fill=INK, width=width)

    def triangle_up(self, x, y, s=22):  # вістря вгору у (x,y)
        self.d.polygon([(x, y), (x - s, y + 2 * s), (x + s, y + 2 * s)], fill="white", outline=INK, width=3)

    def diamond_right(self, x, y, s=20, filled=False):  # ромб біля (x,y), що лежить ліворуч від точки
        pts = [(x, y), (x + s, y - s * 0.6), (x + 2 * s, y), (x + s, y + s * 0.6)]
        self.d.polygon(pts, fill=INK if filled else "white", outline=INK, width=3)

    def arrow_head(self, x, y, direction, s=18):
        dx, dy = direction
        px, py = -dy, dx
        pts = [(x, y), (x - dx * 2 * s + px * s, y - dy * 2 * s + py * s),
               (x - dx * 2 * s - px * s, y - dy * 2 * s - py * s)]
        self.d.line([pts[1], pts[0], pts[2]], fill=INK, width=3)

    def inherit(self, child, parents_bottom, bus_y):
        """Лінія успадкування: дочірній (x,y_top) → батьківський (x,y_bottom)."""
        cx = (child[0] + child[2]) // 2
        px = parents_bottom
        self.line([(cx, child[1]), (cx, bus_y), (px[0], bus_y), (px[0], px[1] + 44)])
        self.triangle_up(px[0], px[1])


def class_diagram():
    """Діаграма класів у книжковій орієнтації (вміщується на сторінку A4)."""
    W, H = 2000, 2300
    c = Canvas(W, H)
    d = c.d
    f_title, f_it, f_txt, f_st = font(BOLD, 32), font(ITAL, 32), font(MONO, 25), font(REG, 22)
    row = 34

    def box(x, y, w, title, attrs, methods, abstract=False, fill=FILL_C):
        head = 84 if abstract else 58
        ha = 14 + row * len(attrs) if attrs else 14
        hm = 14 + row * len(methods) if methods else 14
        h = head + ha + hm
        d.rectangle([x, y, x + w, y + h], fill=fill, outline=INK, width=3)
        d.line([x, y + head, x + w, y + head], fill=INK, width=2)
        d.line([x, y + head + ha, x + w, y + head + ha], fill=INK, width=2)
        if abstract:
            c.text((x + w / 2, y + 24), "«abstract»", f_st, GREY, "mm")
            c.text((x + w / 2, y + 58), title, f_it, INK, "mm")
        else:
            c.text((x + w / 2, y + 30), title, f_title, INK, "mm")
        for i, t in enumerate(attrs):
            c.text((x + 12, y + head + 7 + i * row), t, f_txt)
        for i, t in enumerate(methods):
            c.text((x + 12, y + head + ha + 7 + i * row), t, f_txt)
        return (x, y, x + w, y + h)

    def dashed_arrow(pts, label=None, label_xy=None):
        c.line(pts, dash=True)
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        dx, dy = (x2 > x1) - (x2 < x1), (y2 > y1) - (y2 < y1)
        c.arrow_head(x2, y2, (dx, dy))
        if label:
            c.text(label_xy, label, font(ITAL, 24), GREY, "mm")

    # --- верхній ряд: інтерфейс, ферма, сховище
    app = box(20, 60, 470, "App", ["+farm: Farm", "+storage: JsonStorage"],
              ["+launch()", "+run()", "+farm_report() ..."], fill=(245, 235, 255))
    inp = box(20, app[3] + 60, 470, "ConsoleInput", [],
              ["+ask() / ask_int()", "+ask_float() / ask_date()", "+choose(options, title)"],
              fill=(245, 235, 255))
    farm = box(560, 60, 880, "Farm",
               ["+employees: dict[int, Employee]", "+birds: dict[int, Bird]"],
               ["+add_employee() / remove_employee()", "+add_bird() / assign()",
                "+add_record(bird_id, day, value)", "+birds_of(emp_id)",
                "+employee_stats(emp_id)", "+stats() / top_birds(n)",
                "+to_dict() / from_dict()"])
    stor = box(1510, 60, 470, "JsonStorage", ["+path: Path"], ["+save(farm)", "+load(): Farm"],
               fill=(245, 235, 255))
    # --- абстрактні класи
    ry = max(farm[3], inp[3]) + 150
    emp = box(30, ry, 860, "Employee", ["+id: int", "+name: str", "+base_salary: float"],
              ["+role: str", "+salary(bird_count, avg_eff)", "+to_dict()"],
              abstract=True, fill=FILL_A)
    bird = box(1110, ry, 860, "Bird",
               ["+id: int", "+tag: str", "+birth_date: date", "+weight_g: float",
                "+employee_id: int | None", "+records: list[PerformanceRecord]"],
               ["+add_record(day, value)", "+average() / efficiency()", "+describe_metric(): str",
                "+to_dict()"], abstract=True, fill=FILL_A)
    # --- нащадки
    sy = bird[3] + 110
    subs_e = [box(20 + i * 297, sy, 280, n, [a], [m]) for i, (n, a, m) in enumerate(
        [("Worker", "BONUS_PER_BIRD=15", "+salary()"),
         ("Veterinarian", "BONUS_PER_BIRD=25", "+salary()"),
         ("Manager", "PREMIUM_RATE=0.1", "+salary()")])]
    subs_b = [box(1110 + i * 287, sy, 270, n, [a1, a2], ["+describe_metric()"]) for i, (n, a1, a2) in
              enumerate([("LayingHen", "NORM=0.85", "UNIT=яєць/день"),
                         ("Broiler", "NORM=55", "UNIT=г/день"),
                         ("Duck", "NORM=0.70", "UNIT=яєць/день")])]
    # успадкування (порожній трикутник біля базового класу)
    for base, subs in ((emp, subs_e), (bird, subs_b)):
        bx = (base[0] + base[2]) // 2
        bus = sy - 50
        c.line([(bx, base[3] + 44), (bx, bus)])
        c.triangle_up(bx, base[3])
        for s in subs:
            cx = (s[0] + s[2]) // 2
            c.line([(cx, s[1]), (cx, bus), (bx, bus)])
    # --- фабрики та запис показника
    fy = max(s[3] for s in subs_e + subs_b) + 130
    efac = box(30, fy, 860, "EmployeeFactory", ["+TYPES: dict[str, type]"],
               ["+labels(): dict", "+create(kind, emp_id, name, salary)", "+from_dict(data)"],
               fill=(255, 255, 255))
    bfac = box(1110, fy, 560, "BirdFactory", ["+TYPES: dict[str, type]"],
               ["+labels(): dict", "+create(kind, ...)", "+from_dict(data)"], fill=(255, 255, 255))
    rec = box(1110, bfac[3] + 60, 560, "PerformanceRecord", ["+day: date", "+value: float"],
              ["+to_dict() / from_dict()"], fill=(240, 255, 240))
    for fac, subs in ((efac, subs_e), (bfac, subs_b)):
        x = (subs[1][0] + subs[1][2]) // 2
        dashed_arrow([(x, fac[1]), (x, subs[1][3] + 4)], "«create»", (x + 80, fac[1] - 55))
    # --- агрегація Farm ◇— Employee / Bird
    for x, target, label in ((700, emp, "працівники"), (1300, bird, "птиця")):
        c.line([(x, farm[3] + 40), (x, target[1])])
        d.polygon([(x, farm[3]), (x + 13, farm[3] + 20), (x, farm[3] + 40), (x - 13, farm[3] + 20)],
                  fill="white", outline=INK, width=3)
        c.text((x + 16, target[1] - 34), "0..*", font(REG, 24), GREY)
        c.text((x + 16, farm[3] + 50), label, font(REG, 24), GREY)
    # --- асоціація Employee — Bird (відповідальність)
    ay = emp[1] + 200
    c.line([(emp[2], ay), (bird[0], ay)])
    c.text((emp[2] + 10, ay - 34), "0..1", font(REG, 24), GREY)
    c.text((bird[0] - 10, ay - 34), "0..*", font(REG, 24), GREY, "ra")
    c.text(((emp[2] + bird[0]) / 2, ay + 32), "відповідає", font(ITAL, 24), GREY, "mm")
    # --- композиція Bird ◆— PerformanceRecord
    rx, mid = 1830, (rec[1] + rec[3]) // 2
    c.line([(rx, bird[3] + 40), (rx, sy - 75), (1990, sy - 75), (1990, mid), (rec[2], mid)])
    d.polygon([(rx, bird[3]), (rx + 13, bird[3] + 20), (rx, bird[3] + 40), (rx - 13, bird[3] + 20)], fill=INK)
    c.text((rec[2] + 14, mid - 34), "0..*", font(REG, 24), GREY)
    # --- залежності сервісних класів
    dashed_arrow([(app[2], 170), (farm[0] - 2, 170)])
    dashed_arrow([(stor[0], 170), (farm[2] + 2, 170)])
    dashed_arrow([(255, app[3]), (255, inp[1] - 2)])
    dashed_arrow([(400, app[1]), (400, 24), (1745, 24), (1745, stor[1] - 2)])
    # --- легенда
    lx, ly = 40, efac[3] + 70
    c.text((lx, ly), "Умовні позначення:", font(BOLD, 26), INK)
    items = [("агрегація", "agg"), ("композиція", "comp"), ("успадкування", "inh"), ("залежність", "dep")]
    for i, (label, kind) in enumerate(items):
        x = lx + (i % 2) * 420
        y = ly + 55 + (i // 2) * 50
        if kind in ("agg", "comp"):
            d.polygon([(x, y + 14), (x + 20, y + 2), (x + 40, y + 14), (x + 20, y + 26)],
                      fill=INK if kind == "comp" else "white", outline=INK, width=3)
        elif kind == "inh":
            c.triangle_up(x + 20, y, 13)
        else:
            c.line([(x, y + 14), (x + 50, y + 14)], dash=True)
        c.text((x + 70, y), label, font(REG, 26), GREY)
    bottom = max(rec[3], ly + 170) + 30
    c.img = c.img.crop((0, 0, W, bottom))
    c.save("class_diagram.png")


def use_case():
    c = Canvas(2200, 1500)
    d = c.d
    d.rounded_rectangle([420, 40, 1780, 1460], radius=24, outline=INK, width=3)
    c.text((1100, 80), "Автоматизована система обліку птахоферми", font(BOLD, 34), INK, "mm")

    def actor(x, y, label):
        d.ellipse([x - 28, y - 100, x + 28, y - 44], outline=INK, width=4)
        d.line([x, y - 44, x, y + 40], fill=INK, width=4)
        d.line([x - 50, y - 10, x + 50, y - 10], fill=INK, width=4)
        d.line([x, y + 40, x - 40, y + 110], fill=INK, width=4)
        d.line([x, y + 40, x + 40, y + 110], fill=INK, width=4)
        c.text((x, y + 150), label, font(BOLD, 26), INK, "mm")

    ucs_adm = ["Керування працівниками", "Облік птиці", "Закріплення птиці\nза працівником",
               "Метрики ферми", "Метрики персоналу", "Розрахунок оплати праці"]
    ucs_wrk = ["Введення показників\nефективності", "Перегляд показників\nпатиці"]
    ucs_wrk[1] = "Перегляд показників\nптиці"
    pos = {}
    for i, u in enumerate(ucs_adm):
        pos[u] = (900, 230 + i * 190)
    pos[ucs_wrk[0]] = (1450, 400)
    pos[ucs_wrk[1]] = (1450, 800)
    sv = ("Збереження / завантаження\nданих (JSON)", (1450, 1200))
    f = font(REG, 26)
    for u, (x, y) in {**pos, sv[0]: sv[1]}.items():
        d.ellipse([x - 230, y - 62, x + 230, y + 62], fill=FILL_A, outline=INK, width=3)
        c.text((x, y), u, f, INK, "mm")
    actor(210, 520, "Керівник ферми")
    actor(1990, 600, "Птахівник /\nветеринар")
    for u in ucs_adm:
        d.line([260, 520, pos[u][0] - 230, pos[u][1]], fill=INK, width=2)
    for u in ucs_wrk:
        d.line([1940, 600, pos[u][0] + 230, pos[u][1]], fill=INK, width=2)
    c.text((1450, 1300), "використовується при кожній зміні даних", font(ITAL, 24), GREY, "mm")
    c.save("use_case.png")


def architecture():
    c = Canvas(2000, 1300)
    d = c.d
    layers = [
        ("Рівень подання (UI)", "poultry_farm/ui/, main.py", "App: меню і звіти;\nConsoleInput: введення з перевіркою", (225, 238, 255)),
        ("Рівень зберігання", "poultry_farm/storage/", "JsonStorage:\nатомарний запис / читання JSON", (245, 232, 255)),
        ("Рівень бізнес-логіки", "poultry_farm/farm/", "Farm, EmployeeStats, FarmStats:\nоблік, закріплення, метрики", (255, 245, 215)),
        ("Доменна модель", "poultry_farm/staff/, birds/, errors/", "Employee, Bird, їх нащадки та фабрики,\nPerformanceRecord, винятки", (232, 250, 232)),
    ]
    y = 50
    for t, files, desc, col in layers:
        d.rounded_rectangle([200, y, 1500, y + 230], radius=20, fill=col, outline=INK, width=3)
        c.text((850, y + 45), t, font(BOLD, 36), INK, "mm")
        c.text((850, y + 95), files, font(MONO, 26), GREY, "mm")
        c.text((850, y + 160), desc, font(REG, 28), INK, "mm")
        if y < 800:
            d.line([850, y + 230, 850, y + 290], fill=INK, width=4)
            c.arrow_head(850, y + 290, (0, 1))
        y += 290
    # файл
    d.rounded_rectangle([1620, 340, 1950, 540], radius=14, fill=(255, 255, 255), outline=INK, width=3)
    c.text((1785, 420), "data/farm.json", font(MONO, 28), INK, "mm")
    c.text((1785, 470), "(файл даних)", font(REG, 24), GREY, "mm")
    d.line([1500, 455, 1620, 455], fill=INK, width=4)
    c.arrow_head(1620, 455, (1, 0))
    c.save("architecture.png")


if __name__ == "__main__":
    class_diagram()
    use_case()
    architecture()
    print("ok")
