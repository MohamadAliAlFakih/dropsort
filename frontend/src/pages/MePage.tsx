import { useAuth } from "../auth/AuthContext";
import { Button } from "../components/Button";
import { StatusBadge } from "../components/data/StatusBadge";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";

export function MePage() {
  const { me, meLoading, refreshMe, logout } = useAuth();

  if (meLoading && !me) {
    return (
      <div className="page">
        <PageHeader title="Account" />
        <LoadingSpinner label="Loading profile…" />
      </div>
    );
  }

  if (!me) {
    return (
      <div className="page">
        <PageHeader title="Account" />
        <p className="muted">No profile loaded. Try signing in again.</p>
        <Button type="button" variant="muted" onClick={() => void refreshMe()}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="page">
      <PageHeader
        title="Account"
        description="Profile from GET /me (UserOut)."
        actions={
          <>
            <Button type="button" variant="muted" onClick={() => void refreshMe()}>
              Refresh
            </Button>
            <Button type="button" variant="muted" onClick={logout}>
              Log out
            </Button>
          </>
        }
      />

      <dl
        className="muted"
        style={{
          display: "grid",
          gridTemplateColumns: "auto 1fr",
          gap: "0.5rem 1rem",
        }}
      >
        <dt>Email</dt>
        <dd style={{ margin: 0 }}>{me.email}</dd>
        <dt>Role</dt>
        <dd style={{ margin: 0 }}>
          <StatusBadge tone="neutral">{me.role}</StatusBadge>
        </dd>
        <dt>Active</dt>
        <dd style={{ margin: 0 }}>{me.is_active ? "Yes" : "No"}</dd>
        <dt>User id</dt>
        <dd style={{ margin: 0 }}>
          <code>{me.id}</code>
        </dd>
        <dt>Created</dt>
        <dd style={{ margin: 0 }}>{me.created_at}</dd>
      </dl>
    </div>
  );
}
