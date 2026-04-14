"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import { seedUser } from "@/lib/api";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { getToken } = useAuth();
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null);

  useEffect(() => {
    async function check() {
      const token = await getToken();
      if (!token) return;
      // In dev, ensure user row exists
      if (process.env.NODE_ENV === "development") {
        await seedUser(token).catch(() => {});
      }
      // Check admin status by calling any admin route
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001"}/admin/users`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setIsAdmin(res.ok);
      } catch {
        setIsAdmin(false);
      }
    }
    check();
  }, []);

  if (isAdmin === null) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-gray-400">Checking access...</p>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-20 text-center">
        <h1 className="text-2xl font-bold text-red-400">Access Denied</h1>
        <p className="mt-4 text-gray-400">Admin access required.</p>
        <a href="/dashboard" className="mt-4 inline-block text-brand">
          Go to Dashboard
        </a>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <h1 className="text-xl font-bold text-white">TEX Admin</h1>
        <nav className="flex gap-4">
          <a href="/admin" className="text-sm text-gray-400 hover:text-white">
            Corrections
          </a>
          <a
            href="/admin/patterns"
            className="text-sm text-gray-400 hover:text-white"
          >
            Patterns
          </a>
          <a
            href="/admin/users"
            className="text-sm text-gray-400 hover:text-white"
          >
            Users
          </a>
          <a href="/dashboard" className="text-sm text-gray-400 hover:text-white">
            Dashboard
          </a>
        </nav>
      </div>
      <div className="mt-6">{children}</div>
    </div>
  );
}
