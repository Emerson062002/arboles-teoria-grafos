const form = document.getElementById("login-form");
const message = document.getElementById("login-message");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.classList.remove("error");
  message.textContent = "Verificando credenciales…";
  try {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: document.getElementById("username").value,
        password: document.getElementById("password").value
      })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "No fue posible iniciar sesión.");
    window.location.assign("/");
  } catch (error) {
    message.classList.add("error");
    message.textContent = error instanceof TypeError
      ? "No se pudo contactar al servidor. Inténtalo de nuevo."
      : error.message;
  }
});
