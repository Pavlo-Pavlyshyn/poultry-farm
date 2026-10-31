import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from poultry_farm.birds import Broiler, LayingHen
from poultry_farm.errors import FarmError, NotFoundError, ValidationError
from poultry_farm.farm import Farm
from poultry_farm.staff import Manager, Worker
from poultry_farm.storage import JsonStorage
from poultry_farm.ui import App


class FarmTestCase(unittest.TestCase):
    """Спільні тестові дані."""
    D = date(2024, 1, 1)

    @classmethod
    def sample_farm(cls):
        f = Farm()
        w = f.add_employee("Worker", "Іван Коваль", 12000)
        f.add_employee("Veterinarian", "Олена Мельник", 15000)
        h = f.add_bird("LayingHen", "H-1", cls.D, 1800, w.id)
        b = f.add_bird("Broiler", "B-1", cls.D, 900, w.id)
        return f, w, h, b


class ModelTests(FarmTestCase):
    def test_efficiency_laying_hen(self):
        h = LayingHen(1, "H", self.D, 1500)
        h.add_record(date(2024, 2, 1), 1)
        h.add_record(date(2024, 2, 2), 0)
        self.assertAlmostEqual(h.average(), 0.5)
        self.assertAlmostEqual(h.efficiency(), 0.5 / 0.85 * 100)

    def test_efficiency_without_records(self):
        self.assertEqual(Broiler(1, "B", self.D, 800).efficiency(), 0.0)

    def test_negative_value_rejected(self):
        with self.assertRaises(ValidationError):
            Broiler(1, "B", self.D, 800).add_record(date(2024, 2, 1), -5)

    def test_record_before_birth_rejected(self):
        with self.assertRaises(ValidationError):
            Broiler(1, "B", self.D, 800).add_record(date(2023, 12, 1), 5)

    def test_future_dates_rejected(self):
        with self.assertRaises(ValidationError):
            LayingHen(1, "H", date(2999, 1, 1), 1500)
        with self.assertRaises(ValidationError):
            Broiler(1, "B", self.D, 800).add_record(date(2999, 1, 1), 5)

    def test_empty_tag_and_weight(self):
        with self.assertRaises(ValidationError):
            LayingHen(1, " ", self.D, 1000)
        with self.assertRaises(ValidationError):
            LayingHen(1, "T", self.D, 0)

    def test_polymorphic_salary(self):
        self.assertEqual(Worker(1, "A", 10000).salary(10, 0), 10150)
        self.assertEqual(Manager(2, "M", 10000).salary(0, 120), 11000)
        self.assertEqual(Manager(2, "M", 10000).salary(0, 80), 10000)


class FarmTests(FarmTestCase):
    def test_assignment_and_birds_of(self):
        f, w, h, b = self.sample_farm()
        self.assertEqual(len(f.birds_of(w.id)), 2)
        f.assign(h.id, 2)
        self.assertEqual([x.id for x in f.birds_of(w.id)], [b.id])
        f.assign(h.id, None)
        self.assertIsNone(h.employee_id)

    def test_unknown_ids(self):
        f, *_ = self.sample_farm()
        with self.assertRaises(NotFoundError):
            f.get_bird(99)
        with self.assertRaises(NotFoundError):
            f.assign(1, 99)
        with self.assertRaises(NotFoundError):
            f.add_bird("Duck", "D", self.D, 1000, employee_id=99)

    def test_duplicate_tag(self):
        f, *_ = self.sample_farm()
        with self.assertRaises(ValidationError):
            f.add_bird("Duck", "H-1", self.D, 1000)

    def test_remove_employee_frees_birds(self):
        f, w, *_ = self.sample_farm()
        self.assertEqual(f.remove_employee(w.id), 2)
        self.assertEqual(f.stats().unassigned, 2)

    def test_stats(self):
        f, w, h, b = self.sample_farm()
        f.add_record(h.id, date(2024, 2, 1), 1)
        f.add_record(b.id, date(2024, 2, 1), 55)
        s = f.stats()
        self.assertEqual((s.employees, s.birds, s.unassigned), (2, 2, 0))
        self.assertEqual(s.by_species, {"Курка-несучка": 1, "Бройлер": 1})
        expected = (1 / 0.85 * 100 + 100) / 2
        self.assertAlmostEqual(s.avg_efficiency, expected)
        es = f.employee_stats(w.id)
        self.assertEqual(es.bird_count, 2)
        self.assertAlmostEqual(es.salary, 12000 + 15 * 2)
        self.assertEqual(f.top_birds(1)[0].id, h.id)

    def test_empty_farm_stats(self):
        s = Farm().stats()
        self.assertEqual((s.birds, s.avg_efficiency, s.total_salary), (0, 0.0, 0.0))


class StorageTests(FarmTestCase):
    def test_roundtrip(self):
        f, w, h, b = self.sample_farm()
        f.add_record(h.id, date(2024, 2, 1), 1)
        with tempfile.TemporaryDirectory() as d:
            st = JsonStorage(Path(d) / "sub" / "farm.json")
            st.save(f)
            g = st.load()
        self.assertEqual(g.to_dict(), f.to_dict())
        self.assertIsInstance(g.get_bird(h.id), LayingHen)
        self.assertEqual(g.get_bird(h.id).records[0].value, 1.0)
        self.assertEqual(g.add_bird("Duck", "D-1", self.D, 900).id, 3)

    def test_missing_file_gives_empty_farm(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(len(JsonStorage(Path(d) / "x.json").load().birds), 0)

    def test_corrupted_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.json"
            p.write_text("{не json", encoding="utf-8")
            with self.assertRaises(FarmError):
                JsonStorage(p).load()


class CliTests(FarmTestCase):
    def test_list_birds_with_dangling_employee(self):
        f, w, *_ = self.sample_farm()
        data = f.to_dict()
        data["employees"] = []  # файл відредаговано вручну: відповідального немає
        farm = Farm.from_dict(data)
        with tempfile.TemporaryDirectory() as d, patch("builtins.print") as pr:
            App(farm, JsonStorage(Path(d) / "f.json")).list_birds()
        self.assertEqual(pr.call_count, 2)

    def test_session_persists(self):
        inputs = iter(["1", "1", "Петро", "10000",              # додати птахівника
                       "4", "1", "T-1", "2024-01-01", "1500", "1",  # додати несучку
                       "7", "1", "0,9", "2024-02-01",           # показник
                       "9", "10", "abc", "3", "77", "0"])       # звіти, помилки, вихід
        with tempfile.TemporaryDirectory() as d:
            st = JsonStorage(Path(d) / "farm.json")
            with patch("builtins.input", lambda _="": next(inputs)), patch("builtins.print"):
                App(st.load(), st).run()
            g = st.load()
        self.assertEqual(len(g.employees), 1)
        self.assertEqual(g.get_bird(1).records[0].value, 0.9)
        self.assertEqual(g.get_bird(1).employee_id, 1)


if __name__ == "__main__":
    unittest.main()
