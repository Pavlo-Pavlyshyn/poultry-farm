"""Консольний інтерфейс користувача."""
from pathlib import Path

from ..birds import BirdFactory
from ..errors import FarmError
from ..farm import Farm
from ..staff import EmployeeFactory
from ..storage import JsonStorage
from .console_input import ConsoleInput as In


class App:
    """Головне меню програми та обробники його пунктів."""
    MENU = """
===== ПТАХОФЕРМА: ОБЛІК =====
 1. Додати працівника        6. Закріпити птицю за працівником
 2. Список працівників       7. Ввести показник ефективності
 3. Видалити працівника      8. Показники птиці
 4. Додати птицю             9. Метрики ферми
 5. Список птиці            10. Метрики персоналу
 0. Вийти
"""
    DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "farm.json"

    def __init__(self, farm: Farm, storage: JsonStorage):
        self.farm = farm
        self.storage = storage

    @classmethod
    def launch(cls) -> None:
        """Точка входу: завантажує дані з файлу та запускає меню."""
        storage = JsonStorage(cls.DATA_FILE)
        try:
            farm = storage.load()
        except FarmError as exc:
            print(f"Помилка завантаження: {exc}")
            return
        cls(farm, storage).run()

    # --- дії
    def add_employee(self):
        kind = In.choose(EmployeeFactory.labels(), "Посада")
        emp = self.farm.add_employee(kind, In.ask("Ім'я: "), In.ask_float("Оклад, грн: "))
        print(f"Додано: {emp}")

    def list_employees(self):
        if not self.farm.employees:
            print("Працівників немає.")
        for e in self.farm.employees.values():
            print(f"  {e}, оклад {e.base_salary:.2f} грн, птиці: {len(self.farm.birds_of(e.id))}")

    def remove_employee(self):
        freed = self.farm.remove_employee(In.ask_int("ID працівника: "))
        print(f"Видалено. Птиці без відповідального: {freed}")

    def add_bird(self):
        kind = In.choose(BirdFactory.labels(), "Вид птиці")
        tag = In.ask("Бирка: ")
        born = In.ask_date("Дата народження")
        weight = In.ask_float("Маса, г: ")
        emp_id = In.ask_optional_int("ID відповідального (Enter — без): ")
        bird = self.farm.add_bird(kind, tag, born, weight, emp_id)
        print(f"Додано: {bird}")

    def list_birds(self):
        if not self.farm.birds:
            print("Птиці немає.")
        for b in self.farm.birds.values():
            emp = self.farm.employees.get(b.employee_id)
            who = emp.name if emp else "—"
            print(f"  {b}, маса {b.weight_g:.0f} г, вік {b.age_days()} дн., відповідальний: {who}")

    def assign(self):
        emp_id = In.ask_optional_int("ID працівника (Enter — зняти закріплення): ")
        self.farm.assign(In.ask_int("ID птиці: "), emp_id)
        print("Закріплення оновлено.")

    def add_record(self):
        bird = self.farm.get_bird(In.ask_int("ID птиці: "))
        value = In.ask_float(f"{bird.METRIC} ({bird.UNIT}): ")
        self.farm.add_record(bird.id, In.ask_date("Дата"), value)
        print("Показник збережено.")

    def bird_report(self):
        bird = self.farm.get_bird(In.ask_int("ID птиці: "))
        print(f"{bird}: {bird.describe_metric()}")
        print(f"  Ефективність: {bird.efficiency():.1f} % від норми, записів: {len(bird.records)}")
        for r in bird.records[-10:]:
            print(f"    {r.day}: {r.value:g}")

    def farm_report(self):
        s = self.farm.stats()
        print(f"Працівників: {s.employees}; птиці: {s.birds} (без відповідального: {s.unassigned})")
        for sp, n in s.by_species.items():
            print(f"  {sp}: {n}")
        print(f"Середня ефективність ферми: {s.avg_efficiency:.1f} %")
        print(f"Фонд оплати праці: {s.total_salary:.2f} грн")
        top = self.farm.top_birds(3)
        if top:
            print("Найкраща птиця:")
            for b in top:
                print(f"  {b} — {b.efficiency():.1f} %")

    def staff_report(self):
        rows = self.farm.all_employee_stats()
        if not rows:
            print("Працівників немає.")
        for r in rows:
            print(f"  {r.employee}: птиці {r.bird_count}, ефективність "
                  f"{r.avg_efficiency:.1f} %, оплата {r.salary:.2f} грн")

    # --- цикл
    def run(self):
        actions = {"1": self.add_employee, "2": self.list_employees, "3": self.remove_employee,
                   "4": self.add_bird, "5": self.list_birds, "6": self.assign,
                   "7": self.add_record, "8": self.bird_report, "9": self.farm_report,
                   "10": self.staff_report}
        mutating = {"1", "3", "4", "6", "7"}
        while True:
            print(self.MENU)
            try:
                choice = In.ask("Ваш вибір: ")
            except EOFError:
                choice = "0"
            if choice == "0":
                self.storage.save(self.farm)
                print("Дані збережено. До побачення!")
                return
            action = actions.get(choice)
            if action is None:
                print("Невірний пункт меню.")
                continue
            try:
                action()
                if choice in mutating:
                    self.storage.save(self.farm)
            except FarmError as exc:
                print(f"Помилка: {exc}")
            except (KeyboardInterrupt, EOFError):
                print("\nСкасовано.")
