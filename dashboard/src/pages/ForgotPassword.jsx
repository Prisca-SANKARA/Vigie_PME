import { useState } from "react";
import { Link } from "react-router-dom";
import { forgotPassword } from "../api";
import Logo from "../components/Logo";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await forgotPassword(email);
      setMessage(result.message);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-form" onSubmit={handleSubmit}>
        <Logo />
        <h1>Mot de passe oublié</h1>
        {message ? (
          <p className="success">{message}</p>
        ) : (
          <>
            <p className="subtitle">
              Entre ton email, on t'envoie un lien pour réinitialiser ton mot de passe.
            </p>
            {error && <p className="error">{error}</p>}
            <label htmlFor="forgot-email">
              Email
              <input
                id="forgot-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <button type="submit" disabled={submitting}>
              {submitting ? "Envoi..." : "Envoyer le lien"}
            </button>
          </>
        )}
        <p>
          <Link to="/login">&larr; Retour à la connexion</Link>
        </p>
      </form>
    </div>
  );
}
