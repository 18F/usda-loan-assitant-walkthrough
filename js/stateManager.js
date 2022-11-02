// steps - the step in th elegibility and loan discovery tools wizard-content.json
// currentLoanType - the current loan type being viewed.

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
        var largest = Math.max.apply(Math, getCookie("steps").split(","));

        if (largest < 35) {
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

function deleteCookies() {
    setCookie("steps", '', -1);
    setCookie("currentLoanType", '', -1);
}