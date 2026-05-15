import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ROLE_LABELS } from "../lib/roleLabels";

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return isActive ? "nav-link nav-link--active" : "nav-link";
}

function SettingsMenu() {
  const { me, meLoading, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!open) {
      return;
    }
    function onClick(ev: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(ev.target as Node)) {
        setOpen(false);
      }
    }
    function onKey(ev: KeyboardEvent) {
      if (ev.key === "Escape") {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="settings-menu" ref={wrapperRef}>
      <button
        type="button"
        className="settings-menu__trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Open account menu"
        onClick={() => setOpen((v) => !v)}
      >
        <svg
          className="settings-menu__icon"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
          focusable="false"
        >
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h.01a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h.01a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v.01a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      </button>

      {open ? (
        <div className="settings-menu__panel" role="menu">
          <div className="settings-menu__identity">
            {me ? (
              <>
                <div className="settings-menu__email">{me.email}</div>
                <div className="settings-menu__role muted">{ROLE_LABELS[me.role]}</div>
              </>
            ) : meLoading ? (
              <span className="nav-user-skeleton" aria-label="Loading account" />
            ) : (
              <div className="settings-menu__email">Account</div>
            )}
          </div>
          <button
            type="button"
            className="settings-menu__item"
            role="menuitem"
            onClick={() => {
              setOpen(false);
              navigate("/settings/account");
            }}
          >
            Account settings
          </button>
          <button
            type="button"
            className="settings-menu__item settings-menu__item--danger"
            role="menuitem"
            onClick={() => {
              setOpen(false);
              logout();
            }}
          >
            Sign out
          </button>
        </div>
      ) : null}
    </div>
  );
}

export function Layout() {
  const { token, me } = useAuth();
  const canSeeAudit = me?.role === "admin" || me?.role === "auditor";

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
                  {canSeeAudit ? (
                    <NavLink className={navLinkClass} to="/audit">
                      Audit
                    </NavLink>
                  ) : null}
                </div>
              ) : null}
            </div>

            <div className="site-nav__end">
              {token ? (
                <SettingsMenu />
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
