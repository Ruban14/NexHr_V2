import { useEffect, useMemo, useRef, useState } from 'react';
import { useWorkspace } from '../workspace/WorkspaceContext';
import './BranchSwitcher.css';

export function BranchSwitcher() {
  const { branches, currentBranch, switchBranch, loading } = useWorkspace();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onPointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false);
    }
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return branches;
    return branches.filter((item) => {
      const haystack = `${item.branch_name} ${item.branch_code} ${item.organization_name}`.toLowerCase();
      return haystack.includes(q);
    });
  }, [branches, query]);

  if (branches.length <= 1) {
    if (!currentBranch) return null;
    return (
      <div className="branch-switcher branch-switcher--static" title={currentBranch.branch_name}>
        <span className="branch-switcher__label">Branch</span>
        <strong>{currentBranch.branch_name}</strong>
      </div>
    );
  }

  return (
    <div className={`branch-switcher ${open ? 'is-open' : ''}`} ref={rootRef}>
      <button
        type="button"
        className="branch-switcher__trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        disabled={loading}
        onClick={() => setOpen((value) => !value)}
      >
        <span className="branch-switcher__meta">
          <span className="branch-switcher__label">Branch</span>
          <strong>{currentBranch?.branch_name || 'Select branch'}</strong>
        </span>
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      {open ? (
        <div className="branch-switcher__panel" role="listbox" aria-label="Switch branch">
          <input
            type="search"
            className="branch-switcher__search"
            placeholder="Search branches…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            autoFocus
          />
          <ul className="branch-switcher__list">
            {filtered.map((item) => {
              const selected = item.branch_id === currentBranch?.branch_id;
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={selected}
                    className={selected ? 'is-selected' : undefined}
                    onClick={() => {
                      void switchBranch(item.branch_id);
                      setOpen(false);
                      setQuery('');
                    }}
                  >
                    <span>
                      <strong>{item.branch_name}</strong>
                      <em>
                        {item.branch_code}
                        {item.is_headquarters ? ' · HQ' : ''}
                      </em>
                    </span>
                    {selected ? <span className="branch-switcher__check">✓</span> : null}
                  </button>
                </li>
              );
            })}
            {!filtered.length ? <li className="branch-switcher__empty">No branches match</li> : null}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
