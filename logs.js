document.addEventListener('DOMContentLoaded', function() {
    fetch('/logs_data', { credentials: 'include' })
        .then(r => {
            if (r.status === 401) {
                window.location.href = '/login';
                return;
            }
            return r.json();
        })
        .then(data => {
            const corpo = document.getElementById('corpo');
            if (!data || data.length === 0) {
                corpo.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:40px;color:#888;">Nenhum log registrado</td></tr>';
                return;
            }

            corpo.innerHTML = '';
            data.reverse().forEach(log => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${log.data}</td>
                    <td>${log.hora}</td>
                    <td><b>${log.usuario}</b></td>
                    <td>${log.acao}</td>
                    <td><pre>${log.raw}</pre></td>
                `;
                corpo.appendChild(tr);
            });
        })
        .catch(error => {
            const corpo = document.getElementById('corpo');
            corpo.innerHTML = `
                <tr>
                    <td colspan="5" style="color:#dc3545;text-align:center;padding:40px;">
                        ❌ Erro ao carregar logs: ${error.message}
                    </td>
                </tr>
            `;
        });
});