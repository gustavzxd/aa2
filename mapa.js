// Ícones simplificados usando emojis
const redIcon = L.divIcon({
    html: '📍',
    iconSize: [30, 30],
    className: 'red-marker'
});

const blueIcon = L.divIcon({
    html: '📌',
    iconSize: [30, 30],
    className: 'blue-marker'
});

// Inicializa o mapa
let map;
let tempMarker = null;

// Aguardar DOM carregar
document.addEventListener('DOMContentLoaded', function() {
    map = L.map('map').setView([-14.235, -51.925], 4);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    carregarOcorrencias();
    configurarEventos();
});

// 1. Carregar Ocorrências já salvas
function carregarOcorrencias() {
    fetch('/ocorrencias', {
            credentials: 'include'
        })
        .then(res => {
            if (res.status === 401) {
                window.location.href = '/login';
                return;
            }
            return res.json();
        })
        .then(data => {
            if (data && !data.error) {
                data.forEach(occ => {
                    const m = L.marker([occ.lat, occ.lon], { icon: blueIcon }).addTo(map);
                    m.bindPopup(`
                    <b>${occ.tipo}</b><br>
                    <small>${occ.endereco}</small><br>
                    <small>Prioridade: ${occ.prioridade}</small><br>
                    <small>${occ.data} ${occ.hora}</small>
                `);
                });
            }
        })
        .catch(error => {
            console.error('Erro ao carregar ocorrências:', error);
        });
}

// 2. Configurar eventos
function configurarEventos() {
    // Clique no Mapa (Gera endereço automático)
    map.on('click', function(e) {
        const lat = e.latlng.lat.toFixed(6);
        const lon = e.latlng.lng.toFixed(6);

        // Atualiza visual e inputs
        document.getElementById('displayLat').textContent = lat;
        document.getElementById('displayLon').textContent = lon;
        document.getElementById('latitude').value = lat;
        document.getElementById('longitude').value = lon;

        const enderecoInput = document.getElementById('endereco');

        // Simplifica o endereço - não faz geolocalização detalhada
        enderecoInput.value = `Local: ${lat}, ${lon}`;

        // Alternativa: usa apenas coordenadas básicas
        // Se quiser um nome mais amigável:
        const opcoes = [
            "Trecho da estrada",
            "Localização na via",
            "Ponto da rodovia",
            "Área da estrada",
            "Segmento viário"
        ];
        const nomeAleatorio = opcoes[Math.floor(Math.random() * opcoes.length)];
        enderecoInput.value = `${nomeAleatorio} (${lat}, ${lon})`;

        // Marcador Vermelho
        if (tempMarker) {
            map.removeLayer(tempMarker);
        }
        tempMarker = L.marker(e.latlng, { icon: redIcon }).addTo(map);
        tempMarker.bindPopup('📍 Local selecionado').openPopup();
    });

    // Botão Buscar (Texto -> Lat/Lon) - REMOVIDO para simplificar
    // document.getElementById('searchBtn').onclick = function() {
    //     alert('Funcionalidade de busca desativada. Clique diretamente no mapa.');
    // };

    // 4. Salvar
    document.getElementById('salvarBtn').onclick = function() {
        const tipo = document.getElementById('tipo').value;
        const prioridade = document.getElementById('prioridade').value;
        const endereco = document.getElementById('endereco').value;
        const lat = document.getElementById('latitude').value;
        const lon = document.getElementById('longitude').value;

        if (!tipo || !lat || !lon) {
            alert('Por favor, clique no mapa para selecionar um local e preencha o tipo.');
            return;
        }

        fetch('/registrar_ocorrencia', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    tipo: tipo,
                    prioridade: prioridade,
                    endereco: endereco || `Local: ${lat}, ${lon}`,
                    lat: parseFloat(lat),
                    lon: parseFloat(lon)
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.ok) {
                    alert("✅ Ocorrência registrada com sucesso! ID: #" + data.id);
                    setTimeout(() => {
                        window.location.href = '/lista';
                    }, 1000);
                } else {
                    alert("❌ Erro ao salvar: " + (data.error || "Tente novamente"));
                }
            })
            .catch(() => {
                alert("❌ Erro de conexão");
            });
    };
}