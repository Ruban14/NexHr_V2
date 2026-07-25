import type { ReactNode } from 'react';
import './DataTable.css';

export type DataTableColumn<T> = {
  key: string;
  header: string;
  width?: string;
  render: (row: T) => ReactNode;
};

type DataTableProps<T extends { id: string }> = {
  columns: DataTableColumn<T>[];
  rows: T[];
  selectedId?: string | null;
  onRowClick?: (row: T) => void;
  empty?: ReactNode;
};

export function DataTable<T extends { id: string }>({
  columns,
  rows,
  selectedId,
  onRowClick,
  empty,
}: DataTableProps<T>) {
  if (!rows.length) {
    return <>{empty}</>;
  }

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} style={column.width ? { width: column.width } : undefined}>
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.id}
              className={selectedId === row.id ? 'is-selected' : undefined}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              tabIndex={onRowClick ? 0 : undefined}
              onKeyDown={
                onRowClick
                  ? (event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        onRowClick(row);
                      }
                    }
                  : undefined
              }
            >
              {columns.map((column) => (
                <td key={column.key}>{column.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
