/*****************************************************************
 * Background.js
 *     HttpSendInfo : This extenstion opens a dialog box to the
 *     user. On user selection the extension sends traffic info
 *     to storage.
 ****************************************************************/


/*****************************************************************
 * Global Variables
 ****************************************************************/
let targetPage = "<all_urls>"; // Which pages trigger the dialog box

let globalHeaders = [];    // Used to pass message to popup window
let DEBUG = "ON";
let optionsSendWith = "Python"
let optionsExtendedWith = "";
let FirefoxPID = "";
let popupOptionsList = [];
let CREATEAPIADDRESS = undefined;
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
// extendedData: [], eventData that might want to be saved
// host: "", domain name of the server
// port: "", TCP port number on which the server is listening
// completedTime: "", from Completed Details
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
        console.log(requests);
    }

    // Create an entry for this request
    // Check if there is an entry for this requestId
    let requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
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
            destinationPort: "",
            BeforeRedirectDestIp: "",
            globalHdrs: [],
            completedIp: "",
            requestStatus: "",
            extendedData: []
        };
        requests.push(newRequest);

        requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
        if (requestHandle === undefined) {
            // Should be an error
            // Even redirects get a new request id. 
            console.error("Request not found after creating request");
            console.log(eventDetails);
        }
    }
    else {
        //Redirected?
        if (requestHandle.requestStatus != "Redirected") {
            console.error("Request in before request again without redirection");
            console.log(requestHandle);
        }
        else {
            requestHandle.originalUrl = requestHandle.url;
            requestHandle.url = eventDetails.url;
        }
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

    // Get event datails?
    if (optionsExtendedWith === "All" || optionsExtendedWith.includes("BeforeRequest")) {
        extendedData = { source: "BeforeRequest", eventDetails: eventDetails };
        requestHandle.extendedData.push(extendedData);
    }

}

/* onBeforeSendHeaders Handler
   This event is triggered before sending any HTTP data, but after all HTTP headers are available.
   This is a good place to listen if you want to modify HTTP request headers. */
function logOnBeforeSendHeaders(eventDetails) {
    if (DEBUG === "ON") {
        console.log("Entrace to logOnBeforeSendHeaders");
        console.log(eventDetails);
        console.log(requests);
    }

    requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
    if (requestHandle === undefined) {
        // Should be an error
        // Even redirects get a new request id. 
        console.error("Request not found after creating request");
        console.log(eventDetails);
    }

    // Get HOST ip and port number
    for (let hdr of eventDetails.requestHeaders) {
        if (hdr.name.toLowerCase() === "host") {
            requestHandle.host = hdr.value;
        }
        if (hdr.name.toLowerCase() === "port") {
            requestHandle.port = hdr.value;
        }
    }

    // If no port is included, the default port for the service requested is implied (e.g., 443 for an HTTPS URL, and 80 for an HTTP URL).
    if (requestHandle.port === undefined) {
        let type = eventDetails.url.split(':')[0];
        if (type.toLowerCase() === "https") {
            requestHandle.destinationPort = "443";
        }
        else if (type.toLowerCase() === "http") {
            requestHandle.destinationPort = "80";
        }
        else {
            requestHandle.destinationPort = undefined;
        }
    }


    // Get event datails?
    if (optionsExtendedWith === "All" || optionsExtendedWith.includes("BeforeSendHeaders")) {
        extendedData = { source: "BeforeSendHeaders", eventDetails: eventDetails };
        requestHandle.extendedData.push(extendedData);
    }
}

/* onSendHeaders
   This event is fired just before sending headers.
   If your extension or some other extension modified headers in onBeforeSendHeaders,
   you'll see the modified version here. */
function logOnSendHeaders(eventDetails) {
    if (DEBUG === "ON") {
        console.log("Entrace to logOnSendHeaders");
        console.log(eventDetails);
    }

    requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
    if (requestHandle === undefined) {
        // Should be an error
        // Even redirects get a new request id. 
        console.error("Request not found after creating request");
        console.log(eventDetails);
    }

    // Get event datails?
    if (optionsExtendedWith === "All" || optionsExtendedWith.includes("SendHeaders")) {
        extendedData = { source: "SendHeaders", eventDetails: eventDetails };
        requestHandle.extendedData.push(extendedData);
    }
}

/* onHeadersReceived
   Fired when the HTTP response headers for a request are received.
   Use this event to modify HTTP response headers. */
function logOnHeadersReceived(eventDetails) {
    if (DEBUG === "ON") {
        console.log("Entrace to logOnHeadersReceived");
        console.log(eventDetails);
        console.log(requests);
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

        // Check if it got response from cache
        if (eventDetails.ip === null) {
            const requestHandleBkp = requests.find(({ url }) => url === eventDetails.url);
            if (requestHandleBkp === undefined) {
                console.error("The request ip is null and cannot be retrieved from backup : rqst : " + eventDetails.url);
            }
            else {
                requestHandle.destinationIp = requestHandleBkp.destinationIp;

                // Mark to remove the original and let the new one be referenced
                requestHandleBkp.statusCode = "Remove";
            }
        }
        else {
            requestHandle.destinationIp = eventDetails.ip;
        }
    }



    // Get event datails?
    if (optionsExtendedWith === "All" || optionsExtendedWith.includes("HeadersReceived")) {
        extendedData = { source: "HeadersReceived", eventDetails: eventDetails };
        requestHandle.extendedData.push(extendedData);
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
    const requestHandle = requests.find(({ id }) => id === eventDetails.requestId);

    if (requestHandle === undefined) {
        // why are we here without a request for this requestId?
        console.error("No request struct for id: " + eventDetails.requestId + " in logOnBeforeRedirect!!!");
    }
    else {
        requestHandle.requestStatus = "Redirected";
    }

    // Get event datails?
    if (optionsExtendedWith === "All" || optionsExtendedWith.includes("BeforeRedirect")) {
        extendedData = { source: "BeforeRedirect", eventDetails: eventDetails };
        requestHandle.extendedData.push(extendedData);
    }
}

/* onResponseStarted
   Fired when the first byte of the response body is received. */
function logOnResponseStarted(eventDetails) {
    if (DEBUG === "ON") {
        console.log("Entrace to logOnResponseStarted");
        console.log(eventDetails);
        console.log(requests);
    }

    requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
    if (requestHandle === undefined) {
        // Should be an error
        // Even redirects get a new request id. 
        console.error("No request struct for id: " + eventDetails.requestId + " in logOnResponseStarted!!!");
    }

    // Get event datails?
    if (optionsExtendedWith === "All" || optionsExtendedWith.includes("ResponseStarted")) {
        extendedData = { source: "ResponseStarted", eventDetails: eventDetails };
        requestHandle.extendedData.push(extendedData);
    }
}

/* onCompleted
   Fired when a request has completed. */
async function logOnCompleted(eventDetails) {
    if (DEBUG === "ON") {
        console.log("Entrace to logOnCompleted");
        console.log(eventDetails);
        console.log(requests);
    }

    // Log onCompleted time
    const requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
    if (requestHandle === undefined) {
        // why are we here without a request for this requestId?
        console.error("No request for id: " + eventDetails.requestId + " in logOnCompleted!!!");
    }
    else {
        requestHandle.completedTime = eventDetails.timeStamp;
        // The onCompleted ip might yet be different here
        requestHandle.completedIp = eventDetails.ip;
        requestHandle.requestStatus = eventDetails.statusCode;
    }

    // Call pop up
    if (eventDetails.method.toLowerCase() === "get" && eventDetails.type.toLowerCase() === "main_frame") {
        console.log(requestHandle);
        try {
            browser.windows.create({
                type: "popup", url: "/popup.html",
                top: 0, left: 0, width: 400, height: 300,
                titlePreface: "%" + requestHandle.id + "%"
            });
        }
        catch (err) {
            console.log("Creating popup failed");
            console.error(err);
        }

        // Lets look for any straggler requests
        // We do this here because this is less likely to happen so we don't do it often and slow everything else down
        for (let rqst of requests) {
            if (rqst.method.toLowerCase() != "get" || rqst.type.toLowerCase() != "main_frame" || rqst.statusCode === "Remove") {
                result = requests.findIndex(({ id }) => id === rqst.id);
                if (result === -1) {
                    // why are we here without a request for this requestId?
                    console.error("No request for id: " + rqst.id + " in logOnCompleted!!!");
                }
                while (result != -1) {
                    requests.splice(result, 1);
                    result = requests.findIndex(({ id }) => id === rqst.id);
                }
            }
        }
    }

    // Get event details?
    if (optionsExtendedWith === "All" || optionsExtendedWith.includes("Completed")) {
        extendedData = { source: "Completed", eventDetails: eventDetails };
        requestHandle.extendedData.push(extendedData);
    }

    // destroy request for anything not "GET" and "main_frame"
    if (requestHandle.method.toLowerCase() != "get" || requestHandle.type.toLowerCase() != "main_frame") {
        result = requests.findIndex(({ id }) => id === eventDetails.requestId);
        if (result === -1) {
            // why are we here without a request for this requestId?
            console.error("No request for id: " + eventDetails.requestId + " in onCompleted!!!");
        }
        while (result != -1) {
            requests.splice(result, 1);
            result = requests.findIndex(({ id }) => id === eventDetails.requestId);
        }
    }
    else {
        // destroy duplicate requests. LILO
        duplicate = requests.find(({ url }) => url === requestHandle.url);
        if (duplicate === undefined) {
            // This is bad because it should at least find itself in here.
            console.error("GET Main_Frame request url : " + requestHandle.url + " does not exist in delete dupes in onCompleted!")
        }

        while (duplicate != undefined) {
            if (duplicate.completedTime != requestHandle.completedTime) {
                // Delete dupe
                dupeIndex = requests.findIndex(({ id }) => id === duplicate.id);
                requests.splice(dupeIndex, 1);
                duplicate = requests.find(({ url }) => url === requestHandle.url);
            }
            else {
                // Itself. Break while
                break;
            }
        }
    }
}

/* callNative
 * This function is called when the user makes a selection or when new request need to be saved
 * the selection along with netstat data is ready to be sent to database */

function handleStartup() {
    // This function is not called when we manually load
    // Moving all of the code that would be in handleStartup to logCreateTab
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

    // Check if output file exists if not create it
    // Get the options
    state = "session_start";
    message = {
        state: state,
        dataIn: [],
        dataOut: [],
        exitMessage: ""
    };

    callNative();
}

function callNative() {
    //  if (DEBUG === "ON") {
    console.log("In callNative");
    console.log("message is : " + JSON.stringify(message));
    console.log(message);
    //  }
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
    else {
        console.log("In onResponse");
        console.log(response);
    }

    if (response.state === "session_start") {
        // Default to 
        optionsSendWith = "Python"
        optionsExtendedWith = "";
        popupOptionsList = [];

        // Get set options
        for (var i = 0; i < response.dataOut.length; i++) {
            if (response.dataOut[i][0] === "-s") {
                console.log("option " + response.dataOut[i][0] + " with : " + response.dataOut[i][1]);
                optionsSendWith = "Extension";
                CREATEAPIADDRESS = response.dataOut[i][1];
            }
            if (response.dataOut[i][0] === "-E") {
                console.log("option " + response.dataOut[i][0] + " with : " + response.dataOut[i][1]);
                optionsExtendedWith = response.dataOut[i][1];
            }
            if (response.dataOut[i][0] === "popupOption") {
                console.log("option " + response.dataOut[i][0] + " with : " + response.dataOut[i][1]);
                popupOptionsList.push(response.dataOut[i][1]);
            }
            if (response.dataOut[i][0] === "FirefoxPID") {
                console.log("option " + response.dataOut[i][0] + " with : " + response.dataOut[i][1]);
                FirefoxPID = response.dataOut[i][1];
            }
        }
    }

    if (response.state === "add_connection") {
        console.log("options sendwith is " + optionsSendWith);
        if (response.dataOut.connections.length > 0) {
            for (let connection of response.dataOut.connections) {
                if (optionsSendWith === "Extension") {
                    var request = new XMLHttpRequest();
                    request.open("POST", CREATEAPIADDRESS);
                    request.setRequestHeader("Content-Type", "application/json");
                    request.overrideMimeType("text/plain");
                    request.onload = function () {
                        console.log("Response received: " + request.responseText);
                    };
                    console.log("connection :" + JSON.stringify(connection));
                    request.send(JSON.stringify(connection));
                }
                else {
                    console.log("connection :" + JSON.stringify(connection));
                }
            }
        }
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

    /* get_options  */
    if (msg.type === "get_options") {
        popupOptions = popupOptionsList;
        console.log("in get_options background");
        console.log(popupOptions);
        return Promise.resolve(popupOptions);
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
                    destinationPort: requestHandle.destinationPort,
                    userSelection: requestHandle.userSelection,
                    epochTime: requestHandle.completedTime,
                    completedIp: requestHandle.completedIp,
                    requestId: requestHandle.id,
                    originalDestIp: requestHandle.originalDestIp,
                    extendedData: requestHandle.extendedData,
                    FirefoxPID: FirefoxPID
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
// onBeforeSendHeaders Listener
browser.webRequest.onBeforeSendHeaders.addListener(
    logOnBeforeSendHeaders,
    { urls: [targetPage] },
    ["blocking", "requestHeaders"]
);
//  onSendHeaders Listener
browser.webRequest.onSendHeaders.addListener(
    logOnSendHeaders,
    { urls: [targetPage] },
    ["requestHeaders"]
);
// onHeadersReceived
browser.webRequest.onHeadersReceived.addListener(
    logOnHeadersReceived,
    { urls: [targetPage] },
    ["blocking", "responseHeaders"]
);
// onResponseStarted
browser.webRequest.onResponseStarted.addListener(
    logOnResponseStarted,
    { urls: [targetPage] },
    ["responseHeaders"]
);
// OnCompleted Listener
browser.webRequest.onCompleted.addListener(
    logOnCompleted,
    { urls: [targetPage] },
    ["responseHeaders"]);
// OnBeforeRedirect
browser.webRequest.onBeforeRedirect.addListener(
    logOnBeforeRedirect,
    { urls: [targetPage] }
);

// onStartup
// Get the global options
browser.runtime.onStartup.addListener(handleStartup);

// Tab Created Listener
browser.tabs.onCreated.addListener(logCreatedTab);

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