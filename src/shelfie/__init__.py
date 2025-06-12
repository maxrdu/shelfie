import warnings

from .shelf import Shelf
from .fields import Field, DateField, TimestampField


def load_from_shelf(root):
    from collections import defaultdict
    import pandas as pd
    import json

    shlf = Shelf.load_from_root(root)

    records = []
    for path in shlf.root.rglob("*"):
        if path.is_dir() and not path.name.startswith('.'):
            relative_path = path.relative_to(shlf.root)
            path_parts = relative_path.parts
            
            # Check if this matches our field structure
            if len(path_parts) == len(shlf.field_names):
                record_info = {}
                
                # Add field values
                for field_name, path_part in zip(shlf.field_names, path_parts):
                    record_info[field_name] = path_part
                
                # List available files
                record_info['__csv_files'] = [f.absolute() for f in path.glob("*.csv")]
                
                # Check for metadata
                metadata_file = path / f"{shlf.metadata_name}.json"

                metadata = {}
                if metadata_file.exists():
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)

                record_info['__metadata'] = metadata
                records.append(record_info)


    dataframes = defaultdict(list)
    for record in records:

        csv_files = record.pop("__csv_files")
        metadata = record.pop("__metadata")

        # Always save metadata
        metadata_df = pd.Series(metadata).to_frame().T
        records_df = pd.Series(record).to_frame().T
        combined = pd.concat([metadata_df, records_df], axis=1)
        dataframes['metadata'].append(combined)

        if not csv_files:
            warnings.warn(f"No csv files available for {record}.")

        for csv_file in csv_files:
            name = csv_file.stem
            data = pd.read_csv(csv_file, index_col=0)

            # Add all metadata fields
            for key, value in metadata.items():
                assert key not in data.columns, f"{key} already exists in the data ({csv_file})"
                data[key] = value

            for key, value in record.items():
                assert key not in data.columns, f"{key} already exists in the data ({csv_file})"
                data[key] = value

            dataframes[name].append(data)

    
    return {
        k: pd.concat(dfs, ignore_index=True) for k, dfs in dataframes.items()
    }
                
        
__all__ = [
    Shelf, Field, DateField, TimestampField, load_from_shelf
]