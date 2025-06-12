import abc
import json
import pathlib
import pickle
import warnings

import pandas as pd


class DataObject(abc.ABC):

    write_mode = "w"
    read_mode = "r"

    @abc.abstractmethod
    def write(self, data, file):
        ...

    @abc.abstractmethod
    def read(self, file):
        ...


class ByteObject(DataObject, abc.ABC):
    write_mode = "wb"
    read_mode = "rb"

class _CSVObject(DataObject):

    def write(self, data, file):
        assert isinstance(data, pd.DataFrame)
        data.to_csv(file)

    def read(self, file):
        return pd.read_csv(file)


class _PythonObject(ByteObject):
    def write(self, data, file):
        pickle.dump(data, file)

    def read(self, file):
        return pickle.load(file)
    

class _JSONObject(DataObject):
    def write(self, data, file):
        json.dump(data, file)

    def read(self, file):
        json.load(file)


class _TXTObject(DataObject):
    def write(self, data, file):
        file.write(data)
    
    def read(self, file):
        return file.read()


SUFFIX_TO_OBJECT = {
    ".json": _JSONObject(),
    ".csv": _CSVObject(),
    ".txt": _TXTObject(),
    ".pkl": _PythonObject()
}

def _get_writer_reader(file: pathlib.Path) -> DataObject:
    suffix = file.suffix
    wr = SUFFIX_TO_OBJECT.get(suffix, None)
    if wr is None:
        warnings.warns(f"No default writer/reader for '{suffix}' found. Defaulting to pickle based storage.")
        wr = _PythonObject()

    return wr


def write(data, file: pathlib.Path):
    wr = _get_writer_reader(file)
    with open(file, wr.write_mode) as f:
        wr.write(data, f)


def read(file: pathlib.Path):
    wr = _get_writer_reader(file)
    with open(file, wr.read_mode) as f:
        wr.read(f)