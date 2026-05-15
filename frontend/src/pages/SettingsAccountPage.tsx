import { useAuth } from "../auth/AuthContext";
import { Button } from "../components/Button";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { RefreshButton } from "../components/RefreshButton";
import { ROLE_LABELS } from "../lib/roleLabels";

export function SettingsAccountPage() {
  const { me, meLoading, refreshMe, logout } = useAuth();

  if (meLoading && !me) {
    return <LoadingSpinner label="Loading profile…" />;
  }

  if (!me) {
    return (
      <>
        <PageHeader title="Profile & access" />
        <p className="muted">No profile loaded. Try signing in again.</p>
        <Button type="button" variant="muted" onClick={() => void refreshMe()}>
          Retry
        </Button>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Profile & access"
        description="How you appear in this workspace and the permissions tied to your account."
        actions={
          <>
            <RefreshButton pending={meLoading} onClick={() => void refreshMe()} />
            <Button type="button" variant="muted" onClick={logout}>
              Sign out
            </Button>
          </>
        }
      />

      <section className="settings-profile-card panel" aria-labelledby="settings-profile-heading">
        <h2 id="settings-profile-heading" className="settings-profile-card__title">
          Account details
        </h2>
        <dl className="settings-dl">
          <div className="settings-dl__row">
            <dt>Email</dt>
            <dd>{me.email}</dd>
          </div>
          <div className="settings-dl__row">
            <dt>Access level</dt>
            <dd>{ROLE_LABELS[me.role]}</dd>
          </div>
          <div className="settings-dl__row">
            <dt>Account status</dt>
            <dd>{me.is_active ? "Active" : "Inactive"}</dd>
          </div>
          <div className="settings-dl__row">
            <dt>User ID</dt>
            <dd>
              <code>{me.id}</code>
            </dd>
          </div>
          <div className="settings-dl__row">
            <dt>Member since</dt>
            <dd className="muted">{me.created_at}</dd>
          </div>
        </dl>
      </section>
    </>
  );
}
