import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function Layout() {
  const { token, logout } = useAuth();

  return (
    <>
      <header>
        <nav>
          <strong>dropsort</strong>

          <Link to="/">Home</Link>

          <Link to="/login">Login</Link>

          {token ? (
            <button type="button" onClick={logout}>
              Log out
            </button>
          ) : null}
        </nav>
      </header>

      <Outlet />
    </>
  );
}