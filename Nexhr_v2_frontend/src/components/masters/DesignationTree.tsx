import { useCallback, useEffect, useMemo, useState, type DragEvent } from 'react';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import type { Department, Designation } from '../../types';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import { Button } from '../Button';
import { ConfirmDialog } from '../ui/ConfirmDialog';
import { EmptyState } from '../ui/EmptyState';
import { FormModal } from '../ui/FormModal';
import {
  IconAction,
  IconActivate,
  IconAdd,
  IconDeactivate,
  IconDelete,
  IconEdit,
  IconMoveDown,
  IconMoveUp,
} from '../ui/IconAction';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { PageHeader } from '../ui/PageHeader';
import { SearchBar } from '../ui/SearchBar';
import { StatusBadge } from '../ui/StatusBadge';
import { Toolbar } from '../ui/Toolbar';
import { getInitial } from '../../utils/initials';
import './DesignationTree.css';

type DropPosition = 'before' | 'after' | 'inside';

type DropTarget = {
  id: string;
  position: DropPosition;
};

type TreeNodeProps = {
  node: Designation;
  depth: number;
  siblings: Designation[];
  index: number;
  isLast: boolean;
  ancestorLines: boolean[];
  expanded: Set<string>;
  selectedId: string | null;
  draggingId: string | null;
  dropTarget: DropTarget | null;
  onToggle: (id: string) => void;
  onSelect: (id: string) => void;
  onAddChild: (parent: Designation) => void;
  onEdit: (node: Designation) => void;
  onDelete: (node: Designation) => void;
  onToggleActive: (node: Designation) => void;
  onMove: (node: Designation, direction: 'up' | 'down') => void;
  onDragStart: (node: Designation) => void;
  onDragEnd: () => void;
  onDragOverNode: (node: Designation, position: DropPosition) => void;
  onDropOnNode: (node: Designation, position: DropPosition) => void;
};

function isDescendantOf(tree: Designation[], ancestorId: string, maybeDescendantId: string): boolean {
  const walk = (nodes: Designation[]): boolean => {
    for (const node of nodes) {
      if (node.id === ancestorId) {
        const contains = (kids: Designation[]): boolean =>
          kids.some((kid) => kid.id === maybeDescendantId || contains(kid.children || []));
        return contains(node.children || []);
      }
      if (walk(node.children || [])) return true;
    }
    return false;
  };
  return walk(tree);
}

function resolveDropPosition(event: DragEvent<HTMLElement>): DropPosition {
  const rect = event.currentTarget.getBoundingClientRect();
  const offset = (event.clientY - rect.top) / rect.height;
  if (offset < 0.28) return 'before';
  if (offset > 0.72) return 'after';
  return 'inside';
}

function ChevronIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg
      className={`teams-tree__chevron-icon ${expanded ? 'is-expanded' : ''}`}
      viewBox="0 0 24 24"
      width="14"
      height="14"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.4"
      aria-hidden
    >
      <path d="m9 6 6 6-6 6" />
    </svg>
  );
}

function TreeNode({
  node,
  depth,
  siblings,
  index,
  isLast,
  ancestorLines,
  expanded,
  selectedId,
  draggingId,
  dropTarget,
  onToggle,
  onSelect,
  onAddChild,
  onEdit,
  onDelete,
  onToggleActive,
  onMove,
  onDragStart,
  onDragEnd,
  onDragOverNode,
  onDropOnNode,
}: TreeNodeProps) {
  const children = node.children || [];
  const hasChildren = children.length > 0;
  const isExpanded = expanded.has(node.id);
  const initial = getInitial(node.name, 'D');
  const childCount = children.length;
  const isDragging = draggingId === node.id;
  const isDropBefore = dropTarget?.id === node.id && dropTarget.position === 'before';
  const isDropAfter = dropTarget?.id === node.id && dropTarget.position === 'after';
  const isDropInside = dropTarget?.id === node.id && dropTarget.position === 'inside';

  return (
    <li className={`teams-tree__item ${isLast ? 'is-last' : ''}`} role="none">
      <div
        className={[
          'teams-tree__row',
          selectedId === node.id ? 'is-selected' : '',
          node.is_active ? '' : 'is-inactive',
          hasChildren ? 'has-children' : '',
          isExpanded ? 'is-expanded' : '',
          isDragging ? 'is-dragging' : '',
          isDropBefore ? 'drop-before' : '',
          isDropAfter ? 'drop-after' : '',
          isDropInside ? 'drop-inside' : '',
        ]
          .filter(Boolean)
          .join(' ')}
        style={{ ['--tree-depth' as string]: depth }}
        draggable
        onDragStart={(event) => {
          event.dataTransfer.effectAllowed = 'move';
          event.dataTransfer.setData('text/plain', node.id);
          onDragStart(node);
        }}
        onDragEnd={onDragEnd}
        onDragOver={(event) => {
          event.preventDefault();
          event.dataTransfer.dropEffect = 'move';
          if (!draggingId || draggingId === node.id) return;
          onDragOverNode(node, resolveDropPosition(event));
        }}
        onDragLeave={() => {
          // no-op; parent clears on drag end / new target
        }}
        onDrop={(event) => {
          event.preventDefault();
          event.stopPropagation();
          if (!draggingId || draggingId === node.id) return;
          onDropOnNode(node, resolveDropPosition(event));
        }}
        onClick={() => onSelect(node.id)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            onSelect(node.id);
          }
        }}
        role="treeitem"
        aria-selected={selectedId === node.id}
        aria-expanded={hasChildren ? isExpanded : undefined}
        aria-grabbed={isDragging}
        tabIndex={0}
      >
        <div className="teams-tree__guides" aria-hidden>
          {ancestorLines.map((showLine, guideIndex) => (
            <span
              key={guideIndex}
              className={`teams-tree__guide ${showLine ? 'has-line' : ''}`}
            />
          ))}
          {depth > 0 ? (
            <span className={`teams-tree__branch ${isLast ? 'is-last' : ''}`}>
              <span className="teams-tree__branch-stem" />
              <span className="teams-tree__branch-arm" />
            </span>
          ) : null}
        </div>

        <span className="teams-tree__drag-handle" data-tooltip="Drag to reorder" aria-hidden>
          <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
            <circle cx="9" cy="7" r="1.4" />
            <circle cx="15" cy="7" r="1.4" />
            <circle cx="9" cy="12" r="1.4" />
            <circle cx="15" cy="12" r="1.4" />
            <circle cx="9" cy="17" r="1.4" />
            <circle cx="15" cy="17" r="1.4" />
          </svg>
        </span>

        <button
          type="button"
          className={`teams-tree__chevron ${hasChildren ? '' : 'is-leaf'}`}
          aria-label={isExpanded ? 'Collapse' : 'Expand'}
          data-tooltip={hasChildren ? (isExpanded ? 'Collapse' : 'Expand') : undefined}
          disabled={!hasChildren}
          onClick={(event) => {
            event.stopPropagation();
            if (hasChildren) onToggle(node.id);
          }}
        >
          {hasChildren ? <ChevronIcon expanded={isExpanded} /> : <span className="teams-tree__leaf-dot" />}
        </button>

        <div className="teams-tree__card">
          <span className={`teams-tree__avatar teams-tree__avatar--L${(depth % 4) + 1}`} aria-hidden>
            {initial}
          </span>

          <div className="teams-tree__meta">
            <div className="teams-tree__title-row">
              <strong className="teams-tree__name">{node.name}</strong>
              <StatusBadge active={node.is_active} />
            </div>
            <span className="teams-tree__subtitle">
              {hasChildren
                ? `${childCount} direct report${childCount === 1 ? '' : 's'}`
                : depth === 0
                  ? 'Top-level designation'
                  : 'Reports to parent'}
              {' · Drag to move'}
            </span>
          </div>

          <div className="teams-tree__actions" onClick={(event) => event.stopPropagation()}>
            <IconAction label={`Add child under ${node.name}`} onClick={() => onAddChild(node)}>
              <IconAdd />
            </IconAction>
            <IconAction label={`Edit ${node.name}`} onClick={() => onEdit(node)}>
              <IconEdit />
            </IconAction>
            <IconAction
              label={`Move ${node.name} up`}
              disabled={index === 0}
              onClick={() => onMove(node, 'up')}
            >
              <IconMoveUp />
            </IconAction>
            <IconAction
              label={`Move ${node.name} down`}
              disabled={index >= siblings.length - 1}
              onClick={() => onMove(node, 'down')}
            >
              <IconMoveDown />
            </IconAction>
            <IconAction
              label={node.is_active ? `Deactivate ${node.name}` : `Activate ${node.name}`}
              className={node.is_active ? 'icon-action--warning' : 'icon-action--success'}
              onClick={() => onToggleActive(node)}
            >
              {node.is_active ? <IconDeactivate /> : <IconActivate />}
            </IconAction>
            <IconAction label={`Delete ${node.name}`} danger onClick={() => onDelete(node)}>
              <IconDelete />
            </IconAction>
          </div>
        </div>
      </div>

      {hasChildren && isExpanded ? (
        <ul className="teams-tree__children" role="group">
          {children.map((child, childIndex) => (
            <TreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              siblings={children}
              index={childIndex}
              isLast={childIndex === children.length - 1}
              ancestorLines={[...ancestorLines, !isLast]}
              expanded={expanded}
              selectedId={selectedId}
              draggingId={draggingId}
              dropTarget={dropTarget}
              onToggle={onToggle}
              onSelect={onSelect}
              onAddChild={onAddChild}
              onEdit={onEdit}
              onDelete={onDelete}
              onToggleActive={onToggleActive}
              onMove={onMove}
              onDragStart={onDragStart}
              onDragEnd={onDragEnd}
              onDragOverNode={onDragOverNode}
              onDropOnNode={onDropOnNode}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function DesignationTree() {
  const { currentBranch } = useWorkspace();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [departmentId, setDepartmentId] = useState('');
  const [tree, setTree] = useState<Designation[]>([]);
  const [search, setSearch] = useState('');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<DropTarget | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Designation | null>(null);
  const [parentId, setParentId] = useState<string | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Designation | null>(null);
  const [confirmLoading, setConfirmLoading] = useState(false);

  const loadDepartments = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    const data = await organizationApi.listDepartments(token, { page_size: 100, is_active: true });
    setDepartments(data.items);
    setDepartmentId((prev) => prev || data.items[0]?.id || '');
  }, []);

  const loadTree = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token || !departmentId) {
      setTree([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await organizationApi.listDesignations(token, departmentId, search.trim());
      setTree(data);
      setExpanded((prev) => {
        const next = new Set(prev);
        const walk = (nodes: Designation[]) => {
          for (const node of nodes) {
            next.add(node.id);
            if (node.children?.length) walk(node.children);
          }
        };
        walk(data);
        return next;
      });
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load designations.'));
      setTree([]);
    } finally {
      setLoading(false);
    }
  }, [departmentId, search]);

  useEffect(() => {
    void loadDepartments().catch((err) => {
      setError(extractErrorMessage(err, 'Unable to load departments.'));
      setLoading(false);
    });
  }, [loadDepartments, currentBranch?.branch_id]);

  useEffect(() => {
    void loadTree();
  }, [loadTree]);

  function toggleExpand(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function expandAll() {
    const next = new Set<string>();
    const walk = (nodes: Designation[]) => {
      for (const node of nodes) {
        if (node.children?.length) {
          next.add(node.id);
          walk(node.children);
        }
      }
    };
    walk(tree);
    setExpanded(next);
  }

  function collapseAll() {
    setExpanded(new Set());
  }

  function openCreate(parent: Designation | null = null) {
    setEditing(null);
    setParentId(parent?.id ?? null);
    setFormError(null);
    setFormOpen(true);
  }

  function openEdit(node: Designation) {
    setEditing(node);
    setParentId(node.parent_id);
    setFormError(null);
    setFormOpen(true);
  }

  async function handleSubmit(values: Record<string, string>) {
    const token = tokenStorage.getAccessToken();
    if (!token || !departmentId) return;
    setFormLoading(true);
    setFormError(null);
    try {
      if (editing) {
        await organizationApi.updateDesignation(token, editing.id, { name: values.name });
      } else {
        await organizationApi.createDesignation(token, departmentId, {
          name: values.name,
          parent_id: parentId,
        });
      }
      setFormOpen(false);
      await loadTree();
    } catch (err) {
      setFormError(extractErrorMessage(err, 'Unable to save designation.'));
    } finally {
      setFormLoading(false);
    }
  }

  async function handleToggleActive(node: Designation) {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    try {
      await organizationApi.updateDesignation(token, node.id, { is_active: !node.is_active });
      await loadTree();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to update status.'));
    }
  }

  async function handleMove(node: Designation, direction: 'up' | 'down') {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    try {
      const data = await organizationApi.moveDesignation(token, node.id, direction);
      setTree(data);
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to reorder designation.'));
    }
  }

  function handleDragOverNode(node: Designation, position: DropPosition) {
    if (!draggingId || draggingId === node.id) return;
    if (position === 'inside' && isDescendantOf(tree, draggingId, node.id)) return;
    setDropTarget((prev) =>
      prev?.id === node.id && prev.position === position ? prev : { id: node.id, position },
    );
  }

  async function handleDropOnNode(node: Designation, position: DropPosition) {
    const token = tokenStorage.getAccessToken();
    const sourceId = draggingId;
    setDraggingId(null);
    setDropTarget(null);
    if (!token || !sourceId || sourceId === node.id) return;
    if (position === 'inside' && isDescendantOf(tree, sourceId, node.id)) {
      setError('Cannot move a designation under its own descendant.');
      return;
    }
    try {
      const data = await organizationApi.repositionDesignation(token, sourceId, {
        target_id: node.id,
        position,
      });
      setTree(data);
      if (position === 'inside') {
        setExpanded((prev) => new Set(prev).add(node.id));
      }
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to move designation.'));
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setConfirmLoading(true);
    try {
      await organizationApi.deleteDesignation(token, pendingDelete.id);
      setConfirmOpen(false);
      setPendingDelete(null);
      await loadTree();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to delete designation.'));
      setConfirmOpen(false);
    } finally {
      setConfirmLoading(false);
    }
  }

  const formTitle = useMemo(() => {
    if (editing) return 'Edit designation';
    if (parentId) return 'Add child designation';
    return 'Add designation';
  }, [editing, parentId]);

  const selectedDepartment = departments.find((item) => item.id === departmentId);

  return (
    <section className="designation-tree">
      <PageHeader
        title="Designations"
        description="Drag nodes to reorder or nest them. Drop on the top/bottom edge to place beside, or on the center to make a child."
        actions={
          <Button onClick={() => openCreate(null)} disabled={!departmentId}>
            Add root
          </Button>
        }
      />

      <Toolbar
        left={
          <>
            <label className="dept-select">
              <span>Department</span>
              <select
                value={departmentId}
                onChange={(event) => setDepartmentId(event.target.value)}
                aria-label="Select department"
              >
                {!departments.length ? <option value="">No departments</option> : null}
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name}
                  </option>
                ))}
              </select>
            </label>
            <SearchBar
              value={search}
              placeholder="Search designations…"
              onValueChange={setSearch}
              aria-label="Search designations"
            />
          </>
        }
        right={
          tree.length ? (
            <div className="teams-tree__toolbar-actions">
              <Button variant="ghost" onClick={expandAll}>
                Expand all
              </Button>
              <Button variant="ghost" onClick={collapseAll}>
                Collapse all
              </Button>
            </div>
          ) : null
        }
      />

      {error ? <div className="auth-alert auth-alert--error">{error}</div> : null}

      {!departments.length && !loading ? (
        <EmptyState
          title="Create a department first"
          description="Designations belong to a department. Add one under Departments, then return here."
        />
      ) : loading ? (
        <LoadingSkeleton rows={6} />
      ) : !tree.length ? (
        <EmptyState
          title="No designations yet"
          description="Start with a root designation, then add children to build the hierarchy."
          action={
            <Button onClick={() => openCreate(null)} disabled={!departmentId}>
              Add root
            </Button>
          }
        />
      ) : (
        <div className={`teams-tree ${draggingId ? 'is-dnd-active' : ''}`}>
          <header className="teams-tree__header">
            <div className="teams-tree__header-mark" aria-hidden>
              {getInitial(selectedDepartment?.name, 'D')}
            </div>
            <div>
              <h3>{selectedDepartment?.name || 'Department'}</h3>
              <p>{draggingId ? 'Drop on a row to reposition' : 'Reporting structure · drag & drop enabled'}</p>
            </div>
          </header>

          <ul className="teams-tree__root" role="tree" aria-label="Designation hierarchy">
            {tree.map((node, index) => (
              <TreeNode
                key={node.id}
                node={node}
                depth={0}
                siblings={tree}
                index={index}
                isLast={index === tree.length - 1}
                ancestorLines={[]}
                expanded={expanded}
                selectedId={selectedId}
                draggingId={draggingId}
                dropTarget={dropTarget}
                onToggle={toggleExpand}
                onSelect={setSelectedId}
                onAddChild={(parent) => openCreate(parent)}
                onEdit={openEdit}
                onDelete={(item) => {
                  setPendingDelete(item);
                  setConfirmOpen(true);
                }}
                onToggleActive={(item) => void handleToggleActive(item)}
                onMove={(item, direction) => void handleMove(item, direction)}
                onDragStart={(item) => {
                  setDraggingId(item.id);
                  setSelectedId(item.id);
                }}
                onDragEnd={() => {
                  setDraggingId(null);
                  setDropTarget(null);
                }}
                onDragOverNode={handleDragOverNode}
                onDropOnNode={(item, position) => void handleDropOnNode(item, position)}
              />
            ))}
          </ul>
        </div>
      )}

      <FormModal
        open={formOpen}
        title={formTitle}
        fields={[{ name: 'name', label: 'Designation name', required: true, maxLength: 160 }]}
        initialValues={editing ? { name: editing.name } : {}}
        submitLabel={editing ? 'Save changes' : 'Create'}
        loading={formLoading}
        error={formError}
        onSubmit={handleSubmit}
        onClose={() => setFormOpen(false)}
      />

      <ConfirmDialog
        open={confirmOpen}
        title="Delete designation?"
        message={`“${pendingDelete?.name ?? ''}” will be removed. Child designations will move up one level.`}
        confirmLabel="Delete"
        danger
        loading={confirmLoading}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={() => void confirmDelete()}
      />
    </section>
  );
}
