"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import { Film, Team, createTeam, listFilms, listTeams, seedUser } from "@/lib/api";

const LEVELS = [
  { value: "d1", label: "D1" },
  { value: "d2", label: "D2" },
  { value: "d3", label: "D3" },
  { value: "eybl", label: "EYBL" },
  { value: "aau", label: "AAU" },
  { value: "high_school", label: "High School" },
  { value: "unknown", label: "Unknown" },
];

export default function DashboardPage() {
  const { getToken } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [films, setFilms] = useState<Film[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Team modal state
  const [showModal, setShowModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newLevel, setNewLevel] = useState("unknown");
  const [creating, setCreating] = useState(false);

  async function loadData() {
    try {
      const token = await getToken();
      if (!token) return;

      // In local dev, ensure the user row exists before any API call.
      // This replaces the Clerk webhook which can't reach localhost.
      if (process.env.NODE_ENV === "development") {
        await seedUser(token).catch(() => {});
      }

      const [t, f] = await Promise.all([listTeams(token), listFilms(token)]);
      setTeams(t);
      setFilms(f);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleCreateTeam(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const token = await getToken();
      if (!token) return;
      await createTeam(token, { name: newName.trim(), level: newLevel });
      setShowModal(false);
      setNewName("");
      setNewLevel("unknown");
      await loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create team");
    } finally {
      setCreating(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }

  // No teams — onboarding state
  if (teams.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-20 text-center">
        <h1 className="text-3xl font-bold text-white">Welcome to TEX</h1>
        <p className="mt-4 text-gray-400">
          TEX analyzes game film and generates a PDF scouting report in 30–50
          minutes.
        </p>
        <div className="mt-8 space-y-4 text-left text-gray-300">
          <div className="flex items-start gap-3">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-bold text-black">
              1
            </span>
            <span>Create a team</span>
          </div>
          <div className="flex items-start gap-3">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-bold text-black">
              2
            </span>
            <span>Add a roster</span>
          </div>
          <div className="flex items-start gap-3">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-bold text-black">
              3
            </span>
            <span>Upload film</span>
          </div>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="mt-8 rounded-lg bg-brand px-6 py-3 font-semibold text-black hover:bg-orange-400"
        >
          Create Your First Team
        </button>
        {showModal && <NewTeamModal />}
      </div>
    );
  }

  // Has teams — main dashboard
  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <button
          onClick={() => setShowModal(true)}
          className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-black hover:bg-orange-400"
        >
          New Team
        </button>
      </div>

      {error && (
        <p className="mt-4 rounded bg-red-900/50 px-4 py-2 text-red-300">
          {error}
        </p>
      )}

      {/* Teams */}
      <h2 className="mt-8 text-lg font-semibold text-gray-300">Teams</h2>
      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {teams.map((team) => {
          const teamFilms = films.filter((f) => f.team_id === team.id);
          return (
            <a
              key={team.id}
              href={`/teams/${team.id}`}
              className="block rounded-lg border border-border bg-surface p-4 hover:border-brand"
            >
              <h3 className="font-semibold text-white">{team.name}</h3>
              <p className="mt-1 text-sm text-gray-400">
                {team.level.toUpperCase()} &middot; {teamFilms.length} film
                {teamFilms.length !== 1 ? "s" : ""}
              </p>
            </a>
          );
        })}
      </div>

      {/* Recent Films */}
      {films.length > 0 && (
        <>
          <h2 className="mt-10 text-lg font-semibold text-gray-300">
            Recent Films
          </h2>
          <div className="mt-4 space-y-2">
            {films.slice(0, 5).map((film) => (
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
        </>
      )}

      {showModal && <NewTeamModal />}
    </div>
  );

  function NewTeamModal() {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
        <form
          onSubmit={handleCreateTeam}
          className="w-full max-w-md rounded-lg border border-border bg-surface p-6"
        >
          <h2 className="text-lg font-semibold text-white">New Team</h2>
          <div className="mt-4">
            <label className="block text-sm text-gray-400">Team Name</label>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              maxLength={100}
              required
              className="mt-1 w-full rounded border border-border bg-background px-3 py-2 text-white focus:border-brand focus:outline-none"
              autoFocus
            />
          </div>
          <div className="mt-4">
            <label className="block text-sm text-gray-400">
              Competition Level
            </label>
            <select
              value={newLevel}
              onChange={(e) => setNewLevel(e.target.value)}
              className="mt-1 w-full rounded border border-border bg-background px-3 py-2 text-white focus:border-brand focus:outline-none"
            >
              {LEVELS.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>
          <div className="mt-6 flex justify-end gap-3">
            <button
              type="button"
              onClick={() => setShowModal(false)}
              className="rounded px-4 py-2 text-sm text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={creating || !newName.trim()}
              className="rounded bg-brand px-4 py-2 text-sm font-semibold text-black hover:bg-orange-400 disabled:opacity-50"
            >
              {creating ? "Creating..." : "Create Team"}
            </button>
          </div>
        </form>
      </div>
    );
  }
}
