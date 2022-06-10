var WizardBuilder = window.WizardBuilder || {};
(function() {
    "use strict";

    // TODO: Add in accessibility tags throughout

    var _mdlWizardItemCount = 0;
    const _MDL_STEP_INDEX = {};

    /**
     * Helper method to recursively find the first descendent element with a target class
     * Based on: https://stackoverflow.com/a/25414784
     * @param {HTMLElement} element  top-level element at which to begin the search
     * @param {string} className     name of the element class to search for
     * @returns {HTMLElement}        the first descendent element that contains the target class / null, if not found
     */
    function _findFirstChildByClass(element, className) {
        var foundElement = null,
            found;

        function recurse(element, className, found) {
            for (var i = 0; i < element.childNodes.length && !found; i++) {
                var el = element.childNodes[i];
                var classes = el.className != undefined ? el.className.split(" ") : [];
                for (var j = 0, jl = classes.length; j < jl; j++) {
                    if (classes[j] == className) {
                        found = true;
                        foundElement = element.childNodes[i];
                        break;
                    }
                }
                if (found) {
                    break;
                }
                recurse(element.childNodes[i], className, found);
            }
        }
        recurse(element, className, false);
        return foundElement;
    }

    /**
     * Helper function to build an MDL-Stepper Label element
     * @param {string} title     the title of the wizard step
     * @param {string} subtitle  OPTIONAL - the subtitle of the wizard step
     * @returns {HTMLElement}    <span> element representing the wizard step's label
     */
    function _createWizardTitleElement(title, subtitle) {
        let labelSpan = document.createElement("span");
        labelSpan.classList.add("mdl-step__label");

        let titleSpan = document.createElement("span");
        titleSpan.classList.add("mdl-step__title");

        let titleTextSpan = document.createElement("span");
        titleTextSpan.classList.add("mdl-step__title-text");
        titleTextSpan.appendChild(document.createTextNode(title));
        titleSpan.appendChild(titleTextSpan);

        // If subtitle is present, then we add that in
        if (subtitle) {
            let subtitleTextSpan = document.createElement("span");
            subtitleTextSpan.classList.add("mdl-step__title-message");
            subtitleTextSpan.appendChild(document.createTextNode(subtitle));
            titleSpan.appendChild(subtitleTextSpan);
        }

        labelSpan.appendChild(titleSpan);

        return labelSpan;
    }

    /**
     * Helper function to build a simple paragraph element
     * @param {string} paragraphText  the content to place in the paragraph element
     * @returns {HTMLElement}         <p> element representing the wizard step's label
     */
    function _createParagraphElement(paragraphText) {
        let paragraphElement = document.createElement("p");
        paragraphElement.appendChild(document.createTextNode(paragraphText));
        return paragraphElement;
    }

    /**
     * Helper function to build a video content element
     * @param {string} src          path to remote video file (presently has to be mp4)
     * @param {string} captionText  text to caption the video for the purposes of instruction or description
     * @returns {HTMLElement}       <section> element containing video content for embedding in a wizard step
     */
    function _createVideoContentElement(src, captionText, frameHeigh = 400, frameWidth = 600) {
        let videoSection = document.createElement("section");

        // Split the video and caption into two "mdl-grids" to ensure they're on different "rows" visually
        let mdlGridVideoElement = document.createElement("div");
        mdlGridVideoElement.classList.add("mdl-grid");

        // TODO: Modify or make configurable via the wizard-content.json
        
        if(src.includes("http")){
            // External video
            let videoElement = document.createElement("iframe");
            videoElement.height = frameHeigh;
            videoElement.width = frameWidth;
            videoElement.src = src;
            mdlGridVideoElement.appendChild(videoElement);
        }else{
            // Intenal video
            let videoElement = document.createElement("video");
            videoElement.height = frameHeigh;
            videoElement.width = frameWidth;
    
            // Add in control to the video player
            videoElement.setAttribute("controls", "");
    
            // TODO: Modify wizard-content.json to allow for multiple source files to support multiple video types
            let videoSourceElement = document.createElement("source");
            videoSourceElement.src = src;
            videoSourceElement.type = "video/mp4";
    
            videoElement.appendChild(videoSourceElement);
            mdlGridVideoElement.appendChild(videoElement);
        }
        

        // Create caption paragraph element
        let mdlGridCaptionElement = document.createElement("div");
        mdlGridCaptionElement.classList.add("mdl-grid");

        let videoCaptionParagraphElement = _createParagraphElement(captionText);

        mdlGridCaptionElement.appendChild(videoCaptionParagraphElement);

        // Add both video and caption to the enclosing video section
        videoSection.appendChild(mdlGridVideoElement);
        videoSection.appendChild(mdlGridCaptionElement);

        return videoSection;
    }

    /**
     * Helper function to build a bulleted list element
     * @param {Array} bullets    array containing "bullet" objects for conversion into list
     * @param {string} listType  string specificying the type of list ("numbered" -> ordered list | "unordered" -> unordered list)
     * @returns {HTMLElement}    <ol> or <ul> element containing bullet contents
     */
    function _createBulletedListElement(bullets, listType) {
        let listElement = null;
        // Do some light preprocessing to ensure the type is trimmed and all lowercase
        let cleanListType = listType.trim().toLowerCase();
        // If "numbered" make "ol" element
        if (cleanListType === "numbered") {
            listElement = document.createElement("ol");
            // If "unordered" make "ul" element
        } else if (cleanListType === "unordered") {
            listElement = document.createElement("ul");
        } else {
            alert("Unrecognized bulleted list type detected: " + listType);
        }

        var bulletArrayLength = bullets.length;
        for (var i = 0; i < bulletArrayLength; i++) {
            let bullet = bullets[i];
            let bulletElement = document.createElement("li");
            // For each bullet add the bullet's content
            bulletElement.appendChild(document.createTextNode(bullet.bulletContent));
            // Check if the current bullet has subbullets, if so, recursively add them
            let subBullets = bullet.subBullets;
            if (subBullets !== null && subBullets !== undefined && typeof subBullets === 'object' && !Array.isArray(subBullets)) {
                let subListElement = _createBulletedListElement(subBullets.bullets, subBullets.type);
                bulletElement.appendChild(subListElement);
            }
            // Add the bullet to the parent bulleted list
            listElement.appendChild(bulletElement);
        }
        return listElement;
    }

    /**
     * Helper function to build an informational content element
     * @param {Array} paragraphs  array of paragraphs that comprise the informational content
     * @returns {HTMLElement}     <div> element containing the informational content
     */
    function _createInformationalContentElement(paragraphs) {
        let gridDiv = document.createElement("div");
        gridDiv.classList.add("mdl-grid");

        var paragraphArrayLength = paragraphs.length;
        for (var i = 0; i < paragraphArrayLength; i++) {
            let paragraph = paragraphs[i];
            let paragraphContent = paragraph.paragraphContent;
            // For each paragraph, check if it's a string or an object 
            if (paragraphContent !== null && paragraphContent !== undefined) {
                // If it's a string, then create a simple paragraph element
                if (typeof paragraphContent === 'string' || paragraphContent instanceof String) {
                    var paragraphElement = _createParagraphElement(paragraphContent);
                    // If it's an object, then it should represent a bulleted list, so create that instead
                } else if (typeof paragraphContent === 'object' && !Array.isArray(paragraphContent)) {
                    var paragraphElement = _createBulletedListElement(paragraphContent.bullets, paragraphContent.type);
                } else {
                    alert("Unrecognized paragraphContent element detected: " + paragraphContent.toString());
                }
            }
            // Append the paragraph to the parent div
            gridDiv.appendChild(paragraphElement);
        }

        return gridDiv;
    }

    /**
     * Helper function to build an MDL-Stepper Content element
     * @param {object} content        object containing the step's content
     * @param {string} stepType       string indicating type of step ("video" -> video or "informational" -> paragraphs/bulleted lists)
     * @param {string} sectionHeader  OPTIONAL - string providing a small section header for the current step
     * @returns {HTMLElement}         <div> element representing the wizard step's content
     */
    function _createWizardContentElement(content, stepType, sectionHeader) {
        let contentDiv = document.createElement("div");
        contentDiv.classList.add("mdl-step__content");

        // If the sectionHeader is present, then add it to the content as the first child element
        if (sectionHeader) {
            let sectionHeaderDiv = document.createElement("div");
            sectionHeaderDiv.classList.add("mdl-grid");
            // Current default to indicate section header is "Italic" font
            sectionHeaderDiv.style.fontStyle = "italic";
            sectionHeaderDiv.appendChild(document.createTextNode(sectionHeader));
            contentDiv.appendChild(sectionHeaderDiv);
        }

        // Do light preprocessing on "stepType" to ensure consistent value comparison
        var cleanStepType = stepType.trim().toLowerCase();
        if (cleanStepType === "video") {
            contentDiv.appendChild(_createVideoContentElement(content.src, content.captionText));
        } else if (cleanStepType === "informational") {
            contentDiv.appendChild(_createInformationalContentElement(content.paragraphs));
        } else {
            alert("An invalid step type was detected: " + stepType);
        }

        return contentDiv;
    }

    /**
     * Helper function to generate a simple button element
     * @param {string} buttonText       string containing the text to embed in the button
     * @param {string} backgroundColor  color for the button's background color
     * @param {string} textColor        OPTIONAL - color for the text in the button (DEFAULT: "black"/"#000")
     * @param {Number} orderNumber      OPTIONAL - number indicating the order in the flexbox that the number should appear compared to other buttons
     * @returns {HTMLElement}           <button> element representing a simple button
     */
    function _createButtonElement(buttonText, backgroundColor, textColor, orderNumber) {
        let button = document.createElement("button");
        button.classList.add("mdl-button", "mdl-js-button", "mdl-js-ripple-effect", "mdl-button--raised");
        // Add background color to the button
        button.style.backgroundColor = backgroundColor;
        // Check if textColor is present, and if so, add it to the button
        if (textColor) {
            button.style.color = textColor;
        }
        // Check if orderNumber is present, and if so, add it to the button
        if (orderNumber) {
            button.style.order = orderNumber;
        }
        // Add text to the button
        button.appendChild(document.createTextNode(buttonText));
        return button;
    }

    /**
     * Helper function to build an MDL-Stepper Action element
     * @param {string} wizardElementId  the id given to the target, parent <ul> element
     * @param {Array} buttons           array of objects containing the necessary information for generating the step's buttons
     * @param {Number} resetToStepId    OPTIONAL - number indicating the step to jump back to for the optional reset button
     * @returns {HTMLElement}           <div> element containing the various buttons/actions that can be taken on a given step
     */
    function _createWizardActionElement(wizardElementId, buttons, resetToStepId) {
        let actionElement = document.createElement("div");
        actionElement.classList.add("mdl-step__actions");

        var buttonArrayLength = buttons.length;
        for (var i = 0; i < buttonArrayLength; i++) {
            let button = buttons[i];
            // For each button, create a button element
            let buttonElement = _createButtonElement(button.buttonText, button.color, button.textColor, i);
            if (button.nextStepId) {
                // If the button indicates a "nextStepId", then the onclick should add the next step and navigate to it
                buttonElement.onclick = function(_) {
                    WizardBuilder.addStep(wizardElementId, button.nextStepId);
                    WizardBuilder.goToStep(wizardElementId, button.nextStepId);
                }
            } else if (button.url) {
                // If the button indicates a "url", then the onclick should simply navigate to the given "url"
                buttonElement.onclick = function(_) {
                    location.href = button.url;
                }
            } else {
                alert("A button object must have either a \"nextStepId\" attribute or \"url\" attribute.");
            }
            // Add margin between the button for stylistic purposes
            buttonElement.style.marginRight = "8px";
            actionElement.appendChild(buttonElement);
        }

        // If an optional "resetToStepId" was given, then create a "Start Over"
        if (resetToStepId) {
            let resetButtonElement = _createButtonElement("Start Over", "white", "#CCC", buttonArrayLength);
            resetButtonElement.style.marginLeft = "auto";
            resetButtonElement.style.border = "none";
            // The button jumps back to the given step whose ID equals "resetToStepId"
            resetButtonElement.onclick = function(_) {
                WizardBuilder.goToStep(wizardElementId, resetToStepId);
            }
            actionElement.appendChild(resetButtonElement);
        }

        return actionElement;
    }

    /**
     * Helper function to create a new wizard step element for a target wizard.
     * @param {string} wizardElementId  the id given to the target, parent <ul> element
     * @param {object} step             object representing the wizard step and all of its attributes/content
     * @returns {HTMLElement}           <li> element containing the whole wizard step
     */
    function _createWizardStepElement(wizardElementId, step) {
        let wizardStepElement = document.createElement("li");
        wizardStepElement.classList.add("mdl-step");
        // Add the step's id as a "data" attribute on the element for later reference purposes
        wizardStepElement.dataset.stepId = step.id;

        let wizardStepTitleElement = _createWizardTitleElement(step.title, step.subtitle);
        wizardStepElement.appendChild(wizardStepTitleElement);

        let wizardStepContentElement = _createWizardContentElement(step.content, step.type, step.sectionHeader);
        wizardStepElement.appendChild(wizardStepContentElement);

        let wizardStepActionElement = _createWizardActionElement(wizardElementId, step.buttons, step.resetToStepId);
        wizardStepElement.appendChild(wizardStepActionElement);

        return wizardStepElement;
    }

    /**
     * Function to retrieve the JSON file containing the wizard's content from the remote source.
     * @param {string} wizardContentPath remote source path to JSON
     * @returns {Array}                  array containing the possible steps in the wizard
     */
    function _getWizardContent(wizardContentPath) {
        var result = null;
        var xmlhttp = new XMLHttpRequest();
        xmlhttp.open("GET", wizardContentPath, false);
        xmlhttp.send();
        if (xmlhttp.status === 200) {
            result = JSON.parse(xmlhttp.responseText);
        }
        return result["steps"];
    }

    /**
     * Initialize the Wizard in a given <ul> element on the page with content from a standardized JSON format.
     * @param {string} wizardElementId the id given to the target <ul> element
     * @param {string} wizardContentPath the remote source path to the JSON file containing the wizard's content
     */
    this.initialize = function(wizardElementId, wizardContentPath) {
        // Make sure given element is a <ul>
        const stepperElement = document.getElementById(wizardElementId);
        if (stepperElement.nodeName !== "UL") {
            alert("The wizard must be placed in a <ul> element on the page. Please provide an ID for an empty <ul> element.");
            return;
        }
        // Double-check that the necessary Material Design Lite classes are on the <ul>
        if (!stepperElement.classList.contains("mdl-stepper")) {
            // Marks the class for the 3rd party MDL stepper library to initialize.
            stepperElement.classList.add("mdl-stepper");
        }
        if (!stepperElement.classList.contains("mdl-stepper--linear")) {
            // This class is necessary since we override the non-linear behavior of the 3rd party stepper library.
            // If we didn't do this, we wouldn't have direct control over what happens when the user clicks back to an earlier step.
            stepperElement.classList.add("mdl-stepper--linear");
        }

        // Pull the wizard content from the remote source
        let wizardSteps = _getWizardContent(wizardContentPath);
        if (!Array.isArray(wizardSteps)) {
            alert("Attempt to parse the file at " + wizardContentPath + " failed. Could not find top level array attribute called \"steps\".");
            return;
        }

        // The wizard content is written as an array, but can be optimized for lookups by extracting the
        // step ID for use as a key in a lookup dictionary/object/associative array, so we do that here.
        const firstStep = wizardSteps[0];
        var stepArrayLength = wizardSteps.length;
        for (var i = 0; i < stepArrayLength; i++) {
            let step = wizardSteps[i];
            // Not in the JSON format, but added as an internal value to track placement in the 3rd party Stepper and also if the step has been added yet or not.
            step.mdlStepNumber = -1;
            _MDL_STEP_INDEX[step.id] = step;
        }

        // Use the first step at the top of the wizard content step list to create an initial first step for the page.
        let firstStepElement = _createWizardStepElement(wizardElementId, firstStep);

        stepperElement.appendChild(firstStepElement);
        _mdlWizardItemCount += 1;
        _MDL_STEP_INDEX[firstStep.id].mdlStepNumber = _mdlWizardItemCount;
        return stepperElement;
    }

    /**
     * Add a step from the preloaded wizard content to the target wizard element.
     * @param {string} wizardElementId the id given to the target <ul> element containing the wizard
     * @param {Number} stepId the id of the step to add to the page
     */
    this.addStep = function(wizardElementId, stepId) {
        let targetStep = _MDL_STEP_INDEX[stepId];
        // First check if the step has been rendered already, if so, we stop here and this is a No-Op.
        if (targetStep.mdlStepNumber > 0) {
            return;
        }

        const stepper = document.getElementById(wizardElementId);

        // Create new step
        const newStep = _createWizardStepElement(wizardElementId, targetStep);

        // Replace old steps with identical copies of themselves to clear possible duplicate event listeners (thanks to how stepper.js is implemented)
        for (var i = 0; i < stepper.children.length; i++) {
            var child = stepper.children[i];
            var childClone = child.cloneNode(true);
            const currentChildStepId = childClone.dataset.stepId;
            // This allows us to hijack what happens when a user clicks on an earlier step in the wizard. Namely we let them jump back to it.
            childClone.onclick = function(_) {
                WizardBuilder.goToStep(wizardElementId, parseInt(currentChildStepId));
            }
            var currentButtons = child.querySelectorAll('.mdl-button');
            var cloneButtons = childClone.querySelectorAll('.mdl-button');
            // When cloning, the onclick doesn't carry over, so we copy over the old buttons' onclick functions.
            for (var j = 0; j < currentButtons.length; j++) {
                cloneButtons[j].onclick = currentButtons[j].onclick;
            }
            child.replaceWith(childClone);
        }

        // Add the new step to the Stepper
        stepper.appendChild(newStep);

        // Make sure the stepper is "upgraded" to wire up the new step correctly
        stepper.setAttribute('data-upgraded', '');
        componentHandler.upgradeElement(stepper);

        _mdlWizardItemCount += 1;
        targetStep.mdlStepNumber = _mdlWizardItemCount;
        window.scrollTo(0, document.body.scrollHeight+999);

    }

    /**
     * Jump to a target rendered step in the wizard.
     * If it's a jump backwards, then clear out the steps in front of it for later re-rendering.
     * @param {string} wizardElementId the id given to the target <ul> element containing the wizard
     * @param {Number} stepId the id of the step to go to on the page
     */
    this.goToStep = function(wizardElementId, stepId) {
        let targetStep = _MDL_STEP_INDEX[stepId];
        // First check if the element hasn't been rendered. If it hasn't then we stop here and this is a No-Op.
        if (targetStep.mdlStepNumber < 0) {
            return;
        }

        const stepperElement = document.getElementById(wizardElementId);
        const stepper = stepperElement.MaterialStepper;
        const currentStep = stepper.getActive();

        // If the current step equals the target step to go to, then this is a No-Op and we stop early.
        if (parseInt(currentStep.dataset.stepId) === stepId) {
            return;
        }

        // Go to the target step
        stepper.goto(targetStep.mdlStepNumber);

        let foundTargetStep = null;
        let stepsToDelete = [];
        // TODO: Make this next loop more efficient by shifting to a binary/boundary search
        // Iterate through the stepper to find the target step
        for (var i = 0; i < stepperElement.children.length; i++) {
            var step = stepperElement.children[i];
            if (foundTargetStep === null) {
                foundTargetStep = parseInt(step.dataset.stepId) === stepId ? step : null;
                continue;
            }
            // Once we've found the target step (i.e. the boundary) then all steps past it in the wizard are marked for deletion
            stepsToDelete.push(step);
        }
        foundTargetStep.onclick = null;

        // If we move forward in the wizard, we need to mark the previous step as completed
        // But if we move backwards in the wizard, we need to mark the target step as not complete and delete all of the marked steps
        let stepWithIndicatorToModify = stepsToDelete.length > 0 ? foundTargetStep : currentStep;
        let labelIndicatorElement = _findFirstChildByClass(stepWithIndicatorToModify, "mdl-step__label-indicator");
        let labelIndicatorContentElement = labelIndicatorElement.children[0];
        if (stepsToDelete.length > 0) {
            // Change the step's label indicator to its corresponding number in the wizard's ordering
            let stepNumberIndicatorElement = document.createElement("span");
            stepNumberIndicatorElement.classList.add("mdl-step__label-indicator-content");
            stepNumberIndicatorElement.appendChild(document.createTextNode(targetStep.mdlStepNumber.toString()));
            labelIndicatorContentElement.replaceWith(stepNumberIndicatorElement);

            // Delete the marked steps from the DOM
            for (var i = 0; i < stepsToDelete.length; i++) {
                var step = stepsToDelete[i];
                _MDL_STEP_INDEX[step.dataset.stepId].mdlStepNumber = -1;
                _mdlWizardItemCount -= 1;
                stepperElement.removeChild(step);
            }
        } else {
            // Change the step's label indicator to a check mark to indicate that it's "done"
            let completedStepIndicatorElement = document.createElement("i");
            completedStepIndicatorElement.classList.add("material-icons", "mdl-step__label-indicator-content");
            completedStepIndicatorElement.appendChild(document.createTextNode("✔"));
            labelIndicatorContentElement.replaceWith(completedStepIndicatorElement);
        }
    }

}).call(WizardBuilder);