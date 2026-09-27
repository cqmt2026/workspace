var result = {
  title: document.title,
  author: '',
  content: ''
};
var nameEl = document.querySelector('#js_name');
if (nameEl) result.author = nameEl.innerText;
var article = document.querySelector('#js_content') || document.querySelector('.rich_media_content') || document.querySelector('[id^="js_content"]');
if (article) {
  result.content = article.innerText.substring(0, 8000);
}
console.log(JSON.stringify(result));
