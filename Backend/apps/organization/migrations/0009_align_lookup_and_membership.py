# Generated manually — align DB with current organization models.
#
# Supports:
# - DBs that still have the interim DDD schema (organizations/iam/people)
# - Fresh installs that reached organization.0008

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def forwards_align_schema(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        def table_exists(name: str) -> bool:
            cursor.execute('SELECT to_regclass(%s)', [name])
            return cursor.fetchone()[0] is not None

        def column_exists(table: str, column: str) -> bool:
            cursor.execute(
                """
                SELECT 1 FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
                """,
                [table, column],
            )
            return cursor.fetchone() is not None

        # --- Lookups: drop code columns ---
        for table in (
            'organization_industrytype',
            'organization_designation',
            'organization_employeetype',
            'organization_accesstype',
        ):
            if table_exists(table) and column_exists(table, 'code'):
                cursor.execute(f'ALTER TABLE {table} DROP COLUMN IF EXISTS code CASCADE')

        # --- OrganizationUnit → OrganizationBranch ---
        if table_exists('organization_organizationunit') and not table_exists('organization_organizationbranch'):
            cursor.execute(
                'ALTER TABLE organization_organizationunit RENAME TO organization_organizationbranch'
            )
        if table_exists('organization_organizationbranch'):
            if column_exists('organization_organizationbranch', 'code') and not column_exists(
                'organization_organizationbranch', 'branch_code'
            ):
                cursor.execute(
                    'ALTER TABLE organization_organizationbranch RENAME COLUMN code TO branch_code'
                )
            if column_exists('organization_organizationbranch', 'name') and not column_exists(
                'organization_organizationbranch', 'branch_name'
            ):
                cursor.execute(
                    'ALTER TABLE organization_organizationbranch RENAME COLUMN name TO branch_name'
                )
            for col in ('parent_id', 'unit_type', 'created_by_id', 'updated_by_id'):
                if column_exists('organization_organizationbranch', col):
                    cursor.execute(
                        f'ALTER TABLE organization_organizationbranch DROP COLUMN IF EXISTS {col} CASCADE'
                    )
            cursor.execute(
                'ALTER TABLE organization_organizationbranch DROP CONSTRAINT IF EXISTS uniq_organization_unit_code'
            )
            cursor.execute('DROP INDEX IF EXISTS uniq_organization_unit_code')
            cursor.execute(
                """
                DO $$ BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uniq_organization_branch_code'
                  ) AND NOT EXISTS (
                    SELECT 1 FROM pg_class WHERE relname = 'uniq_organization_branch_code'
                  ) THEN
                    ALTER TABLE organization_organizationbranch
                      ADD CONSTRAINT uniq_organization_branch_code UNIQUE (organization_id, branch_code);
                  END IF;
                END $$;
                """
            )

        # --- Recreate UserProfile from people employee data when missing ---
        if not table_exists('organization_userprofile'):
            cursor.execute(
                """
                CREATE TABLE organization_userprofile (
                  id uuid PRIMARY KEY,
                  created_at timestamptz NOT NULL,
                  updated_at timestamptz NOT NULL,
                  display_name varchar(255) NOT NULL DEFAULT '',
                  profile_photo varchar(200) NOT NULL DEFAULT '',
                  mobile_number varchar(32) NOT NULL DEFAULT '',
                  alternate_mobile varchar(32) NOT NULL DEFAULT '',
                  date_of_birth date NULL,
                  gender varchar(32) NOT NULL DEFAULT '',
                  blood_group varchar(16) NOT NULL DEFAULT '',
                  country varchar(100) NOT NULL DEFAULT '',
                  state varchar(100) NOT NULL DEFAULT '',
                  city varchar(100) NOT NULL DEFAULT '',
                  address_line1 varchar(255) NOT NULL DEFAULT '',
                  postal_code varchar(20) NOT NULL DEFAULT '',
                  mother_language varchar(100) NOT NULL DEFAULT '',
                  languages_known jsonb NOT NULL DEFAULT '[]'::jsonb,
                  is_profile_completed boolean NOT NULL DEFAULT false,
                  completed_status varchar(10) NOT NULL DEFAULT '',
                  user_id uuid NOT NULL UNIQUE REFERENCES authentication_user(id) DEFERRABLE INITIALLY DEFERRED,
                  created_by_id uuid NULL REFERENCES authentication_user(id) DEFERRABLE INITIALLY DEFERRED,
                  updated_by_id uuid NULL REFERENCES authentication_user(id) DEFERRABLE INITIALLY DEFERRED
                )
                """
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS organization_userprofile_created_at_idx ON organization_userprofile (created_at)'
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS organization_userprofile_mobile_idx ON organization_userprofile (mobile_number)'
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS organizatio_is_prof_1fdbc7_idx
                  ON organization_userprofile (is_profile_completed, completed_status)
                """
            )

            if table_exists('people_employee'):
                cursor.execute(
                    """
                    INSERT INTO organization_userprofile (
                      id, created_at, updated_at, display_name, profile_photo,
                      mobile_number, alternate_mobile, date_of_birth, gender, blood_group,
                      country, state, city, address_line1, postal_code,
                      mother_language, languages_known, is_profile_completed, completed_status,
                      user_id, created_by_id, updated_by_id
                    )
                    SELECT
                      e.id,
                      e.created_at,
                      e.updated_at,
                      COALESCE(NULLIF(e.display_name, ''), au.first_name || ' ' || au.last_name, au.email),
                      COALESCE(e.profile_photo, ''),
                      COALESCE(c.mobile, ''),
                      COALESCE(c.alternate_mobile, ''),
                      p.date_of_birth,
                      COALESCE(p.gender, ''),
                      COALESCE(p.blood_group, ''),
                      COALESCE(c.country, ''),
                      COALESCE(c.state, ''),
                      COALESCE(c.city, ''),
                      COALESCE(c.address, ''),
                      COALESCE(c.postal_code, ''),
                      COALESCE(p.mother_tongue, ''),
                      COALESCE(p.languages_known, '[]'::jsonb),
                      CASE WHEN COALESCE(c.mobile, '') <> '' AND COALESCE(e.display_name, '') <> '' THEN true ELSE false END,
                      CASE WHEN COALESCE(c.mobile, '') <> '' AND COALESCE(e.display_name, '') <> '' THEN 'done' ELSE '' END,
                      e.user_id,
                      e.created_by_id,
                      e.updated_by_id
                    FROM people_employee e
                    JOIN authentication_user au ON au.id = e.user_id
                    LEFT JOIN people_employeecontact c ON c.employee_id = e.id
                    LEFT JOIN people_employeepersonal p ON p.employee_id = e.id
                    WHERE e.user_id IS NOT NULL
                    ON CONFLICT (user_id) DO NOTHING
                    """
                )

            # Preferences table from accounts domain → seed profile if missing
            if table_exists('authentication_userprofile'):
                cursor.execute(
                    """
                    INSERT INTO organization_userprofile (
                      id, created_at, updated_at, display_name, profile_photo,
                      mobile_number, alternate_mobile, is_profile_completed, completed_status,
                      user_id, created_by_id, updated_by_id, languages_known
                    )
                    SELECT
                      up.id, up.created_at, up.updated_at,
                      COALESCE(NULLIF(au.first_name || ' ' || au.last_name, ' '), au.email),
                      COALESCE(up.avatar, ''),
                      '', '', false, '',
                      up.user_id, up.created_by_id, up.updated_by_id, '[]'::jsonb
                    FROM authentication_userprofile up
                    JOIN authentication_user au ON au.id = up.user_id
                    ON CONFLICT (user_id) DO NOTHING
                    """
                )

        # --- Membership: IAM shape → branch/user/employment shape ---
        if table_exists('organization_organizationmembership'):
            # Ensure branch_id
            if not column_exists('organization_organizationmembership', 'branch_id'):
                cursor.execute(
                    """
                    ALTER TABLE organization_organizationmembership
                      ADD COLUMN branch_id uuid NULL
                    """
                )
                if table_exists('people_employeeorganization'):
                    cursor.execute(
                        """
                        UPDATE organization_organizationmembership m
                        SET branch_id = eo.organization_unit_id
                        FROM people_employee e
                        JOIN people_employeeorganization eo ON eo.employee_id = e.id
                        WHERE e.user_id = m.user_id
                          AND e.organization_id = m.organization_id
                        """
                    )
                cursor.execute(
                    """
                    UPDATE organization_organizationmembership m
                    SET branch_id = b.id
                    FROM organization_organizationbranch b
                    WHERE m.branch_id IS NULL
                      AND b.organization_id = m.organization_id
                      AND b.is_headquarters = true
                    """
                )
                cursor.execute(
                    """
                    UPDATE organization_organizationmembership m
                    SET branch_id = b.id
                    FROM organization_organizationbranch b
                    WHERE m.branch_id IS NULL
                      AND b.organization_id = m.organization_id
                    """
                )

            # Ensure user_id (may already exist from IAM)
            if not column_exists('organization_organizationmembership', 'user_id'):
                cursor.execute(
                    'ALTER TABLE organization_organizationmembership ADD COLUMN user_id uuid NULL'
                )
                if column_exists('organization_organizationmembership', 'user_profile_id'):
                    cursor.execute(
                        """
                        UPDATE organization_organizationmembership m
                        SET user_id = p.user_id
                        FROM organization_userprofile p
                        WHERE m.user_profile_id = p.id
                        """
                    )

            # access_type from role_id
            if column_exists('organization_organizationmembership', 'role_id') and not column_exists(
                'organization_organizationmembership', 'access_type_id'
            ):
                cursor.execute(
                    'ALTER TABLE organization_organizationmembership RENAME COLUMN role_id TO access_type_id'
                )
            elif not column_exists('organization_organizationmembership', 'access_type_id'):
                cursor.execute(
                    'ALTER TABLE organization_organizationmembership ADD COLUMN access_type_id uuid NULL'
                )

            for col, ddl in (
                ('designation_id', 'uuid NULL'),
                ('employee_type_id', 'uuid NULL'),
                ('employee_code', "varchar(64) NOT NULL DEFAULT ''"),
                ('joining_date', 'date NULL'),
                ('exit_date', 'date NULL'),
            ):
                if not column_exists('organization_organizationmembership', col):
                    cursor.execute(
                        f'ALTER TABLE organization_organizationmembership ADD COLUMN {col} {ddl}'
                    )

            if column_exists('organization_organizationmembership', 'joined_date'):
                cursor.execute(
                    """
                    UPDATE organization_organizationmembership
                    SET joining_date = COALESCE(joining_date, joined_date)
                    """
                )

            if table_exists('people_employee'):
                cursor.execute(
                    """
                    UPDATE organization_organizationmembership m
                    SET employee_code = COALESCE(NULLIF(e.employee_code, ''), m.employee_code),
                        employee_type_id = COALESCE(m.employee_type_id, emp.employee_type_id),
                        designation_id = COALESCE(m.designation_id, emp.designation_id),
                        joining_date = COALESCE(m.joining_date, emp.joining_date),
                        exit_date = COALESCE(m.exit_date, emp.termination_date)
                    FROM people_employee e
                    LEFT JOIN people_employeeemployment emp ON emp.employee_id = e.id
                    WHERE e.user_id = m.user_id
                    """
                )

            # Flush deferred FK checks before ALTER/SET NOT NULL
            cursor.execute('SET CONSTRAINTS ALL IMMEDIATE')

            # Drop IAM / legacy columns
            for col in (
                'organization_id',
                'user_profile_id',
                'invitation_status',
                'joined_date',
                'invited_by_id',
                'accepted_at',
                'last_login',
                'role_id',
            ):
                if column_exists('organization_organizationmembership', col):
                    cursor.execute(
                        f'ALTER TABLE organization_organizationmembership DROP COLUMN IF EXISTS {col} CASCADE'
                    )

            cursor.execute('SET CONSTRAINTS ALL IMMEDIATE')
            cursor.execute(
                'ALTER TABLE organization_organizationmembership ALTER COLUMN branch_id SET NOT NULL'
            )
            cursor.execute(
                'ALTER TABLE organization_organizationmembership ALTER COLUMN user_id SET NOT NULL'
            )

            cursor.execute('ALTER TABLE organization_organizationmembership DROP CONSTRAINT IF EXISTS uniq_iam_membership_org_user')
            cursor.execute('ALTER TABLE organization_organizationmembership DROP CONSTRAINT IF EXISTS uniq_org_membership_branch_profile')
            cursor.execute('ALTER TABLE organization_organizationmembership DROP CONSTRAINT IF EXISTS uniq_org_membership_branch_user')
            cursor.execute('DROP INDEX IF EXISTS uniq_org_membership_branch_employee_code')
            cursor.execute('DROP INDEX IF EXISTS iam_membership_org_status_idx')
            cursor.execute('DROP INDEX IF EXISTS iam_membership_user_status_idx')
            cursor.execute('DROP INDEX IF EXISTS organizatio_branch__2a1037_idx')
            cursor.execute('DROP INDEX IF EXISTS organizatio_user_pr_f7664a_idx')

            cursor.execute(
                """
                DO $$ BEGIN
                  ALTER TABLE organization_organizationmembership
                    ADD CONSTRAINT organization_membership_branch_id_fk
                    FOREIGN KEY (branch_id) REFERENCES organization_organizationbranch(id)
                    DEFERRABLE INITIALLY DEFERRED;
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
                """
            )
            cursor.execute(
                """
                DO $$ BEGIN
                  ALTER TABLE organization_organizationmembership
                    ADD CONSTRAINT organization_membership_user_id_fk
                    FOREIGN KEY (user_id) REFERENCES authentication_user(id)
                    DEFERRABLE INITIALLY DEFERRED;
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
                """
            )
            cursor.execute(
                """
                DO $$ BEGIN
                  ALTER TABLE organization_organizationmembership
                    ADD CONSTRAINT organization_membership_access_type_id_fk
                    FOREIGN KEY (access_type_id) REFERENCES organization_accesstype(id)
                    DEFERRABLE INITIALLY DEFERRED;
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
                """
            )
            cursor.execute(
                """
                DO $$ BEGIN
                  ALTER TABLE organization_organizationmembership
                    ADD CONSTRAINT organization_membership_designation_id_fk
                    FOREIGN KEY (designation_id) REFERENCES organization_designation(id)
                    DEFERRABLE INITIALLY DEFERRED;
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
                """
            )
            cursor.execute(
                """
                DO $$ BEGIN
                  ALTER TABLE organization_organizationmembership
                    ADD CONSTRAINT organization_membership_employee_type_id_fk
                    FOREIGN KEY (employee_type_id) REFERENCES organization_employeetype(id)
                    DEFERRABLE INITIALLY DEFERRED;
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
                """
            )
            cursor.execute(
                """
                DO $$ BEGIN
                  ALTER TABLE organization_organizationmembership
                    ADD CONSTRAINT uniq_org_membership_branch_user UNIQUE (branch_id, user_id);
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
                """
            )
            cursor.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uniq_org_membership_branch_employee_code
                  ON organization_organizationmembership (branch_id, employee_code)
                  WHERE employee_code <> ''
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS organizatio_branch_status_idx
                  ON organization_organizationmembership (branch_id, status)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS organizatio_user_id_5f60fd_idx
                  ON organization_organizationmembership (user_id, status)
                """
            )
            cursor.execute('DROP INDEX IF EXISTS organizatio_user_status_idx')
            cursor.execute('DROP INDEX IF EXISTS organizatio_user_id_status_idx')

        # Drop org status column if DDD added it and model no longer has it
        if table_exists('organization_organization') and column_exists('organization_organization', 'status'):
            cursor.execute('ALTER TABLE organization_organization DROP COLUMN IF EXISTS status CASCADE')

        # Drop interim DDD tables
        for table in (
            'people_employeedocument',
            'people_employeelifecycle',
            'people_employeeorganization',
            'people_employeeemployment',
            'people_employeecontact',
            'people_employeepersonal',
            'people_employee',
            'iam_rolepermission',
            'iam_permission',
            'organizations_organizationsettings',
            'authentication_userprofile',
        ):
            if table_exists(table):
                cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE')

        # Content types: remove interim DDD labels (keep admin log consistent)
        cursor.execute(
            """
            DELETE FROM django_admin_log
            WHERE content_type_id IN (
              SELECT id FROM django_content_type
              WHERE app_label IN ('organizations', 'iam', 'people')
                 OR (app_label = 'authentication' AND model = 'userprofile')
            )
            """
        )
        cursor.execute(
            """
            DELETE FROM auth_permission
            WHERE content_type_id IN (
              SELECT id FROM django_content_type
              WHERE app_label IN ('organizations', 'iam', 'people')
                 OR (app_label = 'authentication' AND model = 'userprofile')
            )
            """
        )
        cursor.execute(
            """
            DELETE FROM django_content_type
            WHERE app_label IN ('organizations', 'iam', 'people')
               OR (app_label = 'authentication' AND model = 'userprofile')
            """
        )


def noop_reverse(apps, schema_editor):
    raise RuntimeError('Schema alignment is not reversible.')


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organization', '0008_remove_membership_organization_fk'),
    ]

    operations = [
        migrations.RunPython(forwards_align_schema, noop_reverse),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(model_name='accesstype', name='code'),
                migrations.RemoveField(model_name='designation', name='code'),
                migrations.RemoveField(model_name='employeetype', name='code'),
                migrations.RemoveField(model_name='industrytype', name='code'),
                migrations.RemoveConstraint(
                    model_name='organizationmembership',
                    name='uniq_org_membership_branch_profile',
                ),
                migrations.RemoveIndex(
                    model_name='organizationmembership',
                    name='organizatio_user_pr_f7664a_idx',
                ),
                migrations.RemoveField(
                    model_name='organizationmembership',
                    name='user_profile',
                ),
                migrations.AddField(
                    model_name='organizationmembership',
                    name='user',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='memberships',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                migrations.AddConstraint(
                    model_name='organizationmembership',
                    constraint=models.UniqueConstraint(
                        fields=('branch', 'user'),
                        name='uniq_org_membership_branch_user',
                    ),
                ),
                migrations.AddIndex(
                    model_name='organizationmembership',
                    index=models.Index(fields=['user', 'status'], name='organizatio_user_id_5f60fd_idx'),
                ),
            ],
            database_operations=[],
        ),
    ]
