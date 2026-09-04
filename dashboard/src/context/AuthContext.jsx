import { createContext, useContext, useEffect, useState } from "react";
import { fetchMe, login as apiLogin, register as apiRegister } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    fetchMe(token)
      .then(setClient)
      .catch(() => {
        localStorage.removeItem("token");
        setToken(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  async function login(email, password) {
    const { access_token } = await apiLogin({ email, password });
    localStorage.setItem("token", access_token);
    setToken(access_token);
  }

  async function register(email, password, companyName) {
    const { access_token } = await apiRegister({ email, password, companyName });
    localStorage.setItem("token", access_token);
    setToken(access_token);
  }

  function logout() {
    localStorage.removeItem("token");
    setToken(null);
    setClient(null);
  }

  return (
    <AuthContext.Provider value={{ token, client, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
