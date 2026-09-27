var el = document.querySelector('#js_content');
if (el) {
    console.log(el.innerText.substring(0,10000));
} else {
    var els = document.querySelectorAll('[id^="js_content"]');
    if (els.length) {
        console.log(els[0].innerText.substring(0,10000));
    } else {
        console.log(document.body.innerText.substring(0,3000));
    }
}
