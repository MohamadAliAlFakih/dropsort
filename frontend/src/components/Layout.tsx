import { NavLink, Outlet, useMatch } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Button } from "./Button";
import { ROLE_LABELS } from "../lib/roleLabels";

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return isActive ? "nav-link nav-link--active" : "nav-link";
}

function settingsNavLinkClass(active: boolean): string {
  return active ? "nav-link nav-link--active nav-link--settings" : "nav-link nav-link--settings";
}

export function Layout() {
  const { token, me, meLoading, logout } = useAuth();
  const settingsArea = useMatch({ path: "/settings/*", end: false });

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>

      <header className="site-header">
        <div className="site-header-bar">
          <nav className="site-nav" aria-label="Primary">
            <div className="site-nav__start">
              <div className="site-nav-brand">
                <NavLink
                  className={({ isActive }) =>
                    ["nav-link", "nav-link-brand", isActive ? "nav-link-brand--active" : ""]
                      .filter(Boolean)
                      .join(" ")
                  }
                  to="/"
                  end
                >
                  <span className="nav-link-brand__name">Dropsort</span>
                  <span className="nav-link-brand__tag">Document intelligence</span>
                </NavLink>
              </div>

              {token ? (
                <div className="site-nav-ops" role="group" aria-label="Workspace">
                  <NavLink className={navLinkClass} to="/" end>
                    Home
                  </NavLink>
                  <NavLink className={navLinkClass} to="/batches">
                    Batches
                  </NavLink>
                  <NavLink className={navLinkClass} to="/predictions/recent">
                    Predictions
                  </NavLink>
                  <NavLink className={navLinkClass} to="/audit">
                    Audit
                  </NavLink>
                </div>
              ) : null}
            </div>

            <div className="site-nav__end">
              {token ? (
                <>
                  <NavLink className={() => settingsNavLinkClass(Boolean(settingsArea))} to="/settings/account">
                    Settings
                  </NavLink>
                  {me && !meLoading ? (
                    <div className="nav-user" aria-label="Signed-in account">
                      <span className="nav-user__email">{me.email}</span>
                      <span className="nav-user__access">Access level · {ROLE_LABELS[me.role]}</span>
                    </div>
                  ) : meLoading ? (
                    <span className="nav-user nav-user--loading muted">Loading account…</span>
                  ) : null}
                  <Button type="button" variant="muted" onClick={logout}>
                    Sign out
                  </Button>
                </>
              ) : (
                <NavLink className={navLinkClass} to="/login">
                  Sign in
                </NavLink>
              )}
            </div>
          </nav>
        </div>
      </header>

      <main id="main-content" className="site-main" tabIndex={-1}>
        <Outlet />
      </main>
    </>
  );
}
