var resultContainer = document.getElementById('qr-reader-results');
var lastResult, countResults = 0;

async function onScanSuccess(decodedText, decodedResult) {
    if (decodedText !== lastResult) {
        ++countResults;
        lastResult = decodedText;
        let url = "/scanner/" + decodedText;

        htmx.ajax('GET', url, {
            target: '#qr-reader-results', // Replace with the ID of your target container
            swap: 'outerHTML'          // Optional: specify the swap strategy
        });

        console.log(`Scan result ${decodedText}`, decodedResult);
    }
}
var scanner = document.getElementById('qr-reader');
var screen_w = scanner.offsetWidth/2;
var screen_h = scanner.offsetWidth/4;
console.log(screen_h)
console.log(screen_w)
var html5QrcodeScanner = new Html5QrcodeScanner(
    "qr-reader", { fps: 10, qrbox: {width: screen_w, height: screen_h}});
html5QrcodeScanner.render(onScanSuccess);