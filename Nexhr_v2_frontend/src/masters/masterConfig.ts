import { organizationApi } from '../api/auth';
import type { FormFieldConfig } from '../components/ui/FormModal';
import type { MasterListParams, MasterRecord, PaginatedResponse } from '../types';

export type MasterKey =
  | 'departments'
  | 'employee-types'
  | 'access-types'
  | 'shifts'
  | 'work-weeks'
  | 'leave-types';

export type MasterConfig = {
  key: MasterKey;
  title: string;
  singular: string;
  description: string;
  fields: FormFieldConfig[];
  list: (token: string, params: MasterListParams) => Promise<PaginatedResponse<MasterRecord>>;
  create: (token: string, values: Record<string, string>) => Promise<MasterRecord>;
  update: (token: string, id: string, values: Record<string, string | boolean>) => Promise<MasterRecord>;
  remove: (token: string, id: string) => Promise<void>;
  getSubtitle?: (row: MasterRecord) => string | null;
  getInitialValues?: (row: MasterRecord) => Record<string, string>;
};

const WEEKDAY_LABELS: Record<number, string> = {
  1: 'Mon',
  2: 'Tue',
  3: 'Wed',
  4: 'Thu',
  5: 'Fri',
  6: 'Sat',
  7: 'Sun',
};

function parseWorkingDays(value: string): number[] {
  return value
    .split(',')
    .map((part) => Number(part.trim()))
    .filter((day) => day >= 1 && day <= 7);
}

export const MASTER_CONFIGS: Record<MasterKey, MasterConfig> = {
  departments: {
    key: 'departments',
    title: 'Departments',
    singular: 'Department',
    description: 'Manage departments for the organization.',
    fields: [{ name: 'name', label: 'Name', required: true, maxLength: 150 }],
    list: (token, params) => organizationApi.listDepartments(token, params),
    create: (token, values) => organizationApi.createDepartment(token, { name: values.name }),
    update: (token, id, values) =>
      organizationApi.updateDepartment(token, id, {
        name: typeof values.name === 'string' ? values.name : undefined,
        is_active: typeof values.is_active === 'boolean' ? values.is_active : undefined,
      }),
    remove: (token, id) => organizationApi.deleteDepartment(token, id),
  },
  'employee-types': {
    key: 'employee-types',
    title: 'Employee Types',
    singular: 'Employee type',
    description: 'Permanent, contract, intern, and other employment categories.',
    fields: [{ name: 'name', label: 'Name', required: true, maxLength: 160 }],
    list: (token, params) => organizationApi.listEmployeeTypes(token, params),
    create: (token, values) => organizationApi.createEmployeeType(token, { name: values.name }),
    update: (token, id, values) =>
      organizationApi.updateEmployeeType(token, id, {
        name: typeof values.name === 'string' ? values.name : undefined,
        is_active: typeof values.is_active === 'boolean' ? values.is_active : undefined,
      }),
    remove: (token, id) => organizationApi.deleteEmployeeType(token, id),
  },
  'access-types': {
    key: 'access-types',
    title: 'Access Types',
    singular: 'Access type',
    description: 'Roles that control what users can do in the organization.',
    fields: [
      { name: 'name', label: 'Name', required: true, maxLength: 160 },
      { name: 'description', label: 'Description', type: 'textarea', maxLength: 500 },
    ],
    list: (token, params) => organizationApi.listAccessTypes(token, params),
    create: (token, values) =>
      organizationApi.createAccessType(token, {
        name: values.name,
        description: values.description,
      }),
    update: (token, id, values) =>
      organizationApi.updateAccessType(token, id, {
        name: typeof values.name === 'string' ? values.name : undefined,
        description: typeof values.description === 'string' ? values.description : undefined,
        is_active: typeof values.is_active === 'boolean' ? values.is_active : undefined,
      }),
    remove: (token, id) => organizationApi.deleteAccessType(token, id),
  },
  shifts: {
    key: 'shifts',
    title: 'Shifts',
    singular: 'Shift',
    description: 'Define working shift timings for attendance.',
    fields: [
      { name: 'name', label: 'Name', required: true, maxLength: 150 },
      { name: 'start_time', label: 'Start time', type: 'time', required: true },
      { name: 'end_time', label: 'End time', type: 'time', required: true },
    ],
    list: (token, params) => organizationApi.listShifts(token, params),
    create: (token, values) =>
      organizationApi.createShift(token, {
        name: values.name,
        start_time: values.start_time,
        end_time: values.end_time,
      }),
    update: (token, id, values) =>
      organizationApi.updateShift(token, id, {
        name: typeof values.name === 'string' ? values.name : undefined,
        start_time: typeof values.start_time === 'string' ? values.start_time : undefined,
        end_time: typeof values.end_time === 'string' ? values.end_time : undefined,
        is_active: typeof values.is_active === 'boolean' ? values.is_active : undefined,
      }),
    remove: (token, id) => organizationApi.deleteShift(token, id),
    getSubtitle: (row) =>
      row.start_time && row.end_time ? `${row.start_time} – ${row.end_time}` : null,
    getInitialValues: (row) => ({
      name: row.name,
      start_time: row.start_time || '',
      end_time: row.end_time || '',
    }),
  },
  'work-weeks': {
    key: 'work-weeks',
    title: 'Work Weeks',
    singular: 'Work week',
    description: 'Set which weekdays count as working days.',
    fields: [
      { name: 'name', label: 'Name', required: true, maxLength: 100 },
      { name: 'working_days', label: 'Working days', type: 'weekdays', required: true },
    ],
    list: (token, params) => organizationApi.listWorkWeeks(token, params),
    create: (token, values) =>
      organizationApi.createWorkWeek(token, {
        name: values.name,
        working_days: parseWorkingDays(values.working_days || ''),
      }),
    update: (token, id, values) =>
      organizationApi.updateWorkWeek(token, id, {
        name: typeof values.name === 'string' ? values.name : undefined,
        working_days:
          typeof values.working_days === 'string'
            ? parseWorkingDays(values.working_days)
            : undefined,
        is_active: typeof values.is_active === 'boolean' ? values.is_active : undefined,
      }),
    remove: (token, id) => organizationApi.deleteWorkWeek(token, id),
    getSubtitle: (row) => {
      const days = row.working_days || [];
      if (!days.length) return null;
      return days.map((day) => WEEKDAY_LABELS[day] || String(day)).join(', ');
    },
    getInitialValues: (row) => ({
      name: row.name,
      working_days: (row.working_days || []).join(','),
    }),
  },
  'leave-types': {
    key: 'leave-types',
    title: 'Leave Types',
    singular: 'Leave type',
    description: 'Casual, sick, earned, and other leave categories.',
    fields: [{ name: 'name', label: 'Name', required: true, maxLength: 150 }],
    list: (token, params) => organizationApi.listLeaveTypes(token, params),
    create: (token, values) => organizationApi.createLeaveType(token, { name: values.name }),
    update: (token, id, values) =>
      organizationApi.updateLeaveType(token, id, {
        name: typeof values.name === 'string' ? values.name : undefined,
        is_active: typeof values.is_active === 'boolean' ? values.is_active : undefined,
      }),
    remove: (token, id) => organizationApi.deleteLeaveType(token, id),
  },
};

export type SetupNavItem = {
  to: string;
  label: string;
  description: string;
  end?: boolean;
  icon:
    | 'overview'
    | 'departments'
    | 'designations'
    | 'employee-types'
    | 'access-types'
    | 'shifts'
    | 'work-weeks'
    | 'leave-types'
    | 'holidays';
};

export const SETUP_NAV: SetupNavItem[] = [
  {
    to: '/app/setup',
    label: 'Overview',
    description: 'Setup guide & context',
    end: true,
    icon: 'overview',
  },
  {
    to: '/app/setup/departments',
    label: 'Departments',
    description: 'Org structure',
    icon: 'departments',
  },
  {
    to: '/app/setup/designations',
    label: 'Designations',
    description: 'Reporting hierarchy',
    icon: 'designations',
  },
  {
    to: '/app/setup/employee-types',
    label: 'Employee Types',
    description: 'Employment categories',
    icon: 'employee-types',
  },
  {
    to: '/app/setup/access-types',
    label: 'Access Types',
    description: 'Roles & permissions',
    icon: 'access-types',
  },
  {
    to: '/app/setup/shifts',
    label: 'Shifts',
    description: 'Working hours',
    icon: 'shifts',
  },
  {
    to: '/app/setup/work-weeks',
    label: 'Work Weeks',
    description: 'Working days',
    icon: 'work-weeks',
  },
  {
    to: '/app/setup/leave-types',
    label: 'Leave Types',
    description: 'Leave categories',
    icon: 'leave-types',
  },
  {
    to: '/app/setup/holidays',
    label: 'Holidays',
    description: 'Calendars & dates',
    icon: 'holidays',
  },
];

export const SETUP_MODULES = [
  {
    step: '01',
    to: '/app/setup/departments',
    title: 'Departments',
    description: 'Create organization-wide business units. Hierarchy lives in designations.',
    icon: 'departments' as const,
  },
  {
    step: '02',
    to: '/app/setup/designations',
    title: 'Designations',
    description: 'Build the reporting tree inside each department with drag-and-drop nesting.',
    icon: 'designations' as const,
  },
  {
    step: '03',
    to: '/app/setup/employee-types',
    title: 'Employee Types',
    description: 'Define Permanent, Contract, Intern, and other employment categories.',
    icon: 'employee-types' as const,
  },
  {
    step: '04',
    to: '/app/setup/access-types',
    title: 'Access Types',
    description: 'Set Admin, Manager, Employee and other roles for membership access.',
    icon: 'access-types' as const,
  },
  {
    step: '05',
    to: '/app/setup/shifts',
    title: 'Shifts',
    description: 'Configure shift names with start and end times for attendance.',
    icon: 'shifts' as const,
  },
  {
    step: '06',
    to: '/app/setup/work-weeks',
    title: 'Work Weeks',
    description: 'Choose which weekdays are working days for each schedule pattern.',
    icon: 'work-weeks' as const,
  },
  {
    step: '07',
    to: '/app/setup/leave-types',
    title: 'Leave Types',
    description: 'Create leave categories such as Casual, Sick, and Earned leave.',
    icon: 'leave-types' as const,
  },
  {
    step: '08',
    to: '/app/setup/holidays',
    title: 'Holidays',
    description: 'Build yearly holiday calendars and add dates for each observance.',
    icon: 'holidays' as const,
  },
];
