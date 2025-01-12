navigator.geolocation.getCurrentPosition(getCity);
async function getCity(position) {
    cookieVal = getCookie("municipality")
    if (cookieVal != null) return;
    let response = await fetch('/get_location/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({latitude: position.coords.latitude, longitude: position.coords.longitude})
    });

    if (response.ok) {
        location.reload();
    }
}
    // then(response => response.json())
    //     .then(response => {
    //         if (!response.ok) {
    //             throw new Error(`HTTP error! status: ${response.status}`);
    //         }
    //         return response.json();
    //     })
    //     .then(data => {
    //         console.log('city:', data.city);
    //         location.reload(); // Reload the page when the response status is OK
    //     })
    //     .catch(error => console.error('Error:', error));
    // }

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