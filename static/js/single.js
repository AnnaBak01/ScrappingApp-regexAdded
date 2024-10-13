import { html, render } from "https://unpkg.com/lit-html?module";

function renderPage(subjects) {
  const element = subjects[0];
  const template = document.createElement("div");
  template.innerHTML = element[6];
  const itemsContainer = html`
    <div class="container text-dark" style="margin-top: 3em;">
      <div class="row">
        <div class="col-lg-12 col-sm-12 col-md-12 col-xs-12 pl-3">
          <span class="text-muted">${element[1]}</span>
          <h1>${element[4]}</h1>
          <div class="mt-5" id="homeworkTags">
            ${template.childNodes}
          </div>
        </div>
      </div>
    </div>
  `;

  render(itemsContainer, document.getElementById("app"));
}

const xhttp = new XMLHttpRequest();
xhttp.onreadystatechange = function () {
  if (this.readyState == 4 && this.status == 200) {
    renderPage(JSON.parse(xhttp.responseText));
  }
};
xhttp.open("GET", "/api/" + subjectId, true);
xhttp.send();
