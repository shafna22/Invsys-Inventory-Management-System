"""Update default value for profile_picture in User model

Revision ID: e127b8c0aafe
Revises: 72ee27f57d6e
Create Date: 2025-03-17 12:23:11.526219

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e127b8c0aafe'
down_revision = '72ee27f57d6e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('profile_picture',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('profile_picture',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)

    # ### end Alembic commands ###
