import { html, render } from "https://unpkg.com/lit-html?module";

function renderPage(subjects) {
  let itemsList = [];
  for (let i = 0; i < subjects.length; i++) {
    const element = subjects[i];
    itemsList.push(html`
      <div class="col-lg-4 my-4">
          <div class="card" id="card${element[0]}">
               <div class="card-body">
                    <p class="title">
                         <div class="row">
                              <div class="col-10" id="${element[0]}">
                                  <span class="text-muted">Ostatnia zmiana: ${
      element[5].split(",")[0]
      }</span>
                                  <h4><a id="sub-name">${element[4]}</a><h4>
                                  <span class="text-muted"><small>${
      element[1]
      }</small></span>
                              </div>
                         <div class="col-2 mt-1">
                    <div class="notice" id="notice${element[0]}"></div>
               </div>
          </div>
     </p>
     <p class="card-text" id="text">${element[3]}</p>
     </div>
     </div>
     </div>
    `);
  }

  const itemsContainer = html`
    <div class="container" style="margin-top: 7em;">
      <div class="row">
        ${itemsList}
      </div>
    </div>
  `;

  $(document).ready(function () {
    $(".notice").click(function () {
      const notice = this.id;
      if ($("#" + notice).hasClass("on")) {
        $("strong").html("Ukończono pracę domową!");
        $(".toast-body").html(
          "Od teraz ten przedmiot nie będzie już przypominany do czasu następnego update'u!"
        );
        $(".toast").toast("show");
        $("#" + notice).removeClass("on");
        $("#" + notice).addClass("off");
        setCookie(notice, "off");
      } else if ($("#" + notice).hasClass("off")) {
        $("strong").html("Dodano znacznik pracy domowej!");
        $(".toast-body").html(
          "Znacznik będzie tutaj dopóki nie odrobisz lekcji z tego przedmiotu."
        );
        $(".toast").toast("show");
        $("#" + notice).removeClass("off");
        $("#" + notice).addClass("on");
        setCookie(notice, "on");
      }
    });
  });

  $(document).ready(function () {
    $(".col-10").click(function () {
      location.href = "/single/" + this.id;
      document.getElementById("sub-name").href = "https://crapapp-staszic.herokuapp.com/single/" + this.id;
    });
  });

  render(itemsContainer, document.getElementsByTagName("app")[0]);
}
const xhttp = new XMLHttpRequest();
xhttp.onreadystatechange = function () {
  if (this.readyState == 4 && this.status == 200) {
    renderPage(JSON.parse(xhttp.responseText));
    loadCookies();
  }
};
xhttp.open("GET", "api/all", true);
xhttp.send();

function setCookie(notice, vclass) {
  Cookies.set(notice, vclass, { expires: 30 });
}

function loadCookies() {
  for (let j = 1; j < 19; j++) {
    const el = document.getElementById("notice" + j);
    const a = Cookies.get("notice" + j);
    if (Cookies.get("notice" + j) === undefined) {
      el.classList.add("off");
    } else {
      var cookie = Cookies.get("notice" + j);
      el.classList.add(cookie);
    }
  }
}
