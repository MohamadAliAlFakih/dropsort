import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { RequireAuth } from "./components/RequireAuth";
import { AuditPage } from "./pages/AuditPage";
import { BatchDetailPage } from "./pages/BatchDetailPage";
import { BatchesPage } from "./pages/BatchesPage";
import { ForbiddenPage } from "./pages/ForbiddenPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { MePage } from "./pages/MePage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PredictionsRecentPage } from "./pages/PredictionsRecentPage";

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
              <MePage />
            </RequireAuth>
          }
        />
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
