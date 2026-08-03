import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage, extractFieldErrors } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import type { AssetRecord, AssetType, PaginationMeta } from '../../types';
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
import { Modal } from '../ui/Modal';
import { PageHeader } from '../ui/PageHeader';
import { SearchBar } from '../ui/SearchBar';
import { StatusBadge } from '../ui/StatusBadge';
import { Toolbar } from '../ui/Toolbar';
import './AssetsManager.css';
import './MasterManager.css';

const EMPTY_FORM = {
  asset_type_id: '',
  asset_code: '',
  name: '',
  brand: '',
  model: '',
  serial_number: '',
  purchase_date: '',
  warranty_expiry: '',
  status: 'available',
  remarks: '',
};

const STATUS_OPTIONS = [
  { value: 'available', label: 'Available' },
  { value: 'assigned', label: 'Assigned' },
  { value: 'lost', label: 'Lost' },
  { value: 'damaged', label: 'Damaged' },
  { value: 'retired', label: 'Retired' },
];

function statusTone(status: string): string {
  if (status === 'available') return 'is-ok';
  if (status === 'assigned') return 'is-info';
  if (status === 'lost' || status === 'damaged') return 'is-bad';
  return 'is-muted';
}

export function AssetsManager() {
  const { currentBranch } = useWorkspace();
  const [items, setItems] = useState<AssetRecord[]>([]);
  const [types, setTypes] = useState<AssetType[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<AssetRecord | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const [typeModalOpen, setTypeModalOpen] = useState(false);
  const [typeName, setTypeName] = useState('');
  const [typeDescription, setTypeDescription] = useState('');
  const [typeLoading, setTypeLoading] = useState(false);
  const [typeError, setTypeError] = useState<string | null>(null);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<AssetRecord | null>(null);
  const [confirmLoading, setConfirmLoading] = useState(false);

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [assets, assetTypes] = await Promise.all([
        organizationApi.listAssets(token, {
          search: search.trim() || undefined,
          asset_type_id: typeFilter || undefined,
          status: statusFilter || undefined,
          page,
          page_size: 20,
        }),
        organizationApi.listAssetTypes(token, { is_active: true }),
      ]);
      setItems(assets.items);
      setPagination(assets.pagination);
      setTypes(assetTypes);
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load assets.'));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [search, typeFilter, statusFilter, page]);

  useEffect(() => {
    void load();
  }, [load, currentBranch?.branch_id]);

  useEffect(() => {
    setPage(1);
  }, [search, typeFilter, statusFilter, currentBranch?.branch_id]);

  function openCreate() {
    setEditing(null);
    setForm({
      ...EMPTY_FORM,
      asset_type_id: typeFilter || types[0]?.id || '',
    });
    setFormError(null);
    setFieldErrors({});
    setFormOpen(true);
  }

  function openEdit(row: AssetRecord) {
    setEditing(row);
    setForm({
      asset_type_id: row.asset_type_id,
      asset_code: row.asset_code,
      name: row.name,
      brand: row.brand || '',
      model: row.model || '',
      serial_number: row.serial_number || '',
      purchase_date: row.purchase_date || '',
      warranty_expiry: row.warranty_expiry || '',
      status: row.status || 'available',
      remarks: row.remarks || '',
    });
    setFormError(null);
    setFieldErrors({});
    setFormOpen(true);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const token = tokenStorage.getAccessToken();
    if (!token) return;

    const nextErrors: Record<string, string> = {};
    if (!form.asset_code.trim()) nextErrors.asset_code = 'Asset code is required.';
    if (!form.name.trim()) nextErrors.name = 'Name is required.';
    if (!form.asset_type_id) nextErrors.asset_type_id = 'Asset type is required.';
    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    const payload = {
      asset_type_id: form.asset_type_id,
      asset_code: form.asset_code.trim(),
      name: form.name.trim(),
      brand: form.brand.trim(),
      model: form.model.trim(),
      serial_number: form.serial_number.trim(),
      purchase_date: form.purchase_date || null,
      warranty_expiry: form.warranty_expiry || null,
      status: form.status,
      remarks: form.remarks.trim(),
    };

    setFormLoading(true);
    setFormError(null);
    try {
      if (editing) {
        await organizationApi.updateAsset(token, editing.id, payload);
      } else {
        await organizationApi.createAsset(token, payload);
      }
      setFormOpen(false);
      await load();
    } catch (err) {
      setFormError(extractErrorMessage(err, 'Unable to save asset.'));
      setFieldErrors(extractFieldErrors(err));
    } finally {
      setFormLoading(false);
    }
  }

  async function toggleActive(row: AssetRecord) {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    try {
      await organizationApi.updateAsset(token, row.id, { is_active: !row.is_active });
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to update asset status.'));
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setConfirmLoading(true);
    try {
      await organizationApi.deleteAsset(token, pendingDelete.id);
      setConfirmOpen(false);
      setPendingDelete(null);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to delete asset.'));
      setConfirmOpen(false);
    } finally {
      setConfirmLoading(false);
    }
  }

  async function createType(event: FormEvent) {
    event.preventDefault();
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    if (!typeName.trim()) {
      setTypeError('Type name is required.');
      return;
    }
    setTypeLoading(true);
    setTypeError(null);
    try {
      await organizationApi.createAssetType(token, {
        name: typeName.trim(),
        description: typeDescription.trim(),
      });
      setTypeName('');
      setTypeDescription('');
      const assetTypes = await organizationApi.listAssetTypes(token, { is_active: true });
      setTypes(assetTypes);
    } catch (err) {
      setTypeError(extractErrorMessage(err, 'Unable to create asset type.'));
    } finally {
      setTypeLoading(false);
    }
  }

  async function deactivateType(row: AssetType) {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    try {
      await organizationApi.updateAssetType(token, row.id, { is_active: false });
      const assetTypes = await organizationApi.listAssetTypes(token, { is_active: true });
      setTypes(assetTypes);
    } catch (err) {
      setTypeError(extractErrorMessage(err, 'Unable to update asset type.'));
    }
  }

  const columns = useMemo<DataTableColumn<AssetRecord>[]>(
    () => [
      {
        key: 'asset',
        header: 'Asset',
        render: (row) => (
          <div className="assets-name">
            <strong>
              {row.asset_code} · {row.name}
            </strong>
            <span>
              {[row.brand, row.model, row.serial_number].filter(Boolean).join(' · ') || '—'}
            </span>
          </div>
        ),
      },
      {
        key: 'type',
        header: 'Type',
        width: '140px',
        render: (row) => <span className="assets-chip">{row.asset_type_name || '—'}</span>,
      },
      {
        key: 'status',
        header: 'Status',
        width: '120px',
        render: (row) => (
          <span className={`assets-status ${statusTone(row.status)}`}>
            {STATUS_OPTIONS.find((item) => item.value === row.status)?.label || row.status}
          </span>
        ),
      },
      {
        key: 'active',
        header: 'Active',
        width: '100px',
        render: (row) => <StatusBadge active={row.is_active} />,
      },
      {
        key: 'actions',
        header: '',
        width: '140px',
        render: (row) => (
          <div className="assets-actions" onClick={(event) => event.stopPropagation()}>
            <IconAction label="Edit" onClick={() => openEdit(row)}>
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
    [],
  );

  return (
    <div className="master-manager assets-manager">
      <PageHeader
        title="Assets"
        description="Maintain organization asset inventory. Assign and revoke assets from each employee profile."
        actions={
          <>
            <Button type="button" variant="secondary" onClick={() => setTypeModalOpen(true)}>
              Manage types
            </Button>
            <Button type="button" onClick={openCreate}>
              Add asset
            </Button>
          </>
        }
      />

      <Toolbar
        left={
          <>
            <SearchBar value={search} onValueChange={setSearch} placeholder="Search assets…" />
            <label className="assets-filter">
              <span>Type</span>
              <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
                <option value="">All types</option>
                {types.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="assets-filter">
              <span>Status</span>
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
              >
                <option value="">All statuses</option>
                {STATUS_OPTIONS.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
          </>
        }
        right={
          pagination ? (
            <span className="master-count">
              {pagination.total} asset{pagination.total === 1 ? '' : 's'}
            </span>
          ) : null
        }
      />

      {error ? <p className="assets-banner assets-banner--error">{error}</p> : null}

      {loading ? (
        <LoadingSkeleton rows={6} />
      ) : (
        <DataTable
          columns={columns}
          rows={items}
          empty={
            <EmptyState
              title="No assets yet"
              description="Add laptops, phones, access cards, or other company assets. Then assign them from employee profiles."
              action={
                <Button type="button" onClick={openCreate}>
                  Add your first asset
                </Button>
              }
            />
          }
        />
      )}

      {pagination && pagination.total_pages > 1 ? (
        <div className="assets-pagination">
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

      <Modal
        open={formOpen}
        title={editing ? 'Edit asset' : 'Add asset'}
        onClose={() => setFormOpen(false)}
        footer={
          <>
            <Button type="button" variant="ghost" onClick={() => setFormOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" form="asset-form" loading={formLoading}>
              {editing ? 'Save changes' : 'Create asset'}
            </Button>
          </>
        }
      >
        <form id="asset-form" className="assets-form" onSubmit={handleSubmit}>
          {formError ? <p className="assets-banner assets-banner--error">{formError}</p> : null}
          <div className="assets-form__grid">
            <label className="assets-field">
              <span>Asset code</span>
              <input
                value={form.asset_code}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, asset_code: event.target.value }))
                }
                placeholder="e.g. LAP-001"
                maxLength={50}
                autoFocus
              />
              {fieldErrors.asset_code ? <em>{fieldErrors.asset_code}</em> : null}
            </label>
            <label className="assets-field">
              <span>Asset type</span>
              <select
                value={form.asset_type_id}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, asset_type_id: event.target.value }))
                }
              >
                <option value="">Select type</option>
                {types.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
              {fieldErrors.asset_type_id ? <em>{fieldErrors.asset_type_id}</em> : null}
            </label>
            <label className="assets-field assets-field--full">
              <span>Name</span>
              <input
                value={form.name}
                onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                placeholder="e.g. Dell Latitude 5440"
                maxLength={150}
              />
              {fieldErrors.name ? <em>{fieldErrors.name}</em> : null}
            </label>
            <label className="assets-field">
              <span>Brand</span>
              <input
                value={form.brand}
                onChange={(event) => setForm((prev) => ({ ...prev, brand: event.target.value }))}
                maxLength={100}
              />
            </label>
            <label className="assets-field">
              <span>Model</span>
              <input
                value={form.model}
                onChange={(event) => setForm((prev) => ({ ...prev, model: event.target.value }))}
                maxLength={100}
              />
            </label>
            <label className="assets-field">
              <span>Serial number</span>
              <input
                value={form.serial_number}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, serial_number: event.target.value }))
                }
                maxLength={100}
              />
            </label>
            <label className="assets-field">
              <span>Status</span>
              <select
                value={form.status}
                onChange={(event) => setForm((prev) => ({ ...prev, status: event.target.value }))}
                disabled={editing?.status === 'assigned'}
              >
                {STATUS_OPTIONS.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="assets-field">
              <span>Purchase date</span>
              <input
                type="date"
                value={form.purchase_date}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, purchase_date: event.target.value }))
                }
              />
            </label>
            <label className="assets-field">
              <span>Warranty expiry</span>
              <input
                type="date"
                value={form.warranty_expiry}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, warranty_expiry: event.target.value }))
                }
              />
            </label>
            <label className="assets-field assets-field--full">
              <span>Remarks</span>
              <textarea
                value={form.remarks}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, remarks: event.target.value }))
                }
                rows={3}
              />
            </label>
          </div>
          {!types.length ? (
            <p className="assets-banner assets-banner--warn">
              Create an asset type first using Manage types.
            </p>
          ) : null}
        </form>
      </Modal>

      <Modal
        open={typeModalOpen}
        title="Asset types"
        onClose={() => setTypeModalOpen(false)}
        footer={
          <Button type="button" variant="ghost" onClick={() => setTypeModalOpen(false)}>
            Close
          </Button>
        }
      >
        <form className="assets-form" onSubmit={createType}>
          {typeError ? <p className="assets-banner assets-banner--error">{typeError}</p> : null}
          <div className="assets-form__grid">
            <label className="assets-field">
              <span>Type name</span>
              <input
                value={typeName}
                onChange={(event) => setTypeName(event.target.value)}
                placeholder="e.g. Laptop"
                maxLength={100}
              />
            </label>
            <label className="assets-field">
              <span>Description</span>
              <input
                value={typeDescription}
                onChange={(event) => setTypeDescription(event.target.value)}
                placeholder="Optional"
              />
            </label>
          </div>
          <div className="assets-type-actions">
            <Button type="submit" loading={typeLoading}>
              Add type
            </Button>
          </div>
        </form>
        <ul className="assets-type-list">
          {types.map((item) => (
            <li key={item.id}>
              <div>
                <strong>{item.name}</strong>
                {item.description ? <span>{item.description}</span> : null}
              </div>
              <Button type="button" variant="ghost" onClick={() => void deactivateType(item)}>
                Deactivate
              </Button>
            </li>
          ))}
          {!types.length ? <li className="assets-type-list__empty">No active types yet.</li> : null}
        </ul>
      </Modal>

      <ConfirmDialog
        open={confirmOpen}
        title="Delete asset?"
        message={
          pendingDelete
            ? `“${pendingDelete.asset_code}” will be permanently removed. Active assignments must be revoked first.`
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
