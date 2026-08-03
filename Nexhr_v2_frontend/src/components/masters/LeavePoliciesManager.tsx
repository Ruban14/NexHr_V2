import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import type { LeavePolicy, LeavePolicyRule, PaginationMeta } from '../../types';
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
import './LeavePoliciesManager.css';
import './MasterManager.css';

function modeLabel(frequency: string): string {
  if (frequency === 'monthly') return 'Monthly';
  if (frequency === 'quarterly') return 'Quarterly';
  return 'Upfront';
}

function summarizeRules(rules: LeavePolicyRule[] | undefined): string {
  if (!rules?.length) return 'No leave types yet';
  const modes = new Set(rules.map((rule) => modeLabel(String(rule.allocation_frequency))));
  const modeText = Array.from(modes).join(' · ');
  return `${rules.length} leave type${rules.length === 1 ? '' : 's'} · ${modeText}`;
}

export function LeavePoliciesManager() {
  const navigate = useNavigate();
  const { currentBranch } = useWorkspace();
  const [items, setItems] = useState<LeavePolicy[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<LeavePolicy | null>(null);
  const [confirmLoading, setConfirmLoading] = useState(false);

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await organizationApi.listLeavePolicies(token, {
        search: search.trim() || undefined,
        page,
        page_size: 20,
      });
      setItems(data.items);
      setPagination(data.pagination);
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load leave policies.'));
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

  async function toggleActive(row: LeavePolicy) {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    try {
      await organizationApi.updateLeavePolicy(token, row.id, {
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
      await organizationApi.deleteLeavePolicy(token, pendingDelete.id);
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

  const columns = useMemo<DataTableColumn<LeavePolicy>[]>(
    () => [
      {
        key: 'name',
        header: 'Policy',
        render: (row) => (
          <div className="docs-name leave-policies__name">
            <strong>
              {row.name}
              {row.is_default ? <span className="policy-default">Default</span> : null}
            </strong>
            <span>
              {row.code}
              {row.description ? ` · ${row.description}` : ''}
            </span>
            <em className="leave-policies__summary">{summarizeRules(row.rules)}</em>
          </div>
        ),
      },
      {
        key: 'employee_type',
        header: 'Applies to',
        width: '150px',
        render: (row) => <span className="docs-chip">{row.employee_type_name || '—'}</span>,
      },
      {
        key: 'effective',
        header: 'Effective',
        width: '160px',
        render: (row) => (
          <span className="leave-policies__dates">
            {row.effective_from || '—'}
            {row.effective_to ? (
              <>
                <br />
                to {row.effective_to}
              </>
            ) : null}
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
            <IconAction label="Edit" onClick={() => navigate(`/app/setup/leave-policies/${row.id}`)}>
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
    <div className="master-manager docs-manager leave-policies">
      <PageHeader
        title="Leave Policies"
        description="One policy per employee type. Choose upfront annual leave or monthly accrual for each leave type."
        actions={
          <Button type="button" onClick={() => navigate('/app/setup/leave-policies/new')}>
            New leave policy
          </Button>
        }
      />

      <div className="leave-policies__guide">
        <div>
          <strong>Upfront</strong>
          <span>Full annual leave available from joining / year start</span>
        </div>
        <div>
          <strong>Earn monthly</strong>
          <span>Balance grows each month up to the annual cap</span>
        </div>
      </div>

      <Toolbar
        left={<SearchBar value={search} onValueChange={setSearch} placeholder="Search policies…" />}
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
        <LoadingSkeleton rows={6} />
      ) : (
        <DataTable
          columns={columns}
          rows={items}
          onRowClick={(row) => navigate(`/app/setup/leave-policies/${row.id}`)}
          empty={
            <EmptyState
              title="No leave policies yet"
              description="Create a policy for an employee type, then add Casual, Sick, or Earned leave rules."
              action={
                <Button type="button" onClick={() => navigate('/app/setup/leave-policies/new')}>
                  Create your first policy
                </Button>
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
        title="Delete leave policy?"
        message={
          pendingDelete
            ? `“${pendingDelete.name}” and its leave rules will be permanently removed.`
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
