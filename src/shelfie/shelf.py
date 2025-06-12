import json
import pickle
import warnings
from pathlib import Path
from typing import Any, Dict, List, Union
import pandas as pd
import numpy as np


from .fields import Field
from .data import write, read


class StorageRecord:
    """Represents a single storage record with its path and metadata."""

    def __init__(
        self, path: Path, metadata: Dict[str, Any], metadata_name: str
    ):
        self.path = path
        self.metadata = metadata
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
    
    def attach(self, data, filename):
        file = self.path / filename

        # Also save to metadata
        self.metadata[file.stem] = file
        self._save_metadata()
        write(data, file)


class Shelf:
    """Simple filesystem-based structured storage for CSV files with metadata."""
    @classmethod
    def load_from_root(cls, root: str) -> "Shelf":
        """
        Load a Shelf instance from its root directory by reading the .shelfie.pkl file.
        
        Args:
            root: Root directory containing the .shelfie.pkl file
            
        Returns:
            Shelf instance
        """
        root_path = Path(root)
        shelf_file = root_path / ".shelfie.pkl"
        
        if not shelf_file.exists():
            raise FileNotFoundError(
                f"No .shelfie.pkl file found in {root}. "
                "Make sure this directory contains a valid shelf."
            )
        
        try:
            with open(shelf_file, "rb") as f:
                shelf = pickle.load(f)
            
            # Update the root path in case the shelf was moved
            shelf.root = root_path
            return shelf
            
        except Exception as e:
            raise RuntimeError(f"Could not load shelf from {shelf_file}: {e}")


    def __init__(
        self,
        root: str,
        fields: List[Union[str, Field]],
        attributes: List[str] = None,
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
        self.metadata_name = metadata_name

        # Create root directory if it doesn't exist
        self.root.mkdir(parents=True, exist_ok=True)

    def _save_shelf(self):
        
        shelf_file = self.root / ".shelfie.pkl"
        with open(shelf_file, "wb") as f:
            pickle.dump(self, f)

    def create(self, **kwargs) -> "StorageRecord":
        """
        Create a new storage record.

        Args:
            **kwargs: Field values and attributes

        Returns:
            StorageRecord object
        """
        # Save the fields and attributes associated with this file
        self._save_shelf()

        # Separate fields from attributes
        field_values = {}
        metadata = {}

        # Process field values
        for field_name in self.field_names:
            field_obj = self.fields[field_name]
            provided_value = kwargs.get(field_name)
            # Returns provided value or default
            field_values[field_name] = field_obj.get_value(provided_value)

        # Process attributes (everything else goes to metadata)
        for key, value in kwargs.items():
            if key not in self.field_names:
                metadata[key] = value

        # make sure that every attribute is set
        for attribute in self.attributes:
            if attribute not in metadata:
                raise ValueError(f"{attribute} is a required attribute but has not been provided.")

        # Build directory path from field values
        path_parts = [str(field_values[name]) for name in self.field_names]
        record_path = self.root / Path(*path_parts)

        return StorageRecord(
            path=record_path,
            metadata=metadata,
            metadata_name=self.metadata_name,
        )

