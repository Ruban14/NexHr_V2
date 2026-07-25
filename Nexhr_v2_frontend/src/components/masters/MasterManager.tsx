import { useCallback, useEffect, useMemo, useState } from 'react';
import { extractErrorMessage, extractFieldErrors } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import { Button } from '../Button';
import { ConfirmDialog } from '../ui/ConfirmDialog';
import { DataTable, type DataTableColumn } from '../ui/DataTable';
import { EmptyState } from '../ui/EmptyState';
import { FormModal } from '../ui/FormModal';
import {
  IconAction,
  IconActivate,
  IconDeactivate,
  IconDelete,
  IconEdit,
} from '../ui/IconAction';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { PageHeader } from '../ui/PageHeader';
import { SearchBar } from '../ui/SearchBar';
import { StatusBadge } from '../ui/StatusBadge';
import { Toolbar } from '../ui/Toolbar';
import type { MasterConfig } from '../../masters/masterConfig';
import type { MasterRecord, PaginationMeta } from '../../types';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import './MasterManager.css';

type MasterManagerProps = {
  config: MasterConfig;
};

export function MasterManager({ config }: MasterManagerProps) {
  const { currentBranch } = useWorkspace();
  const [items, setItems] = useState<MasterRecord[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<MasterRecord | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<MasterRecord | null>(null);
  const [confirmLoading, setConfirmLoading] = useState(false);

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await config.list(token, {
        search: search.trim() || undefined,
        page,
        page_size: 20,
      });
      setItems(data.items);
      setPagination(data.pagination);
    } catch (err) {
      setError(extractErrorMessage(err, `Unable to load ${config.title.toLowerCase()}.`));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [config, search, page]);

  useEffect(() => {
    void load();
  }, [load, currentBranch?.branch_id]);

  useEffect(() => {
    setPage(1);
  }, [search, currentBranch?.branch_id, config.key]);

  function openCreate() {
    setEditing(null);
    setFormError(null);
    setFieldErrors({});
    setFormOpen(true);
  }

  function openEdit(row: MasterRecord) {
    setEditing(row);
    setFormError(null);
    setFieldErrors({});
    setFormOpen(true);
  }

  async function handleSubmit(values: Record<string, string>) {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setFormLoading(true);
    setFormError(null);
    setFieldErrors({});
    try {
      if (editing) {
        await config.update(token, editing.id, values);
      } else {
        await config.create(token, values);
      }
      setFormOpen(false);
      await load();
    } catch (err) {
      setFormError(extractErrorMessage(err, 'Unable to save.'));
      setFieldErrors(extractFieldErrors(err));
    } finally {
      setFormLoading(false);
    }
  }

  async function toggleActive(row: MasterRecord) {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    try {
      await config.update(token, row.id, { is_active: !row.is_active });
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to update status.'));
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setConfirmLoading(true);
    try {
      await config.remove(token, pendingDelete.id);
      setConfirmOpen(false);
      setPendingDelete(null);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to delete.'));
      setConfirmOpen(false);
    } finally {
      setConfirmLoading(false);
    }
  }

  const columns = useMemo<DataTableColumn<MasterRecord>[]>(
    () => [
      {
        key: 'name',
        header: 'Name',
        render: (row) => {
          const subtitle =
            config.getSubtitle?.(row) ||
            ('description' in row && row.description ? String(row.description) : null);
          return (
            <div>
              <strong>{row.name}</strong>
              {subtitle ? <div className="master-desc">{subtitle}</div> : null}
            </div>
          );
        },
      },
      {
        key: 'status',
        header: 'Status',
        width: '120px',
        render: (row) => <StatusBadge active={row.is_active} />,
      },
      {
        key: 'actions',
        header: 'Actions',
        width: '180px',
        render: (row) => (
          <div className="table-actions" onClick={(event) => event.stopPropagation()}>
            <IconAction label={`Edit ${row.name}`} onClick={() => openEdit(row)}>
              <IconEdit />
            </IconAction>
            <IconAction
              label={row.is_active ? `Deactivate ${row.name}` : `Activate ${row.name}`}
              className={row.is_active ? 'icon-action--warning' : 'icon-action--success'}
              onClick={() => void toggleActive(row)}
            >
              {row.is_active ? <IconDeactivate /> : <IconActivate />}
            </IconAction>
            <IconAction
              label={`Delete ${row.name}`}
              danger
              onClick={() => {
                setPendingDelete(row);
                setConfirmOpen(true);
              }}
            >
              <IconDelete />
            </IconAction>
          </div>
        ),
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [config.key],
  );

  const initialValues = useMemo(() => {
    if (!editing) return {};
    if (config.getInitialValues) return config.getInitialValues(editing);
    const values: Record<string, string> = { name: editing.name };
    if ('description' in editing) {
      values.description = String(editing.description || '');
    }
    return values;
  }, [editing, config]);

  return (
    <section className="master-manager">
      <PageHeader
        title={config.title}
        description={config.description}
        actions={
          <Button onClick={openCreate}>Add {config.singular}</Button>
        }
      />

      <Toolbar
        left={
          <SearchBar
            value={search}
            placeholder={`Search ${config.title.toLowerCase()}…`}
            onValueChange={setSearch}
            aria-label={`Search ${config.title}`}
          />
        }
        right={
          pagination ? (
            <span className="master-count">{pagination.total} total</span>
          ) : null
        }
      />

      {error ? <div className="auth-alert auth-alert--error">{error}</div> : null}

      {loading ? (
        <LoadingSkeleton />
      ) : (
        <DataTable
          columns={columns}
          rows={items}
          selectedId={selectedId}
          onRowClick={(row) => setSelectedId(row.id)}
          empty={
            <EmptyState
              title={`No ${config.title.toLowerCase()} yet`}
              description={`Create your first ${config.singular.toLowerCase()} to get started.`}
              action={<Button onClick={openCreate}>Add {config.singular}</Button>}
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
            <Button
              variant="secondary"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
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
        title={editing ? `Edit ${config.singular}` : `Add ${config.singular}`}
        fields={config.fields}
        initialValues={initialValues}
        submitLabel={editing ? 'Save changes' : 'Create'}
        loading={formLoading}
        error={formError}
        fieldErrors={fieldErrors}
        onSubmit={handleSubmit}
        onClose={() => setFormOpen(false)}
      />

      <ConfirmDialog
        open={confirmOpen}
        title={`Delete ${config.singular.toLowerCase()}?`}
        message={`“${pendingDelete?.name ?? ''}” will be permanently removed. This cannot be undone.`}
        confirmLabel="Delete"
        danger
        loading={confirmLoading}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={() => void confirmDelete()}
      />
    </section>
  );
}
