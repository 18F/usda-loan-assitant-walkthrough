function showPDF(fileName, title = "", desc = "", viewerId = 'mozViewerFrame') {
  console.log('loading pdf '+ fileName +' '+title);
  viewerUrl = 'js/pdfjs/web/viewer.html?';
  fileName = 'file=/forms/'+fileName;
  document.getElementById(viewerId).src = viewerUrl+fileName;

  $('#form-title').html(title);
  $('#form-desc').html(desc);

  return false;
}

showPDFHook = function(evt){
  fileName = evt.currentTarget.getAttribute("data-file-name");
  title = evt.currentTarget.getAttribute("data-title");
  desc = evt.currentTarget.getAttribute("data-desc");
  showPDF(fileName, title, desc);
}

activateShowPDF = function(){
  const showPdfElements = document.querySelectorAll('.show-pdf');
  showPdfElements.forEach(function(elem) {
    elem.addEventListener('click', showPDFHook, false);
    });
  }

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

setupMenu = function(hov=false){
  forms = getForms()
  // console.log(forms)  
  i=0;
  forms.forEach(form => {
    // console.log(form, hov);
    if (hov==true){
      li = '<li><a href="/form.html?q='+i+'&hov=true"><i class="bi bi-circle"></i><span>'+form.name+'</span></a></li>';
    }else{
      li = '<li><a href="/form.html?q='+i+'&hov=false"><i class="bi bi-circle"></i><span>'+form.name+'</span></a></li>';
    }
    $("#forms-nav").append(li);
    i=i+1;
  });
}

getQueryVar = function(name="q"){
  const params = new Proxy(new URLSearchParams(window.location.search), {
    get: (searchParams, prop) => searchParams.get(prop),
  });
  return params[name]; 
}

getForm = function(){
  return getForms()[getQueryVar(name="q")]
}
