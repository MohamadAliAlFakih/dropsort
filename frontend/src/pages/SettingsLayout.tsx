import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { PageHeader } from "../components/PageHeader";

function settingsNavClass({ isActive }: { isActive: boolean }): string {
  return isActive ? "settings-nav-link settings-nav-link--active" : "settings-nav-link";
}

export function SettingsLayout() {
  const { me, meLoading } = useAuth();
  const showAdmin = Boolean(me && !meLoading && me.role === "admin");

  return (
    <div className="page settings-page">
      <PageHeader
        title="Settings"
        description="Your profile, access level, and (for administrators) workspace accounts."
      />

      <div className="settings-shell">
        <nav className="settings-side-nav" aria-label="Settings sections">
          <NavLink className={settingsNavClass} to="/settings/account" end>
            Profile & access
          </NavLink>
          {showAdmin ? (
            <NavLink className={settingsNavClass} to="/settings/admin/users">
              Team & accounts
            </NavLink>
          ) : null}
          {showAdmin ? (
            <NavLink className={settingsNavClass} to="/settings/system">
              System health
            </NavLink>
          ) : null}
        </nav>
        <div className="settings-outlet">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
