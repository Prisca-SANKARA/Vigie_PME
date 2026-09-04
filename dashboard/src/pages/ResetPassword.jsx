import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { resetPassword } from "../api";
import Logo from "../components/Logo";
import PasswordInput from "../components/PasswordInput";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token") || "";

  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await resetPassword(token, newPassword);
      setMessage(result.message);
      setTimeout(() => navigate("/login"), 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (!token) {
    return (
      <div className="auth-page">
        <div className="auth-form">
          <Logo />
          <h1>Lien invalide</h1>
          <p className="error">Ce lien de réinitialisation est incomplet ou invalide.</p>
          <p>
            <Link to="/forgot-password">Demander un nouveau lien</Link>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <form className="auth-form" onSubmit={handleSubmit}>
        <Logo />
        <h1>Nouveau mot de passe</h1>
        {message ? (
          <p className="success">{message} Redirection vers la connexion...</p>
        ) : (
          <>
            {error && <p className="error">{error}</p>}
            <PasswordInput
              id="new-password"
              label="Nouveau mot de passe"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              minLength={8}
              required
            />
            <button type="submit" disabled={submitting}>
              {submitting ? "Réinitialisation..." : "Réinitialiser le mot de passe"}
            </button>
          </>
        )}
      </form>
    </div>
  );
}
