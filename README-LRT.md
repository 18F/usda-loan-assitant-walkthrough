# usda-loan-assitant-lrt

## How to Load the Library On a Page

Looking at the [index.html](index.html) in the root of the project, there's a few things to note.

1. The CSS files listed in the `<link>` tags in the document's `<head>` are required for the 3rd party MDL libraries to function.
1. It's recommended to have a top level container with the `mdl-grid` class, which acts like a "row" for those familiar with Bootstrap
1. The child div with `mdl-cell` and `mdl-cell--12-col` are the equivalent of columns in Bootstrap, and the latter class indicates that the entire width of the grid should be used for its content.
1. At a bare minimum, even if the last two steps are not followed, then you MUST have `<ul>` tag with a readily referenceable `id` attribute. Everything else provided by this wrapper library is dynamically generated within the `<ul>` tag.
1. The JavaScript that's listed in the bottom `<script>` tags is all required and must be imported in that exact order.
1. The script that says `WizardBuilder.initialize("demo-stepper", "wizard-content.json");` should be customized with the `<ul>` tag's `id` as the first attribute (no `#`) and a path/URL to the JSON file that holds the dynamic wizard's contents.


## How the Library Works

There's ample JSDoc strings throughout the [wizardBuilder.js](wizardBuilder.js) file to learn how the code works. More importantly, there's content that
must be written from which the wizard is generated. This content can reside in any file as long as it adheres to a specific JSON format.

The layout of this JSON can be mostly intuited from the example [wizard-content.json](wizard-content.json), but this is supplemented by an informal schema
provided in the [wizard-content-schema.yaml](wizard-content-schema.yaml) file. The schema file defines what the various JS objects look like when writing
the wizard's content. Descriptions for each of the fields are provided such that it should be fairly obvious what the purpose of the field is, as well as
any constraints on the field.


## How to Run the Demo

1. Pull the repository down using either `git` or downloading the ZIP file
1. Navigate into the root of the project
1. Start your favorite local server
    1. Install Python
    1. Run `python -m http.server`
1. Go into a web browser and enter the URL provided by your local web server
1. Play around with the wizard

### Archived Wizard Test

Several wizard libraries were considered for this initial implementation. Ultimately, the [MDL Stepper](https://ahlechandre.github.io/mdl-stepper/)
won the day; however, the test page for demoing the different libraries still exists for reference purposes.

This test page can be accessed by going to the root of the project. Navigating down into the `archive/wizard-test/` directory, and then starting a local
web server, the same as above. Both this test and the actual dynamic wizard demo page are self-contained.
