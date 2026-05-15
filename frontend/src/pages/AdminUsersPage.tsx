import { useCallback, useEffect, useState, type FormEvent } from "react";
import { apiFetch } from "../api/client";
import { getNetworkErrorMessage } from "../api/httpErrors";
import { routes } from "../api/routes";
import type { Role, RoleChangeIn, UserActiveIn, UserCreate, UserOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { ROLE_LABELS } from "../lib/roleLabels";
import { shortId } from "../lib/formatId";
import {
  DataEmpty,
  DataSkeleton,
  DataTable,
  PageSection,
} from "../components/data";
import type { DataTableColumn } from "../components/data/DataTable";
import { Button } from "../components/Button";
import { ErrorAlert } from "../components/ErrorAlert";
import { ListRefreshingHint } from "../components/ListRefreshingHint";
import { PageHeader } from "../components/PageHeader";
import { RefreshButton } from "../components/RefreshButton";
import { useApiErrorHandler } from "../hooks/useApiErrorHandler";

const ROLES: Role[] = ["admin", "reviewer", "auditor"];

/** Primary label for the admin directory (never shows internal `removed.<uuid>@…`). */
function adminDirectoryPrimaryLabel(u: UserOut): string {
  if (u.deleted_at) {
    if (u.original_email) {
      return `Removed account (${u.original_email})`;
    }
    return "Removed account";
  }
  return u.email;
}

function RolePill({ role }: { role: Role }) {
  return <span className={`role-pill role-pill--${role}`}>{ROLE_LABELS[role]}</span>;
}

function AccountStatusPill({ user }: { user: UserOut }) {
  if (user.deleted_at) {
    return <span className="account-status account-status--removed">Removed</span>;
  }
  if (!user.is_active) {
    return <span className="account-status account-status--inactive">Inactive</span>;
  }
  return <span className="account-status account-status--active">Active</span>;
}

const columns: DataTableColumn[] = [
  { id: "email", label: "Email" },
  { id: "role", label: "Access" },
  { id: "status", label: "Status" },
  { id: "created", label: "Joined" },
  { id: "id", label: "User ID" },
  { id: "manage", label: "Manage" },
];

type UserRoleEditorProps = {
  user: UserOut;
  onUpdated: () => Promise<void>;
};

function UserRoleEditor({ user, onUpdated }: UserRoleEditorProps) {
  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: true });
  const { me, refreshMe } = useAuth();
  const [role, setRole] = useState<Role>(user.role);
  const [saving, setSaving] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const locked =
    Boolean(user.deleted_at) || me?.id === user.id || user.role === "admin";

  useEffect(() => {
    setRole(user.role);
    setLocalError(null);
  }, [user.id, user.role]);

  const dirty = role !== user.role;

  async function save() {
    if (!dirty || locked) {
      return;
    }
    setSaving(true);
    setLocalError(null);
    try {
      const body: RoleChangeIn = { role };
      const res = await apiFetch(routes.adminUserRole(user.id), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      await assertOk(res);
      if (me?.id === user.id) {
        await refreshMe();
      }
      await onUpdated();
    } catch (e) {
      setLocalError(getNetworkErrorMessage(e) || "Could not update role.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="user-role-toolbar">
      <label className="sr-only" htmlFor={`role-${user.id}`}>
        Permissions for {adminDirectoryPrimaryLabel(user)}
      </label>
      <select
        id={`role-${user.id}`}
        className="select-tool"
        value={role}
        disabled={saving || locked}
        title={
          locked
            ? user.role === "admin"
              ? "Administrator access cannot be changed here."
              : "You cannot change your own access level here, or edit a removed account."
            : undefined
        }
        onChange={(ev) => setRole(ev.target.value as Role)}
      >
        {ROLES.map((r) => (
          <option key={r} value={r}>
            {ROLE_LABELS[r]}
          </option>
        ))}
      </select>
      <Button type="button" variant="muted" disabled={!dirty || saving || locked} onClick={() => void save()}>
        {saving ? "Saving…" : "Save access"}
      </Button>
      {localError ? (
        <span className="user-role-toolbar__err" role="alert">
          {localError}
        </span>
      ) : null}
    </div>
  );
}

type UserAccessToolbarProps = {
  user: UserOut;
  onUpdated: () => Promise<void>;
  onRequestRemove: (user: UserOut) => void;
};

function UserAccessToolbar({ user, onUpdated, onRequestRemove }: UserAccessToolbarProps) {
  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: true });
  const { me } = useAuth();
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const isSelf = me?.id === user.id;
  const removed = Boolean(user.deleted_at);
  const isTargetAdmin = user.role === "admin";

  async function setActive(next: boolean) {
    if (removed || isSelf || isTargetAdmin) {
      return;
    }
    setBusy(true);
    setLocalError(null);
    try {
      const body: UserActiveIn = { is_active: next };
      const res = await apiFetch(routes.adminUserActive(user.id), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      await assertOk(res);
      await onUpdated();
    } catch (e) {
      setLocalError(getNetworkErrorMessage(e) || "Could not update access.");
    } finally {
      setBusy(false);
    }
  }

  if (removed) {
    return <span className="muted user-access-toolbar__note">Account removed from directory</span>;
  }

  if (isSelf) {
    return <span className="muted user-access-toolbar__note">Use another administrator to change your access.</span>;
  }

  if (isTargetAdmin) {
    return (
      <span className="muted user-access-toolbar__note">Administrator accounts cannot be deactivated or removed here.</span>
    );
  }

  return (
    <div className="user-access-toolbar">
      {user.is_active ? (
        <Button type="button" variant="muted" disabled={busy} onClick={() => void setActive(false)}>
          {busy ? "Updating…" : "Deactivate access"}
        </Button>
      ) : (
        <>
          <Button type="button" variant="muted" disabled={busy} onClick={() => void setActive(true)}>
            {busy ? "Updating…" : "Reactivate access"}
          </Button>
          <Button type="button" variant="muted" className="btn--danger-quiet" disabled={busy} onClick={() => onRequestRemove(user)}>
            Remove account…
          </Button>
        </>
      )}
      {localError ? (
        <span className="user-access-toolbar__err" role="alert">
          {localError}
        </span>
      ) : null}
    </div>
  );
}

export function AdminUsersPage() {
  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: true });
  const [listPending, setListPending] = useState(true);
  const [rows, setRows] = useState<UserOut[] | null>(null);
  const [listError, setListError] = useState<string | null>(null);

  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteSecret, setInviteSecret] = useState("");
  const [inviteRole, setInviteRole] = useState<Role>("reviewer");
  const [invitePending, setInvitePending] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteSuccess, setInviteSuccess] = useState<string | null>(null);

  const [removeTarget, setRemoveTarget] = useState<UserOut | null>(null);
  const [removeBusy, setRemoveBusy] = useState(false);
  const [removeError, setRemoveError] = useState<string | null>(null);

  const loadList = useCallback(async () => {
    setListPending(true);
    setListError(null);
    try {
      const res = await apiFetch(routes.adminUsers);
      await assertOk(res);
      const data = (await res.json()) as UserOut[];
      setRows(data);
    } catch (e) {
      setRows(null);
      setListError(getNetworkErrorMessage(e));
    } finally {
      setListPending(false);
    }
  }, [assertOk]);

  useEffect(() => {
    void loadList();
  }, [loadList]);

  async function onInviteSubmit(e: FormEvent) {
    e.preventDefault();
    setInviteError(null);
    setInviteSuccess(null);
    const email = inviteEmail.trim();
    const initial_secret = inviteSecret;
    if (!email || !initial_secret) {
      setInviteError("Email and temporary password are required.");
      return;
    }
    setInvitePending(true);
    try {
      const body: UserCreate = { email, initial_secret, role: inviteRole };
      const res = await apiFetch(routes.adminUsersInvite, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      await assertOk(res);
      setInviteSuccess(`Account created for ${email}. Share the temporary password securely so they can sign in.`);
      setInviteEmail("");
      setInviteSecret("");
      setInviteRole("reviewer");
      await loadList();
    } catch (err) {
      setInviteError(getNetworkErrorMessage(err) || "Could not create account.");
    } finally {
      setInvitePending(false);
    }
  }

  async function confirmRemoveAccount() {
    if (!removeTarget) {
      return;
    }
    setRemoveBusy(true);
    setRemoveError(null);
    try {
      const res = await apiFetch(routes.adminUser(removeTarget.id), { method: "DELETE" });
      await assertOk(res);
      setRemoveTarget(null);
      await loadList();
    } catch (err) {
      setRemoveError(getNetworkErrorMessage(err) || "Could not remove account.");
    } finally {
      setRemoveBusy(false);
    }
  }

  const showSkeleton = listPending && rows === null;

  return (
    <div className="settings-section">
      <PageHeader
        title="Team & accounts"
        description="Provision workspace access and adjust permissions. Accounts are administrator-created only—there is no public signup. Share each temporary password through a secure channel."
        actions={<RefreshButton pending={listPending} onClick={() => void loadList()} />}
      />

      <PageSection
        title="Create account"
        description="Add someone to the workspace and choose their access level. They use the temporary password you set the first time they sign in."
      >
        <form className="panel admin-invite-form" onSubmit={(ev) => void onInviteSubmit(ev)}>
          <div className="admin-invite-grid">
            <div className="form-field">
              <label htmlFor="invite-email">Work email</label>
              <input
                id="invite-email"
                name="email"
                type="email"
                autoComplete="off"
                value={inviteEmail}
                onChange={(ev) => setInviteEmail(ev.target.value)}
                disabled={invitePending}
                required
              />
            </div>
            <div className="form-field">
              <label htmlFor="invite-secret">Temporary password</label>
              <input
                id="invite-secret"
                name="initial_secret"
                type="password"
                autoComplete="new-password"
                value={inviteSecret}
                onChange={(ev) => setInviteSecret(ev.target.value)}
                disabled={invitePending}
                required
              />
            </div>
            <div className="form-field">
              <label htmlFor="invite-role">Permissions</label>
              <p className="muted field-hint">
                Administrator: full workspace control. Reviewer: document corrections and model feedback. Auditor:
                read-only oversight.
              </p>
              <select
                id="invite-role"
                value={inviteRole}
                disabled={invitePending}
                onChange={(ev) => setInviteRole(ev.target.value as Role)}
              >
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {ROLE_LABELS[r]}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <ErrorAlert message={inviteError} />
          {inviteSuccess ? (
            <p className="alert alert--success" role="status">
              {inviteSuccess}
            </p>
          ) : null}
          <div className="form-actions">
            <Button type="submit" disabled={invitePending}>
              {invitePending ? "Creating…" : "Create account"}
            </Button>
          </div>
        </form>
      </PageSection>

      <PageSection
        title="Directory"
        description="Everyone who can sign in. Access determines which areas of the product they can use. Deactivate suspends sign-in; remove account frees the email for a future invite while keeping history intact."
      >
        <ListRefreshingHint show={listPending && rows !== null && rows.length > 0} />
        {showSkeleton ? <DataSkeleton rows={6} columns={6} /> : null}
        <ErrorAlert message={listError} />

        {!showSkeleton && rows && rows.length === 0 ? (
          <DataEmpty
            title="No accounts yet"
            description="Create the first account above. There is no self-service signup—each person is added by an administrator."
          />
        ) : null}

        {!showSkeleton && rows && rows.length > 0 ? (
          <DataTable className="data-table--interactive admin-users-table" columns={columns} aria-label="Team members">
            {rows.map((u) => (
              <tr key={u.id} className={u.deleted_at ? "admin-user-row admin-user-row--removed" : !u.is_active ? "admin-user-row admin-user-row--inactive" : undefined}>
                <td className="data-table-cell-strong">{adminDirectoryPrimaryLabel(u)}</td>
                <td>
                  <RolePill role={u.role} />
                </td>
                <td>
                  <AccountStatusPill user={u} />
                </td>
                <td className="data-table-cell-muted">{u.created_at}</td>
                <td>
                  <code className="audit-code" title={u.id}>
                    {shortId(u.id)}
                  </code>
                </td>
                <td className="admin-user-manage-cell">
                  <UserRoleEditor user={u} onUpdated={loadList} />
                  <UserAccessToolbar user={u} onUpdated={loadList} onRequestRemove={setRemoveTarget} />
                </td>
              </tr>
            ))}
          </DataTable>
        ) : null}
      </PageSection>

      {removeTarget ? (
        <div
          className="modal-backdrop"
          role="presentation"
          onClick={() => {
            if (!removeBusy) {
              setRemoveTarget(null);
            }
          }}
        >
          <div
            className="modal-card panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="remove-account-title"
            onClick={(ev) => ev.stopPropagation()}
          >
            <h2 id="remove-account-title" className="modal-card__title">
              Remove account
            </h2>
            <p className="modal-card__body">
              This permanently removes <strong>{adminDirectoryPrimaryLabel(removeTarget)}</strong> from the directory,
              revokes sign-in, and frees the address for a new invite. Audit history is preserved.
            </p>
            <ErrorAlert message={removeError} />
            <div className="modal-card__actions">
              <Button type="button" variant="muted" disabled={removeBusy} onClick={() => setRemoveTarget(null)}>
                Cancel
              </Button>
              <Button type="button" variant="muted" className="btn--danger-quiet" disabled={removeBusy} onClick={() => void confirmRemoveAccount()}>
                {removeBusy ? "Removing…" : "Remove account"}
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
