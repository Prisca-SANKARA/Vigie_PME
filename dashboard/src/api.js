const API_BASE_URL = "http://127.0.0.1:8000";

async function request(path, { method = "GET", body, token, form } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body && !form) headers["Content-Type"] = "application/json";

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: form ? body : body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "Une erreur est survenue");
  }

  return response.status === 204 ? null : response.json();
}

export function register({ email, password, companyName }) {
  return request("/auth/register", {
    method: "POST",
    body: { email, password, company_name: companyName },
  });
}

export function login({ email, password }) {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  return request("/auth/login", { method: "POST", body: form, form: true });
}

export function fetchMe(token) {
  return request("/auth/me", { token });
}

export function createScan(target, token) {
  return request("/scans", { method: "POST", body: { target }, token });
}

export function listScans(token) {
  return request("/scans", { token });
}

export function getScanDetail(scanId, token) {
  return request(`/scans/detail/${scanId}`, { token });
}
