import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage, extractFieldErrors } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import type { DocumentCategory, DocumentDefinition, PaginationMeta } from '../../types';
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
import './DocumentsManager.css';
import './MasterManager.css';

const EMPTY_FORM = {
  name: '',
  category_id: '',
  description: '',
};

export function DocumentsManager() {
  const { currentBranch } = useWorkspace();
  const [items, setItems] = useState<DocumentDefinition[]>([]);
  const [categories, setCategories] = useState<DocumentCategory[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<DocumentDefinition | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<DocumentDefinition | null>(null);
  const [confirmLoading, setConfirmLoading] = useState(false);

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [docs, cats] = await Promise.all([
        organizationApi.listDocumentDefinitions(token, {
          search: search.trim() || undefined,
          category_id: categoryFilter || undefined,
          page,
          page_size: 20,
        }),
        organizationApi.listDocumentCategories(token, { is_active: true }),
      ]);
      setItems(docs.items);
      setPagination(docs.pagination);
      setCategories(cats);
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load documents.'));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [search, categoryFilter, page]);

  useEffect(() => {
    void load();
  }, [load, currentBranch?.branch_id]);

  useEffect(() => {
    setPage(1);
  }, [search, categoryFilter, currentBranch?.branch_id]);

  function openCreate() {
    setEditing(null);
    setForm({
      ...EMPTY_FORM,
      category_id: categoryFilter || categories[0]?.id || '',
    });
    setFormError(null);
    setFieldErrors({});
    setFormOpen(true);
  }

  function openEdit(row: DocumentDefinition) {
    setEditing(row);
    setForm({
      name: row.name,
      category_id: row.category_id,
      description: row.description || '',
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
    if (!form.name.trim()) nextErrors.name = 'Name is required.';
    if (!form.category_id) nextErrors.category_id = 'Category is required.';
    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    setFormLoading(true);
    setFormError(null);
    try {
      if (editing) {
        await organizationApi.updateDocumentDefinition(token, editing.id, {
          name: form.name.trim(),
          category_id: form.category_id,
          description: form.description.trim(),
        });
      } else {
        await organizationApi.createDocumentDefinition(token, {
          name: form.name.trim(),
          category_id: form.category_id,
          description: form.description.trim(),
        });
      }
      setFormOpen(false);
      await load();
    } catch (err) {
      setFormError(extractErrorMessage(err, 'Unable to save document.'));
      setFieldErrors(extractFieldErrors(err));
    } finally {
      setFormLoading(false);
    }
  }

  async function toggleActive(row: DocumentDefinition) {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    try {
      await organizationApi.updateDocumentDefinition(token, row.id, {
        is_active: !row.is_active,
      });
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to update document status.'));
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setConfirmLoading(true);
    try {
      await organizationApi.deleteDocumentDefinition(token, pendingDelete.id);
      setConfirmOpen(false);
      setPendingDelete(null);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to delete document.'));
      setConfirmOpen(false);
    } finally {
      setConfirmLoading(false);
    }
  }

  const columns = useMemo<DataTableColumn<DocumentDefinition>[]>(
    () => [
      {
        key: 'name',
        header: 'Document',
        render: (row) => (
          <div className="docs-name">
            <strong>{row.name}</strong>
            {row.description ? <span>{row.description}</span> : null}
          </div>
        ),
      },
      {
        key: 'category',
        header: 'Category',
        width: '160px',
        render: (row) => <span className="docs-chip">{row.category_name || '—'}</span>,
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
    [categories],
  );

  return (
    <div className="master-manager docs-manager">
      <PageHeader
        title="Documents"
        description="Define the document types employees can upload. Group them by category for easier policy setup."
        actions={
          <Button type="button" onClick={openCreate}>
            Add document
          </Button>
        }
      />

      <Toolbar
        left={
          <>
            <SearchBar
              value={search}
              onValueChange={setSearch}
              placeholder="Search documents…"
            />
            <label className="docs-filter">
              <span>Category</span>
              <select
                value={categoryFilter}
                onChange={(event) => setCategoryFilter(event.target.value)}
              >
                <option value="">All categories</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </label>
          </>
        }
        right={
          pagination ? (
            <span className="master-count">
              {pagination.total} document{pagination.total === 1 ? '' : 's'}
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
          empty={
            <EmptyState
              title="No documents yet"
              description="Add documents like Aadhaar, PAN, offer letter, or degree certificate. Then assemble them into policies."
              action={
                <Button type="button" onClick={openCreate}>
                  Add your first document
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

      <Modal
        open={formOpen}
        title={editing ? 'Edit document' : 'Add document'}
        onClose={() => setFormOpen(false)}
        footer={
          <>
            <Button type="button" variant="ghost" onClick={() => setFormOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" form="document-form" loading={formLoading}>
              {editing ? 'Save changes' : 'Create document'}
            </Button>
          </>
        }
      >
        <form id="document-form" className="docs-form" onSubmit={handleSubmit}>
          {formError ? <p className="docs-banner docs-banner--error">{formError}</p> : null}
          <label className="docs-field">
            <span>Document name</span>
            <input
              value={form.name}
              onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
              placeholder="e.g. Aadhaar Card"
              maxLength={150}
              autoFocus
            />
            {fieldErrors.name ? <em>{fieldErrors.name}</em> : null}
          </label>
          <label className="docs-field">
            <span>Category</span>
            <select
              value={form.category_id}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, category_id: event.target.value }))
              }
            >
              <option value="">Select category</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
            {fieldErrors.category_id ? <em>{fieldErrors.category_id}</em> : null}
          </label>
          <label className="docs-field">
            <span>Description</span>
            <textarea
              value={form.description}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, description: event.target.value }))
              }
              placeholder="Optional guidance for employees"
              rows={3}
            />
            {fieldErrors.description ? <em>{fieldErrors.description}</em> : null}
          </label>
        </form>
      </Modal>

      <ConfirmDialog
        open={confirmOpen}
        title="Delete document?"
        message={
          pendingDelete
            ? `“${pendingDelete.name}” will be permanently removed. Policies using it must release it first.`
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
