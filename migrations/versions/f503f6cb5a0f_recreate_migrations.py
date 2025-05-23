"""Recreate migrations

Revision ID: f503f6cb5a0f
Revises: 5a3bc0a44f19
Create Date: 2025-05-13 06:23:23.779072

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f503f6cb5a0f'
down_revision = '5a3bc0a44f19'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('menu_item', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(length=50), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('menu_item', schema=None) as batch_op:
        batch_op.drop_column('category')

    # ### end Alembic commands ###
