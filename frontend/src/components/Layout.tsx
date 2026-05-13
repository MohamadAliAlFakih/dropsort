import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Button } from "./Button";

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return isActive ? "nav-link nav-link-active" : "nav-link";
}

export function Layout() {
  const { token, logout } = useAuth();

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>

      <header className="site-header">
        <nav className="site-nav" aria-label="Primary">
          <NavLink className={navLinkClass} to="/" end>
            <strong className="site-brand">dropsort</strong>
          </NavLink>

          <NavLink className={navLinkClass} to="/" end>
            Home
          </NavLink>

          <NavLink className={navLinkClass} to="/login">
            Login
          </NavLink>

          {token ? (
            <Button type="button" variant="muted" onClick={logout}>
              Log out
            </Button>
          ) : null}
        </nav>
      </header>

      <main id="main-content" className="site-main" tabIndex={-1}>
        <Outlet />
      </main>
    </>
  );
}