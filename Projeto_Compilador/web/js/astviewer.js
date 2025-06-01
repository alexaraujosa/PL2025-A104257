import { processAST } from "./astStruct.js";

const borderColors = ["#f44336", "#4caf50", "#2196f3", "#ff9800", "#9c27b0"];
let borderColorInd = 0;

let AST = undefined;

function getBorderColor() {
    borderColorInd++;
    borderColorInd %= borderColors.length;
    return borderColors[borderColorInd];
}

/**
 * Stores all collapsible elements currently on the AST Tree.
 * It is replaced every time a new AST is proccessed. Here I rely on the GC for the DOM nodes that are replaced, as all
 * references are removed from every structure I create, a priori.
 * @type {Set<HTMLDivElement>}
 */ 
const collapsible = new Set();
let collapsed = true;
function processASTTreeEvents() {
    collapsible.clear();
    collapsed = true;

    // Add collapsible behavior to nodes.
    document.querySelectorAll(".ast-node .type").forEach(toggle => {
        toggle.parentElement.style.setProperty("--border-color", getBorderColor());
        
        if (!toggle.parentElement.classList.contains("no-chevron")) {
            collapsible.add(toggle.nextElementSibling);
            toggle.addEventListener("click", (e) => {
                e.preventDefault();
                toggle.nextElementSibling.classList.toggle("collapsed");
            });
        }
    });

    // Add collapsible behavior to properties.
    document.querySelectorAll(".prop-name").forEach(toggle => {
        toggle.parentElement.style.setProperty("--border-color", getBorderColor());

        if (!toggle.parentElement.classList.contains("no-chevron")) {
            collapsible.add(toggle.nextElementSibling);
            toggle.addEventListener("click", () => {
                toggle.nextElementSibling.classList.toggle("collapsed");
            });
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    processASTTreeEvents();

    const ASTTree = document.getElementById("astTree");

    //#region -------------- Upload AST Button --------------
    /** @type {HTMLInputElement} */
    const ASTInput = document.getElementById("_AST");
    ASTInput.addEventListener("change", async (e) => {
        console.log("User uploaded new AST dump.");

        ASTInput.disabled = true;
        try {
            const file = ASTInput.files[0];
            console.debug("AST Input File:", file);

            const textData = await file.text();
            const data = JSON.parse(textData);
            console.debug("AST Input:", data);
            
            console.log("Processing AST...");
            AST = processAST(data);
            console.log("Finished processing AST.");

            ASTTree.removeChild(ASTTree.lastElementChild);
            ASTTree.append(AST);
            processASTTreeEvents();
            console.log("Reloaded AST Tree.");
        } catch (e) {
            console.error("Unable to process AST input:", e);
            ASTInput.disabled = false;
        }
    });
    
    const uploadASTBtn = document.getElementById("uploadAST");
    uploadASTBtn.addEventListener("click", (e) => {
        ASTInput.click();
    });
    //#endregion -------------- Upload AST Button --------------

    //#region -------------- Expand / Collapse Button --------------
    const toggleCollapseBtn = document.getElementById("toggleCollapseBtn");
    toggleCollapseBtn.addEventListener("click", (e) => {
        if (collapsed) {
            for (const v of collapsible) {
                v.classList.remove("collapsed");
            }
        } else {
            for (const v of collapsible) {
                v.classList.add("collapsed");
            }
        }

        collapsed = !collapsed;
    });

    const toggleCollapseNoPosBtn = document.getElementById("toggleCollapseNoPosBtn");
    toggleCollapseNoPosBtn.addEventListener("click", (e) => {
        if (collapsed) {
            for (const v of collapsible) {
                if (v.parentElement.getAttribute("name") === "pos") {
                    v.classList.add("collapsed");
                    continue;
                }
                
                v.classList.remove("collapsed");
            }
        } else {
            for (const v of collapsible) {
                v.classList.add("collapsed");
            }
        }

        collapsed = !collapsed;
    });
    //#endregion -------------- Expand / Collapse Button --------------
});

// function (ev) {
//     var el = window._protected_reference = document.createElement("INPUT");
//     el.type = "file";
//     el.accept = "image/*";
//     el.multiple = "multiple"; // remove to have a single file selection
    
//     // (cancel will not trigger 'change')
//     el.addEventListener('change', function(ev2) {
//       // access el.files[] to do something with it (test its length!)
      
//       // add first image, if available
//       if (el.files.length) {
//         document.getElementById('out').src = URL.createObjectURL(el.files[0]);
//       }
  
  
//       // test some async handling
//       new Promise(function(resolve) {
//         setTimeout(function() { console.log(el.files); resolve(); }, 1000);
//       })
//       .then(function() {
//         // clear / free reference
//         el = window._protected_reference = undefined;
//       });
  
//     });
  
//     el.click(); // open
// }