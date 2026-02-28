"""create imdb metadata tables

Revision ID: 8b9c2d1e3f4a
Revises: 1a25264b9958
Create Date: 2026-02-28 00:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8b9c2d1e3f4a"
down_revision: Union[str, Sequence[str], None] = "1a25264b9958"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "movies",
        sa.Column("tconst", sa.String(length=16), nullable=False),
        sa.Column("primaryTitle", sa.Text(), nullable=False),
        sa.Column("startYear", sa.Integer(), nullable=True),
        sa.Column("genres", sa.Text(), nullable=True),
        sa.Column("originalTitle", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("tconst"),
    )

    op.create_table(
        "titles_localized",
        sa.Column("tconst", sa.String(length=16), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["tconst"], ["movies.tconst"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("tconst", "language", "title"),
    )

    op.create_index(
        "ix_titles_localized_tconst_language",
        "titles_localized",
        ["tconst", "language"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_titles_localized_tconst_language", table_name="titles_localized")
    op.drop_table("titles_localized")
    op.drop_table("movies")

