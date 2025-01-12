navigator.geolocation.getCurrentPosition(getCity);
async function getCity(position) {
    fetch('/get_location/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ latitude: position.coords.latitude, longitude: position.coords.longitude }), // Example coordinates for Bratislava
    })
.then(response => response.json())
        .then(data => {
            console.log('City:', data.city);
            document.getElementById('municipality').innerHTML = data.city;
        })
        .catch(error => console.error('Error:', error));
}