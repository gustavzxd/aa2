function entrar() {
    const username = document.getElementById("user").value;
    const password = document.getElementById("pass").value;

    if (!username || !password) {
        mostrarErro("Preencha usuário e senha");
        return;
    }

    fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username, password })
        })
        .then(res => {
            if (res.status === 401) {
                throw new Error('Credenciais inválidas');
            }
            return res.json();
        })
        .then(data => {
            if (data.ok) {
                window.location.href = "/index";
            } else {
                mostrarErro(data.error || "Credenciais inválidas");
            }
        })
        .catch(error => {
            mostrarErro("Erro de conexão: " + error.message);
        });
}

function mostrarErro(mensagem) {
    const erroEl = document.getElementById("erro");
    erroEl.textContent = mensagem;
    erroEl.style.display = "block";
}

// Permitir login com Enter
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("pass").addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            entrar();
        }
    });
});