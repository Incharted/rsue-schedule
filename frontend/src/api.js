import { reactive } from "vue";

export const auth = reactive({ user: null, ready: false, error: "" });
let csrfToken = "";
let pendingSession;

export async function refreshSession() {
  const response = await fetch("/api/auth/session/", {
    credentials: "same-origin",
  });
  if (!response.ok)
    throw new Error("Не удалось проверить сессию. Попробуйте позже.");
  const data = await response.json();
  auth.user = data.user;
  csrfToken = data.csrfToken;
  auth.ready = true;
  auth.error = "";
  return data;
}

export async function initializeSession() {
  if (auth.ready) return;
  if (!pendingSession)
    pendingSession = refreshSession().catch(() => {
      auth.error =
        "Сервис временно недоступен. Проверьте запуск сервера и обновите страницу.";
      auth.ready = true;
    });
  await pendingSession;
}

function errorMessage(data) {
  const labels = {
    username: "Логин",
    email: "Почта",
    full_name: "Имя",
    password1: "Пароль",
    password2: "Повтор пароля",
    group: "Группа",
  };
  if (data.errors)
    return Object.entries(data.errors)
      .map(
        ([field, messages]) =>
          (labels[field] || field) + ": " + messages.join(" "),
      )
      .join("\n");
  return (
    Object.values(data).flat().join(" ") || "Не удалось выполнить действие."
  );
}

export async function api(url, options = {}) {
  const method = options.method || "GET";
  const headers = { ...options.headers };
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    headers["X-CSRFToken"] = csrfToken;
    if (options.body) headers["Content-Type"] = "application/json";
  }
  let response;
  try {
    response = await fetch("/api/" + url, {
      ...options,
      method,
      headers,
      credentials: "same-origin",
    });
  } catch {
    throw new Error(
      "Нет связи с сервером. Проверьте подключение и повторите действие.",
    );
  }
  if (!response.ok) {
    const data = await response
      .json()
      .catch(() => ({ detail: "Сервер временно недоступен." }));
    if (response.status === 403 && !url.startsWith("auth/")) {
      await refreshSession().catch(() => {});
      if (!auth.user) window.dispatchEvent(new Event("session-expired"));
    }
    throw new Error(
      response.status >= 500
        ? "Сервер временно недоступен. Попробуйте позже."
        : errorMessage(data),
    );
  }
  if (response.status === 204) return null;
  const data = await response.json();
  if (data.csrfToken) {
    csrfToken = data.csrfToken;
    auth.user = data.user;
  }
  return data;
}

export async function signOut() {
  await api("auth/logout/", { method: "POST" });
  auth.user = null;
}
