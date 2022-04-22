function showPDF(fileName, viewerId = 'mozViewerFrame') {
  console.log('loading pdf '+ fileName);
  viewerUrl = 'assets/vendor/pdfjs/web/viewer.html?';
  fileName = 'file=/application/'+fileName;
  document.getElementById(viewerId).src = viewerUrl+fileName;
  return false;
}

showPDFHook = function(evt){
  fileName = evt.currentTarget.getAttribute("data-file-name");
  showPDF(fileName);
}

const showPdfElements = document.querySelectorAll('.show-pdf');
showPdfElements.forEach(function(elem) {
  elem.addEventListener('click', showPDFHook, false);
  });

function getForms() {
  var content_file = "/application/content.json"
  var result = null;
  var xmlhttp = new XMLHttpRequest();
  xmlhttp.open("GET", content_file, false);
  xmlhttp.send();
  if (xmlhttp.status==200) {
    result = JSON.parse(xmlhttp.responseText);
  }
  return result["Forms"];
  }

setupMenu = function(){
  forms = getForms()
  // console.log(forms)  
  i=0;
  forms.forEach(form => {
    // console.log(form);
    li = '<li><a href="/form.html?q='+i+'"><i class="bi bi-circle"></i><span>'+form.name+'</span></a></li>';
    $("#forms-nav").append(li);
    i=i+1;
  });
}

getQ = function(){
  const params = new Proxy(new URLSearchParams(window.location.search), {
    get: (searchParams, prop) => searchParams.get(prop),
  });
  
  return params.q; 
}

getForm = function(){
  return getForms()[getQ()]
}
