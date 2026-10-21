"""Add user profiles

Revision ID: 003
Revises: 002
Create Date: 2024-03-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    # Create profiles table
    op.create_table('profiles',
        sa.Column('profile_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('profession', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('role', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('custom_fields', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('profile_id')
    )
    
    # Add profile_id to inputs table
    op.add_column('inputs', sa.Column('profile_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.create_foreign_key('fk_inputs_profiles', 'inputs', 'profiles', ['profile_id'], ['profile_id'])

def downgrade():
    op.drop_constraint('fk_inputs_profiles', 'inputs', type_='foreignkey')
    op.drop_column('inputs', 'profile_id')
    op.drop_table('profiles')
