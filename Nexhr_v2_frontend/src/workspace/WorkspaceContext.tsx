import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { useNavigate } from 'react-router-dom';
import { organizationApi } from '../api/auth';
import { setActiveBranchId } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { tokenStorage } from '../auth/tokenStorage';
import type { BranchMembership, Organization, UserProfileDetail } from '../types';
import { branchStorage } from './branchStorage';

type WorkspaceContextValue = {
  organization: Organization | null;
  profile: UserProfileDetail | null;
  branches: BranchMembership[];
  currentBranch: BranchMembership | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  switchBranch: (branchId: string) => Promise<void>;
  setOrganization: (organization: Organization | null) => void;
  setProfile: (profile: UserProfileDetail | null) => void;
};

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const auth = useAuth();
  const navigate = useNavigate();
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [profile, setProfile] = useState<UserProfileDetail | null>(null);
  const [branches, setBranches] = useState<BranchMembership[]>([]);
  const [currentBranch, setCurrentBranch] = useState<BranchMembership | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const applyBranch = useCallback((memberships: BranchMembership[], preferredId?: string | null) => {
    const stored = preferredId ?? branchStorage.get();
    const selected =
      memberships.find((item) => item.branch_id === stored) ||
      memberships.find((item) => item.is_headquarters) ||
      memberships[0] ||
      null;
    setCurrentBranch(selected);
    setActiveBranchId(selected?.branch_id ?? null);
    branchStorage.set(selected?.branch_id ?? null);
    return selected;
  }, []);

  const refresh = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) {
      navigate('/auth/login', { replace: true });
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const status = await organizationApi.getSetupStatus(token);
      if (status.needs_setup) {
        navigate('/organizations/create', { replace: true });
        return;
      }

      const memberships = await organizationApi.listBranches(token);
      setBranches(memberships);
      applyBranch(memberships);

      const [org, userProfile] = await Promise.all([
        organizationApi.getCurrent(token),
        organizationApi.getProfile(token),
      ]);
      setOrganization(org);
      setProfile(userProfile);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load workspace.');
    } finally {
      setLoading(false);
    }
  }, [navigate, applyBranch]);

  const switchBranch = useCallback(
    async (branchId: string) => {
      const token = tokenStorage.getAccessToken();
      if (!token) return;
      const next = branches.find((item) => item.branch_id === branchId);
      if (!next) return;

      setCurrentBranch(next);
      setActiveBranchId(branchId);
      branchStorage.set(branchId);
      setLoading(true);
      setError(null);
      try {
        const [org, userProfile] = await Promise.all([
          organizationApi.getCurrent(token),
          organizationApi.getProfile(token),
        ]);
        setOrganization(org);
        setProfile(userProfile);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to switch branch.');
      } finally {
        setLoading(false);
      }
    },
    [branches],
  );

  useEffect(() => {
    if (!auth.isAuthenticated) return;
    void refresh();
  }, [auth.isAuthenticated, refresh]);

  const value = useMemo(
    () => ({
      organization,
      profile,
      branches,
      currentBranch,
      loading,
      error,
      refresh,
      switchBranch,
      setOrganization,
      setProfile,
    }),
    [organization, profile, branches, currentBranch, loading, error, refresh, switchBranch],
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace(): WorkspaceContextValue {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) {
    throw new Error('useWorkspace must be used within WorkspaceProvider');
  }
  return ctx;
}
