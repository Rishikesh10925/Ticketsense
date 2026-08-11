import { useEffect, useState, type FormEvent } from "react";
import { fetchHealth, type HealthResponse } from "../api/client";

export default function TicketSubmission() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [attachment, setAttachment] = useState<File | null>(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err: Error) => setHealthError(err.message));
  }, []);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    alert("Ticket submission isn't wired to the backend yet — this is a Phase 1 placeholder.");
  }

  return (
    <main style={{ maxWidth: 640, margin: "2rem auto", fontFamily: "system-ui, sans-serif" }}>
      <h1>TicketSense</h1>

      <p>
        Backend status:{" "}
        {health ? (
          <strong style={{ color: health.database === "ok" ? "green" : "orange" }}>
            {health.status} (db: {health.database})
          </strong>
        ) : healthError ? (
          <strong style={{ color: "red" }}>unreachable ({healthError})</strong>
        ) : (
          "checking..."
        )}
      </p>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "1rem" }}>
          <label htmlFor="subject">Subject</label>
          <br />
          <input
            id="subject"
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            required
            style={{ width: "100%" }}
          />
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label htmlFor="description">Description</label>
          <br />
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
            rows={6}
            style={{ width: "100%" }}
          />
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label htmlFor="attachment">Attachment (image or PDF/log, optional)</label>
          <br />
          <input
            id="attachment"
            type="file"
            accept="image/*,.pdf,.log,.txt"
            onChange={(e) => setAttachment(e.target.files?.[0] ?? null)}
          />
          {attachment && <p>Selected: {attachment.name}</p>}
        </div>

        <button type="submit">Submit ticket</button>
      </form>
    </main>
  );
}
