"""Offline tests of seed preparation; fixtures reuse existing MemoryDB words."""
import hashlib
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "prepare_dictionary", Path(__file__).resolve().parents[1] / "tools/prepare_dictionary.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DictionaryPreparationTests(unittest.TestCase):
    def test_normalizes_deduplicates_and_sorts_existing_fixture_words(self):
        result = module.build_seed(b" perro \ncasas\nCASAS\n\n")
        self.assertEqual(result.count("('CASAS')"), 1)
        self.assertLess(result.index("('CASAS')"), result.index("('PERRO')"))
        self.assertIn("Distinct normalized words: 2", result)
        self.assertIn("ON CONFLICT (palabra) DO NOTHING", result)

    def test_records_source_hash_and_is_reproducible(self):
        raw = b"CASAS\nPERRO\n"
        first = module.build_seed(raw)
        self.assertEqual(first, module.build_seed(raw))
        self.assertIn(hashlib.sha256(raw).hexdigest(), first)

    def test_rejects_wrong_alphabet_length_and_sql_delimiters(self):
        for word in ("CASA", "12345", "CA SS", "CAFÉS", "CAßS", "ßAAAA", "A'AAS"):
            with self.subTest(word=word), self.assertRaises(ValueError):
                module.build_seed(word.encode("utf-8"))

    def test_rejects_empty_or_non_utf8_sources(self):
        for raw in (b"", b" \n\n", b"\xff"):
            with self.subTest(raw=raw), self.assertRaises((ValueError, UnicodeError)):
                module.build_seed(raw)

    def test_result_contains_only_dictionary_writes(self):
        result = module.build_seed(b"CASAS\n")
        self.assertIn("INSERT INTO public.palabras", result)
        for forbidden in ("DELETE", "UPDATE", "DROP", "GRANT", "CREATE TABLE"):
            self.assertNotIn(forbidden, result)
