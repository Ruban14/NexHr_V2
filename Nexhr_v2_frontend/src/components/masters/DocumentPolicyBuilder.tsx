import { useCallback, useEffect, useMemo, useState, type DragEvent, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage, extractFieldErrors } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import type { DocumentDefinition, DocumentPolicyItem, EmployeeType } from '../../types';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import { Button } from '../Button';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { PageHeader } from '../ui/PageHeader';
import { SearchBar } from '../ui/SearchBar';
import './DocumentPolicyBuilder.css';

type DraftItem = DocumentPolicyItem & {
  document_name: string;
  category_name: string;
};

type DragPayload =
  | { source: 'catalog'; documentId: string }
  | { source: 'policy'; documentId: string };

function parseDragPayload(event: DragEvent): DragPayload | null {
  const raw = event.dataTransfer.getData('application/x-nexhr-doc') || event.dataTransfer.getData('text/plain');
  if (!raw) return null;
  try {
    return JSON.parse(raw) as DragPayload;
  } catch {
    return null;
  }
}

function reorderItems(items: DraftItem[], fromId: string, toId: string, placeAfter: boolean): DraftItem[] {
  if (fromId === toId) return items;
  const next = [...items];
  const fromIndex = next.findIndex((item) => item.document_id === fromId);
  const toIndex = next.findIndex((item) => item.document_id === toId);
  if (fromIndex < 0 || toIndex < 0) return items;
  const [moved] = next.splice(fromIndex, 1);
  let insertAt = toIndex;
  if (fromIndex < toIndex) insertAt -= 1;
  if (placeAfter) insertAt += 1;
  next.splice(Math.max(0, insertAt), 0, moved);
  return next.map((item, index) => ({ ...item, display_order: index }));
}

export function DocumentPolicyBuilder() {
  const { policyId } = useParams<{ policyId: string }>();
  const isNew = !policyId || policyId === 'new';
  const navigate = useNavigate();
  const { currentBranch } = useWorkspace();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const [employeeTypes, setEmployeeTypes] = useState<EmployeeType[]>([]);
  const [documents, setDocuments] = useState<DocumentDefinition[]>([]);
  const [catalogSearch, setCatalogSearch] = useState('');

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [employeeTypeId, setEmployeeTypeId] = useState('');
  const [isDefault, setIsDefault] = useState(false);
  const [items, setItems] = useState<DraftItem[]>([]);

  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dropTargetId, setDropTargetId] = useState<string | null>(null);
  const [dropAfter, setDropAfter] = useState(false);
  const [overPolicy, setOverPolicy] = useState(false);

  const selectedIds = useMemo(() => new Set(items.map((item) => item.document_id)), [items]);

  const catalog = useMemo(() => {
    const query = catalogSearch.trim().toLowerCase();
    return documents
      .filter((doc) => doc.is_active && !selectedIds.has(doc.id))
      .filter((doc) => {
        if (!query) return true;
        return (
          doc.name.toLowerCase().includes(query) ||
          (doc.category_name || '').toLowerCase().includes(query) ||
          (doc.description || '').toLowerCase().includes(query)
        );
      });
  }, [documents, selectedIds, catalogSearch]);

  const groupedCatalog = useMemo(() => {
    const groups = new Map<string, DocumentDefinition[]>();
    for (const doc of catalog) {
      const key = doc.category_name || 'Other';
      const list = groups.get(key) || [];
      list.push(doc);
      groups.set(key, list);
    }
    return Array.from(groups.entries());
  }, [catalog]);

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [types, docs] = await Promise.all([
        organizationApi.listEmployeeTypes(token, { page_size: 100, is_active: true }),
        organizationApi.listDocumentDefinitions(token, { page_size: 100, is_active: true }),
      ]);
      setEmployeeTypes(types.items);
      setDocuments(docs.items);

      if (!isNew && policyId) {
        const policy = await organizationApi.getDocumentPolicy(token, policyId);
        setName(policy.name);
        setDescription(policy.description || '');
        setEmployeeTypeId(policy.employee_type_id);
        setIsDefault(policy.is_default);
        setItems(
          policy.items.map((item, index) => ({
            ...item,
            document_name: item.document_name || 'Document',
            category_name: item.category_name || 'Other',
            display_order: item.display_order ?? index,
          })),
        );
      } else {
        setEmployeeTypeId(types.items[0]?.id || '');
      }
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load policy builder.'));
    } finally {
      setLoading(false);
    }
  }, [isNew, policyId]);

  useEffect(() => {
    void load();
  }, [load, currentBranch?.branch_id]);

  function addDocument(doc: DocumentDefinition) {
    setItems((prev) => {
      if (prev.some((item) => item.document_id === doc.id)) return prev;
      return [
        ...prev,
        {
          document_id: doc.id,
          document_name: doc.name,
          category_name: doc.category_name || 'Other',
          category_id: doc.category_id,
          display_order: prev.length,
          is_required: true,
          allow_multiple: false,
          verification_required: true,
          requires_expiry: false,
        },
      ];
    });
  }

  function removeItem(documentId: string) {
    setItems((prev) =>
      prev
        .filter((item) => item.document_id !== documentId)
        .map((item, index) => ({ ...item, display_order: index })),
    );
  }

  function updateItem(documentId: string, patch: Partial<DraftItem>) {
    setItems((prev) =>
      prev.map((item) => (item.document_id === documentId ? { ...item, ...patch } : item)),
    );
  }

  function startDrag(event: DragEvent, payload: DragPayload) {
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('application/x-nexhr-doc', JSON.stringify(payload));
    event.dataTransfer.setData('text/plain', JSON.stringify(payload));
    setDraggingId(payload.documentId);
  }

  function clearDragState() {
    setDraggingId(null);
    setDropTargetId(null);
    setDropAfter(false);
    setOverPolicy(false);
  }

  function handlePolicyDragOver(event: DragEvent) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    setOverPolicy(true);
  }

  function handleItemDragOver(event: DragEvent, documentId: string) {
    event.preventDefault();
    event.stopPropagation();
    event.dataTransfer.dropEffect = 'move';
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    setDropTargetId(documentId);
    setDropAfter(event.clientY > rect.top + rect.height / 2);
    setOverPolicy(true);
  }

  function handleDropOnPolicy(event: DragEvent) {
    event.preventDefault();
    const payload = parseDragPayload(event);
    clearDragState();
    if (!payload) return;

    if (payload.source === 'catalog') {
      const doc = documents.find((item) => item.id === payload.documentId);
      if (doc) addDocument(doc);
      return;
    }

    if (payload.source === 'policy' && dropTargetId) {
      setItems((prev) => reorderItems(prev, payload.documentId, dropTargetId, dropAfter));
    }
  }

  function handleDropOnItem(event: DragEvent, targetId: string) {
    event.preventDefault();
    event.stopPropagation();
    const payload = parseDragPayload(event);
    const placeAfter = dropAfter;
    clearDragState();
    if (!payload) return;

    if (payload.source === 'catalog') {
      const doc = documents.find((item) => item.id === payload.documentId);
      if (!doc) return;
      setItems((prev) => {
        if (prev.some((item) => item.document_id === doc.id)) return prev;
        const next = [...prev];
        const targetIndex = next.findIndex((item) => item.document_id === targetId);
        const insertAt = targetIndex < 0 ? next.length : targetIndex + (placeAfter ? 1 : 0);
        next.splice(insertAt, 0, {
          document_id: doc.id,
          document_name: doc.name,
          category_name: doc.category_name || 'Other',
          category_id: doc.category_id,
          display_order: insertAt,
          is_required: true,
          allow_multiple: false,
          verification_required: true,
          requires_expiry: false,
        });
        return next.map((item, index) => ({ ...item, display_order: index }));
      });
      return;
    }

    if (payload.source === 'policy') {
      setItems((prev) => reorderItems(prev, payload.documentId, targetId, placeAfter));
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const token = tokenStorage.getAccessToken();
    if (!token) return;

    const nextErrors: Record<string, string> = {};
    if (!name.trim()) nextErrors.name = 'Policy name is required.';
    if (!employeeTypeId) nextErrors.employee_type_id = 'Employee type is required.';
    if (!items.length) nextErrors.items = 'Add at least one document to the policy.';
    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    setSaving(true);
    setError(null);
    const payload = {
      name: name.trim(),
      employee_type_id: employeeTypeId,
      description: description.trim(),
      is_default: isDefault,
      items: items.map((item, index) => ({
        document_id: item.document_id,
        display_order: index,
        is_required: item.is_required,
        allow_multiple: item.allow_multiple,
        verification_required: item.verification_required,
        requires_expiry: item.requires_expiry,
      })),
    };

    try {
      if (isNew) {
        const created = await organizationApi.createDocumentPolicy(token, payload);
        navigate(`/app/setup/document-policies/${created.id}`, { replace: true });
      } else if (policyId) {
        await organizationApi.updateDocumentPolicy(token, policyId, payload);
        navigate('/app/setup/document-policies');
      }
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to save policy.'));
      setFieldErrors(extractFieldErrors(err));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="policy-builder">
        <PageHeader title={isNew ? 'Create policy' : 'Edit policy'} description="Loading…" />
        <LoadingSkeleton rows={8} />
      </div>
    );
  }

  return (
    <div className={`policy-builder ${draggingId ? 'is-dragging' : ''}`}>
      <PageHeader
        title={isNew ? 'Create document policy' : 'Edit document policy'}
        description="Drag documents from the catalog into the checklist. Reorder them to match your onboarding sequence."
        breadcrumb={
          <Link to="/app/setup/document-policies" className="policy-builder__back">
            ← Back to policies
          </Link>
        }
        actions={
          <div className="policy-builder__actions">
            <Button type="button" variant="ghost" onClick={() => navigate('/app/setup/document-policies')}>
              Cancel
            </Button>
            <Button type="submit" form="policy-builder-form" loading={saving}>
              {isNew ? 'Create policy' : 'Save policy'}
            </Button>
          </div>
        }
      />

      {error ? <p className="policy-builder__banner">{error}</p> : null}

      <form id="policy-builder-form" className="policy-builder__layout" onSubmit={handleSubmit}>
        <section className="policy-builder__meta">
          <label className="policy-field">
            <span>Policy name</span>
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="e.g. Permanent employee onboarding"
              maxLength={150}
            />
            {fieldErrors.name ? <em>{fieldErrors.name}</em> : null}
          </label>
          <label className="policy-field">
            <span>Employee type</span>
            <select value={employeeTypeId} onChange={(event) => setEmployeeTypeId(event.target.value)}>
              <option value="">Select employee type</option>
              {employeeTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.name}
                </option>
              ))}
            </select>
            {fieldErrors.employee_type_id ? <em>{fieldErrors.employee_type_id}</em> : null}
          </label>
          <label className="policy-field policy-field--wide">
            <span>Description</span>
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Optional notes for HR"
              rows={2}
            />
          </label>
          <label className="policy-check">
            <input
              type="checkbox"
              checked={isDefault}
              onChange={(event) => setIsDefault(event.target.checked)}
            />
            <span>Set as default policy for this employee type</span>
          </label>
        </section>

        <div className="policy-builder__boards">
          <section className="policy-panel">
            <header className="policy-panel__header">
              <div>
                <h2>Document catalog</h2>
                <p>Drag a document into the policy, or click Add.</p>
              </div>
              <SearchBar
                value={catalogSearch}
                onValueChange={setCatalogSearch}
                placeholder="Filter documents…"
              />
            </header>

            {documents.length === 0 ? (
              <div className="policy-panel__empty">
                <p>No documents available yet.</p>
                <Link to="/app/setup/documents">Add documents first</Link>
              </div>
            ) : catalog.length === 0 ? (
              <div className="policy-panel__empty">
                <p>
                  {selectedIds.size
                    ? 'All matching documents are already in this policy.'
                    : 'No documents match your search.'}
                </p>
              </div>
            ) : (
              <div className="policy-catalog">
                {groupedCatalog.map(([category, docs]) => (
                  <div key={category} className="policy-catalog__group">
                    <h3>{category}</h3>
                    <ul>
                      {docs.map((doc) => (
                        <li
                          key={doc.id}
                          className={`policy-catalog__item ${draggingId === doc.id ? 'is-dragging' : ''}`}
                          draggable
                          onDragStart={(event) =>
                            startDrag(event, { source: 'catalog', documentId: doc.id })
                          }
                          onDragEnd={clearDragState}
                        >
                          <span className="policy-drag-handle" aria-hidden>
                            ⋮⋮
                          </span>
                          <div className="policy-catalog__copy">
                            <strong>{doc.name}</strong>
                            {doc.description ? <em>{doc.description}</em> : null}
                          </div>
                          <button
                            type="button"
                            className="policy-add-btn"
                            onClick={() => addDocument(doc)}
                          >
                            Add
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section
            className={`policy-panel policy-panel--drop ${overPolicy ? 'is-over' : ''}`}
            onDragOver={handlePolicyDragOver}
            onDragLeave={() => setOverPolicy(false)}
            onDrop={handleDropOnPolicy}
          >
            <header className="policy-panel__header">
              <div>
                <h2>Policy checklist</h2>
                <p>
                  {items.length
                    ? `${items.length} document${items.length === 1 ? '' : 's'} · drag to reorder`
                    : 'Drop documents here'}
                </p>
              </div>
            </header>

            {fieldErrors.items ? <p className="policy-builder__inline-error">{fieldErrors.items}</p> : null}

            {items.length === 0 ? (
              <div className="policy-dropzone">
                <div className="policy-dropzone__mark" aria-hidden>
                  ↓
                </div>
                <strong>Drop documents here</strong>
                <p>Build the required checklist for this employee type. You can reorder anytime.</p>
              </div>
            ) : (
              <ol className="policy-list">
                {items.map((item, index) => (
                  <li
                    key={item.document_id}
                    className={[
                      'policy-list__item',
                      draggingId === item.document_id ? 'is-dragging' : '',
                      dropTargetId === item.document_id
                        ? dropAfter
                          ? 'is-drop-after'
                          : 'is-drop-before'
                        : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                    draggable
                    onDragStart={(event) =>
                      startDrag(event, { source: 'policy', documentId: item.document_id })
                    }
                    onDragEnd={clearDragState}
                    onDragOver={(event) => handleItemDragOver(event, item.document_id)}
                    onDrop={(event) => handleDropOnItem(event, item.document_id)}
                  >
                    <div className="policy-list__top">
                      <span className="policy-list__order">{index + 1}</span>
                      <span className="policy-drag-handle" aria-hidden>
                        ⋮⋮
                      </span>
                      <div className="policy-list__copy">
                        <strong>{item.document_name}</strong>
                        <em>{item.category_name}</em>
                      </div>
                      <button
                        type="button"
                        className="policy-remove-btn"
                        onClick={() => removeItem(item.document_id)}
                        aria-label={`Remove ${item.document_name}`}
                      >
                        Remove
                      </button>
                    </div>
                    <div className="policy-list__flags">
                      <label>
                        <input
                          type="checkbox"
                          checked={item.is_required}
                          onChange={(event) =>
                            updateItem(item.document_id, { is_required: event.target.checked })
                          }
                        />
                        Required
                      </label>
                      <label>
                        <input
                          type="checkbox"
                          checked={item.verification_required}
                          onChange={(event) =>
                            updateItem(item.document_id, {
                              verification_required: event.target.checked,
                            })
                          }
                        />
                        Verify
                      </label>
                      <label>
                        <input
                          type="checkbox"
                          checked={item.allow_multiple}
                          onChange={(event) =>
                            updateItem(item.document_id, { allow_multiple: event.target.checked })
                          }
                        />
                        Multiple
                      </label>
                      <label>
                        <input
                          type="checkbox"
                          checked={item.requires_expiry}
                          onChange={(event) =>
                            updateItem(item.document_id, { requires_expiry: event.target.checked })
                          }
                        />
                        Expiry
                      </label>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>
      </form>
    </div>
  );
}
