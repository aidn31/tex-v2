const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001";

async function apiFetch<T>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, ...fetchOptions } = options;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...fetchOptions,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error: ${res.status}`);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

// --- Teams ---

export interface Team {
  id: string;
  name: string;
  level: string;
  created_at: string;
  updated_at: string;
}

export function listTeams(token: string): Promise<Team[]> {
  return apiFetch("/teams/", { token });
}

export function createTeam(
  token: string,
  data: { name: string; level: string }
): Promise<Team> {
  return apiFetch("/teams/", {
    method: "POST",
    token,
    body: JSON.stringify(data),
  });
}

export function deleteTeam(token: string, teamId: string): Promise<void> {
  return apiFetch(`/teams/${teamId}`, { method: "DELETE", token });
}

// --- Films ---

export interface Film {
  id: string;
  team_id: string;
  file_name: string;
  file_size_bytes: number;
  status: string;
  duration_seconds: number | null;
  chunk_count: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export function listFilms(token: string): Promise<Film[]> {
  return apiFetch("/films/", { token });
}
