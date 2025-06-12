import json
import pathlib
import shutil
import tempfile
import unittest

import pandas as pd

from shelfie import Shelf, Field


class TestWithTmpDir(unittest.TestCase):

    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)


def dummy_default_factory():
    return "dummy"


class TestWithShelf(TestWithTmpDir):

    def setUp(self):
        super().setUp()
        self.shelf = Shelf(
            root=self.test_dir,
            fields=["a", Field("b", default="B"), Field("c", default_factory=dummy_default_factory)],
            attributes=["attribute"],
        )

class TestShelfWrite(TestWithShelf):
    """Test suite for file operations"""

    def test_create_requires_all_keys(self):
        with self.assertRaises(ValueError):
            self.shelf.create(attribute="test")

        with self.assertRaises(ValueError):
            # a is not set
            self.shelf.create(b=2, attribute="test")

    def test_create_requires_all_attributes(self):
        with self.assertRaises(ValueError):
            self.shelf.create(a="A")

    def test_create_with_default(self):
        self.record = self.shelf.create(a="A", attribute="test")
        expected_dir = self.test_dir / "A" / "B" / "dummy"
        self.assertTrue(expected_dir.exists())
        self.assertTrue(expected_dir.is_dir())

        # Check metadata file exists and only contains attribute=test
        metadata_file = expected_dir / "metadata.json"
        self.assertTrue(metadata_file.exists())
        self.assertTrue(metadata_file.is_file())

        metadata = json.loads(metadata_file.read_text())
        self.assertDictEqual(metadata, {"attribute": "test"})

    def test_create_additional_metadata(self):
        self.record = self.shelf.create(a="A", other=[1, 2], attribute="test")
        metadata_file = self.test_dir / "A" / "B" / "dummy" / "metadata.json"
        metadata = json.loads(metadata_file.read_text())
        self.assertDictEqual(metadata, {"other": [1, 2], "attribute": "test"})


    def test_create_data(self):
        self.record = self.shelf.create(a="A", other=[1, 2], attribute="test")
        df = pd.DataFrame({
            "A": [1, 2, 3],
        })
        self.record.attach(df, "data.csv")
        data_file = self.test_dir / "A" / "B" / "dummy" / "data.csv"
        self.assertTrue(data_file.exists())
        self.assertTrue(data_file.is_file())


    def test_metadata_exists_warns(self):
        self.record = self.shelf.create(a="A", other=[1, 2], attribute="test")
        with self.assertWarns(UserWarning):
            self.shelf.create(a="A", other=[1, 2], attribute="test")


    def test_shelfie_pkl_exists_after_record_creation(self):
        self.shelf.create(a="A", other=[1, 2], attribute="test")
        shlf_file = self.test_dir / ".shelfie.pkl"
        self.assertTrue(shlf_file.exists())



if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2)