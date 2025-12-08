const ctx = document.getElementById('temperatureChart').getContext('2d');
const temperatureChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Temperature (°C)',
            data: [],
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1
        }]
    },
    options: {
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'second'
                }
            },
            y: {
                beginAtZero: true
            }
        }
    }
});

const temperatureData = document.getElementById('temperatureData');

let thingyDevice;
let temperatureCharacteristic;

connectButton.addEventListener('click', async () => {
    try {
        thingyDevice = await navigator.bluetooth.requestDevice({
            filters: [{ services: ['ef680200-9b35-4933-9b10-52ffa9740042'] }]
        });

        const server = await thingyDevice.gatt.connect();
        const service = await server.getPrimaryService('ef680200-9b35-4933-9b10-52ffa9740042');
        temperatureCharacteristic = await service.getCharacteristic('ef680201-9b35-4933-9b10-52ffa9740042');
        
        temperatureCharacteristic.addEventListener('characteristicvaluechanged', handleTemperatureData);
        await temperatureCharacteristic.startNotifications();

        console.log('Connected to Thingy:52');
    } catch (error) {
        console.error('Error connecting to Thingy:52', error);
    }
});

function handleTemperatureData(event) {
    const value = event.target.value.getUint8(0);
    const temperature = value / 10;
    temperatureData.textContent = `Temperature: ${temperature}°C`;

    const currentTime = new Date();
    temperatureChart.data.labels.push(currentTime);
    temperatureChart.data.datasets[0].data.push(temperature);
    temperatureChart.update();
}