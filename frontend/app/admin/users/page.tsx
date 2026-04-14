"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import { AdminUser, grantCredits, listAdminUsers } from "@/lib/api";

export default function AdminUsersPage() {
  const { getToken } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Credit grant state
  const [grantingFor, setGrantingFor] = useState<string | null>(null);
  const [creditAmount, setCreditAmount] = useState(1);

  async function loadUsers() {
    try {
      const token = await getToken();
      if (!token) return;
      const data = await listAdminUsers(token);
      setUsers(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers();
  }, []);

  async function handleGrant(userId: string) {
    const token = await getToken();
    if (!token) return;
    try {
      const result = await grantCredits(token, userId, creditAmount);
      setUsers((prev) =>
        prev.map((u) =>
          u.id === userId
            ? { ...u, report_credits: result.new_balance }
            : u
        )
      );
      setGrantingFor(null);
      setCreditAmount(1);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to grant credits");
    }
  }

  if (loading) {
    return <p className="text-gray-400">Loading users...</p>;
  }

  return (
    <div>
      <h2 className="text-lg font-semibold text-white">
        Users ({users.length})
      </h2>

      {error && (
        <p className="mt-3 rounded bg-red-900/50 px-4 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      <table className="mt-4 w-full text-left text-sm">
        <thead>
          <tr className="border-b border-border text-gray-400">
            <th className="pb-2 pr-4">Email</th>
            <th className="pb-2 pr-4 text-right">Reports</th>
            <th className="pb-2 pr-4 text-right">Credits</th>
            <th className="pb-2 pr-4">Joined</th>
            <th className="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id} className="border-b border-border/50">
              <td className="py-2 pr-4 text-white">
                {u.email}
                {u.is_admin && (
                  <span className="ml-2 rounded bg-brand/20 px-1.5 py-0.5 text-xs text-brand">
                    admin
                  </span>
                )}
              </td>
              <td className="py-2 pr-4 text-right text-gray-300">
                {u.report_count}
              </td>
              <td className="py-2 pr-4 text-right text-gray-300">
                {u.report_credits}
              </td>
              <td className="py-2 pr-4 text-gray-400">
                {new Date(u.created_at).toLocaleDateString()}
              </td>
              <td className="py-2">
                {grantingFor === u.id ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min={1}
                      value={creditAmount}
                      onChange={(e) =>
                        setCreditAmount(parseInt(e.target.value) || 1)
                      }
                      className="w-16 rounded border border-border bg-background px-2 py-0.5 text-sm text-white"
                    />
                    <button
                      onClick={() => handleGrant(u.id)}
                      className="rounded bg-brand px-2 py-0.5 text-xs font-semibold text-black"
                    >
                      Grant
                    </button>
                    <button
                      onClick={() => setGrantingFor(null)}
                      className="text-xs text-gray-500"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setGrantingFor(u.id)}
                    className="text-xs text-gray-400 hover:text-white"
                  >
                    Add Credits
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
