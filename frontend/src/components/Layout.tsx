import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Button } from "./Button";
import { StatusBadge } from "./data/StatusBadge";

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return isActive ? "nav-link nav-link-active" : "nav-link";
}

export function Layout() {
  const { token, me, meLoading, logout } = useAuth();

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>

      <header className="site-header">
        <nav className="site-nav" aria-label="Primary">
          <div className="site-nav-brand">
            <NavLink className={navLinkClass} to="/" end>
              dropsort
            </NavLink>
          </div>

          <div className="site-nav-links">
            <NavLink className={navLinkClass} to="/" end>
              Home
            </NavLink>
            {token ? (
              <>
                <NavLink className={navLinkClass} to="/batches">
                  Batches
                </NavLink>
                <NavLink className={navLinkClass} to="/predictions/recent">
                  Predictions
                </NavLink>
                <NavLink className={navLinkClass} to="/audit">
                  Audit
                </NavLink>
                <NavLink className={navLinkClass} to="/me">
                  Account
                </NavLink>
              </>
            ) : (
              <NavLink className={navLinkClass} to="/login">
                Login
              </NavLink>
            )}
          </div>

          <span className="site-nav-spacer" aria-hidden="true" />

          <div className="site-nav-actions">
            {token && me && !meLoading ? (
              <span className="muted" style={{ fontSize: "0.875rem" }}>
                <StatusBadge tone="neutral">{me.role}</StatusBadge>
              </span>
            ) : null}
            {token ? (
              <Button type="button" variant="muted" onClick={logout}>
                Log out
              </Button>
            ) : null}
          </div>
        </nav>
      </header>

      <main id="main-content" className="site-main" tabIndex={-1}>
        <Outlet />
      </main>
    </>
  );
}
