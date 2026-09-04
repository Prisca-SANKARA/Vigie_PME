import { useState } from "react";
import { Link } from "react-router-dom";
import { changePassword } from "../api";
import PasswordInput from "../components/PasswordInput";
import { useAuth } from "../context/AuthContext";

export default function Settings() {
  const { token, client } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    setSubmitting(true);
    try {
      const result = await changePassword(currentPassword, newPassword, token);
      setMessage(result.message);
      setCurrentPassword("");
      setNewPassword("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <Link to="/">&larr; Retour au tableau de bord</Link>
      <header className="page-header">
        <div>
          <h1>Paramètres</h1>
          {client && <p className="subtitle">{client.company_name}</p>}
        </div>
      </header>

      <form className="form-card" onSubmit={handleSubmit}>
        <h2>Changer le mot de passe</h2>
        {message && <p className="success">{message}</p>}
        {error && <p className="error">{error}</p>}
        <PasswordInput
          id="current-password"
          label="Mot de passe actuel"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          required
        />
        <PasswordInput
          id="new-password-settings"
          label="Nouveau mot de passe"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          minLength={8}
          required
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Mise à jour..." : "Mettre à jour le mot de passe"}
        </button>
      </form>
    </div>
  );
}
