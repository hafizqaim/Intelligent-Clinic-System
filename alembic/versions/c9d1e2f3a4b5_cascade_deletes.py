"""Cascade deletes on tenant/patient foreign keys

Deleting a patient or a clinic through the API previously raised an unhandled
500 (ForeignKeyViolationError) whenever dependent rows existed (telemetry
readings, users, documents, chat history) — the foreign keys had no ON DELETE
behavior, so Postgres defaulted to blocking the delete. This makes "delete"
actually delete the whole record, which is what the API's DELETE endpoints
already implied.

Revision ID: c9d1e2f3a4b5
Revises: b2c3d4e5f6a7
Create Date: 2026-09-12 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c9d1e2f3a4b5'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (table, constraint_name, fk_column, referenced_table)
FOREIGN_KEYS = [
    ('users', 'users_clinic_id_fkey', 'clinic_id', 'clinics'),
    ('patients', 'patients_clinic_id_fkey', 'clinic_id', 'clinics'),
    ('telemetry_readings', 'telemetry_readings_clinic_id_fkey', 'clinic_id', 'clinics'),
    ('telemetry_readings', 'telemetry_readings_patient_id_fkey', 'patient_id', 'patients'),
    ('document_embeddings', 'document_embeddings_clinic_id_fkey', 'clinic_id', 'clinics'),
    ('chat_histories', 'chat_histories_clinic_id_fkey', 'clinic_id', 'clinics'),
    ('chat_histories', 'chat_histories_user_id_fkey', 'user_id', 'users'),
]


def upgrade() -> None:
    for table, constraint, column, ref_table in FOREIGN_KEYS:
        op.drop_constraint(constraint, table, type_='foreignkey')
        op.create_foreign_key(constraint, table, ref_table, [column], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    for table, constraint, column, ref_table in FOREIGN_KEYS:
        op.drop_constraint(constraint, table, type_='foreignkey')
        op.create_foreign_key(constraint, table, ref_table, [column], ['id'])
