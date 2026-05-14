import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { RequireAuth } from "./components/RequireAuth";
import { RequireAdmin } from "./components/RequireAdmin";
import { AdminUsersPage } from "./pages/AdminUsersPage";
import { AuditPage } from "./pages/AuditPage";
import { BatchDetailPage } from "./pages/BatchDetailPage";
import { BatchesPage } from "./pages/BatchesPage";
import { ForbiddenPage } from "./pages/ForbiddenPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PredictionsRecentPage } from "./pages/PredictionsRecentPage";
import { SettingsAccountPage } from "./pages/SettingsAccountPage";
import { SettingsLayout } from "./pages/SettingsLayout";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/me"
          element={
            <RequireAuth>
              <Navigate to="/settings/account" replace />
            </RequireAuth>
          }
        />
        <Route
          path="settings"
          element={
            <RequireAuth>
              <SettingsLayout />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/settings/account" replace />} />
          <Route path="account" element={<SettingsAccountPage />} />
          <Route
            path="admin/users"
            element={
              <RequireAdmin>
                <AdminUsersPage />
              </RequireAdmin>
            }
          />
        </Route>
        <Route path="/admin/users" element={<Navigate to="/settings/admin/users" replace />} />
        <Route
          path="/batches"
          element={
            <RequireAuth>
              <BatchesPage />
            </RequireAuth>
          }
        />
        <Route
          path="/batches/:id"
          element={
            <RequireAuth>
              <BatchDetailPage />
            </RequireAuth>
          }
        />
        <Route
          path="/predictions/recent"
          element={
            <RequireAuth>
              <PredictionsRecentPage />
            </RequireAuth>
          }
        />
        <Route
          path="/audit"
          element={
            <RequireAuth>
              <AuditPage />
            </RequireAuth>
          }
        />
        <Route path="/forbidden" element={<ForbiddenPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
