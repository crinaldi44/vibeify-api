"""convert_user_roles_to_table

Revision ID: 20260118_235358
Revises: 
Create Date: 2026-01-18 23:53:58.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260118_235358'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)
    
    # Insert default roles
    op.execute("""
        INSERT INTO roles (name, description, is_active, created_at, updated_at)
        VALUES 
            ('User', 'Standard user role', true, NOW(), NOW()),
            ('Administrator', 'Administrator role with full access', true, NOW(), NOW())
    """)
    
    # Check if users table exists and has role column (enum)
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    if 'users' in tables:
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        # Add role_id column (nullable initially)
        if 'role_id' not in columns:
            op.add_column('users', sa.Column('role_id', sa.Integer(), nullable=True))
            op.create_index(op.f('ix_users_role_id'), 'users', ['role_id'], unique=False)
            op.create_foreign_key('fk_users_role_id', 'users', 'roles', ['role_id'], ['id'])
            
            # Migrate existing enum data to role_id
            if 'role' in columns:
                # Map enum values to role IDs
                op.execute("""
                    UPDATE users 
                    SET role_id = (SELECT id FROM roles WHERE name = LOWER(users.role::text))
                    WHERE role_id IS NULL
                """)
                
                # Set default role_id for any remaining NULL values
                op.execute("""
                    UPDATE users 
                    SET role_id = (SELECT id FROM roles WHERE name = 'user')
                    WHERE role_id IS NULL
                """)
                
                # Make role_id NOT NULL
                op.alter_column('users', 'role_id', nullable=False)
                
                # Drop the old enum column
                op.drop_column('users', 'role')
            else:
                # No existing role column, set default for all users
                op.execute("""
                    UPDATE users 
                    SET role_id = (SELECT id FROM roles WHERE name = 'user')
                    WHERE role_id IS NULL
                """)
                op.alter_column('users', 'role_id', nullable=False)
        else:
            # role_id already exists, just ensure foreign key
            try:
                op.create_foreign_key('fk_users_role_id', 'users', 'roles', ['role_id'], ['id'])
            except Exception:
                pass  # Foreign key might already exist
    else:
        # Users table doesn't exist yet, it will be created by model definition
        pass


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint('fk_users_role_id', 'users', type_='foreignkey')
    
    # Add back enum column
    user_role_enum = postgresql.ENUM('user', 'admin', 'moderator', name='userrole')
    user_role_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('users', sa.Column('role', user_role_enum, nullable=True))
    
    # Migrate role_id back to enum
    op.execute("""
        UPDATE users 
        SET role = (SELECT name FROM roles WHERE id = users.role_id)::userrole
    """)
    
    # Set default for any NULL values
    op.execute("""
        UPDATE users 
        SET role = 'user'::userrole
        WHERE role IS NULL
    """)
    
    op.alter_column('users', 'role', nullable=False)
    
    # Drop role_id column
    op.drop_index(op.f('ix_users_role_id'), table_name='users')
    op.drop_column('users', 'role_id')
    
    # Drop roles table
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_table('roles')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS userrole')
