// steps - Deprecated with the MDL Stepper:the step in th elegibility and loan discovery tools wizard-content.json
// answers - the users progress with answers
// currentPage - the page the user is on
// currentLoanType - the current loan type being viewed.
// currentFormType - the current form type being viewed.

function setStep(question, answer) {
    // Create object for question  and ansers pairs
    var value = '{"q":' + parseInt(question) + ', ' + '"a":"' + answer + `"}`;

    // console.log(JSON.parse(value)); 
    // If empty add first
    if(getCookie("steps")=='') {
        setCookie("steps", value, 365)
    }
    // if not empty add to array
    else {
        setCookie("steps", getCookie("steps")+","+value, 365);
    }    
}

// Get and Set current page
function setCurrentPage(currentPage) {
    setCookie('currentPage', currentPage, 1);
}
function getCurrentPage() {
    return getCookie('currentPage');
}

// Get list of pages
function getPageList() {
    return ["home","guides","eligibility","discovery","support","form"];
}

// Get and Set Loan Type
function setloanType(loanType) {
    setCookie('currentLoanType', loanType, 1);
}
function getloanType() {
    return getCookie('currentLoanType');
}

// Get and Set Form Type
function setFormType(formType) {
    setCookie('currentFormType', formType, 1);
}
function getFormType() {
    return getCookie('currentFormType');
}

function setCookie(cname, cvalue, exdays) {
    const d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    let expires = "expires="+d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}
  
function getCookie(cname) {
    let name = cname + "=";
    let ca = document.cookie.split(';');
    for(let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
        c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
        return c.substring(name.length, c.length);
        }
    }
    return "";
}

function userState() {
    // Returns a number indicating user's returning state
    // 0 = new user
    // 1 = returing need to Continue eligibility check 
    // 2 = returing need to Continue loan discovery 

    if (getCookie("steps") != "") {
        console.log("Welcome back");

        //  If the eligiblity check is not complere
        // TODO: Define in JSON instead of using magic number 35
        if (Math.max(...returnStepsJSON().map(o => o.q)) < 35) {
            console.log("Continue eligibility check");
            return 1;
        }
        else {
            console.log("Continue loan discovery");
            return 2;
        }
    }
    else {
        console.log("Welcome new user");
        return 0;
    }
}

function returnStepsJSON() {
    return JSON.parse("[" + getCookie("steps") + "]")
}

function resetCookies() {
    setCookie("steps", '', -1);
    setCookie("answers", '', -1);
    setCookie("currentLoanType", '', -1);
    setCookie("currentFormType", '', -1);
    setCookie("currentPage", '', -1);
    console.log("Cookies Reset");
}

function debugTools(hostname, e) {
    if (hostname === "localhost" || 
        hostname === "127.0.0.1" || 
        hostname === "192.168.0.106") 
    {
        // press 0 key to reset cookies 
        if (e.which == 48 || e.keyCode == 48 || window.event.keyCode == 48) {
            e.preventDefault();
            /// From: js/stateManager.js
            resetCookies();
        };

        // press 1 key to show questions and answers 
        if (e.which == 49 || e.keyCode == 49 || window.event.keyCode == 49) {
            e.preventDefault();
            /// From: js/stateManager.js
            console.log(returnStepsJSON());
        };

        // press 2 key to show user stste 
        if (e.which == 50 || e.keyCode == 50 || window.event.keyCode == 50) {
            e.preventDefault();
            /// From: js/stateManager.js
            userState();
        };
    }
}