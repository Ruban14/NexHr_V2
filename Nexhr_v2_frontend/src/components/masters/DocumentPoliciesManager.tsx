import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import type { DocumentPolicy, PaginationMeta } from '../../types';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import { Button } from '../Button';
import { ConfirmDialog } from '../ui/ConfirmDialog';
import { DataTable, type DataTableColumn } from '../ui/DataTable';
import { EmptyState } from '../ui/EmptyState';
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
import './DocumentsManager.css';
import './MasterManager.css';

export function DocumentPoliciesManager() {
  const navigate = useNavigate();
  const { currentBranch } = useWorkspace();
  const [items, setItems] = useState<DocumentPolicy[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<DocumentPolicy | null>(null);
  const [confirmLoading, setConfirmLoading] = useState(false);

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await organizationApi.listDocumentPolicies(token, {
        search: search.trim() || undefined,
        page,
        page_size: 20,
      });
      setItems(data.items);
      setPagination(data.pagination);
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load document policies.'));
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

  async function toggleActive(row: DocumentPolicy) {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    try {
      await organizationApi.updateDocumentPolicy(token, row.id, {
        is_active: !row.is_active,
      });
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to update policy status.'));
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setConfirmLoading(true);
    try {
      await organizationApi.deleteDocumentPolicy(token, pendingDelete.id);
      setConfirmOpen(false);
      setPendingDelete(null);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to delete policy.'));
      setConfirmOpen(false);
    } finally {
      setConfirmLoading(false);
    }
  }

  const columns = useMemo<DataTableColumn<DocumentPolicy>[]>(
    () => [
      {
        key: 'name',
        header: 'Policy',
        render: (row) => (
          <div className="docs-name">
            <strong>
              {row.name}
              {row.is_default ? <span className="policy-default">Default</span> : null}
            </strong>
            {row.description ? <span>{row.description}</span> : null}
          </div>
        ),
      },
      {
        key: 'employee_type',
        header: 'Employee type',
        width: '160px',
        render: (row) => <span className="docs-chip">{row.employee_type_name || '—'}</span>,
      },
      {
        key: 'items',
        header: 'Documents',
        width: '110px',
        render: (row) => (
          <span className="policy-count">
            {row.item_count} doc{row.item_count === 1 ? '' : 's'}
          </span>
        ),
      },
      {
        key: 'status',
        header: 'Status',
        width: '110px',
        render: (row) => <StatusBadge active={row.is_active} />,
      },
      {
        key: 'actions',
        header: '',
        width: '140px',
        render: (row) => (
          <div className="docs-actions" onClick={(event) => event.stopPropagation()}>
            <IconAction label="Edit" onClick={() => navigate(`/app/setup/document-policies/${row.id}`)}>
              <IconEdit />
            </IconAction>
            <IconAction
              label={row.is_active ? 'Deactivate' : 'Activate'}
              onClick={() => void toggleActive(row)}
            >
              {row.is_active ? <IconDeactivate /> : <IconActivate />}
            </IconAction>
            <IconAction
              label="Delete"
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
    [navigate],
  );

  return (
    <div className="master-manager docs-manager">
      <PageHeader
        title="Document policies"
        description="Build policies by dragging documents into the required checklist for each employee type."
        actions={
          <Button type="button" onClick={() => navigate('/app/setup/document-policies/new')}>
            Create policy
          </Button>
        }
      />

      <Toolbar
        left={
          <SearchBar value={search} onValueChange={setSearch} placeholder="Search policies…" />
        }
        right={
          pagination ? (
            <span className="master-count">
              {pagination.total} polic{pagination.total === 1 ? 'y' : 'ies'}
            </span>
          ) : null
        }
      />

      {error ? <p className="docs-banner docs-banner--error">{error}</p> : null}

      {loading ? (
        <LoadingSkeleton rows={5} />
      ) : (
        <DataTable
          columns={columns}
          rows={items}
          onRowClick={(row) => navigate(`/app/setup/document-policies/${row.id}`)}
          empty={
            <EmptyState
              title="No policies yet"
              description="Create a policy, then drag documents from the catalog into the checklist. Reorder them to match onboarding flow."
              action={
                <div className="policy-empty-actions">
                  <Button type="button" onClick={() => navigate('/app/setup/document-policies/new')}>
                    Create policy
                  </Button>
                  <Link to="/app/setup/documents" className="policy-empty-link">
                    Manage documents first
                  </Link>
                </div>
              }
            />
          }
        />
      )}

      {pagination && pagination.total_pages > 1 ? (
        <div className="docs-pagination">
          <Button
            type="button"
            variant="secondary"
            disabled={page <= 1}
            onClick={() => setPage((prev) => Math.max(1, prev - 1))}
          >
            Previous
          </Button>
          <span>
            Page {pagination.page} of {pagination.total_pages}
          </span>
          <Button
            type="button"
            variant="secondary"
            disabled={page >= pagination.total_pages}
            onClick={() => setPage((prev) => prev + 1)}
          >
            Next
          </Button>
        </div>
      ) : null}

      <ConfirmDialog
        open={confirmOpen}
        title="Delete policy?"
        message={
          pendingDelete
            ? `“${pendingDelete.name}” and its document checklist will be permanently removed.`
            : ''
        }
        confirmLabel="Delete"
        danger
        loading={confirmLoading}
        onConfirm={() => void confirmDelete()}
        onCancel={() => {
          setConfirmOpen(false);
          setPendingDelete(null);
        }}
      />
    </div>
  );
}
