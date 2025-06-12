import json
import pathlib
import shutil
import tempfile
import unittest

import numpy as np
import pandas as pd

from shelfie import Shelf, Field, DateField, TimestampField, load_from_shelf


class TestWithTmpDir(unittest.TestCase):
    """Base class that provides temporary directory setup/teardown."""

    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)


def dummy_default_factory():
    """Test helper for default factory."""
    return "dummy"


class TestWithShelf(TestWithTmpDir):
    """Base class that sets up a test shelf."""

    def setUp(self):
        super().setUp()
        self.shelf = Shelf(
            root=self.test_dir,
            fields=["a", Field("b", default="B"), Field("c", default_factory=dummy_default_factory)],
            attributes=["attribute"],
        )


class TestShelfInitialization(TestWithTmpDir):
    """Test shelf initialization and configuration."""

    def test_shelf_with_string_fields(self):
        """Test creating shelf with only string field names."""
        shelf = Shelf(
            root=self.test_dir,
            fields=["field1", "field2", "field3"],
            attributes=["attr1"]
        )

        self.assertEqual(len(shelf.field_names), 3)
        self.assertEqual(shelf.field_names, ["field1", "field2", "field3"])
        self.assertTrue(self.test_dir.exists())

    def test_shelf_with_field_objects(self):
        """Test creating shelf with Field objects."""
        shelf = Shelf(
            root=self.test_dir,
            fields=[Field("f1"), Field("f2", default="default"), Field("f3", default_factory=lambda: "factory")],
            attributes=["attr1"]
        )

        self.assertEqual(len(shelf.field_names), 3)
        self.assertEqual(shelf.field_names, ["f1", "f2", "f3"])

    def test_shelf_mixed_fields(self):
        """Test creating shelf with mixed string and Field objects."""
        shelf = Shelf(
            root=self.test_dir,
            fields=["string_field", Field("field_obj", default="test")],
            attributes=[]
        )

        self.assertEqual(len(shelf.field_names), 2)
        self.assertEqual(shelf.field_names, ["string_field", "field_obj"])

    def test_shelf_invalid_field_type(self):
        """Test that invalid field types raise ValueError."""
        with self.assertRaises(ValueError) as cm:
            Shelf(
                root=self.test_dir,
                fields=["valid", 123, "also_valid"],  # 123 is invalid
                attributes=[]
            )
        self.assertIn("Fields must be either strings or Field objects", str(cm.exception))

    def test_shelf_no_attributes(self):
        """Test creating shelf without attributes."""
        shelf = Shelf(
            root=self.test_dir,
            fields=["field1"],
            attributes=None
        )
        self.assertEqual(shelf.attributes, [])

    def test_shelf_custom_metadata_name(self):
        """Test shelf with custom metadata filename."""
        shelf = Shelf(
            root=self.test_dir,
            fields=["field1"],
            attributes=["attr1"],
            metadata_name="custom_meta"
        )
        self.assertEqual(shelf.metadata_name, "custom_meta")


class TestFieldBehavior(unittest.TestCase):
    """Test Field class behavior."""

    def test_field_with_default_value(self):
        """Test field with default value."""
        field = Field("test", default="default_val")
        self.assertEqual(field.get_value(), "default_val")
        self.assertEqual(field.get_value("provided"), "provided")

    def test_field_with_default_factory(self):
        """Test field with default factory."""
        field = Field("test", default_factory=lambda: "factory_val")
        self.assertEqual(field.get_value(), "factory_val")
        self.assertEqual(field.get_value("provided"), "provided")

    def test_field_factory_over_default(self):
        """Test that factory takes precedence over default."""
        field = Field("test", default="default", default_factory=lambda: "factory")
        self.assertEqual(field.get_value(), "factory")

    def test_field_no_default_no_value(self):
        """Test field without default when no value provided."""
        field = Field("test")
        with self.assertRaises(ValueError) as cm:
            field.get_value()
        self.assertIn("Either a value must be provided", str(cm.exception))

    def test_date_field(self):
        """Test DateField generates date format."""
        field = DateField("date")
        value = field.get_value()
        # Should be in YYYY-MM-DD format
        self.assertRegex(value, r'\d{4}-\d{2}-\d{2}')

    def test_timestamp_field(self):
        """Test TimestampField generates timestamp format."""
        field = TimestampField("timestamp")
        value = field.get_value()
        # Should be in YYYY-MM-DD_HH-MM-SS format
        self.assertRegex(value, r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}')

    def test_field_str_representation(self):
        """Test Field string representation."""
        field = Field("test_field")
        self.assertEqual(str(field), "Field(test_field)")


class TestShelfWrite(TestWithShelf):
    """Test suite for creating records and writing data."""

    def test_create_requires_all_keys(self):
        """Test that missing field values raise ValueError."""
        with self.assertRaises(ValueError):
            self.shelf.create(attribute="test")  # Missing 'a'

        with self.assertRaises(ValueError):
            self.shelf.create(b=2, attribute="test")  # Missing 'a'

    def test_create_requires_all_attributes(self):
        """Test that missing attributes raise ValueError."""
        with self.assertRaises(ValueError) as cm:
            self.shelf.create(a="A")
        self.assertIn("attribute is a required attribute", str(cm.exception))

    def test_create_with_defaults(self):
        """Test record creation with default values."""
        record = self.shelf.create(a="A", attribute="test")
        expected_dir = self.test_dir / "A" / "B" / "dummy"

        self.assertTrue(expected_dir.exists())
        self.assertTrue(expected_dir.is_dir())

        # Check metadata
        metadata_file = expected_dir / "metadata.json"
        self.assertTrue(metadata_file.exists())

        with open(metadata_file) as f:
            metadata = json.load(f)
        self.assertEqual(metadata, {"attribute": "test"})

    def test_create_override_defaults(self):
        """Test overriding default field values."""
        record = self.shelf.create(a="A", b="CustomB", c="CustomC", attribute="test")
        expected_dir = self.test_dir / "A" / "CustomB" / "CustomC"

        self.assertTrue(expected_dir.exists())

    def test_create_additional_metadata(self):
        """Test storing additional metadata beyond required attributes."""
        record = self.shelf.create(a="A", other=[1, 2], extra="info", attribute="test")
        metadata_file = self.test_dir / "A" / "B" / "dummy" / "metadata.json"

        with open(metadata_file) as f:
            metadata = json.load(f)

        expected = {"other": [1, 2], "extra": "info", "attribute": "test"}
        self.assertEqual(metadata, expected)

    def test_create_numpy_types_in_metadata(self):
        """Test that numpy types are properly serialized to JSON."""
        record = self.shelf.create(
            a="A",
            attribute="test",
            numpy_int=np.int64(42),
            numpy_float=np.float64(3.14),
            numpy_array=np.array([1, 2, 3]),
            numpy_nan=np.nan
        )

        metadata_file = self.test_dir / "A" / "B" / "dummy" / "metadata.json"
        with open(metadata_file) as f:
            metadata = json.load(f)

        self.assertEqual(metadata["numpy_int"], 42)
        self.assertEqual(metadata["numpy_float"], 3.14)
        self.assertEqual(metadata["numpy_array"], [1, 2, 3])
        self.assertTrue(np.isnan(metadata["numpy_nan"]))

    def test_attach_csv_data(self):
        """Test attaching CSV data."""
        record = self.shelf.create(a="A", attribute="test")
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        record.attach(df, "data.csv")

        data_file = self.test_dir / "A" / "B" / "dummy" / "data.csv"
        self.assertTrue(data_file.exists())

        # Verify data can be read back
        loaded_df = pd.read_csv(data_file, index_col=0)
        pd.testing.assert_frame_equal(df, loaded_df)

    def test_attach_multiple_files(self):
        """Test attaching multiple files to same record."""
        record = self.shelf.create(a="A", attribute="test")

        df1 = pd.DataFrame({"x": [1, 2]})
        df2 = pd.DataFrame({"y": [3, 4]})

        record.attach(df1, "data1.csv")
        record.attach(df2, "data2.csv")

        base_path = self.test_dir / "A" / "B" / "dummy"
        self.assertTrue((base_path / "data1.csv").exists())
        self.assertTrue((base_path / "data2.csv").exists())

    def test_attach_updates_metadata(self):
        """Test that attaching files updates metadata with file paths."""
        record = self.shelf.create(a="A", attribute="test")
        df = pd.DataFrame({"col": [1, 2, 3]})
        record.attach(df, "results.csv")

        metadata_file = self.test_dir / "A" / "B" / "dummy" / "metadata.json"
        with open(metadata_file) as f:
            metadata = json.load(f)

        self.assertIn("results_path__", metadata)
        expected_path = str(self.test_dir / "A" / "B" / "dummy" / "results.csv")
        self.assertEqual(metadata["results_path__"], expected_path)

    def test_metadata_exists_warning(self):
        """Test warning when metadata file already exists."""
        self.shelf.create(a="A", attribute="test1")

        with self.assertWarns(UserWarning) as cm:
            self.shelf.create(a="A", attribute="test2")

        self.assertIn("Metadata file already exists", str(cm.warning))

    def test_shelf_pickle_created(self):
        """Test that .shelfie.pkl file is created after record creation."""
        self.shelf.create(a="A", attribute="test")
        shelf_file = self.test_dir / ".shelfie.pkl"
        self.assertTrue(shelf_file.exists())


class TestShelfRead(TestWithShelf):
    """Test suite for reading data back from shelf."""

    def setUp(self):
        super().setUp()
        # Create test records
        self.record1 = self.shelf.create(a="A1", attribute="test1")
        self.record2 = self.shelf.create(a="A2", b="B2", attribute="test2")

    def test_load_metadata_only(self):
        """Test loading shelf with only metadata."""
        dfs = load_from_shelf(self.test_dir)

        self.assertEqual(len(dfs), 1)
        self.assertIn("metadata", dfs)

        metadata_df = dfs["metadata"]
        self.assertEqual(len(metadata_df), 2)
        self.assertSetEqual(set(metadata_df.columns), {"attribute", "a", "b", "c"})

    def test_load_with_data_files(self):
        """Test loading shelf with attached data files."""
        test_df1 = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        test_df2 = pd.DataFrame({"col1": [5, 6], "col2": [7, 8]})

        self.record1.attach(test_df1, "data.csv")
        self.record2.attach(test_df2, "data.csv")

        dfs = load_from_shelf(self.test_dir)

        self.assertEqual(len(dfs), 2)
        self.assertIn("data", dfs)
        self.assertIn("metadata", dfs)

        data_df = dfs["data"]
        self.assertEqual(len(data_df), 4)  # 2 rows from each file

        # Check that metadata fields are added to data
        expected_cols = {"col1", "col2", "attribute", "data_path__", "a", "b", "c"}
        self.assertSetEqual(set(data_df.columns), expected_cols)

    def test_load_multiple_file_types(self):
        """Test loading shelf with different file types."""
        df1 = pd.DataFrame({"results": [0.85, 0.87]})
        df2 = pd.DataFrame({"predictions": [1, 0]})

        self.record1.attach(df1, "results.csv")
        self.record1.attach(df2, "predictions.csv")

        dfs = load_from_shelf(self.test_dir)

        self.assertIn("results", dfs)
        self.assertIn("predictions", dfs)
        self.assertIn("metadata", dfs)

    def test_load_no_csv_files_warning(self):
        """Test warning when no CSV files are found."""
        with self.assertWarns(UserWarning) as cm:
            load_from_shelf(self.test_dir)

        # Should warn for both records that have no CSV files
        warnings_messages = [str(w.message) for w in cm.warnings]
        self.assertTrue(any("No csv files available" in msg for msg in warnings_messages))

    def test_column_conflict_assertion(self):
        """Test that column name conflicts raise AssertionError."""
        # Create data with column that conflicts with metadata
        conflicting_df = pd.DataFrame({"attribute": [1, 2], "other": [3, 4]})
        self.record1.attach(conflicting_df, "data.csv")

        with self.assertRaises(AssertionError) as cm:
            load_from_shelf(self.test_dir)

        self.assertIn("attribute already exists in the data", str(cm.exception))


class TestShelfLoadExisting(TestWithTmpDir):
    """Test loading existing shelf configurations."""

    def test_load_existing_shelf(self):
        """Test loading shelf from existing .shelfie.pkl file."""
        # Create and save a shelf
        original_shelf = Shelf(
            root=self.test_dir,
            fields=["field1", "field2"],
            attributes=["attr1"]
        )
        original_shelf.create(field1="test", field2="value", attr1="metadata")

        # Load the shelf
        loaded_shelf = Shelf.load_from_root(self.test_dir)

        self.assertEqual(loaded_shelf.field_names, ["field1", "field2"])
        self.assertEqual(loaded_shelf.attributes, ["attr1"])
        self.assertEqual(loaded_shelf.root, self.test_dir)

    def test_load_nonexistent_shelf(self):
        """Test loading shelf from directory without .shelfie.pkl."""
        with self.assertRaises(FileNotFoundError) as cm:
            Shelf.load_from_root(self.test_dir)

        self.assertIn("No .shelfie.pkl file found", str(cm.exception))

    def test_load_corrupted_shelf(self):
        """Test loading corrupted .shelfie.pkl file."""
        # Create corrupted pickle file
        shelf_file = self.test_dir / ".shelfie.pkl"
        with open(shelf_file, "w") as f:
            f.write("corrupted data")

        with self.assertRaises(RuntimeError) as cm:
            Shelf.load_from_root(self.test_dir)

        self.assertIn("Could not load shelf", str(cm.exception))

    def test_load_moved_shelf(self):
        """Test that loaded shelf updates its root path if moved."""
        # Create shelf in temp directory
        original_root = self.test_dir / "original"
        original_root.mkdir()

        shelf = Shelf(root=original_root, fields=["f1"], attributes=[])
        shelf.create(f1="test")

        # Move the shelf directory
        new_root = self.test_dir / "moved"
        shutil.move(original_root, new_root)

        # Load from new location
        loaded_shelf = Shelf.load_from_root(new_root)
        self.assertEqual(loaded_shelf.root, new_root)


class TestDataFileOperations(TestWithTmpDir):
    """Test various data file operations."""

    def test_different_file_extensions(self):
        """Test that different file extensions are handled appropriately."""
        shelf = Shelf(root=self.test_dir, fields=["f1"], attributes=["attr"])
        record = shelf.create(f1="test", attr="value")

        # Test different data types (based on what's supported in data.py)
        df = pd.DataFrame({"test": [1, 2, 3]})
        record.attach(df, "data.csv")

        # JSON data
        json_data = {"key": "value", "number": 42}
        record.attach(json_data, "config.json")

        # Text data
        text_data = "This is test text content"
        record.attach(text_data, "notes.txt")

        # Python object (pickle)
        py_data = {"complex": [1, 2, {"nested": True}]}
        record.attach(py_data, "object.pkl")

        # Verify files exist
        base_path = self.test_dir / "test"
        self.assertTrue((base_path / "data.csv").exists())
        self.assertTrue((base_path / "config.json").exists())
        self.assertTrue((base_path / "notes.txt").exists())
        self.assertTrue((base_path / "object.pkl").exists())


class TestEdgeCases(TestWithTmpDir):
    """Test edge cases and error conditions."""

    def test_empty_fields_list(self):
        """Test creating shelf with empty fields list."""
        shelf = Shelf(root=self.test_dir, fields=[], attributes=[])
        record = shelf.create()

        # Should create record directly in root
        self.assertTrue((self.test_dir / "metadata.json").exists())

    def test_unicode_field_values(self):
        """Test handling unicode characters in field values."""
        shelf = Shelf(root=self.test_dir, fields=["unicode_field"], attributes=[])
        record = shelf.create(unicode_field="тест_español_中文")

        expected_dir = self.test_dir / "тест_español_中文"
        self.assertTrue(expected_dir.exists())

    def test_special_characters_in_metadata(self):
        """Test handling special characters in metadata."""
        shelf = Shelf(root=self.test_dir, fields=["f1"], attributes=[])
        record = shelf.create(
            f1="test",
            special_chars="<>&\"'",
            unicode_meta="тест",
            symbols="!@#$%^&*()"
        )

        metadata_file = self.test_dir / "test" / "metadata.json"
        with open(metadata_file, encoding='utf-8') as f:
            metadata = json.load(f)

        self.assertEqual(metadata["special_chars"], "<>&\"'")
        self.assertEqual(metadata["unicode_meta"], "тест")
        self.assertEqual(metadata["symbols"], "!@#$%^&*()")

    def test_very_long_field_values(self):
        """Test handling very long field values."""
        long_value = "x" * 200
        shelf = Shelf(root=self.test_dir, fields=["long_field"], attributes=[])
        record = shelf.create(long_field=long_value)

        expected_dir = self.test_dir / long_value
        # Note: This might fail on some filesystems with path length limits
        # In a real implementation, you might want to hash long field values
        try:
            self.assertTrue(expected_dir.exists())
        except OSError:
            # Expected on systems with path length limits
            pass


class TestIntegration(TestWithTmpDir):
    """Integration tests that test complete workflows."""

    def test_complete_ml_workflow(self):
        """Test a complete ML experiment workflow."""
        # Set up ML experiments shelf
        ml_shelf = Shelf(
            root=self.test_dir,
            fields=["experiment", "model", DateField("date")],
            attributes=["epochs", "learning_rate"]
        )

        # Create experiment
        experiment = ml_shelf.create(
            experiment="baseline",
            model="random_forest",
            epochs=100,
            learning_rate=0.01
        )

        # Attach results
        training_results = pd.DataFrame({
            "epoch": [1, 2, 3],
            "train_loss": [0.5, 0.3, 0.2],
            "val_loss": [0.6, 0.4, 0.3]
        })

        test_results = pd.DataFrame({
            "metric": ["accuracy", "precision", "recall"],
            "value": [0.85, 0.82, 0.78]
        })

        experiment.attach(training_results, "training.csv")
        experiment.attach(test_results, "test_results.csv")

        # Load and verify
        data = load_from_shelf(self.test_dir)

        self.assertIn("training", data)
        self.assertIn("test_results", data)
        self.assertIn("metadata", data)

        # Check that metadata is properly merged
        training_df = data["training"]
        self.assertIn("epochs", training_df.columns)
        self.assertIn("learning_rate", training_df.columns)
        self.assertIn("experiment", training_df.columns)

        # Verify values
        self.assertTrue((training_df["epochs"] == 100).all())
        self.assertTrue((training_df["learning_rate"] == 0.01).all())

    def test_multiple_experiments_analysis(self):
        """Test analyzing multiple experiments."""
        shelf = Shelf(
            root=self.test_dir,
            fields=["model_type", DateField("date")],
            attributes=["hyperparams"]
        )

        # Create multiple experiments
        models = [
            ("rf", {"n_estimators": 100}),
            ("svm", {"C": 1.0, "kernel": "rbf"}),
            ("nn", {"layers": [64, 32], "dropout": 0.2})
        ]

        for model_name, params in models:
            exp = shelf.create(model_type=model_name, hyperparams=params)
            results = pd.DataFrame({
                "metric": ["accuracy", "f1"],
                "value": [np.random.random(), np.random.random()]
            })
            exp.attach(results, "metrics.csv")

        # Analyze all results
        data = load_from_shelf(self.test_dir)
        metrics_df = data["metrics"]

        # Should have 6 rows (2 metrics × 3 models)
        self.assertEqual(len(metrics_df), 6)

        # Should have model_type column for analysis
        self.assertIn("model_type", metrics_df.columns)
        model_types = set(metrics_df["model_type"])
        self.assertEqual(model_types, {"rf", "svm", "nn"})


if __name__ == '__main__':
    # Run tests with high verbosity
    unittest.main(verbosity=2)