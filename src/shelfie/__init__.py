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
                csv_files = list(path.glob("*.csv"))
                record_info['__csv_files'] = [f.name for f in csv_files]
                
                # Check for metadata
                metadata_file = path / f"{shlf.metadata_name}.json"
                record_info['__has_metadata'] = metadata_file.exists()
                records.append(record_info)


    dataframes = defaultdict(list)
    for record in records:

        csv_files = record.pop("__csv_file")
        
        metadata = None
        if record.pop("__has_metadata"):
            with open(f"{shlf.metadata_name}.json", "r") as f:
                metadata = json.load(f)

        for csv_file in csv_files:
            name = csv_files.stem
            data = pd.read_csv(csv_file)

            if metadata:
                for key, value in metadata.items():
                    assert key not in data.columns
                    data[key] = value

            dataframes[name].append(data)

    
    return {
        k: pd.concat(dfs) for k, dfs in dataframes.items()
    }
                
        
__all__ = [
    Shelf, Field, DateField, TimestampField, load_from_shelf
]