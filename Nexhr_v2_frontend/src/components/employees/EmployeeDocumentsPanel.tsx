import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import type {
  DocumentCompliance,
  DocumentComplianceItem,
  DocumentDefinition,
  EmployeeDocumentRecord,
} from '../../types';
import { Button } from '../Button';
import { ConfirmDialog } from '../ui/ConfirmDialog';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { Modal } from '../ui/Modal';
import './EmployeeDocumentsPanel.css';

type EmployeeDocumentsPanelProps = {
  employeeId: string;
  employeeTypeName?: string | null;
};

const STATUS_LABELS: Record<string, string> = {
  compliant: 'Compliant',
  incomplete: 'Incomplete',
  pending_review: 'Pending review',
  no_policy: 'No policy',
  missing: 'Missing',
  optional_missing: 'Optional',
  pending: 'Pending approval',
  approved: 'Approved',
  expired: 'Expired',
  rejected: 'Rejected',
};

function formatBytes(size: number): string {
  if (!size) return '—';
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function statusClass(status: string): string {
  if (status === 'approved' || status === 'compliant') return 'is-ok';
  if (status === 'pending' || status === 'pending_review' || status === 'optional_missing') {
    return 'is-warn';
  }
  if (status === 'no_policy') return 'is-muted';
  return 'is-bad';
}

export function EmployeeDocumentsPanel({
  employeeId,
  employeeTypeName,
}: EmployeeDocumentsPanelProps) {
  const [compliance, setCompliance] = useState<DocumentCompliance | null>(null);
  const [definitions, setDefinitions] = useState<DocumentDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadTarget, setUploadTarget] = useState<DocumentComplianceItem | null>(null);
  const [documentId, setDocumentId] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [issueDate, setIssueDate] = useState('');
  const [expiryDate, setExpiryDate] = useState('');
  const [remarks, setRemarks] = useState('');
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<EmployeeDocumentRecord | null>(null);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [complianceData, docs] = await Promise.all([
        organizationApi.checkEmployeeDocumentCompliance(token, employeeId),
        organizationApi.listDocumentDefinitions(token, { page_size: 100, is_active: true }),
      ]);
      setCompliance(complianceData);
      setDefinitions(docs.items);
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load employee documents.'));
      setCompliance(null);
    } finally {
      setLoading(false);
    }
  }, [employeeId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runCheck() {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setChecking(true);
    setError(null);
    try {
      const data = await organizationApi.checkEmployeeDocumentCompliance(token, employeeId);
      setCompliance(data);
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to check policy status.'));
    } finally {
      setChecking(false);
    }
  }

  function openUpload(item?: DocumentComplianceItem) {
    setUploadTarget(item || null);
    setDocumentId(item?.document_id || definitions[0]?.id || '');
    setFile(null);
    setIssueDate('');
    setExpiryDate('');
    setRemarks('');
    setUploadError(null);
    setUploadOpen(true);
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault();
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    if (!documentId) {
      setUploadError('Select a document type.');
      return;
    }
    if (!file) {
      setUploadError('Choose a file to upload.');
      return;
    }

    const form = new FormData();
    form.append('document_id', documentId);
    form.append('file', file);
    if (issueDate) form.append('issue_date', issueDate);
    if (expiryDate) form.append('expiry_date', expiryDate);
    if (remarks.trim()) form.append('remarks', remarks.trim());

    setUploadLoading(true);
    setUploadError(null);
    try {
      await organizationApi.uploadEmployeeDocument(token, employeeId, form);
      setUploadOpen(false);
      await load();
    } catch (err) {
      setUploadError(extractErrorMessage(err, 'Unable to upload document.'));
    } finally {
      setUploadLoading(false);
    }
  }

  async function review(row: EmployeeDocumentRecord, approve: boolean) {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setActionLoadingId(row.id);
    try {
      await organizationApi.reviewEmployeeDocument(token, employeeId, row.id, {
        approve,
        remarks: approve ? undefined : 'Rejected by admin',
      });
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to review document.'));
    } finally {
      setActionLoadingId(null);
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setConfirmLoading(true);
    try {
      await organizationApi.deleteEmployeeDocument(token, employeeId, pendingDelete.id);
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

  const items = compliance?.items || [];
  const uploads = compliance?.uploads || [];
  const pendingUploads = useMemo(
    () => compliance?.pending || uploads.filter((row) => row.status === 'pending'),
    [compliance?.pending, uploads],
  );
  const overall = compliance?.overall_status || 'no_policy';

  const definitionOptions = useMemo(() => {
    if (uploadTarget) {
      return definitions.filter((item) => item.id === uploadTarget.document_id);
    }
    return definitions;
  }, [definitions, uploadTarget]);

  if (loading) {
    return (
      <article className="emp-profile__card">
        <header className="emp-profile__card-head">
          <div>
            <h2>Documents</h2>
            <p>Loading policy checklist…</p>
          </div>
        </header>
        <LoadingSkeleton rows={5} />
      </article>
    );
  }

  return (
    <>
      <article className="emp-profile__card emp-docs">
        <header className="emp-profile__card-head emp-profile__card-head--row">
          <div>
            <h2>Documents</h2>
            <p>
              {compliance?.policy
                ? `Policy: ${compliance.policy.name}${
                    employeeTypeName ? ` · ${employeeTypeName}` : ''
                  }`
                : 'Check required documents against the active policy for this employee type.'}
            </p>
          </div>
          <div className="emp-docs__actions">
            <Button type="button" variant="secondary" loading={checking} onClick={() => void runCheck()}>
              Check policy
            </Button>
            <Button type="button" onClick={() => openUpload()}>
              Upload document
            </Button>
          </div>
        </header>

        {error ? <p className="emp-docs__banner emp-docs__banner--error">{error}</p> : null}

        <div className={`emp-docs__status ${statusClass(overall)}`}>
          <div>
            <strong>{STATUS_LABELS[overall] || overall}</strong>
            <p>{compliance?.message || 'Run a policy check to see status.'}</p>
          </div>
          {compliance?.summary ? (
            <ul className="emp-docs__summary">
              <li>
                <em>{compliance.summary.required}</em>
                <span>Required</span>
              </li>
              <li>
                <em>{compliance.summary.approved}</em>
                <span>Approved</span>
              </li>
              <li>
                <em>{pendingUploads.length || compliance.summary.pending}</em>
                <span>Pending</span>
              </li>
              <li>
                <em>{compliance.summary.missing}</em>
                <span>Missing</span>
              </li>
            </ul>
          ) : null}
        </div>

        <section className="emp-docs__pending" aria-label="Pending approvals">
          <header className="emp-docs__section-head">
            <div>
              <h3>Pending approval</h3>
              <p>Employee uploads waiting for review.</p>
            </div>
            <span className="emp-docs__count">{pendingUploads.length}</span>
          </header>

          {pendingUploads.length === 0 ? (
            <div className="emp-docs__pending-empty">
              <strong>No pending documents</strong>
              <p>New employee uploads will appear here until approved or rejected.</p>
            </div>
          ) : (
            <ul className="emp-docs__pending-list">
              {pendingUploads.map((row) => (
                <li key={row.id} className="emp-docs__pending-item">
                  <div className="emp-docs__pending-copy">
                    <strong>{row.document_name || 'Document'}</strong>
                    <p>
                      <a href={row.file_url} target="_blank" rel="noreferrer">
                        {row.file_name || 'View file'}
                      </a>
                      {' · '}
                      {formatBytes(row.file_size)}
                      {' · '}
                      {new Date(row.created_at).toLocaleString()}
                    </p>
                    {row.remarks ? <span className="emp-docs__remarks">{row.remarks}</span> : null}
                    {row.category_name ? (
                      <span className="emp-docs__category">{row.category_name}</span>
                    ) : null}
                  </div>
                  <div className="emp-docs__pending-actions">
                    <span className={`emp-docs__pill ${statusClass(row.status)}`}>
                      {STATUS_LABELS[row.status] || row.status}
                    </span>
                    <Button
                      type="button"
                      loading={actionLoadingId === row.id}
                      onClick={() => void review(row, true)}
                    >
                      Approve
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      loading={actionLoadingId === row.id}
                      onClick={() => void review(row, false)}
                    >
                      Reject
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        {!compliance?.policy ? (
          <div className="employees__empty-block">
            <strong>No policy linked</strong>
            <p>
              {employeeTypeName
                ? `Create a document policy for “${employeeTypeName}” in organization setup.`
                : 'Assign an employee type, then create a document policy.'}
            </p>
            <Link to="/app/setup/document-policies" className="emp-docs__link">
              Open document policies
            </Link>
          </div>
        ) : items.length === 0 ? (
          <div className="employees__empty-block">
            <strong>Policy has no documents</strong>
            <p>Add documents to this policy checklist in organization setup.</p>
          </div>
        ) : (
          <>
            <header className="emp-docs__section-head emp-docs__section-head--spaced">
              <div>
                <h3>Policy checklist</h3>
                <p>Required and optional documents for this employee type.</p>
              </div>
            </header>
            <ul className="emp-docs__checklist">
              {items.map((item) => (
                <li key={item.policy_item_id} className="emp-docs__check-item">
                  <div className="emp-docs__check-top">
                    <div>
                      <strong>{item.document_name}</strong>
                      <p>
                        {item.category_name || 'Document'}
                        {item.is_required ? ' · Required' : ' · Optional'}
                        {item.requires_expiry ? ' · Needs expiry' : ''}
                      </p>
                    </div>
                    <span className={`emp-docs__pill ${statusClass(item.status)}`}>
                      {STATUS_LABELS[item.status] || item.status}
                    </span>
                  </div>
                  {item.latest_document ? (
                    <div className="emp-docs__latest">
                      <a href={item.latest_document.file_url} target="_blank" rel="noreferrer">
                        {item.latest_document.file_name || 'View file'}
                      </a>
                      <span>{formatBytes(item.latest_document.file_size)}</span>
                      {item.latest_document.remarks ? (
                        <span className="emp-docs__remarks">{item.latest_document.remarks}</span>
                      ) : null}
                    </div>
                  ) : (
                    <p className="emp-docs__missing-copy">No file uploaded yet.</p>
                  )}
                  <div className="emp-docs__row-actions">
                    <Button type="button" variant="secondary" onClick={() => openUpload(item)}>
                      {item.latest_document ? 'Upload new' : 'Upload'}
                    </Button>
                    {item.latest_document?.status === 'pending' ? (
                      <>
                        <Button
                          type="button"
                          loading={actionLoadingId === item.latest_document.id}
                          onClick={() => void review(item.latest_document!, true)}
                        >
                          Approve
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          loading={actionLoadingId === item.latest_document.id}
                          onClick={() => void review(item.latest_document!, false)}
                        >
                          Reject
                        </Button>
                      </>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}
      </article>

      {uploads.length ? (
        <article className="emp-profile__card emp-docs">
          <header className="emp-profile__card-head">
            <div>
              <h2>Upload history</h2>
              <p>All files uploaded for this employee.</p>
            </div>
          </header>
          <ul className="emp-docs__history">
            {uploads.map((row) => (
              <li key={row.id}>
                <div>
                  <strong>{row.document_name || 'Document'}</strong>
                  <p>
                    <a href={row.file_url} target="_blank" rel="noreferrer">
                      {row.file_name || 'File'}
                    </a>
                    {' · '}
                    {formatBytes(row.file_size)}
                    {row.remarks ? ` · ${row.remarks}` : ''}
                  </p>
                </div>
                <div className="emp-docs__history-meta">
                  <span className={`emp-docs__pill ${statusClass(row.status)}`}>
                    {STATUS_LABELS[row.status] || row.status}
                  </span>
                  <button
                    type="button"
                    className="emp-docs__text-btn"
                    onClick={() => {
                      setPendingDelete(row);
                      setConfirmOpen(true);
                    }}
                  >
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </article>
      ) : null}

      <Modal
        open={uploadOpen}
        title={uploadTarget ? `Upload ${uploadTarget.document_name}` : 'Upload document'}
        onClose={() => setUploadOpen(false)}
        footer={
          <>
            <Button type="button" variant="ghost" onClick={() => setUploadOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" form="emp-doc-upload" loading={uploadLoading}>
              Upload
            </Button>
          </>
        }
      >
        <form id="emp-doc-upload" className="emp-docs__form" onSubmit={handleUpload}>
          <p className="emp-docs__hint">
            Admin uploads are auto-approved with remark “Uploaded by admin”. Employee uploads stay
            pending until approved.
          </p>
          {uploadError ? <p className="emp-docs__banner emp-docs__banner--error">{uploadError}</p> : null}
          <label className="emp-docs__field">
            <span>Document type</span>
            <select
              value={documentId}
              disabled={Boolean(uploadTarget)}
              onChange={(event) => setDocumentId(event.target.value)}
            >
              <option value="">Select document</option>
              {definitionOptions.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.category_name ? `${item.category_name} · ` : ''}
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label className="emp-docs__field">
            <span>File</span>
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.webp,.doc,.docx,.xls,.xlsx"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>
          <div className="emp-docs__grid">
            <label className="emp-docs__field">
              <span>Issue date</span>
              <input type="date" value={issueDate} onChange={(event) => setIssueDate(event.target.value)} />
            </label>
            <label className="emp-docs__field">
              <span>Expiry date</span>
              <input
                type="date"
                value={expiryDate}
                onChange={(event) => setExpiryDate(event.target.value)}
              />
            </label>
          </div>
          <label className="emp-docs__field">
            <span>Remarks</span>
            <textarea
              value={remarks}
              onChange={(event) => setRemarks(event.target.value)}
              placeholder="Leave blank to use “Uploaded by admin”"
              rows={2}
            />
          </label>
        </form>
      </Modal>

      <ConfirmDialog
        open={confirmOpen}
        title="Delete document?"
        message={
          pendingDelete
            ? `“${pendingDelete.file_name || pendingDelete.document_name || 'Document'}” will be removed.`
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
    </>
  );
}
