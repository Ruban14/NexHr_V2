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
import { useAuth } from '../auth/AuthContext';
import { tokenStorage } from '../auth/tokenStorage';
import type { Organization, UserProfileDetail } from '../types';

type WorkspaceContextValue = {
  organization: Organization | null;
  profile: UserProfileDetail | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  setOrganization: (organization: Organization | null) => void;
  setProfile: (profile: UserProfileDetail | null) => void;
};

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const auth = useAuth();
  const navigate = useNavigate();
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [profile, setProfile] = useState<UserProfileDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
  }, [navigate]);

  useEffect(() => {
    if (!auth.isAuthenticated) return;
    void refresh();
  }, [auth.isAuthenticated, refresh]);

  const value = useMemo(
    () => ({
      organization,
      profile,
      loading,
      error,
      refresh,
      setOrganization,
      setProfile,
    }),
    [organization, profile, loading, error, refresh],
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
