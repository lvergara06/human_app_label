/* global saveCollectedBlobs, uuidv4, preventWindowDragAndDrop */

"use strict";

class Popup {
    constructor(containerEl) {
        this.containerEl = containerEl;

        this.state = {
            headers: [],
            lastMessage: undefined,
            firstRender: "true",
            requestId: ""
        };

        this.onClickNews = this.onClickNews.bind(this);
        this.onClickStream = this.onClickStream.bind(this);
        this.onClickSocial = this.onClickSocial.bind(this);
        this.onClickNo = this.onClickNo.bind(this);
        this.returnAnswer = this.returnAnswer.bind(this);

        this.containerEl.querySelector("button.answer-news").onclick = this.onClickNews;
        this.containerEl.querySelector("button.answer-stream").onclick = this.onClickStream;
        this.containerEl.querySelector("button.answer-social").onclick = this.onClickSocial;
        this.containerEl.querySelector("button.answer-na").onclick = this.onClickNo;

    }

    setState(state) {
        // Merge the new state on top of the previous one and re-render everything.
        this.state = Object.assign(this.state, state);
        this.render();
    }

    onClickNews() {
        this.returnAnswer("News")
    }

    onClickStream() {
        this.returnAnswer("Stream")
    }

    onClickSocial() {
        this.returnAnswer("Social")
    }

    onClickNo() {
        setTimeout(() => {
            this.setState({ lastMessage: { text: "no", type: "success" } });
        }, 20);

        return;
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

preventWindowDragAndDrop();

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

// Get current window
function getCurrentWindow() {
    return browser.windows.getCurrent();
}

// Update the headers when get_hdrs message gets a reply.
function updatehdrs(response) {
    let headers = popup.state.headers || [];
    for (const hdr of response) {
        headers.push(hdr);
    }
    popup.setState({ headers });
}

function onError(error) {
    console.log(`Error: ${error}`);
}


// On User selection get the requestId and send the response back
function setUserSelection(selection) {
    if (popup.state.requestId === undefined || popup.state.requestId === "") {
        console.log("could not find the requestId hdr");
    }
    else {
        try {
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

