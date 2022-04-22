# -*- coding: utf-8 -*-

import os
from abc import ABCMeta, abstractmethod
from operator import itemgetter
from typing import Dict, Set, Tuple, Type

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from cytoolz import memoize
from pyarrow.feather import FeatherReader, write_feather
from tqdm import tqdm

from .genesig import GeneSignature


class PyArrowThreads:
    """
    A static class to control how many threads PyArrow is allowed to use to convert a Feather database to a pandas
    dataframe.

    By default the number of threads is set to 4.
    Overriding the number of threads is possible by using the environment variable "PYARROW_THREADS=nbr_threads".
    """

    pyarrow_threads = 4

    if os.environ.get("PYARROW_THREADS"):
        try:
            # If "PYARROW_THREADS" is set, check if it is a number.
            pyarrow_threads = int(os.environ.get("PYARROW_THREADS"))
        except ValueError:
            pass

        if pyarrow_threads < 1:
            # Set the number of PyArrow threads to 1 if a negative number or zero was specified.
            pyarrow_threads = 1

    @staticmethod
    def set_nbr_pyarrow_threads(nbr_threads=None):
        # Set number of threads to use for PyArrow when converting Feather database to pandas dataframe.
        pa.set_cpu_count(nbr_threads if nbr_threads else PyArrowThreads.pyarrow_threads)


PyArrowThreads.set_nbr_pyarrow_threads()


class RankingDatabase(metaclass=ABCMeta):
    """
    A class of a database of whole genome rankings. The whole genome is ranked for regulatory features of interest, e.g.
    motifs for a transcription factor.

    The rankings of the genes are 0-based.
    """

    def __init__(self, name: str):
        """
        Create a new instance.

        :param name: The name of the database.
        """
        assert name, "Name must be specified."

        self._name = name

    @property
    def name(self) -> str:
        """
        The name of this database of rankings.
        """
        return self._name

    @property
    @abstractmethod
    def total_genes(self) -> int:
        """
        The total number of genes ranked.
        """
        pass

    @property
    @abstractmethod
    def genes(self) -> Tuple[str]:
        """
        List of genes ranked according to the regulatory features in this database.
        """
        pass

    @property
    @memoize
    def geneset(self) -> Set[str]:
        """
        Set of genes ranked according to the regulatory features in this database.
        """
        return set(self.genes)

    @abstractmethod
    def load_full(self) -> pd.DataFrame:
        """
        Load the whole database into memory.

        :return: a dataframe.
        """
        pass

    @abstractmethod
    def load(self, gs: Type[GeneSignature]) -> pd.DataFrame:
        """
        Load the ranking of the genes in the supplied signature for all features in this database.

        :param gs: The gene signature.
        :return: a dataframe.
        """
        pass

    def __str__(self):
        """
        Returns a readable string representation.
        """
        return self.name

    def __repr__(self):
        """
        Returns a unambiguous string representation.
        """
        return "{}(name=\"{}\")".format(self.__class__.__name__, self._name)


class FeatherRankingDatabase(RankingDatabase):
    def __init__(self, fname: str, name: str):
        """
        Create a new feather database.

        :param fname: The filename of the database.
        :param name: The name of the database.
        """
        super().__init__(name=name)

        assert os.path.isfile(fname), "Database {0:s} doesn't exist.".format(fname)

        # FeatherReader cannot be pickle (important for dask framework) so filename is field instead.
        self._fname = fname

        if (
            fname.endswith('.genes_vs_motifs.rankings.feather')
            or fname.endswith('.regions_vs_motifs.rankings.feather')
            or fname.endswith('.genes_vs_motifs.scores.feather')
            or fname.endswith('.regions_vs_motifs.scores.feather')
        ):
            self._index_name = 'motifs'
        elif (
            fname.endswith('.genes_vs_tracks.rankings.feather')
            or fname.endswith('.regions_vs_tracks.rankings.feather')
            or fname.endswith('.genes_vs_tracks.scores.feather')
            or fname.endswith('.regions_vs_tracks.scores.feather')
        ):
            self._index_name = 'tracks'
        else:
            self._index_name = 'features'

    @property
    @memoize
    def total_genes(self) -> int:
        # Do not count column 1 as it contains the index with the name of the index column ("motifs", "tracks" or
        # "features").
        return FeatherReader(self._fname).num_columns - 1

    @property
    @memoize
    def genes(self) -> Tuple[str]:
        # noinspection PyTypeChecker
        reader = FeatherReader(self._fname)
        # Get all gene names (exclude index column: "motifs", "tracks" or "features").
        return tuple(
            reader.get_column_name(idx)
            for idx in range(reader.num_columns)
            if reader.get_column_name(idx) != self._index_name
        )

    @property
    @memoize
    def genes2idx(self) -> Dict[str, int]:
        return {gene: idx for idx, gene in enumerate(self.genes)}

    def load_full(self) -> pd.DataFrame:
        df = FeatherReader(self._fname).read_pandas()
        # Avoid copying the whole dataframe by replacing the index in place.
        # This makes loading a database twice as fast in case the database file is already in the filesystem cache.
        df.set_index(self._index_name, inplace=True)
        return df

    def load(self, gs: Type[GeneSignature]) -> pd.DataFrame:
        # For some genes in the signature there might not be a rank available in the database.
        gene_set = self.geneset.intersection(set(gs.genes))
        # Read ranking columns for genes in order they appear in the Feather file.
        df = FeatherReader(self._fname).read_pandas(
            columns=(self._index_name,) + tuple(sorted(gene_set, key=lambda gene: self.genes2idx[gene]))
        )
        # Avoid copying the whole dataframe by replacing the index in place.
        # This makes loading a database twice as fast in case the database file is already in the filesystem cache.
        df.set_index(self._index_name, inplace=True)
        return df


INDEX_NAME = "features"


class MemoryDecorator(RankingDatabase):
    """
    A decorator for a ranking database which loads the entire database in memory.
    """

    def __init__(self, db: Type[RankingDatabase]):
        assert db, "Database should be supplied."
        self._db = db
        self._df = db.load_full()
        super().__init__(db.name)

    @property
    def total_genes(self) -> int:
        return self._db.total_genes

    @property
    def genes(self) -> Tuple[str]:
        return self._db.genes

    def load_full(self) -> pd.DataFrame:
        return self._df

    def load(self, gs: Type[GeneSignature]) -> pd.DataFrame:
        return self._df.loc[:, self._df.columns.isin(gs.genes)]


def opendb(fname: str, name: str) -> Type['RankingDatabase']:
    """
    Open a ranking database.

    :param fname: The filename of the database.
    :param name: The name of the database.
    :return: A ranking database.
    """
    assert os.path.isfile(fname), "{} does not exist.".format(fname)
    assert name, "A database should be given a proper name."

    extension = os.path.splitext(fname)[1]
    if extension == ".feather":
        # noinspection PyTypeChecker
        return FeatherRankingDatabase(fname, name=name)
    else:
        raise ValueError("{} is an unknown extension.".format(extension))
