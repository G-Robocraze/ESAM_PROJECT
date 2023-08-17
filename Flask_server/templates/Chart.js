var ctx = document.getElementById('myChart').getContext('2d');

var chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['10:00', '10:01', '10:02', '10:03', '10:04', '10:05', '10:06', '10:07', '10:08', '10:09'],
        datasets: [{
            label: 'Energy Consumption',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1,
            data: [5, 10, 12, 8, 15, 17, 20, 18, 25, 22]
        }]
    },
    options: {
        scales: {
            xAxes: [{
                type: 'time',
                time: {
                    unit: 'minute',
                    displayFormats: {
                        minute: 'h:mm a'
                    }
                },
                scaleLabel: {
                    display: true,
                    labelString: 'Time'
                }
            }],
            yAxes: [{
                ticks: {
                    beginAtZero: true
                },
                scaleLabel: {
                    display: true,
                    labelString: 'Energy (kWh)'
                }
            }]
        }
    }
});