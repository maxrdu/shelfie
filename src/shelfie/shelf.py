import json
import warnings
from pathlib import Path
from typing import Any, Dict, List, Union
import pandas as pd
import numpy as np


from .fields import Field


class StorageRecord:
    """Represents a single storage record with its path and metadata."""

    def __init__(
        self, path: Path, metadata: Dict[str, Any], data_name: str, metadata_name: str
    ):
        self.path = path
        self.metadata = metadata
        self.data_name = data_name
        self.metadata_name = metadata_name

        # Create directory and save metadata immediately upon creation
        self._save_metadata()

    def _save_metadata(self):
        """Save metadata to the filesystem."""
        # Create directory if it doesn't exist
        self.path.mkdir(parents=True, exist_ok=True)

        # Check if metadata file already exists
        metadata_path = self.path / f"{self.metadata_name}.json"
        if metadata_path.exists():
            warnings.warn(
                f"Metadata file already exists and will be overwritten: {metadata_path}"
            )

        # Convert numpy types to Python types for JSON serialization
        serializable_metadata = {}
        for key, value in self.metadata.items():
            if isinstance(value, np.integer):
                serializable_metadata[key] = int(value)
            elif isinstance(value, np.floating):
                if np.isnan(value):
                    serializable_metadata[key] = None
                else:
                    serializable_metadata[key] = float(value)
            elif isinstance(value, np.ndarray):
                serializable_metadata[key] = value.tolist()
            else:
                serializable_metadata[key] = value

        with open(metadata_path, "w") as f:
            json.dump(serializable_metadata, f, indent=2, default=str)

        print(f"Created record at: {self.path}")

    def save(self, data: pd.DataFrame):
        """Save data CSV to the filesystem."""
        if data is None:
            raise ValueError("Data DataFrame is required")

        data_path = self.path / f"{self.data_name}.csv"
        if data_path.exists():
            warnings.warn(
                f"Data file already exists and will be overwritten: {data_path}"
            )

        data.to_csv(data_path, index=False)

        print(f"Saved data to: {data_path}")
        return self


class Shelf:
    """Simple filesystem-based structured storage for CSV files with metadata."""

    def __init__(
        self,
        root: str,
        fields: List[Union[str, Field]],
        attributes: List[str] = None,
        data_name: str = "data",
        metadata_name: str = "metadata",
    ):
        """
        Initialize the structured file storage.

        Args:
            root: Root directory for storage
            fields: List containing field names (strings) or Field objects that define directory structure
            attributes: List of attribute names to store in metadata
            data_name: Name for main CSV file (without extension)
            metadata_name: Name for metadata JSON file (without extension)
        """
        self.root = Path(root)
        self.fields = {}
        self.field_names = []

        # Process fields - can be strings or Field objects in a list
        for field in fields:
            if isinstance(field, str):
                self.fields[field] = Field(field)
                self.field_names.append(field)
            elif isinstance(field, Field):
                self.fields[field.name] = field
                self.field_names.append(field.name)
            else:
                raise ValueError("Fields must be either strings or Field objects")

        self.attributes = attributes or []
        self.data_name = data_name
        self.metadata_name = metadata_name

        # Create root directory if it doesn't exist
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, **kwargs) -> "StorageRecord":
        """
        Create a new storage record.

        Args:
            **kwargs: Field values and attributes

        Returns:
            StorageRecord object
        """
        # Separate fields from attributes
        field_values = {}
        metadata = {}

        # Process field values
        for field_name in self.field_names:
            field_obj = self.fields[field_name]
            provided_value = kwargs.get(field_name)
            field_values[field_name] = field_obj.get_value(provided_value)

        # Process attributes (everything else goes to metadata)
        for key, value in kwargs.items():
            if key not in self.field_names:
                metadata[key] = value

        # Build directory path from field values
        path_parts = [str(field_values[name]) for name in self.field_names]
        record_path = self.root / Path(*path_parts)

        return StorageRecord(
            path=record_path,
            metadata=metadata,
            data_name=self.data_name,
            metadata_name=self.metadata_name,
        )

