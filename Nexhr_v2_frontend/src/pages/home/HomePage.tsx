import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import './HomePage.css';

const FILTERS = ['Home', 'All', 'Recent', 'Starred', 'Recovery', 'Deleted'] as const;

const QUICK_ACCESS = [
  { label: 'Videos', tone: 'red', icon: 'video' },
  { label: 'Apps', tone: 'blue', icon: 'apps' },
  { label: 'Document', tone: 'orange', icon: 'doc' },
  { label: 'Music', tone: 'yellow', icon: 'music' },
  { label: 'Download', tone: 'purple', icon: 'download' },
  { label: 'Folder', tone: 'cyan', icon: 'folder' },
  { label: 'Zip File', tone: 'amber', icon: 'zip' },
  { label: 'Trash', tone: 'pink', icon: 'trash' },
] as const;

const FOLDERS = [
  { name: 'Tivo admin', files: '20 files', when: '2 Hour ago' },
  { name: 'Viho admin', files: '14 files', when: '3 Hour ago' },
  { name: 'Unice admin', files: '15 files', when: '3 Days ago' },
  { name: 'Koho admin', files: '10 files', when: '1 Days ago' },
];

const FILES = [
  { name: 'Logo.psd', meta: '1 hour ago, 2.0 MB', tone: 'blue' },
  { name: 'Backend.xls', meta: '2 Days ago, 3.00 GB', tone: 'green' },
  { name: 'Project.zip', meta: '3 hour ago, 1.90 GB', tone: 'yellow' },
  { name: 'Report.font', meta: '1 Days ago, 0.9 KB', tone: 'purple' },
  { name: 'Project.zip', meta: '3 hour ago, 1.90 GB', tone: 'yellow' },
  { name: 'Report.font', meta: '1 Days ago, 0.9 KB', tone: 'purple' },
  { name: 'Backend.xls', meta: '2 Days ago, 3.00 GB', tone: 'green' },
  { name: 'Report.font', meta: '1 Days ago, 0.9 KB', tone: 'purple' },
];

function QuickIcon({ name }: { name: string }) {
  const props = {
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
  };
  switch (name) {
    case 'video':
      return (
        <svg {...props}>
          <rect x="3" y="6" width="13" height="12" rx="2" />
          <path d="m16 10 5-3v10l-5-3z" />
        </svg>
      );
    case 'apps':
      return (
        <svg {...props}>
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
        </svg>
      );
    case 'doc':
      return (
        <svg {...props}>
          <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
          <path d="M14 3v5h5M9 13h6M9 17h6" />
        </svg>
      );
    case 'music':
      return (
        <svg {...props}>
          <path d="M9 18V6l10-2v12" />
          <circle cx="7" cy="18" r="2.5" />
          <circle cx="17" cy="16" r="2.5" />
        </svg>
      );
    case 'download':
      return (
        <svg {...props}>
          <path d="M12 4v10M8 10l4 4 4-4M5 19h14" />
        </svg>
      );
    case 'folder':
      return (
        <svg {...props}>
          <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" />
        </svg>
      );
    case 'zip':
      return (
        <svg {...props}>
          <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
          <path d="M14 3v5h5M11 9v1M11 12v1M11 15v1" />
        </svg>
      );
    case 'trash':
      return (
        <svg {...props}>
          <path d="M4 7h16M9 7V5h6v2M8 7l1 12h6l1-12" />
        </svg>
      );
    default:
      return null;
  }
}

export function HomePage() {
  const navigate = useNavigate();
  const workspace = useWorkspace();
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>('Home');
  const [query, setQuery] = useState('');

  const folders = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return FOLDERS;
    return FOLDERS.filter((item) => item.name.toLowerCase().includes(q));
  }, [query]);

  const files = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return FILES;
    return FILES.filter((item) => item.name.toLowerCase().includes(q));
  }, [query]);

  return (
    <div className="file-manager">
      <div className="file-manager__layout">
        <aside className="file-sidebar card">
          <div className="file-sidebar__body">
            <div className="file-filter">
              {FILTERS.map((item) => (
                <button
                  key={item}
                  type="button"
                  className={`file-filter__btn ${filter === item ? 'active' : ''}`}
                  onClick={() => setFilter(item)}
                >
                  <span className="file-filter__icon" aria-hidden="true">
                    {item === 'Home' ? '⌂' : item === 'All' ? '▦' : item === 'Recent' ? '⏱' : item === 'Starred' ? '★' : item === 'Recovery' ? '↺' : '🗑'}
                  </span>
                  {item}
                </button>
              ))}
            </div>

            <button type="button" className="btn btn-outline-primary btn-block">
              <span aria-hidden="true">⛁</span> Storage
            </button>
            <div className="storage-meter">
              <div className="progress">
                <div className="progress-bar" style={{ width: '25%' }} />
              </div>
              <p>25 GB of 100 GB used</p>
            </div>

            <button type="button" className="btn btn-outline-primary btn-block">
              Pricing plan
            </button>
            <div className="pricing-plan">
              <h6>Trial Version</h6>
              <h5>FREE</h5>
              <p>100 GB Space</p>
              <button type="button" className="btn btn-primary btn-sm">
                Selected
              </button>
            </div>
          </div>
        </aside>

        <section className="file-content">
          <div className="file-content__toolbar">
            <div className="file-search">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3.5-3.5" />
              </svg>
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search..."
                aria-label="Search files"
              />
            </div>
            <div className="file-content__actions">
              <button
                type="button"
                className="btn btn-primary"
                onClick={() =>
                  workspace.organization?.can_edit
                    ? navigate('/app/organization')
                    : navigate('/app/profile')
                }
              >
                + Add New
              </button>
              <button type="button" className="btn btn-outline-primary">
                ↑ Upload
              </button>
            </div>
          </div>

          <div className="file-section">
            <h5>Quick Access</h5>
            <div className="quick-access">
              {QUICK_ACCESS.map((item) => (
                <button key={item.label} type="button" className={`quick-access__item tone-${item.tone}`}>
                  <span className="quick-access__icon">
                    <QuickIcon name={item.icon} />
                  </span>
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="file-section">
            <h5>Folders</h5>
            <div className="folder-grid">
              {folders.map((folder) => (
                <article key={folder.name} className="folder-card">
                  <button type="button" className="folder-card__menu" aria-label="More">
                    ⋮
                  </button>
                  <div className="folder-card__icon" aria-hidden="true">
                    <svg viewBox="0 0 64 52" width="42" height="34">
                      <path
                        d="M2 12c0-3.3 2.7-6 6-6h12l6 6h30c3.3 0 6 2.7 6 6v26c0 3.3-2.7 6-6 6H8c-3.3 0-6-2.7-6-6V12z"
                        fill="#ffc107"
                      />
                      <path
                        d="M2 18h60v26c0 3.3-2.7 6-6 6H8c-3.3 0-6-2.7-6-6V18z"
                        fill="#ffca28"
                      />
                    </svg>
                  </div>
                  <h6>{folder.name}</h6>
                  <p>
                    {folder.files}
                    <span>{folder.when}</span>
                  </p>
                </article>
              ))}
            </div>
          </div>

          <div className="file-section">
            <h5>Files</h5>
            <div className="file-grid">
              {files.map((file, index) => (
                <article key={`${file.name}-${index}`} className="file-card">
                  <span className={`file-card__icon tone-${file.tone}`} aria-hidden="true">
                    {file.name.split('.').pop()?.toUpperCase().slice(0, 3)}
                  </span>
                  <div>
                    <h6>{file.name}</h6>
                    <p>{file.meta}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
