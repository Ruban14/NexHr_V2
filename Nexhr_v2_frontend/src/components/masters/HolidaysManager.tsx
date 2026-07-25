import { useCallback, useEffect, useMemo, useState } from 'react';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage, extractFieldErrors } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import type { Holiday, HolidayCalendar } from '../../types';
import { useWorkspace } from '../../workspace/WorkspaceContext';
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
import './DesignationTree.css';
import './MasterManager.css';

const currentYear = new Date().getFullYear();

function formatHolidayDate(value: string): string {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function HolidaysManager() {
  const { currentBranch } = useWorkspace();
  const [calendars, setCalendars] = useState<HolidayCalendar[]>([]);
  const [calendarId, setCalendarId] = useState('');
  const [holidays, setHolidays] = useState<Holiday[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [calendarFormOpen, setCalendarFormOpen] = useState(false);
  const [editingCalendar, setEditingCalendar] = useState<HolidayCalendar | null>(null);
  const [holidayFormOpen, setHolidayFormOpen] = useState(false);
  const [editingHoliday, setEditingHoliday] = useState<Holiday | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<
    { type: 'calendar'; item: HolidayCalendar } | { type: 'holiday'; item: Holiday } | null
  >(null);
  const [confirmLoading, setConfirmLoading] = useState(false);

  const selectedCalendar = calendars.find((item) => item.id === calendarId) || null;

  const loadCalendars = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    const data = await organizationApi.listHolidayCalendars(token, { page_size: 100 });
    setCalendars(data.items);
    setCalendarId((prev) => prev || data.items[0]?.id || '');
  }, []);

  const loadHolidays = useCallback(async (id: string) => {
    const token = tokenStorage.getAccessToken();
    if (!token || !id) {
      setHolidays([]);
      return;
    }
    const data = await organizationApi.listHolidays(token, id, search.trim());
    setHolidays(data);
  }, [search]);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await loadCalendars();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load holiday calendars.'));
      setCalendars([]);
    } finally {
      setLoading(false);
    }
  }, [loadCalendars]);

  useEffect(() => {
    void reload();
  }, [reload, currentBranch?.branch_id]);

  useEffect(() => {
    if (!calendarId) {
      setHolidays([]);
      return;
    }
    void loadHolidays(calendarId).catch((err) => {
      setError(extractErrorMessage(err, 'Unable to load holidays.'));
      setHolidays([]);
    });
  }, [calendarId, loadHolidays]);

  function openCreateCalendar() {
    setEditingCalendar(null);
    setFormError(null);
    setFieldErrors({});
    setCalendarFormOpen(true);
  }

  function openEditCalendar() {
    if (!selectedCalendar) return;
    setEditingCalendar(selectedCalendar);
    setFormError(null);
    setFieldErrors({});
    setCalendarFormOpen(true);
  }

  function openCreateHoliday() {
    setEditingHoliday(null);
    setFormError(null);
    setFieldErrors({});
    setHolidayFormOpen(true);
  }

  function openEditHoliday(row: Holiday) {
    setEditingHoliday(row);
    setFormError(null);
    setFieldErrors({});
    setHolidayFormOpen(true);
  }

  async function handleCalendarSubmit(values: Record<string, string>) {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setFormLoading(true);
    setFormError(null);
    setFieldErrors({});
    try {
      const year = Number(values.year);
      if (editingCalendar) {
        const updated = await organizationApi.updateHolidayCalendar(token, editingCalendar.id, {
          name: values.name,
          year,
        });
        setCalendars((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      } else {
        const created = await organizationApi.createHolidayCalendar(token, {
          name: values.name,
          year,
        });
        setCalendars((prev) => [created, ...prev]);
        setCalendarId(created.id);
      }
      setCalendarFormOpen(false);
    } catch (err) {
      setFormError(extractErrorMessage(err, 'Unable to save calendar.'));
      setFieldErrors(extractFieldErrors(err));
    } finally {
      setFormLoading(false);
    }
  }

  async function handleHolidaySubmit(values: Record<string, string>) {
    const token = tokenStorage.getAccessToken();
    if (!token || !calendarId) return;
    setFormLoading(true);
    setFormError(null);
    setFieldErrors({});
    try {
      if (editingHoliday) {
        await organizationApi.updateHoliday(token, editingHoliday.id, {
          name: values.name,
          date: values.date,
        });
      } else {
        await organizationApi.createHoliday(token, calendarId, {
          name: values.name,
          date: values.date,
        });
      }
      setHolidayFormOpen(false);
      await loadHolidays(calendarId);
    } catch (err) {
      setFormError(extractErrorMessage(err, 'Unable to save holiday.'));
      setFieldErrors(extractFieldErrors(err));
    } finally {
      setFormLoading(false);
    }
  }

  async function toggleCalendarActive() {
    if (!selectedCalendar) return;
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    try {
      const updated = await organizationApi.updateHolidayCalendar(token, selectedCalendar.id, {
        is_active: !selectedCalendar.is_active,
      });
      setCalendars((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to update calendar status.'));
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setConfirmLoading(true);
    try {
      if (pendingDelete.type === 'calendar') {
        await organizationApi.deleteHolidayCalendar(token, pendingDelete.item.id);
        setCalendars((prev) => {
          const next = prev.filter((item) => item.id !== pendingDelete.item.id);
          setCalendarId((current) =>
            current === pendingDelete.item.id ? next[0]?.id || '' : current,
          );
          return next;
        });
      } else {
        await organizationApi.deleteHoliday(token, pendingDelete.item.id);
        await loadHolidays(calendarId);
      }
      setConfirmOpen(false);
      setPendingDelete(null);
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to delete.'));
      setConfirmOpen(false);
    } finally {
      setConfirmLoading(false);
    }
  }

  const columns = useMemo<DataTableColumn<Holiday>[]>(
    () => [
      {
        key: 'name',
        header: 'Holiday',
        render: (row) => <strong>{row.name}</strong>,
      },
      {
        key: 'date',
        header: 'Date',
        width: '220px',
        render: (row) => formatHolidayDate(row.date),
      },
      {
        key: 'actions',
        header: 'Actions',
        width: '140px',
        render: (row) => (
          <div className="table-actions" onClick={(event) => event.stopPropagation()}>
            <IconAction label={`Edit ${row.name}`} onClick={() => openEditHoliday(row)}>
              <IconEdit />
            </IconAction>
            <IconAction
              label={`Delete ${row.name}`}
              danger
              onClick={() => {
                setPendingDelete({ type: 'holiday', item: row });
                setConfirmOpen(true);
              }}
            >
              <IconDelete />
            </IconAction>
          </div>
        ),
      },
    ],
    [],
  );

  return (
    <section className="master-manager">
      <PageHeader
        title="Holidays"
        description="Create yearly holiday calendars, then add holiday dates under each calendar."
        actions={
          <>
            <Button variant="secondary" onClick={openCreateCalendar}>
              Add calendar
            </Button>
            <Button onClick={openCreateHoliday} disabled={!calendarId}>
              Add holiday
            </Button>
          </>
        }
      />

      <Toolbar
        left={
          <>
            <label className="dept-select">
              <span>Calendar</span>
              <select
                value={calendarId}
                onChange={(event) => setCalendarId(event.target.value)}
                aria-label="Select holiday calendar"
              >
                {!calendars.length ? <option value="">No calendars</option> : null}
                {calendars.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} ({item.year})
                  </option>
                ))}
              </select>
            </label>
            <SearchBar
              value={search}
              placeholder="Search holidays…"
              onValueChange={setSearch}
              aria-label="Search holidays"
            />
          </>
        }
        right={
          selectedCalendar ? (
            <div className="table-actions">
              <StatusBadge active={selectedCalendar.is_active} />
              <IconAction label="Edit calendar" onClick={openEditCalendar}>
                <IconEdit />
              </IconAction>
              <IconAction
                label={selectedCalendar.is_active ? 'Deactivate calendar' : 'Activate calendar'}
                className={selectedCalendar.is_active ? 'icon-action--warning' : 'icon-action--success'}
                onClick={() => void toggleCalendarActive()}
              >
                {selectedCalendar.is_active ? <IconDeactivate /> : <IconActivate />}
              </IconAction>
              <IconAction
                label="Delete calendar"
                danger
                onClick={() => {
                  setPendingDelete({ type: 'calendar', item: selectedCalendar });
                  setConfirmOpen(true);
                }}
              >
                <IconDelete />
              </IconAction>
            </div>
          ) : null
        }
      />

      {error ? <div className="auth-alert auth-alert--error">{error}</div> : null}

      {!calendars.length && !loading ? (
        <EmptyState
          title="No holiday calendars yet"
          description="Create a calendar for a year, then add holidays like New Year and Diwali."
          action={<Button onClick={openCreateCalendar}>Add calendar</Button>}
        />
      ) : loading ? (
        <LoadingSkeleton />
      ) : (
        <DataTable
          columns={columns}
          rows={holidays}
          empty={
            <EmptyState
              title="No holidays in this calendar"
              description="Add holiday dates for the selected year."
              action={
                <Button onClick={openCreateHoliday} disabled={!calendarId}>
                  Add holiday
                </Button>
              }
            />
          }
        />
      )}

      <FormModal
        open={calendarFormOpen}
        title={editingCalendar ? 'Edit holiday calendar' : 'Add holiday calendar'}
        fields={[
          { name: 'name', label: 'Name', required: true, maxLength: 150 },
          {
            name: 'year',
            label: 'Year',
            type: 'number',
            required: true,
            min: 2000,
            max: 2100,
          },
        ]}
        initialValues={
          editingCalendar
            ? { name: editingCalendar.name, year: String(editingCalendar.year) }
            : { name: '', year: String(currentYear) }
        }
        submitLabel={editingCalendar ? 'Save changes' : 'Create'}
        loading={formLoading}
        error={formError}
        fieldErrors={fieldErrors}
        onSubmit={handleCalendarSubmit}
        onClose={() => setCalendarFormOpen(false)}
      />

      <FormModal
        open={holidayFormOpen}
        title={editingHoliday ? 'Edit holiday' : 'Add holiday'}
        fields={[
          { name: 'name', label: 'Name', required: true, maxLength: 150 },
          { name: 'date', label: 'Date', type: 'date', required: true },
        ]}
        initialValues={
          editingHoliday
            ? { name: editingHoliday.name, date: editingHoliday.date }
            : { name: '', date: '' }
        }
        submitLabel={editingHoliday ? 'Save changes' : 'Create'}
        loading={formLoading}
        error={formError}
        fieldErrors={fieldErrors}
        onSubmit={handleHolidaySubmit}
        onClose={() => setHolidayFormOpen(false)}
      />

      <ConfirmDialog
        open={confirmOpen}
        title={
          pendingDelete?.type === 'calendar' ? 'Delete holiday calendar?' : 'Delete holiday?'
        }
        message={
          pendingDelete?.type === 'calendar'
            ? `“${pendingDelete.item.name} (${pendingDelete.item.year})” and all its holidays will be removed.`
            : `“${pendingDelete?.item.name ?? ''}” will be permanently removed.`
        }
        confirmLabel="Delete"
        danger
        loading={confirmLoading}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={() => void confirmDelete()}
      />
    </section>
  );
}
