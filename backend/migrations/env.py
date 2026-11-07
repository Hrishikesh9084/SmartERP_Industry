from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.database import Base
from app import models, models_enterprise
from app.config import DATABASE_URL
config=context.config
config.set_main_option('sqlalchemy.url',DATABASE_URL.replace('%','%%'))
if config.config_file_name: fileConfig(config.config_file_name)
target_metadata=Base.metadata

def include_object(object_, name, type_, reflected, compare_to):
    # Keep legacy tables and indexes that are no longer represented by the
    # current metadata; they may still contain user data.
    if reflected and compare_to is None:
        return False
    return True

def run_migrations_offline():
    context.configure(url=DATABASE_URL,target_metadata=target_metadata,literal_binds=True,dialect_opts={'paramstyle':'named'},compare_type=False,include_object=include_object)
    with context.begin_transaction(): context.run_migrations()
def run_migrations_online():
    connectable=engine_from_config(config.get_section(config.config_ini_section),prefix='sqlalchemy.',poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection,target_metadata=target_metadata,compare_type=False,include_object=include_object)
        with context.begin_transaction(): context.run_migrations()
if context.is_offline_mode(): run_migrations_offline()
else: run_migrations_online()
