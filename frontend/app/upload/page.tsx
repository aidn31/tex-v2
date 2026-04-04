"use client";

import { useAuth } from "@clerk/nextjs";
import { useSearchParams } from "next/navigation";
import { useCallback, useRef, useState } from "react";
import {
  filmUploadAbort,
  filmUploadComplete,
  filmUploadInitiate,
} from "@/lib/api";

type Step = "select" | "uploading" | "done" | "error";

export default function UploadPage() {
  const { getToken } = useAuth();
  const searchParams = useSearchParams();
  const teamId = searchParams.get("team_id");

  const [step, setStep] = useState<Step>("select");
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [filmId, setFilmId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = useCallback((f: File) => {
    const validTypes = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"];
    if (!validTypes.includes(f.type) && !f.name.match(/\.(mp4|mov|avi|webm)$/i)) {
      setError("Invalid file type. Please upload MP4, MOV, AVI, or WebM.");
      return;
    }
    setFile(f);
    setError(null);
  }, []);

  async function handleUpload() {
    if (!file || !teamId) return;
    setStep("uploading");
    setProgress(0);
    setError(null);

    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      // Step 1: Initiate — get presigned URL
      const { film_id, upload_url } = await filmUploadInitiate(token, {
        team_id: teamId,
        file_name: file.name,
        file_size_bytes: file.size,
      });
      setFilmId(film_id);

      // Step 2: Upload directly to R2
      const xhr = new XMLHttpRequest();
      await new Promise<void>((resolve, reject) => {
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            setProgress(Math.round((e.loaded / e.total) * 100));
          }
        });
        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve();
          } else {
            reject(new Error(`Upload failed: ${xhr.status}`));
          }
        });
        xhr.addEventListener("error", () => reject(new Error("Upload failed")));
        xhr.open("PUT", upload_url);
        xhr.setRequestHeader("Content-Type", file.type || "application/octet-stream");
        xhr.send(file);
      });

      // Step 3: Confirm upload complete
      await filmUploadComplete(token, film_id);
      setStep("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
      setStep("error");

      // Abort the film record if we got a film_id
      if (filmId) {
        try {
          const token = await getToken();
          if (token) await filmUploadAbort(token, filmId);
        } catch {
          // best effort cleanup
        }
      }
    }
  }

  if (!teamId) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-20 text-center">
        <p className="text-gray-400">No team selected.</p>
        <a href="/dashboard" className="mt-4 inline-block text-brand">
          Go to Dashboard
        </a>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-20">
      <a
        href={`/teams/${teamId}`}
        className="text-sm text-gray-400 hover:text-white"
      >
        &larr; Back to team
      </a>
      <h1 className="mt-4 text-2xl font-bold text-white">Upload Game Film</h1>

      {step === "select" && (
        <div className="mt-8">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              const f = e.dataTransfer.files[0];
              if (f) handleFile(f);
            }}
            onClick={() => fileInputRef.current?.click()}
            className={`cursor-pointer rounded-lg border-2 border-dashed p-12 text-center ${
              dragOver ? "border-brand bg-brand/10" : "border-border"
            }`}
          >
            <p className="text-gray-300">
              Drag and drop your game film here, or click to browse
            </p>
            <p className="mt-2 text-sm text-gray-500">
              MP4, MOV, AVI, or WebM
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
              }}
            />
          </div>

          {file && (
            <div className="mt-4 rounded-lg border border-border bg-surface p-4">
              <p className="font-medium text-white">{file.name}</p>
              <p className="text-sm text-gray-400">
                {(file.size / 1_000_000).toFixed(0)} MB
              </p>
              <button
                onClick={handleUpload}
                className="mt-4 rounded bg-brand px-6 py-2 font-semibold text-black hover:bg-orange-400"
              >
                Upload
              </button>
            </div>
          )}

          {error && (
            <p className="mt-4 rounded bg-red-900/50 px-4 py-2 text-red-300">
              {error}
            </p>
          )}
        </div>
      )}

      {step === "uploading" && (
        <div className="mt-8">
          <p className="text-gray-300">
            Uploading {file?.name}... {progress}%
          </p>
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-border">
            <div
              className="h-full rounded-full bg-brand transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="mt-2 text-sm text-gray-500">
            Do not close this page until the upload is complete.
          </p>
        </div>
      )}

      {step === "done" && (
        <div className="mt-8 text-center">
          <p className="text-lg text-white">
            Film uploaded. TEX is processing your film — this takes 10–20
            minutes.
          </p>
          <a
            href="/dashboard"
            className="mt-6 inline-block rounded bg-brand px-6 py-2 font-semibold text-black hover:bg-orange-400"
          >
            Go to Dashboard
          </a>
        </div>
      )}

      {step === "error" && (
        <div className="mt-8">
          <p className="rounded bg-red-900/50 px-4 py-2 text-red-300">
            {error}
          </p>
          <button
            onClick={() => {
              setStep("select");
              setFile(null);
              setProgress(0);
              setError(null);
              setFilmId(null);
            }}
            className="mt-4 rounded border border-border px-4 py-2 text-sm text-gray-300 hover:text-white"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
