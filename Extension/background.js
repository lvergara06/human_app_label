/*****************************************************************
 * Background.js
 *     HttpSendInfo : This extenstion opens a dialog box to the
 *     user. On user selection the extension sends traffic info
 *     to storage.
 ****************************************************************/


/*****************************************************************
 * Global Variables
 ****************************************************************/
let targetPage = "https://*./"; // Which pages trigger the dialog box

let globalHeaders = [];    // Used to pass message to popup window
let DEBUG = "ON";
let optionsSendWith = "Python"
let redirectNeeded = undefined;  // If the request needs a redirection
let message = [];                // Message to be passed to native application {state "" , dataIn [] , dataOut [] , errorMessage ""}
let requests = [];               // Requests made so far
// {
// id: "", request id from request headers
// url: "", url from user 
// method: "", get method from request headers
// type: "", type of object to fetch (in our case only main_frame)
// timeStamp: 0, epoch time from request headers
// tabId: "", the tab id that started the request
// destinationIp: "", the destination ip from response headers
// originalDestIp: "", the destination ip from response headers if there is redicetion involved
// globalHdrs: [], messages to pass to pop up windows
// completedIp: "", destination ip if the compleded ip address is not like the response ip
// requestStatus: "" the status of this request. 
// }


/*****************************************************************
 * Event Handlers
 ****************************************************************/

/* onBeforeRequest Handler
   This event is triggered when a request is about to be made, and before headers are available.
   This is a good place to listen if you want to cancel or redirect the request. */
// This function opens a dialog box, if yes is selected then headers are logged
function logOnBeforeRequest(eventDetails) {
    if (DEBUG === "ON") {
        console.log("Entrace to logOnBeforeRequest");
        console.log(eventDetails);
    }

    // Create an entry for this request
    // Check if there is an entry for this requestId
    if (redirectNeeded === undefined) {
        const requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
        if (requestHandle === undefined) // Create the request 
        {
            newRequest = {
                id: eventDetails.requestId,
                url: eventDetails.url,
                method: eventDetails.method,
                type: eventDetails.type,
                timeStamp: eventDetails.timeStamp,
                tabId: eventDetails.tabId,
                destinationIp: "",
                BeforeRedirectDestIp: "",
                globalHdrs: [],
                completedIp: "",
                requestStatus: ""
            };
            requests.push(newRequest);
        }
        else {
            // A bit weird if this happens because any given request should not be here twice
            // Even redirects get a new request id. 
            console.log("request found at OnBeforeRequest!");
            console.log(requestHandle);
            console.log(eventDetails);
        }
    }
    else {
        // Redirect needed
        // Do not let original request go orphaned
        const redirectHandle = redirectNeeded.find(({ tabId }) => tabId === eventDetails.tabId);

        if (redirectHandle === undefined) {
            // Redirect was not triggered by this event's tabId
            // Create the request 
            const requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
            if (requestHandle === undefined) // Create the request 
            {
                newRequest = {
                    id: eventDetails.requestId,
                    url: eventDetails.url,
                    method: eventDetails.method,
                    type: eventDetails.type,
                    timeStamp: eventDetails.timeStamp,
                    tabId: eventDetails.tabId,
                    destinationIp: "",
                    BeforeRedirectDestIp: "",
                    globalHdrs: [],
                    completedIp: "",
                    requestStatus: "Started"
                };
                requests.push(newRequest);
            }
            else {
                // A bit weird if this happens because any given request should not be here twice
                // Even redirects get a new request id. 
                console.log("request found at OnBeforeRequest!");
                console.log(requestHandle);
                console.log(eventDetails);
            }
        }
        else {
            // This event's tab requested the redirect
            const requestHandle = requests.find(({ id }) => id === redirectHandle.origRequestId);
            if (requestHandle === undefined) {
                // What a strange scenario if no original request is found
                console.log("original request not found for redirect! tabId:" + redirectHandle.tabId + " original request: " + redirectHandle.origRequestId);
            }
            else {
                // Lets use the same request with updated id and timeStamp
                requestHandle.id = eventDetails.requestId;
                requestHandle.timeStamp = eventDetails.timeStamp;
                requestHandle.requestStatus = "Redirected";

                // destroy redirect 
                redirectIndex = redirectNeeded.findIndex(({ origRequestId }) => origRequestId === redirectHandle.origRequestId);
                if (redirectIndex === -1) {
                    // why are we here without a request for this requestId?
                    console.error("No redirect entry for : " + redirectHandle.origRequestId + "!!!");
                }
                else {
                    requests.splice(redirectIndex, 1);
                }

                if (redirectNeeded.length === 0) {
                    redirectNeeded === undefined;
                }
            }
        }
    }

    requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
    if (requestHandle === undefined) {
        // Should be an error
        // Even redirects get a new request id. 
        console.error("Request not found after creating request");
        console.log(eventDetails);
    }
    // Save headers to send to popup
    try {
        const urlHdr = requestHandle.globalHdrs.find(({ name }) => name === "url");
        if (urlHdr === undefined) {
            requestHandle.globalHdrs.push({ name: "url", value: eventDetails.url });
        }
        else {
            urlHdr.value = eventDetails.url;
        }
    } catch (err) {
        console.log("passing headers failed");
        console.error(err);
    }
}

/* onHeadersReceived
   Fired when the HTTP response headers for a request are received.
   Use this event to modify HTTP response headers. */
function logOnHeadersReceived(eventDetails) {
    if (DEBUG === "ON") {
        console.log("Entrace to logOnHeadersReceived");
        console.log(eventDetails);
    }

    // Add destinationIp to the request 
    const requestHandle = requests.find(({ id }) => id === eventDetails.requestId);

    if (requestHandle === undefined) {
        // why are we here without a request for this requestId?
        console.error("No request struct for id: " + eventDetails.requestId + " in lonOnHeadersReceived!!!");
    }
    else {
        if (requestHandle.Status === "Redirected") {
            // When a redirect is needed we might have a different ip address to track
            if (requestHandle.destinationIp != eventDetails.ip) {
                result.BeforeRedirectDestIp = result.detinationIp;
            }
        }

        requestHandle.destinationIp = eventDetails.ip;
    }
}

/* onBeforeRedirect
   Fired when a request has completed. */
function logOnBeforeRedirect(eventDetails) {
    if (DEBUG === "ON") {
        console.log("Entrace to logOnBeforeRedirect");
        console.log(eventDetails);
    }

    // Create a redirection entry
    if (redirectNeeded === undefined) {
        redirectNeeded = [];
    }

    const redirectRequest = {
        tabId: eventDetails.tabId,
        origRequestId: eventDetails.requestId
    }
    redirectNeeded.push(redirectRequest);
}

/* onCompleted
   Fired when a request has completed. */
async function logOnCompleted(eventDetails) {
    if (DEBUG === "ON") {
        console.log("Entrace to logOnCompleted");
        console.log(eventDetails);
    }

    // Log onCompleted time
    const requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
    if (requestHandle === undefined) {
        // why are we here without a request for this requestId?
        console.error("No request for id: " + eventDetails.requestId + " in logOnCompleted!!!");
    }
    else {
        requestHandle.epochTime = eventDetails.timeStamp;
        // The onCompleted ip might yet be different here
        requestHandle.completedIp = eventDetails.ip;
        requestHandle.requestStatus = eventDetails.statusCode;
    }

    // Call pop up

    if (eventDetails.method.toLowerCase() === "get") {
        console.log(requestHandle);
        try {
            browser.windows.create({
                type: "popup", url: "/popup.html",
                top: 0, left: 0, width: 400, height: 300,
                titlePreface: "%" + requestHandle.id + "%"
            });
        } catch (err) {
            console.log("Creating popup failed");
            console.error(err);
        }
    }
}

/* Tab
   This is a good place to start the app.
   Send an init message to the app. */
// Window
function logCreatedTab(createdTab) {
    if (DEBUG === "ON") {
        console.log("Entrace to logCreatedTab");
        console.log(createdTab);
    }

    // Call native function to prepare things for this tab
    tabInfo = { tabId: createdTab.id };
    state = "create_tab";
    message = {
        state: state,
        dataIn: tabInfo,
        dataOut: [],
        exitMessage: ""
    };

    callNative();
}

function handleRemoved(removedId, removeInfo) {
    console.log("removing tabId = " + removedId)
    // close and delete file
    tabInfo = { tabId: removedId };
    state = "delete_tab";
    message = {
        state: state,
        dataIn: tabInfo,
        dataOut: [],
        exitMessage: ""
    };

    // destroy request
    result = requests.findIndex(({ tabId }) => tabId === removedId);
    if (result === -1) {
        // why are we here without a request for this requestId?
        console.error("No request for tabId: " + removedId + " in handleRemoved!!!");
    }

    while (result != -1) {
        requests.splice(result, 1);
        result = requests.findIndex(({ tabId }) => tabId === removedId);
    }
    callNative();

    console.log(removeInfo);
}

/* callNative
 * This function is called when the user makes a selection or when new request need to be saved
 * the selection along with netstat data is ready to be sent to database */
function callNative() {
    console.log("In callNative");

    // dataIn is the input to the native program
    console.log("message is :")
    console.log(message);
    // Send the message to send all data to database
    var sending = browser.runtime.sendNativeMessage(
        "Transport",
        message);
    sending.then(onResponse, onError);
}

function onResponse(response) {
    if (DEBUG === "ON") {
        console.log("In onResponse");
        console.log(response);
    }
}

/*****************************************************************
 * Message Handlers
 ****************************************************************/

browser.runtime.onMessage.addListener((msg) => {
    /* get_hdrs  */
    if (msg.type === "get_hdrs") {
        const requestHandle = requests.find(({ id }) => id === msg.requestId);
        if (requestHandle === undefined) {
            // why are we here without a request for this requestId?
            console.error("No request for id: " + eventDetails.requestId + " in get_hdrs!!!");
        }
        else {
            hdrs = requestHandle.globalHdrs;
        }
        requestHandle.globalHdrs = [];
        return Promise.resolve(hdrs);
    }

    // set_user_selection
    if (msg.type === "set_user_selection") {
        state = "add_connection"
        const requestHandle = requests.find(({ id }) => id === msg.requestId);
        if (requestHandle === undefined) {
            // why are we here without a request for this requestId?
            console.error("No request for id: " + eventDetails.requestId + " in get_hdrs!!!");
        }
        else {
            requestHandle.userSelection = msg.response;
            message = {
                state: state,
                dataIn: [{
                    tabId: requestHandle.tabId,
                    destinationIp: requestHandle.destinationIp,
                    userSelection: requestHandle.userSelection,
                    epochTime: requestHandle.epochTime,
                    completedIp: requestHandle.completedIp,
                    requestId: requestHandle.requestId,
                    originalDestIp: requestHandle.originalDestIp
                }],
                dataOut: [],
                optionsSendWith: optionsSendWith,
                exitMessage: ""
            };
            callNative();
            return Promise.resolve(true);
        }
    }
});

/*****************************************************************
 * Event Listeners
 ****************************************************************/
// onBeforeRequest Listener
browser.webRequest.onBeforeRequest.addListener(
    logOnBeforeRequest,
    { urls: [targetPage] },
    ["requestBody"]
);
// onHeadersReceived
browser.webRequest.onHeadersReceived.addListener(
    logOnHeadersReceived,
    { urls: [targetPage] },
    ["blocking", "responseHeaders"]
);
// OnCompleted Listener
browser.webRequest.onCompleted.addListener(
    logOnCompleted,
    { urls: ["<all_urls>"], types: ["main_frame"] },
    ["responseHeaders"]);
// OnBeforeRedirect
browser.webRequest.onBeforeRedirect.addListener(
    logOnBeforeRedirect,
    { urls: [targetPage] }
);

// Tab Created Listener
browser.tabs.onCreated.addListener(logCreatedTab);

// Tab Removed Listener
browser.tabs.onRemoved.addListener(handleRemoved);

/*****************************************************************
 * Helper Functions
 *
 ****************************************************************/
// Log Errors
function onError(error) {
    console.log(`Error: ${error}`);
}

// On Installed
//browser.runtime.onInstalled.addListener(() => {
//    browser.contextMenus.create({
//        "id": "sampleContextMenu",
//        "title": "Sample Context Menu",
//        "contexts": ["selection"]
//    });
//});

// Local Storage
//set
// browser.storage.local.set({ variable: variableInformation });
//get
//browser.storage.local.get(['variable'], (result) => {
//let someVariable = result.variable;
  // Do something with someVariable
//});