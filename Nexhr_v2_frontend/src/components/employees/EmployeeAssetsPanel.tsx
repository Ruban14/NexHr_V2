import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import type { AssetRecord, EmployeeAssetAssignment } from '../../types';
import { Button } from '../Button';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { Modal } from '../ui/Modal';
import './EmployeeAssetsPanel.css';

type EmployeeAssetsPanelProps = {
  employeeId: string;
};

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function statusClass(status: string): string {
  if (status === 'active') return 'is-ok';
  if (status === 'lost') return 'is-bad';
  return 'is-muted';
}

export function EmployeeAssetsPanel({ employeeId }: EmployeeAssetsPanelProps) {
  const [assignments, setAssignments] = useState<EmployeeAssetAssignment[]>([]);
  const [available, setAvailable] = useState<AssetRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [assignOpen, setAssignOpen] = useState(false);
  const [assetId, setAssetId] = useState('');
  const [assignedAt, setAssignedAt] = useState(todayIso());
  const [expectedReturnAt, setExpectedReturnAt] = useState('');
  const [remarks, setRemarks] = useState('');
  const [assignLoading, setAssignLoading] = useState(false);
  const [assignError, setAssignError] = useState<string | null>(null);

  const [revokeOpen, setRevokeOpen] = useState(false);
  const [pendingRevoke, setPendingRevoke] = useState<EmployeeAssetAssignment | null>(null);
  const [returnedAt, setReturnedAt] = useState(todayIso());
  const [revokeRemarks, setRevokeRemarks] = useState('');
  const [markLost, setMarkLost] = useState(false);
  const [revokeLoading, setRevokeLoading] = useState(false);
  const [revokeError, setRevokeError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const rows = await organizationApi.listEmployeeAssetAssignments(token, employeeId);
      setAssignments(rows);
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load asset assignments.'));
      setAssignments([]);
    } finally {
      setLoading(false);
    }
  }, [employeeId]);

  useEffect(() => {
    void load();
  }, [load]);

  const active = useMemo(
    () => assignments.filter((row) => row.status === 'active'),
    [assignments],
  );
  const history = useMemo(
    () => assignments.filter((row) => row.status !== 'active'),
    [assignments],
  );

  async function openAssign() {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setAssignError(null);
    setAssetId('');
    setAssignedAt(todayIso());
    setExpectedReturnAt('');
    setRemarks('');
    try {
      const rows = await organizationApi.listAvailableAssets(token);
      setAvailable(rows);
      setAssetId(rows[0]?.id || '');
      setAssignOpen(true);
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load available assets.'));
    }
  }

  async function handleAssign(event: FormEvent) {
    event.preventDefault();
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    if (!assetId) {
      setAssignError('Select an asset to assign.');
      return;
    }
    setAssignLoading(true);
    setAssignError(null);
    try {
      await organizationApi.assignEmployeeAsset(token, employeeId, {
        asset_id: assetId,
        assigned_at: assignedAt || null,
        expected_return_at: expectedReturnAt || null,
        remarks: remarks.trim(),
      });
      setAssignOpen(false);
      await load();
    } catch (err) {
      setAssignError(extractErrorMessage(err, 'Unable to assign asset.'));
    } finally {
      setAssignLoading(false);
    }
  }

  function openRevoke(row: EmployeeAssetAssignment) {
    setPendingRevoke(row);
    setReturnedAt(todayIso());
    setRevokeRemarks('');
    setMarkLost(false);
    setRevokeError(null);
    setRevokeOpen(true);
  }

  async function confirmRevoke(event: FormEvent) {
    event.preventDefault();
    if (!pendingRevoke) return;
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setRevokeLoading(true);
    setRevokeError(null);
    try {
      await organizationApi.revokeEmployeeAsset(token, employeeId, pendingRevoke.id, {
        returned_at: returnedAt || null,
        remarks: revokeRemarks.trim(),
        mark_lost: markLost,
      });
      setRevokeOpen(false);
      setPendingRevoke(null);
      await load();
    } catch (err) {
      setRevokeError(extractErrorMessage(err, 'Unable to revoke asset.'));
    } finally {
      setRevokeLoading(false);
    }
  }

  if (loading) {
    return (
      <article className="emp-profile__card">
        <LoadingSkeleton rows={5} />
      </article>
    );
  }

  return (
    <>
      <article className="emp-profile__card emp-assets">
        <header className="emp-profile__card-head emp-profile__card-head--row">
          <div>
            <h2>Assets</h2>
            <p>Company assets currently with this employee, plus assignment history.</p>
          </div>
          <div className="emp-assets__actions">
            <Button type="button" variant="secondary" onClick={() => void openAssign()}>
              Assign asset
            </Button>
            <Link className="emp-assets__setup-link" to="/app/setup/assets">
              Manage inventory
            </Link>
          </div>
        </header>

        {error ? <p className="emp-assets__banner emp-assets__banner--error">{error}</p> : null}

        <div className="emp-assets__section-head">
          <div>
            <h3>Active assignments</h3>
            <p>Assets currently issued to this employee.</p>
          </div>
          <span className="emp-assets__count">{active.length}</span>
        </div>

        {active.length ? (
          <ul className="emp-assets__list">
            {active.map((row) => (
              <li key={row.id} className="emp-assets__item">
                <div className="emp-assets__item-main">
                  <strong>
                    {row.asset_code} · {row.asset_name}
                  </strong>
                  <span>
                    {[row.asset_type_name, row.serial_number].filter(Boolean).join(' · ') || '—'}
                  </span>
                  <div className="emp-assets__meta">
                    <span>Assigned {row.assigned_at || '—'}</span>
                    {row.expected_return_at ? (
                      <span>Expected return {row.expected_return_at}</span>
                    ) : null}
                    {row.issued_by_name ? <span>Issued by {row.issued_by_name}</span> : null}
                  </div>
                  {row.remarks ? <p className="emp-assets__remarks">{row.remarks}</p> : null}
                </div>
                <div className="emp-assets__item-side">
                  <span className={`emp-assets__status ${statusClass(row.status)}`}>Active</span>
                  <Button type="button" variant="secondary" onClick={() => openRevoke(row)}>
                    Revoke
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="emp-assets__empty">No assets assigned yet.</p>
        )}

        <div className="emp-assets__section-head emp-assets__section-head--spaced">
          <div>
            <h3>History</h3>
            <p>Returned or lost assignments.</p>
          </div>
          <span className="emp-assets__count emp-assets__count--muted">{history.length}</span>
        </div>

        {history.length ? (
          <ul className="emp-assets__list emp-assets__list--history">
            {history.map((row) => (
              <li key={row.id} className="emp-assets__item">
                <div className="emp-assets__item-main">
                  <strong>
                    {row.asset_code} · {row.asset_name}
                  </strong>
                  <div className="emp-assets__meta">
                    <span>Assigned {row.assigned_at || '—'}</span>
                    <span>Returned {row.returned_at || '—'}</span>
                    {row.received_by_name ? <span>Received by {row.received_by_name}</span> : null}
                  </div>
                </div>
                <span className={`emp-assets__status ${statusClass(row.status)}`}>
                  {row.status}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="emp-assets__empty">No past assignments.</p>
        )}
      </article>

      <Modal
        open={assignOpen}
        title="Assign asset"
        onClose={() => setAssignOpen(false)}
        footer={
          <>
            <Button type="button" variant="ghost" onClick={() => setAssignOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              form="assign-asset-form"
              loading={assignLoading}
              disabled={!available.length}
            >
              Assign
            </Button>
          </>
        }
      >
        <form id="assign-asset-form" className="emp-assets__form" onSubmit={handleAssign}>
          {assignError ? (
            <p className="emp-assets__banner emp-assets__banner--error">{assignError}</p>
          ) : null}
          {available.length ? (
            <>
              <label className="emp-assets__field">
                <span>Available asset</span>
                <select value={assetId} onChange={(event) => setAssetId(event.target.value)}>
                  {available.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.asset_code} · {item.name}
                      {item.asset_type_name ? ` (${item.asset_type_name})` : ''}
                    </option>
                  ))}
                </select>
              </label>
              <div className="emp-assets__form-grid">
                <label className="emp-assets__field">
                  <span>Assigned on</span>
                  <input
                    type="date"
                    value={assignedAt}
                    onChange={(event) => setAssignedAt(event.target.value)}
                  />
                </label>
                <label className="emp-assets__field">
                  <span>Expected return</span>
                  <input
                    type="date"
                    value={expectedReturnAt}
                    onChange={(event) => setExpectedReturnAt(event.target.value)}
                  />
                </label>
              </div>
              <label className="emp-assets__field">
                <span>Remarks</span>
                <textarea
                  value={remarks}
                  onChange={(event) => setRemarks(event.target.value)}
                  rows={3}
                  placeholder="Optional notes"
                />
              </label>
            </>
          ) : (
            <p className="emp-assets__empty">
              No available assets.{' '}
              <Link to="/app/setup/assets">Add assets in setup</Link> first.
            </p>
          )}
        </form>
      </Modal>

      <Modal
        open={revokeOpen}
        title="Revoke asset"
        onClose={() => {
          setRevokeOpen(false);
          setPendingRevoke(null);
        }}
        footer={
          <>
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setRevokeOpen(false);
                setPendingRevoke(null);
              }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              form="revoke-asset-form"
              loading={revokeLoading}
              className={markLost ? 'nex-btn--danger' : undefined}
            >
              {markLost ? 'Mark lost' : 'Revoke'}
            </Button>
          </>
        }
      >
        <form id="revoke-asset-form" className="emp-assets__revoke" onSubmit={confirmRevoke}>
          {revokeError ? (
            <p className="emp-assets__banner emp-assets__banner--error">{revokeError}</p>
          ) : null}
          <p className="emp-assets__empty" style={{ paddingTop: 0 }}>
            {pendingRevoke
              ? `Return “${pendingRevoke.asset_code} · ${pendingRevoke.asset_name}” from this employee.`
              : ''}
          </p>
          <label className="emp-assets__field">
            <span>Returned on</span>
            <input
              type="date"
              value={returnedAt}
              onChange={(event) => setReturnedAt(event.target.value)}
            />
          </label>
          <label className="emp-assets__field">
            <span>Remarks</span>
            <textarea
              value={revokeRemarks}
              onChange={(event) => setRevokeRemarks(event.target.value)}
              rows={2}
            />
          </label>
          <label className="emp-assets__check">
            <input
              type="checkbox"
              checked={markLost}
              onChange={(event) => setMarkLost(event.target.checked)}
            />
            <span>Mark asset as lost</span>
          </label>
        </form>
      </Modal>
    </>
  );
}
