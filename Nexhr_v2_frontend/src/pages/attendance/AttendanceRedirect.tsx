import { Navigate } from 'react-router-dom';
import { useWorkspace } from '../../workspace/WorkspaceContext';

/** Old /app/attendance route → employee profile Attendance tab. */
export function AttendanceRedirect() {
  const { profile } = useWorkspace();
  if (profile?.id) {
    return <Navigate to={`/app/employees/${profile.id}?tab=attendance`} replace />;
  }
  return <Navigate to="/app/employees" replace />;
}
