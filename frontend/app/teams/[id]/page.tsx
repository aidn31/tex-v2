"use client";

import { useAuth } from "@clerk/nextjs";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Film,
  RosterPlayer,
  Team,
  createPlayer,
  deletePlayer,
  deleteTeam,
  getTeam,
  listFilms,
  listRoster,
  updatePlayer,
  updateTeam,
} from "@/lib/api";

type Tab = "roster" | "films" | "reports";

export default function TeamPage() {
  const { id } = useParams<{ id: string }>();
  const { getToken } = useAuth();
  const router = useRouter();

  const [team, setTeam] = useState<Team | null>(null);
  const [roster, setRoster] = useState<RosterPlayer[]>([]);
  const [films, setFilms] = useState<Film[]>([]);
  const [tab, setTab] = useState<Tab>("roster");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Edit team state
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editLevel, setEditLevel] = useState("");

  // Add player state
  const [adding, setAdding] = useState(false);
  const [newJersey, setNewJersey] = useState("");
  const [newFullName, setNewFullName] = useState("");
  const [newPosition, setNewPosition] = useState("");

  async function loadData() {
    try {
      const token = await getToken();
      if (!token) return;
      const [t, r, f] = await Promise.all([
        getTeam(token, id),
        listRoster(token, id),
        listFilms(token),
      ]);
      setTeam(t);
      setRoster(r);
      setFilms(f.filter((film) => film.team_id === id));
      setEditName(t.name);
      setEditLevel(t.level);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load team");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [id]);

  async function handleSaveTeam() {
    const token = await getToken();
    if (!token || !team) return;
    try {
      const updated = await updateTeam(token, team.id, {
        name: editName,
        level: editLevel,
      });
      setTeam(updated);
      setEditing(false);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update team");
    }
  }

  async function handleDeleteTeam() {
    if (!confirm(`Delete ${team?.name}? This cannot be undone.`)) return;
    const token = await getToken();
    if (!token || !team) return;
    try {
      await deleteTeam(token, team.id);
      router.push("/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete team");
    }
  }

  async function handleAddPlayer(e: React.FormEvent) {
    e.preventDefault();
    if (!newJersey.trim() || !newFullName.trim()) return;
    const token = await getToken();
    if (!token) return;
    try {
      await createPlayer(token, {
        team_id: id,
        jersey_number: newJersey.trim(),
        full_name: newFullName.trim(),
        position: newPosition || undefined,
      });
      setAdding(false);
      setNewJersey("");
      setNewFullName("");
      setNewPosition("");
      await loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add player");
    }
  }

  async function handleDeletePlayer(player: RosterPlayer) {
    if (!confirm(`Remove #${player.jersey_number} ${player.full_name}?`))
      return;
    const token = await getToken();
    if (!token) return;
    try {
      await deletePlayer(token, player.id);
      await loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to remove player");
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }

  if (!team) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-20 text-center">
        <p className="text-gray-400">Team not found.</p>
        <a href="/dashboard" className="mt-4 inline-block text-brand">
          Go to Dashboard
        </a>
      </div>
    );
  }

  const LEVELS = ["d1", "d2", "d3", "eybl", "aau", "high_school", "unknown"];

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          {editing ? (
            <div className="flex items-center gap-3">
              <input
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="rounded border border-border bg-background px-3 py-1 text-xl font-bold text-white focus:border-brand focus:outline-none"
                autoFocus
                onKeyDown={(e) => e.key === "Enter" && handleSaveTeam()}
              />
              <select
                value={editLevel}
                onChange={(e) => setEditLevel(e.target.value)}
                className="rounded border border-border bg-background px-2 py-1 text-sm text-white"
              >
                {LEVELS.map((l) => (
                  <option key={l} value={l}>
                    {l.toUpperCase()}
                  </option>
                ))}
              </select>
              <button
                onClick={handleSaveTeam}
                className="rounded bg-brand px-3 py-1 text-sm font-semibold text-black"
              >
                Save
              </button>
              <button
                onClick={() => setEditing(false)}
                className="text-sm text-gray-400"
              >
                Cancel
              </button>
            </div>
          ) : (
            <div>
              <h1 className="text-2xl font-bold text-white">{team.name}</h1>
              <p className="text-sm text-gray-400">
                {team.level.toUpperCase()}
              </p>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          {!editing && (
            <button
              onClick={() => setEditing(true)}
              className="rounded border border-border px-3 py-1.5 text-sm text-gray-300 hover:text-white"
            >
              Edit Team
            </button>
          )}
          <button
            onClick={handleDeleteTeam}
            className="rounded border border-red-800 px-3 py-1.5 text-sm text-red-400 hover:bg-red-900/30"
          >
            Delete Team
          </button>
          <a
            href="/dashboard"
            className="rounded border border-border px-3 py-1.5 text-sm text-gray-300 hover:text-white"
          >
            Back
          </a>
        </div>
      </div>

      {error && (
        <p className="mt-4 rounded bg-red-900/50 px-4 py-2 text-red-300">
          {error}
        </p>
      )}

      {/* Tabs */}
      <div className="mt-8 flex gap-6 border-b border-border">
        {(["roster", "films", "reports"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`pb-2 text-sm font-medium capitalize ${
              tab === t
                ? "border-b-2 border-brand text-brand"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="mt-6">
        {tab === "roster" && (
          <div>
            {roster.length > 0 ? (
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border text-gray-400">
                    <th className="pb-2 pr-4">#</th>
                    <th className="pb-2 pr-4">Name</th>
                    <th className="pb-2 pr-4">Position</th>
                    <th className="pb-2 pr-4">Height</th>
                    <th className="pb-2 pr-4">Role</th>
                    <th className="pb-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {roster.map((p) => (
                    <tr key={p.id} className="border-b border-border/50">
                      <td className="py-2 pr-4 text-white">
                        {p.jersey_number}
                      </td>
                      <td className="py-2 pr-4 text-white">{p.full_name}</td>
                      <td className="py-2 pr-4 text-gray-300">
                        {p.position || "—"}
                      </td>
                      <td className="py-2 pr-4 text-gray-300">
                        {p.height || "—"}
                      </td>
                      <td className="py-2 pr-4 text-gray-300">
                        {p.role || "—"}
                      </td>
                      <td className="py-2">
                        <button
                          onClick={() => handleDeletePlayer(p)}
                          className="text-red-400 hover:text-red-300"
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-gray-400">
                No players yet. Add your roster so TEX can identify players in
                the film.
              </p>
            )}

            {adding ? (
              <form
                onSubmit={handleAddPlayer}
                className="mt-4 flex items-end gap-3"
              >
                <div>
                  <label className="block text-xs text-gray-400">#</label>
                  <input
                    value={newJersey}
                    onChange={(e) => setNewJersey(e.target.value)}
                    className="w-16 rounded border border-border bg-background px-2 py-1 text-sm text-white"
                    required
                    autoFocus
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-400">Name</label>
                  <input
                    value={newFullName}
                    onChange={(e) => setNewFullName(e.target.value)}
                    className="w-48 rounded border border-border bg-background px-2 py-1 text-sm text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-400">
                    Position
                  </label>
                  <input
                    value={newPosition}
                    onChange={(e) => setNewPosition(e.target.value)}
                    placeholder="PG, SG, SF..."
                    className="w-24 rounded border border-border bg-background px-2 py-1 text-sm text-white"
                  />
                </div>
                <button
                  type="submit"
                  className="rounded bg-brand px-3 py-1 text-sm font-semibold text-black"
                >
                  Add
                </button>
                <button
                  type="button"
                  onClick={() => setAdding(false)}
                  className="text-sm text-gray-400"
                >
                  Cancel
                </button>
              </form>
            ) : (
              <button
                onClick={() => setAdding(true)}
                className="mt-4 rounded border border-border px-3 py-1.5 text-sm text-gray-300 hover:text-white"
              >
                Add Player
              </button>
            )}
          </div>
        )}

        {tab === "films" && (
          <div>
            {films.length > 0 ? (
              <div className="space-y-2">
                {films.map((film) => (
                  <div
                    key={film.id}
                    className="flex items-center justify-between rounded-lg border border-border bg-surface px-4 py-3"
                  >
                    <div>
                      <p className="text-sm font-medium text-white">
                        {film.file_name}
                      </p>
                      <p className="text-xs text-gray-400">
                        {(film.file_size_bytes / 1_000_000).toFixed(0)} MB
                        {film.duration_seconds &&
                          ` · ${Math.round(film.duration_seconds / 60)} min`}
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        film.status === "processed"
                          ? "bg-green-900 text-green-300"
                          : film.status === "error"
                            ? "bg-red-900 text-red-300"
                            : "bg-yellow-900 text-yellow-300"
                      }`}
                    >
                      {film.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400">
                No films uploaded yet for this team.
              </p>
            )}
            <a
              href={`/upload?team_id=${id}`}
              className="mt-4 inline-block rounded bg-brand px-4 py-2 text-sm font-semibold text-black hover:bg-orange-400"
            >
              Upload Film
            </a>
          </div>
        )}

        {tab === "reports" && (
          <div>
            <p className="text-gray-400">
              No reports generated yet. Upload a film and generate your first
              scouting report.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
