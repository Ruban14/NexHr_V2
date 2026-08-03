import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage, extractFieldErrors } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import type { EmployeeType, LeavePolicyRule, LeaveType } from '../../types';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import { Button } from '../Button';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { PageHeader } from '../ui/PageHeader';
import './LeavePolicyBuilder.css';

type DraftRule = LeavePolicyRule;
type CreditMode = 'upfront' | 'monthly' | 'quarterly';

const CREDIT_MODES: {
  value: CreditMode;
  title: string;
  hint: string;
  frequency: string;
}[] = [
  {
    value: 'upfront',
    title: 'Upfront',
    hint: 'Full annual leave on joining / year start',
    frequency: 'yearly',
  },
  {
    value: 'monthly',
    title: 'Earn monthly',
    hint: 'Credit a little each month',
    frequency: 'monthly',
  },
  {
    value: 'quarterly',
    title: 'Earn quarterly',
    hint: 'Credit every quarter',
    frequency: 'quarterly',
  },
];

function modeFromFrequency(frequency: string): CreditMode {
  if (frequency === 'monthly') return 'monthly';
  if (frequency === 'quarterly') return 'quarterly';
  return 'upfront';
}

function ruleSummary(rule: DraftRule): string {
  const qty = Number(rule.allocation_quantity) || 0;
  const annual = Number(rule.annual_limit) || 0;
  const mode = modeFromFrequency(String(rule.allocation_frequency));
  if (mode === 'upfront') {
    return `Gets ${qty || annual || 0} days at once · annual cap ${annual || qty || 0}`;
  }
  if (mode === 'monthly') {
    return `Earns ${qty} day${qty === 1 ? '' : 's'} each month · annual cap ${annual || '—'}`;
  }
  return `Earns ${qty} day${qty === 1 ? '' : 's'} each quarter · annual cap ${annual || '—'}`;
}

function emptyRule(leaveType: LeaveType): DraftRule {
  return {
    leave_type_id: leaveType.id,
    leave_type_name: leaveType.name,
    allocation_frequency: 'yearly',
    allocation_quantity: '12',
    annual_limit: '12',
    carry_forward_allowed: false,
    carry_forward_limit: '0',
    encashment_allowed: false,
    encashment_limit: '0',
    allow_half_day: true,
    allow_negative_balance: false,
    minimum_service_days: 0,
    maximum_consecutive_days: null,
    is_active: true,
  };
}

export function LeavePolicyBuilder() {
  const { policyId } = useParams<{ policyId: string }>();
  const isNew = !policyId || policyId === 'new';
  const navigate = useNavigate();
  const { currentBranch } = useWorkspace();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const [employeeTypes, setEmployeeTypes] = useState<EmployeeType[]>([]);
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);

  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [employeeTypeId, setEmployeeTypeId] = useState('');
  const [effectiveFrom, setEffectiveFrom] = useState(new Date().toISOString().slice(0, 10));
  const [effectiveTo, setEffectiveTo] = useState('');
  const [isDefault, setIsDefault] = useState(false);
  const [rules, setRules] = useState<DraftRule[]>([]);
  const [expandedAdvanced, setExpandedAdvanced] = useState<Record<string, boolean>>({});

  const selectedIds = useMemo(() => new Set(rules.map((rule) => rule.leave_type_id)), [rules]);

  const availableLeaveTypes = useMemo(
    () => leaveTypes.filter((item) => item.is_active && !selectedIds.has(item.id)),
    [leaveTypes, selectedIds],
  );

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [types, leaves] = await Promise.all([
        organizationApi.listEmployeeTypes(token, { page_size: 100, is_active: true }),
        organizationApi.listLeaveTypes(token, { page_size: 100, is_active: true }),
      ]);
      setEmployeeTypes(types.items);
      setLeaveTypes(leaves.items);

      if (!isNew && policyId) {
        const policy = await organizationApi.getLeavePolicy(token, policyId);
        setCode(policy.code);
        setName(policy.name);
        setDescription(policy.description || '');
        setEmployeeTypeId(policy.employee_type_id);
        setEffectiveFrom(policy.effective_from || '');
        setEffectiveTo(policy.effective_to || '');
        setIsDefault(Boolean(policy.is_default));
        setRules(
          policy.rules.map((rule) => ({
            ...rule,
            allocation_quantity: String(rule.allocation_quantity ?? '0'),
            annual_limit: String(rule.annual_limit ?? '0'),
            carry_forward_limit: String(rule.carry_forward_limit ?? '0'),
            encashment_limit: String(rule.encashment_limit ?? '0'),
          })),
        );
      } else {
        setEmployeeTypeId(types.items[0]?.id || '');
      }
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load leave policy builder.'));
    } finally {
      setLoading(false);
    }
  }, [isNew, policyId]);

  useEffect(() => {
    void load();
  }, [load, currentBranch?.branch_id]);

  function addRule(leaveType: LeaveType) {
    if (selectedIds.has(leaveType.id)) return;
    setRules((prev) => [...prev, emptyRule(leaveType)]);
  }

  function updateRule(leaveTypeId: string, patch: Partial<DraftRule>) {
    setRules((prev) =>
      prev.map((rule) => (rule.leave_type_id === leaveTypeId ? { ...rule, ...patch } : rule)),
    );
  }

  function setCreditMode(leaveTypeId: string, mode: CreditMode) {
    const meta = CREDIT_MODES.find((item) => item.value === mode);
    if (!meta) return;
    setRules((prev) =>
      prev.map((rule) => {
        if (rule.leave_type_id !== leaveTypeId) return rule;
        if (mode === 'upfront') {
          const annual = rule.annual_limit || rule.allocation_quantity || '12';
          return {
            ...rule,
            allocation_frequency: meta.frequency,
            allocation_quantity: annual,
            annual_limit: annual,
          };
        }
        const monthlyQty = mode === 'monthly' ? '1' : '3';
        const annual = rule.annual_limit && Number(rule.annual_limit) > 0 ? rule.annual_limit : '12';
        return {
          ...rule,
          allocation_frequency: meta.frequency,
          allocation_quantity: monthlyQty,
          annual_limit: annual,
        };
      }),
    );
  }

  function removeRule(leaveTypeId: string) {
    setRules((prev) => prev.filter((rule) => rule.leave_type_id !== leaveTypeId));
    setExpandedAdvanced((prev) => {
      const next = { ...prev };
      delete next[leaveTypeId];
      return next;
    });
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const token = tokenStorage.getAccessToken();
    if (!token) return;

    const nextErrors: Record<string, string> = {};
    if (!code.trim()) nextErrors.code = 'Code is required.';
    if (!name.trim()) nextErrors.name = 'Name is required.';
    if (!employeeTypeId) nextErrors.employee_type_id = 'Employee type is required.';
    if (!effectiveFrom) nextErrors.effective_from = 'Effective from is required.';
    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    const payload = {
      code: code.trim().toUpperCase(),
      name: name.trim(),
      employee_type_id: employeeTypeId,
      description: description.trim(),
      effective_from: effectiveFrom,
      effective_to: effectiveTo || null,
      is_default: isDefault,
      rules: rules.map((rule) => ({
        leave_type_id: rule.leave_type_id,
        allocation_frequency: rule.allocation_frequency,
        allocation_quantity: rule.allocation_quantity || 0,
        annual_limit: rule.annual_limit || 0,
        carry_forward_allowed: rule.carry_forward_allowed,
        carry_forward_limit: rule.carry_forward_limit || 0,
        encashment_allowed: rule.encashment_allowed,
        encashment_limit: rule.encashment_limit || 0,
        allow_half_day: rule.allow_half_day,
        allow_negative_balance: rule.allow_negative_balance,
        minimum_service_days: Number(rule.minimum_service_days) || 0,
        maximum_consecutive_days: rule.maximum_consecutive_days,
        is_active: rule.is_active,
      })),
    };

    setSaving(true);
    setError(null);
    try {
      if (isNew) {
        const created = await organizationApi.createLeavePolicy(token, payload);
        navigate(`/app/setup/leave-policies/${created.id}`, { replace: true });
      } else if (policyId) {
        await organizationApi.updateLeavePolicy(token, policyId, payload);
        await load();
      }
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to save leave policy.'));
      setFieldErrors(extractFieldErrors(err));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="leave-policy-builder">
        <LoadingSkeleton rows={8} />
      </div>
    );
  }

  return (
    <div className="leave-policy-builder">
      <PageHeader
        title={isNew ? 'New leave policy' : 'Edit leave policy'}
        description="Choose who this covers, then set how each leave type is credited."
        breadcrumb={
          <Link className="leave-policy-builder__back" to="/app/setup/leave-policies">
            ← Leave policies
          </Link>
        }
        actions={
          <div className="leave-policy-builder__actions">
            <Button type="button" variant="secondary" onClick={() => navigate('/app/setup/leave-policies')}>
              Cancel
            </Button>
            <Button type="submit" form="leave-policy-form" loading={saving}>
              {isNew ? 'Create policy' : 'Save changes'}
            </Button>
          </div>
        }
      />

      {error ? <p className="leave-policy-builder__banner">{error}</p> : null}

      <form id="leave-policy-form" className="leave-policy-builder__layout" onSubmit={handleSubmit}>
        <section className="leave-policy-builder__meta">
          <div className="leave-policy-builder__meta-head">
            <h3>Policy basics</h3>
            <p>Identity and who this policy applies to.</p>
          </div>

          <label className="leave-policy-field">
            <span>Code</span>
            <input
              value={code}
              onChange={(event) => setCode(event.target.value)}
              placeholder="PERM-STD"
              maxLength={30}
            />
            {fieldErrors.code ? <em>{fieldErrors.code}</em> : null}
          </label>
          <label className="leave-policy-field">
            <span>Employee type</span>
            <select
              value={employeeTypeId}
              onChange={(event) => setEmployeeTypeId(event.target.value)}
            >
              <option value="">Select employee type</option>
              {employeeTypes.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            {fieldErrors.employee_type_id ? <em>{fieldErrors.employee_type_id}</em> : null}
          </label>
          <label className="leave-policy-field leave-policy-field--wide">
            <span>Name</span>
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Permanent standard leave"
              maxLength={150}
            />
            {fieldErrors.name ? <em>{fieldErrors.name}</em> : null}
          </label>
          <label className="leave-policy-field">
            <span>Effective from</span>
            <input
              type="date"
              value={effectiveFrom}
              onChange={(event) => setEffectiveFrom(event.target.value)}
            />
            {fieldErrors.effective_from ? <em>{fieldErrors.effective_from}</em> : null}
          </label>
          <label className="leave-policy-field">
            <span>Effective to <small>(optional)</small></span>
            <input
              type="date"
              value={effectiveTo}
              onChange={(event) => setEffectiveTo(event.target.value)}
            />
          </label>
          <label className="leave-policy-field leave-policy-field--wide">
            <span>Description <small>(optional)</small></span>
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={2}
              placeholder="Short note for HR about this policy"
            />
          </label>
          <label className="leave-policy-check leave-policy-field--wide">
            <input
              type="checkbox"
              checked={isDefault}
              onChange={(event) => setIsDefault(event.target.checked)}
            />
            <span>Use as default for this employee type</span>
          </label>
        </section>

        <section className="leave-policy-builder__rules">
          <header className="leave-policy-builder__rules-head">
            <div>
              <h3>Leave entitlements</h3>
              <p>Add leave types, then pick upfront or accrual for each.</p>
            </div>
            <span className="leave-policy-builder__count">
              {rules.length} type{rules.length === 1 ? '' : 's'}
            </span>
          </header>

          {!leaveTypes.length ? (
            <div className="leave-policy-builder__empty">
              <strong>No leave types yet</strong>
              <p>
                Create categories like Casual or Sick first, then come back here.
              </p>
              <Link to="/app/setup/leave-types">Go to leave types</Link>
            </div>
          ) : null}

          {availableLeaveTypes.length ? (
            <div className="leave-policy-builder__catalog">
              <span>Add leave type</span>
              <div className="leave-policy-builder__chips">
                {availableLeaveTypes.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className="leave-policy-chip"
                    onClick={() => addRule(item)}
                  >
                    + {item.name}
                  </button>
                ))}
              </div>
            </div>
          ) : leaveTypes.length && rules.length ? (
            <p className="leave-policy-builder__hint">All leave types are already on this policy.</p>
          ) : null}

          {rules.length ? (
            <ul className="leave-policy-rule-list">
              {rules.map((rule) => {
                const mode = modeFromFrequency(String(rule.allocation_frequency));
                const advancedOpen = Boolean(expandedAdvanced[rule.leave_type_id]);
                return (
                  <li key={rule.leave_type_id} className="leave-policy-rule">
                    <header className="leave-policy-rule__head">
                      <div>
                        <strong>{rule.leave_type_name || 'Leave type'}</strong>
                        <p>{ruleSummary(rule)}</p>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() => removeRule(rule.leave_type_id)}
                      >
                        Remove
                      </Button>
                    </header>

                    <div className="leave-policy-mode" role="group" aria-label="Credit mode">
                      {CREDIT_MODES.map((item) => (
                        <button
                          key={item.value}
                          type="button"
                          className={`leave-policy-mode__btn${mode === item.value ? ' is-active' : ''}`}
                          onClick={() => setCreditMode(rule.leave_type_id, item.value)}
                        >
                          <strong>{item.title}</strong>
                          <span>{item.hint}</span>
                        </button>
                      ))}
                    </div>

                    <div className="leave-policy-rule__essentials">
                      {mode === 'upfront' ? (
                        <label className="leave-policy-field">
                          <span>Annual leave days</span>
                          <input
                            type="number"
                            min="0"
                            step="0.5"
                            value={rule.annual_limit}
                            onChange={(event) => {
                              const value = event.target.value;
                              updateRule(rule.leave_type_id, {
                                annual_limit: value,
                                allocation_quantity: value,
                              });
                            }}
                          />
                        </label>
                      ) : (
                        <>
                          <label className="leave-policy-field">
                            <span>
                              {mode === 'monthly' ? 'Days each month' : 'Days each quarter'}
                            </span>
                            <input
                              type="number"
                              min="0"
                              step="0.5"
                              value={rule.allocation_quantity}
                              onChange={(event) =>
                                updateRule(rule.leave_type_id, {
                                  allocation_quantity: event.target.value,
                                })
                              }
                            />
                          </label>
                          <label className="leave-policy-field">
                            <span>Annual cap</span>
                            <input
                              type="number"
                              min="0"
                              step="0.5"
                              value={rule.annual_limit}
                              onChange={(event) =>
                                updateRule(rule.leave_type_id, {
                                  annual_limit: event.target.value,
                                })
                              }
                            />
                          </label>
                        </>
                      )}
                      <label className="leave-policy-field">
                        <span>Waiting period (days)</span>
                        <input
                          type="number"
                          min="0"
                          value={rule.minimum_service_days}
                          onChange={(event) =>
                            updateRule(rule.leave_type_id, {
                              minimum_service_days: Number(event.target.value) || 0,
                            })
                          }
                        />
                      </label>
                    </div>

                    <div className="leave-policy-rule__toggles">
                      <label>
                        <input
                          type="checkbox"
                          checked={rule.allow_half_day}
                          onChange={(event) =>
                            updateRule(rule.leave_type_id, {
                              allow_half_day: event.target.checked,
                            })
                          }
                        />
                        Half day
                      </label>
                      <label>
                        <input
                          type="checkbox"
                          checked={rule.carry_forward_allowed}
                          onChange={(event) =>
                            updateRule(rule.leave_type_id, {
                              carry_forward_allowed: event.target.checked,
                            })
                          }
                        />
                        Carry forward
                      </label>
                      <label>
                        <input
                          type="checkbox"
                          checked={rule.is_active}
                          onChange={(event) =>
                            updateRule(rule.leave_type_id, { is_active: event.target.checked })
                          }
                        />
                        Active
                      </label>
                    </div>

                    <button
                      type="button"
                      className="leave-policy-rule__advanced-toggle"
                      onClick={() =>
                        setExpandedAdvanced((prev) => ({
                          ...prev,
                          [rule.leave_type_id]: !prev[rule.leave_type_id],
                        }))
                      }
                    >
                      {advancedOpen ? 'Hide more options' : 'More options'}
                    </button>

                    {advancedOpen ? (
                      <div className="leave-policy-rule__advanced">
                        <label className="leave-policy-field">
                          <span>Carry forward limit</span>
                          <input
                            type="number"
                            min="0"
                            step="0.5"
                            value={rule.carry_forward_limit}
                            disabled={!rule.carry_forward_allowed}
                            onChange={(event) =>
                              updateRule(rule.leave_type_id, {
                                carry_forward_limit: event.target.value,
                              })
                            }
                          />
                        </label>
                        <label className="leave-policy-field">
                          <span>Max consecutive days</span>
                          <input
                            type="number"
                            min="1"
                            value={rule.maximum_consecutive_days ?? ''}
                            placeholder="No limit"
                            onChange={(event) =>
                              updateRule(rule.leave_type_id, {
                                maximum_consecutive_days: event.target.value
                                  ? Number(event.target.value)
                                  : null,
                              })
                            }
                          />
                        </label>
                        <label className="leave-policy-field">
                          <span>Encashment limit</span>
                          <input
                            type="number"
                            min="0"
                            step="0.5"
                            value={rule.encashment_limit}
                            disabled={!rule.encashment_allowed}
                            onChange={(event) =>
                              updateRule(rule.leave_type_id, {
                                encashment_limit: event.target.value,
                              })
                            }
                          />
                        </label>
                        <div className="leave-policy-rule__toggles leave-policy-rule__toggles--advanced">
                          <label>
                            <input
                              type="checkbox"
                              checked={rule.encashment_allowed}
                              onChange={(event) =>
                                updateRule(rule.leave_type_id, {
                                  encashment_allowed: event.target.checked,
                                })
                              }
                            />
                            Allow encashment
                          </label>
                          <label>
                            <input
                              type="checkbox"
                              checked={rule.allow_negative_balance}
                              onChange={(event) =>
                                updateRule(rule.leave_type_id, {
                                  allow_negative_balance: event.target.checked,
                                })
                              }
                            />
                            Allow negative balance
                          </label>
                        </div>
                      </div>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          ) : leaveTypes.length ? (
            <div className="leave-policy-builder__empty">
              <strong>No entitlements yet</strong>
              <p>Tap a leave type above to start configuring it.</p>
            </div>
          ) : null}
        </section>
      </form>
    </div>
  );
}
