import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getScanDetail } from "../api";
import ScoreBadge from "../components/ScoreBadge";
import { useAuth } from "../context/AuthContext";

const SEVERITY_LABEL = {
  INFO: "Info",
  LOW: "Faible",
  MEDIUM: "Moyen",
  HIGH: "Élevé",
  CRITICAL: "Critique",
};

export default function ScanDetail() {
  const { scanId } = useParams();
  const { token } = useAuth();
  const [scan, setScan] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getScanDetail(scanId, token)
      .then(setScan)
      .catch((err) => setError(err.message));
  }, [scanId, token]);

  if (error) return <p className="error">{error}</p>;
  if (!scan) return <p className="page-loading">Chargement...</p>;

  return (
    <div className="page">
      <Link to="/">&larr; Retour au tableau de bord</Link>
      <header className="page-header">
        <h1>{scan.target}</h1>
        <ScoreBadge score={scan.score} />
      </header>
      <p className="subtitle">{new Date(scan.created_at).toLocaleString("fr-FR")}</p>

      {scan.findings.length === 0 ? (
        <p className="empty">Aucun problème détecté sur ce scan.</p>
      ) : (
        <ul className="findings-list">
          {scan.findings.map((finding, index) => (
            <li key={index} className={`finding finding-${finding.severity.toLowerCase()}`}>
              <div className="finding-header">
                <span className="finding-severity">{SEVERITY_LABEL[finding.severity]}</span>
                <span className="finding-title">{finding.title}</span>
              </div>
              <p className="finding-detail">{finding.detail}</p>
              <p className="finding-recommendation">
                <strong>Recommandation :</strong> {finding.recommendation}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
