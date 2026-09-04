import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { createScan, listScans } from "../api";
import ScoreBadge from "../components/ScoreBadge";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { token, client, logout } = useAuth();
  const [scans, setScans] = useState([]);
  const [target, setTarget] = useState("");
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    refreshScans();
  }, []);

  function refreshScans() {
    listScans(token).then(setScans).catch((err) => setError(err.message));
  }

  async function handleScan(event) {
    event.preventDefault();
    setError("");
    setScanning(true);
    try {
      await createScan(target, token);
      setTarget("");
      refreshScans();
    } catch (err) {
      setError(err.message);
    } finally {
      setScanning(false);
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Tableau de bord sécurité</h1>
          {client && <p className="subtitle">{client.company_name}</p>}
        </div>
        <div className="page-header-actions">
          <Link to="/settings">
            <button type="button" className="secondary">
              Paramètres
            </button>
          </Link>
          <button className="secondary" onClick={logout}>
            Déconnexion
          </button>
        </div>
      </header>

      <form className="scan-form" onSubmit={handleScan}>
        <input
          type="text"
          placeholder="ex. exemple.com"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          required
        />
        <button type="submit" disabled={scanning}>
          {scanning ? "Scan en cours..." : "Lancer un scan"}
        </button>
      </form>
      {error && <p className="error">{error}</p>}

      <table className="scan-table">
        <thead>
          <tr>
            <th>Domaine</th>
            <th>Score</th>
            <th>Date</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {scans.length === 0 && (
            <tr>
              <td colSpan={4} className="empty">
                Aucun scan pour l'instant — lance ta première vérification ci-dessus.
              </td>
            </tr>
          )}
          {scans.map((scan) => (
            <tr key={scan.id}>
              <td>{scan.target}</td>
              <td>
                <ScoreBadge score={scan.score} />
              </td>
              <td>{new Date(scan.created_at).toLocaleString("fr-FR")}</td>
              <td>
                <Link to={`/scans/${scan.id}`}>Voir le rapport</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
