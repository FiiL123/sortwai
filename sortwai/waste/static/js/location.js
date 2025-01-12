navigator.geolocation.getCurrentPosition(getCity);
async function getCity(position) {
    cookieVal = getCookie("municipality")
    if ( cookieVal != null){
        document.getElementById('municipality').innerHTML = cookieVal;
        return;
    }
    fetch('/get_location/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ latitude: position.coords.latitude, longitude: position.coords.longitude }),
    }).then(response => response.json())
            .then(data => {
                console.log('City:', data.city);
                document.getElementById('municipality').innerHTML = data.city;
            })
            .catch(error => console.error('Error:', error));
    }


function getCookie(name) {
    let cookieArr = document.cookie.split(";");

    for(let i = 0; i < cookieArr.length; i++) {
        let cookiePair = cookieArr[i].split("=");

        if(name == cookiePair[0].trim()) {
            return decodeURIComponent(cookiePair[1]);
        }
    }
    return null;
}