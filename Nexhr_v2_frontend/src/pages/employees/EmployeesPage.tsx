import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage, extractFieldErrors } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import { Button } from '../../components/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { FormModal, type FormFieldConfig } from '../../components/ui/FormModal';
import { LoadingSkeleton } from '../../components/ui/LoadingSkeleton';
import { SearchBar } from '../../components/ui/SearchBar';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { Toolbar } from '../../components/ui/Toolbar';
import { DataTable, type DataTableColumn } from '../../components/ui/DataTable';
import type { EmployeeRecord, PaginationMeta } from '../../types';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import './EmployeesPage.css';

const CREATE_EMPLOYEE_FIELDS: FormFieldConfig[] = [
  { name: 'display_name', label: 'Display name', maxLength: 255 },
  { name: 'first_name', label: 'First name', maxLength: 150 },
  { name: 'last_name', label: 'Last name', maxLength: 150 },
  { name: 'email', label: 'Email', maxLength: 255, required: true },
];

export function EmployeesPage() {
  const { currentBranch } = useWorkspace();
  const [items, setItems] = useState<EmployeeRecord[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await organizationApi.listEmployees(token, {
        search: search.trim() || undefined,
        page,
        page_size: 20,
      });
      setItems(data.items);
      setPagination(data.pagination);
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load employees.'));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [search, page]);

  useEffect(() => {
    void load();
  }, [load, currentBranch?.branch_id]);

  useEffect(() => {
    setPage(1);
  }, [search, currentBranch?.branch_id]);

  async function handleCreate(values: Record<string, string>) {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setFormLoading(true);
    setFormError(null);
    setFieldErrors({});
    try {
      await organizationApi.createEmployee(token, {
        first_name: values.first_name,
        last_name: values.last_name,
        display_name: values.display_name,
        email: values.email,
      });
      setFormOpen(false);
      await load();
    } catch (err) {
      setFormError(extractErrorMessage(err, 'Unable to create employee.'));
      setFieldErrors(extractFieldErrors(err));
    } finally {
      setFormLoading(false);
    }
  }

  const columns: DataTableColumn<EmployeeRecord>[] = [
    {
      key: 'name',
      header: 'Employee',
      render: (row) => (
        <div>
          <Link to={`/app/employees/${row.id}`} className="employees__name-link">
            <strong>{row.display_name}</strong>
          </Link>
          {row.email ? <div className="employees__meta">{row.email}</div> : null}
        </div>
      ),
    },
    {
      key: 'code',
      header: 'Code',
      width: '120px',
      render: (row) => row.employee_code || '—',
    },
    {
      key: 'lifecycle',
      header: 'Lifecycle',
      width: '180px',
      render: (row) => (
        <span className="employees__status-pill">{row.lifecycle_status.name}</span>
      ),
    },
    {
      key: 'active',
      header: 'Record',
      width: '110px',
      render: (row) => <StatusBadge active={row.is_active} />,
    },
  ];

  return (
    <section className="employees">
      <div className="employees__list-head">
        <p className="employees__list-lead">
          Manage people through a database-driven lifecycle — only valid next steps are offered.
        </p>
        <Button onClick={() => setFormOpen(true)}>Add employee</Button>
      </div>

      <Toolbar
        left={
          <SearchBar
            value={search}
            placeholder="Search employees…"
            onValueChange={setSearch}
            aria-label="Search employees"
          />
        }
        right={pagination ? <span className="employees__count">{pagination.total} total</span> : null}
      />

      {error ? <div className="auth-alert auth-alert--error">{error}</div> : null}

      {loading ? (
        <LoadingSkeleton />
      ) : (
        <DataTable
          columns={columns}
          rows={items}
          empty={
            <EmptyState
              title="No employees yet"
              description="Create a draft employee to begin the lifecycle."
              action={<Button onClick={() => setFormOpen(true)}>Add employee</Button>}
            />
          }
        />
      )}

      {pagination && pagination.total_pages > 1 ? (
        <div className="pagination">
          <span>
            Page {pagination.page} of {pagination.total_pages}
          </span>
          <div className="pagination__controls">
            <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </Button>
            <Button
              variant="secondary"
              disabled={page >= pagination.total_pages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}

      <FormModal
        open={formOpen}
        title="Add employee"
        fields={CREATE_EMPLOYEE_FIELDS}
        submitLabel="Create"
        loading={formLoading}
        error={formError}
        fieldErrors={fieldErrors}
        onSubmit={handleCreate}
        onClose={() => setFormOpen(false)}
      />
    </section>
  );
}
