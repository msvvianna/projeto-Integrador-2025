document.addEventListener('DOMContentLoaded', function() {
    console.log("Iniciando gráficos...");

    // Criar gráfico de agendamentos
    new Chart(document.getElementById('graficoAgendamentos'), {
        type: 'bar',
        data: {
            labels: agendamentos_meses,
            datasets: [{
                label: 'Agendamentos',
                data: agendamentos_quantidades,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Criar gráfico de produtos utilizados
    new Chart(document.getElementById('graficoProdutosUtilizados'), {
        type: 'bar',
        data: {
            labels: ['Extractus', 'Bactran', 'Sanitizante', 'Sintra'],
            datasets: [{
                label: 'Quantidade de Produtos Utilizados em todos os Agendamentos',
                data: [
                    produtos_utilizados.extractus,
                    produtos_utilizados.bactran,
                    produtos_utilizados.sanitizante,
                    produtos_utilizados.sintra
                ],
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Criar gráfico de estoque de produtos
    new Chart(document.getElementById('graficoEstoqueProdutos'), {
        type: 'bar',
        data: {
            labels: ['Extractus', 'Bactran', 'Sanitizante', 'Sintra'],
            datasets: [{
                label: 'Quantidade de Produtos disponivel em Estoque',
                data: [
                    estoque_produtos.vonixx_extractus,
                    estoque_produtos.vonixx_bactran,
                    estoque_produtos.vonixx_sanitizante,
                    estoque_produtos.vonixx_sintra
                ],
                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    console.log("Gráficos carregados com sucesso.");
});
