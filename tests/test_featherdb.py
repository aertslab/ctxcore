import pytest
from pkg_resources import resource_filename

from ctxcore.genesig import GeneSignature
from ctxcore.rnkdb import FeatherRankingDatabase as RankingDatabase

TEST_DATABASE_FNAME = resource_filename(
    "resources.tests",
    "hg19-tss-centered-10kb-10species.mc9nr.genes_vs_motifs.rankings.feather",
)
TEST_DATABASE_NAME = "hg19-tss-centered-10kb-10species.mc9nr.genes_vs_motifs.rankings"
TEST_SIGNATURE_FNAME = resource_filename("resources.tests", "c6.all.v6.1.symbols.gmt")


@pytest.fixture
def db() -> RankingDatabase:
    return RankingDatabase(TEST_DATABASE_FNAME, TEST_DATABASE_NAME)


@pytest.fixture
def gs() -> GeneSignature:
    return GeneSignature.from_gmt(
        TEST_SIGNATURE_FNAME,
        gene_separator="\t",
        field_separator="\t",
    )[0]


def test_init(db: RankingDatabase) -> None:
    assert db.name == TEST_DATABASE_NAME


def test_total_genes(db: RankingDatabase) -> None:
    assert db.total_genes == 22284


def test_genes(db: RankingDatabase) -> None:
    assert len(db.genes) == 22284


def test_load_full(db: RankingDatabase) -> None:
    rankings = db.load_full()
    assert len(rankings.index) == 5
    assert len(rankings.columns) == 22284


def test_load(db: RankingDatabase, gs: GeneSignature) -> None:
    rankings = db.load(gs)
    assert len(rankings.index) == 5
    assert len(rankings.columns) == 29
