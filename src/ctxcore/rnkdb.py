# -*- coding: utf-8 -*-

import os
from abc import ABCMeta, abstractmethod
from typing import Set, Tuple

import pandas as pd
from cytoolz import memoize

from ctxcore.ctdb import CisTargetDatabase
from ctxcore.datatypes import RegionOrGeneIDs
from ctxcore.genesig import GeneSignature


class RankingDatabase(metaclass=ABCMeta):
    """
    A class of a database of whole genome rankings. The whole genome is ranked for
    regulatory features of interest, e.g. motifs for a transcription factor.

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
    def load(self, gs: GeneSignature) -> pd.DataFrame:
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
        return f'{self.__class__.__name__}(name="{self._name}")'


class FeatherRankingDatabase(RankingDatabase):
    def __init__(self, fname: str, name: str):
        """
        Create a new feather database.

        :param fname: The filename of the database.
        :param name: The name of the database.
        """
        super().__init__(name=name)

        assert os.path.isfile(fname), """Database "{fname}" doesn't exist."""

        self._fname = fname
        self.ct_db = CisTargetDatabase.init_ct_db(
            ct_db_filename=self._fname, engine="pyarrow"
        )

    @property
    @memoize
    def total_genes(self) -> int:
        return self.ct_db.nbr_total_region_or_gene_ids

    @property
    @memoize
    def genes(self) -> Tuple[str]:
        return self.ct_db.all_region_or_gene_ids.ids

    def load_full(self) -> pd.DataFrame:
        return self.ct_db.subset_to_pandas(
            region_or_gene_ids=self.ct_db.all_region_or_gene_ids
        )

    def load(self, gs: GeneSignature) -> pd.DataFrame:
        # For some genes in the signature there might not be a rank available in the database.
        gene_set = self.geneset.intersection(set(gs.genes))

        return self.ct_db.subset_to_pandas(
            region_or_gene_ids=RegionOrGeneIDs(
                region_or_gene_ids=gene_set,
                regions_or_genes_type=self.ct_db.all_region_or_gene_ids.type,
            )
        )


class MemoryDecorator(RankingDatabase):
    """
    A decorator for a ranking database which loads the entire database in memory.
    """

    def __init__(self, db: RankingDatabase):
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

    def load(self, gs: GeneSignature) -> pd.DataFrame:
        return self._df.loc[:, self._df.columns.isin(gs.genes)]


def opendb(fname: str, name: str) -> RankingDatabase:
    """
    Open a ranking database.

    :param fname: The filename of the database.
    :param name: The name of the database.
    :return: A ranking database.
    """
    assert os.path.isfile(fname), f'"{fname}" does not exist.'
    assert name, "A database should be given a proper name."

    extension = os.path.splitext(fname)[1]
    if extension == ".feather":
        # noinspection PyTypeChecker
        return FeatherRankingDatabase(fname, name=name)
    else:
        raise ValueError(f'"{extension}" is an unknown extension.')
