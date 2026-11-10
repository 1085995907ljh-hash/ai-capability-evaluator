import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('inventory', Path(__file__).parents[1] / 'scripts' / 'inventory_inputs.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InventoryTests(unittest.TestCase):
    def test_magic_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'misleading.txt'
            file.write_bytes(b'%PDF-1.7\nexample')
            row = module.inventory([file])['materials'][0]
            self.assertEqual(row['format'], 'pdf')
            self.assertEqual(len(row['sha256']), 64)
            self.assertEqual(row['status'], 'inventoried_not_read')

    def test_symlink_and_size_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'original').write_bytes(b'12345')
            (root / 'alias').symlink_to(root / 'original')
            rows = module.inventory([root], max_bytes=4)['materials']
            self.assertEqual({r['status'] for r in rows}, {'unread_error', 'unread_size_limit'})
            self.assertTrue(all(r['sha256'] is None for r in rows))

    def test_missing_and_truncation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ['a', 'b']:
                (root / name).write_text('x')
            result = module.inventory([root / 'missing', root], max_files=1)
            self.assertEqual(len(result['errors']), 1)
            self.assertTrue(result['truncated'])
            self.assertEqual(len(result['materials']), 1)
