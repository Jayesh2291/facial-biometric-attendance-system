import { useCallback, useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

function formatTimestamp(ts) {
  const date = new Date(ts.replace(" ", "T"));
  if (Number.isNaN(date.getTime())) return ts;
  return date.toLocaleString();
}

export default function App() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | scanning | done | error
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [history, setHistory] = useState([]);
  const [knownFaces, setKnownFaces] = useState([]);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/attendance`);
      const data = await res.json();
      setHistory(data.records || []);
    } catch {
      // Backend not reachable yet; leave history as-is.
    }
  }, []);

  const fetchKnownFaces = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/known`);
      const data = await res.json();
      setKnownFaces(data.known_faces || []);
    } catch {
      // Backend not reachable yet.
    }
  }, []);

  useEffect(() => {
    fetchHistory();
    fetchKnownFaces();
  }, [fetchHistory, fetchKnownFaces]);

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setFile(selected);
    setResult(null);
    setErrorMessage("");
    setStatus("idle");
    setPreviewUrl(URL.createObjectURL(selected));
  };

  const handleScan = async () => {
    if (!file) return;
    setStatus("scanning");
    setErrorMessage("");
    setResult(null);

    const formData = new FormData();
    formData.append("image", file);

    try {
      const res = await fetch(`${API_BASE}/detect`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (!res.ok) {
        setStatus("error");
        setErrorMessage(data.error || "Detection failed.");
        return;
      }

      setResult(data);
      setStatus("done");
      fetchHistory();
    } catch {
      setStatus("error");
      setErrorMessage("Could not reach the backend. Is it running?");
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Face Attendance System</h1>
        <p className="subtitle">
          Upload a photo to scan for known faces and log attendance.
        </p>
      </header>

      <main className="main-grid">
        <section className="panel">
          <h2>Scan</h2>

          <label className="upload-box" htmlFor="image-input">
            {previewUrl ? (
              <img src={previewUrl} alt="Selected preview" className="preview" />
            ) : (
              <span>Click to choose an image</span>
            )}
          </label>
          <input
            id="image-input"
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            hidden
          />

          <button
            type="button"
            className="scan-button"
            onClick={handleScan}
            disabled={!file || status === "scanning"}
          >
            {status === "scanning" ? "Scanning..." : "Scan Image"}
          </button>

          {status === "error" && <p className="status-error">{errorMessage}</p>}

          {status === "done" && result && (
            <div className="result-box">
              <p>
                Detected {result.detected_faces} face
                {result.detected_faces === 1 ? "" : "s"}:
              </p>
              <ul>
                {result.attendance.map((name, i) => (
                  <li
                    key={`${name}-${i}`}
                    className={name === "Unknown" ? "name-unknown" : "name-known"}
                  >
                    {name}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        <section className="panel">
          <h2>Known Faces ({knownFaces.length})</h2>
          {knownFaces.length === 0 ? (
            <p className="muted">
              No known faces registered yet. Add images to{" "}
              <code>backend/faces/</code> and restart the backend.
            </p>
          ) : (
            <ul className="chip-list">
              {knownFaces.map((name) => (
                <li key={name} className="chip">
                  {name}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="panel panel-wide">
          <h2>Recent Attendance</h2>
          {history.length === 0 ? (
            <p className="muted">No attendance recorded yet.</p>
          ) : (
            <table className="history-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {history.map((record, i) => (
                  <tr key={`${record.name}-${record.timestamp}-${i}`}>
                    <td className={record.name === "Unknown" ? "name-unknown" : "name-known"}>
                      {record.name}
                    </td>
                    <td>{formatTimestamp(record.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </main>
    </div>
  );
}
