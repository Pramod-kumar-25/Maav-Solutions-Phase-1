export const API_URL = "http://localhost:8000/api/v1";

export const request = async (endpoint, options = {}) => {
  const token = localStorage.getItem("token");
  const headers = {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  let data;
  try {
    data = await response.json();
  } catch (e) {
    data = null;
  }

  if (!response.ok) {
    const errorMsg = data?.error?.message || data?.detail || "An error occurred";
    throw new Error(errorMsg);
  }

  return data;
};

export const loginAPI = async (email, password) => {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();
  if (!response.ok) {
    const errorMsg = data?.error?.message || data?.detail || "Login failed";
    throw new Error(errorMsg);
  }
  return data;
};
