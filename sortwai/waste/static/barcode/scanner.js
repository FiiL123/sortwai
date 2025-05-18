var resultContainer = document.getElementById('qr-reader-results');
var descriptionWrapper = document.getElementById('description-wrapper');
var qrContainer = document.querySelector('.qr-container');
var lastResult, countResults = 0;

async function onScanSuccess(decodedText, decodedResult) {
    if (decodedText !== lastResult) {
        ++countResults;
        lastResult = decodedText;
        let url = "/scanner/" + decodedText;

        resultContainer.innerHTML=`<p>Scanned: ${decodedText}</p> <a class="search__button" href=${url}><span class="search__button_text">Vyhľadať</span></a>`;

        console.log(`Scan result ${decodedText}`, decodedResult);
        html5QrcodeScanner.pause()
        qrContainer.classList.add('scanned');
        descriptionWrapper.style.display = 'block';
    }
}

var scanner = document.getElementById('qr-reader');
var screen_w = scanner.offsetWidth / 2;
var screen_h = scanner.offsetWidth / 4;

const html5QrcodeScanner = new Html5QrcodeScanner(
    "qr-reader",
    {
        fps: 30,
        qrbox: { width: screen_w, height: screen_h },
    }
);

html5QrcodeScanner.render(onScanSuccess);