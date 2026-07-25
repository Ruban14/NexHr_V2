const BRANCH_KEY = 'nexhr_active_branch_id';

export const branchStorage = {
  get(): string | null {
    try {
      return localStorage.getItem(BRANCH_KEY);
    } catch {
      return null;
    }
  },
  set(branchId: string | null) {
    try {
      if (!branchId) {
        localStorage.removeItem(BRANCH_KEY);
      } else {
        localStorage.setItem(BRANCH_KEY, branchId);
      }
    } catch {
      // ignore storage failures
    }
  },
};
