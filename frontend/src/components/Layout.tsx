import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ROLE_LABELS } from "../lib/roleLabels";

type Role = "admin" | "reviewer" | "auditor";

type TabDef = {
  to: string;
  label: string;
  end?: boolean;
  enabledFor: "any" | Role[];
  disabledTooltip?: string;
};

const TABS: TabDef[] = [
  { to: "/", label: "Home", end: true, enabledFor: "any" },
  { to: "/batches", label: "Batches", enabledFor: "any" },
  {
    to: "/predictions/recent",
    label: "Review",
    enabledFor: ["admin", "reviewer"],
    disabledTooltip: "You don't have access",
  },
  {
    to: "/audit",
    label: "Audit",
    enabledFor: ["admin", "auditor"],
    disabledTooltip: "You don't have access",
  },
];

function isTabEnabled(tab: TabDef, role: Role | undefined): boolean {
  if (tab.enabledFor === "any") return true;
  if (!role) return false;
  return tab.enabledFor.includes(role);
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
    if (!open) return;
    function onClick(ev: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(ev.target as Node)) {
        setOpen(false);
      }
    }
    function onKey(ev: KeyboardEvent) {
      if (ev.key === "Escape") setOpen(false);
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

function TabStrip({ role }: { role: Role | undefined }) {
  const location = useLocation();
  const stripRef = useRef<HTMLDivElement | null>(null);
  const [indicator, setIndicator] = useState<{ left: number; width: number } | null>(null);

  useLayoutEffect(() => {
    const strip = stripRef.current;
    if (!strip) return;
    const active = strip.querySelector<HTMLElement>("[data-tab-active='true']");
    if (!active) {
      setIndicator(null);
      return;
    }
    const stripRect = strip.getBoundingClientRect();
    const aRect = active.getBoundingClientRect();
    setIndicator({ left: aRect.left - stripRect.left, width: aRect.width });
  }, [location.pathname, role]);

  return (
    <div className="tab-strip" role="tablist" aria-label="Primary">
      <div className="tab-strip__inner" ref={stripRef}>
        {TABS.map((tab) => {
          const enabled = isTabEnabled(tab, role);
          const matches = tab.end
            ? location.pathname === tab.to
            : location.pathname === tab.to || location.pathname.startsWith(tab.to + "/");
          if (!enabled) {
            return (
              <span
                key={tab.to}
                className="tab tab--disabled"
                role="tab"
                aria-disabled="true"
                title={tab.disabledTooltip}
              >
                {tab.label}
              </span>
            );
          }
          return (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={tab.end}
              className={({ isActive }) => (isActive ? "tab tab--active" : "tab")}
              role="tab"
              data-tab-active={matches ? "true" : undefined}
            >
              {tab.label}
            </NavLink>
          );
        })}
        {indicator ? (
          <span
            className="tab-strip__indicator"
            style={{ transform: `translateX(${indicator.left}px)`, width: `${indicator.width}px` }}
            aria-hidden="true"
          />
        ) : null}
      </div>
    </div>
  );
}

export function Layout() {
  const { token, me } = useAuth();
  const location = useLocation();
  const role = me?.role as Role | undefined;
  const [pageKey, setPageKey] = useState(location.pathname);

  useEffect(() => {
    setPageKey(location.pathname);
  }, [location.pathname]);

  const isLoginPage = location.pathname === "/login";

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>

      {isLoginPage ? null : (
      <header className={token ? "site-header site-header--authed" : "site-header"}>
        <div className="site-header-bar">
          <div className="site-brand">
            <img className="site-brand__logo" src="/dropsort-logo.png" alt="" aria-hidden="true" />
            <div className="site-brand__text">
              <span className="site-brand__name">Dropsort</span>
              <span className="site-brand__tag">Document intelligence</span>
            </div>
          </div>
          <div className="site-header-actions">
            {token ? (
              <SettingsMenu />
            ) : (
              <NavLink className="nav-link" to="/login">
                Sign in
              </NavLink>
            )}
          </div>
        </div>
        {token ? <TabStrip role={role} /> : null}
      </header>
      )}

      <main id="main-content" className="site-main" tabIndex={-1}>
        <div key={pageKey} className="page-transition">
          <Outlet />
        </div>
      </main>
    </>
  );
}
