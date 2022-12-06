"use strict";

class Popup {
    constructor(containerEl) {
        this.containerEl = containerEl;

        this.state = {
            headers: [],
            lastMessage: undefined,
            firstRender: "true",
            receivedOptions: "false",
            requestId: "",
            options: []
        };

        this.returnAnswer = this.returnAnswer.bind(this);

    }

    setState(state) {
        // Merge the new state on top of the previous one and re-render everything.
        this.state = Object.assign(this.state, state);
        this.render();
    }

    render() {
        // On first render get the headers
        if (this.state.firstRender === "true") {
            // The request id is taken from the title's preface "%requestId%"
            getCurrentWindow().then((currentWindow) => {
                const title = currentWindow.title;
                this.state.requestId = title.split('%')[1];
                getHdrs();
            });

            this.state.firstRender = undefined;
        }

        // Render the website url on the prompt
        const lastMessageEl = this.containerEl.querySelector("h3#main-page");
        if (this.state.headers.length > 0) {
            for (const hdr of this.state.headers) {
                if (hdr.name.toLowerCase() === "url") {
                    lastMessageEl.textContent = hdr.value;
                }
            }
        }

        // Render the options
        if (this.state.receivedOptions === "true") {
            if (this.state.options.length > 0) {
                for (const option of this.state.options) {
                    if (option.toLowerCase() === "rather not say") {
                        const optionElement = document.createElement("BUTTON");
                        optionElement.innerHTML = option;
                        optionElement.onclick = function () {
                            getCurrentWindow().then((currentWindow) => {
                                browser.windows.remove(currentWindow.id);
                            });
                        }
                        this.containerEl.append(optionElement);
                        this.containerEl.appendChild(document.createElement("br"));
                    }
                    else {
                        const optionElement = document.createElement("BUTTON");
                        optionElement.innerHTML = option;
                        optionElement.onclick = function () {
                            popup.returnAnswer(option);
                        }
                        this.containerEl.append(optionElement);
                        this.containerEl.appendChild(document.createElement("br"));
                    }
                }
            }
            else {
                //911 error. Close window.
                console.error("no options found in render");

                getCurrentWindow().then((currentWindow) => {
                    browser.windows.remove(currentWindow.id);
                });
            }
            this.state.receivedOptions = "false";
        }

        // If selection has been made, close window. 
        if (this.state.lastMessage != undefined) {
            getCurrentWindow().then((currentWindow) => {
                browser.windows.remove(currentWindow.id);
            });
        }
    }

    returnAnswer(answer) {
        // On response close the window
        setTimeout(() => {
            this.setState({ lastMessage: { text: answer, type: "success" } });
        }, 200);

        // set_user_selection
        // and requestId
        setUserSelection(answer);

        return;
    }
}

const popup = new Popup(document.getElementById('app'));
popup.render();


//browser.runtime.onMessage.addListener(async (msg) => {
//  if (msg.type === "new-collected-images") {
//    let collectedBlobs = popup.state.collectedBlobs || [];
//    const fetchRes = await fetchBlobFromUrl(msg.url);
//    collectedBlobs.push(fetchRes);
//    popup.setState({collectedBlobs});
//    return true;
//  }
//});

/*****************************************************************
 * Message Handlers
 ****************************************************************/

// Get the headers for the requestId
function getHdrs() {
    const sending = browser.runtime.sendMessage({
        type: "get_hdrs",
        requestId: popup.state.requestId
    });
    sending.then(updatehdrs, onError);
}

// Update the headers when get_hdrs message gets a reply.
function updatehdrs(response) {
    let headers = popup.state.headers || [];
    for (const hdr of response) {
        headers.push(hdr);
    }
    popup.setState({ headers });
}

// Update the options when get_options message gets a reply.
browser.runtime.sendMessage({ type: "get_options" }).then(async response => {
    let options = popup.state.options || [];
    for (const option of response) {
        options.push(option);
    }
    popup.state.receivedOptions = "true";
    popup.setState({ options });
});


// On User selection get the requestId and send the response back
function setUserSelection(selection) {
    if (popup.state.requestId === undefined || popup.state.requestId === "") {
        console.log("could not find the requestId hdr");
    }
    else {
        try {
            console.log("user selection is :" + selection);
            browser.runtime.sendMessage({
                type: "set_user_selection",
                response: selection,
                requestId: popup.state.requestId
            });
        }
        catch {
            console.log("could not return message to background");
        }
    }
    return
}

// Get current window
function getCurrentWindow() {
    return browser.windows.getCurrent();
}

function onError(error) {
    console.log(`Error: ${error}`);
}