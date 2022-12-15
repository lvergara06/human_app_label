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
let os = "";
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

    trace("logOnBeforeRequest", eventDetails);

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
            extendedData: [],
            statusCode: "New",
            originalUrl: undefined,
            userSelection: undefined,
            originUrl: undefined
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
    if (eventDetails.type.toLowerCase() === "main_frame" && eventDetails.method.toLowerCase() === "get") {

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

    logEvent("BeforeRequest", eventDetails, requestHandle);
}

/* onBeforeSendHeaders Handler
   This event is triggered before sending any HTTP data, but after all HTTP headers are available.
   This is a good place to listen if you want to modify HTTP request headers. */
function logOnBeforeSendHeaders(eventDetails) {
    trace("logOnBeforeSendHeaders", eventDetails);

    requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
    if (requestHandle === undefined) {
        // Should be an error
        // Even redirects get a new request id. 
        console.error("Request not found after creating request");
        console.log(eventDetails);
    }

    // Get HOST ip ,port number, connection
    for (let hdr of eventDetails.requestHeaders) {
        if (hdr.name.toLowerCase() === "host") {
            requestHandle.host = hdr.value;
        }
        if (hdr.name.toLowerCase() === "port") {
            requestHandle.port = hdr.value;
        }
        if (hdr.name.toLowerCase() === "connection") {
            hdr.value = "Close";  // TAKE ME OUT
            if (hdr.value.toLowerCase() === "keep-alive") {
                requestHandle.persistent = "true";
            }
            else if (hdr.value.toLowerCase() === "close") {
                requestHandle.persistent = "false";
            }
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

    // If the request connection is "stay-alive" we assume that the connection will create a single flow.
    // If the request connection in turn is "close" we will assume that subsequent http requests will create unique flows.
    if (requestHandle.persistent === undefined) {
        // default to non persistent
        requestHandle.persistent = "false";
    }

    // Get event datails?
    logEvent("BeforeSendHeaders", eventDetails, requestHandle);

    return { requestHeaders: eventDetails.requestHeaders };  // TAKE ME OUT
}

/* onSendHeaders
   This event is fired just before sending headers.
   If your extension or some other extension modified headers in onBeforeSendHeaders,
   you'll see the modified version here. */
function logOnSendHeaders(eventDetails) {
    trace("logOnSendHeaders", eventDetails);

    requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
    if (requestHandle === undefined) {
        // Should be an error
        // Even redirects get a new request id. 
        console.error("Request not found after creating request");
        console.log(eventDetails);
    }

    // TIME STAMP TO USED TO FIND FLOW!!!!
    requestHandle.timeStamp = eventDetails.timeStamp;

    // Get event datails?
    logEvent("SendHeaders", eventDetails, requestHandle);
}

/* onHeadersReceived
   Fired when the HTTP response headers for a request are received.
   Use this event to modify HTTP response headers. */
function logOnHeadersReceived(eventDetails) {
    trace("logOnHeadersReceived", eventDetails);

    // Add destinationIp to the request 
    const requestHandle = requests.find(({ id }) => id === eventDetails.requestId);

    if (requestHandle === undefined) {
        // why are we here without a request for this requestId?
        console.error("No request struct for id: " + eventDetails.requestId + " in lonOnHeadersReceived!!!");
    }
    else {
        // Check if it got response from cache
        if (eventDetails.ip === null) {
            const requestHandleBkp = requests.find(({ url }) => url === eventDetails.url);
            if (requestHandleBkp === undefined) {
                console.error("Request from cache : " + eventDetails.url + " does not exist in backups");
            }
            else {
                while (requestHandleBkp != undefined) {
                    if (requestHandleBkp.id != requestHandle.id) {
                        requestHandle.destinationIp = requestHandleBkp.destinationIp;
                        // Mark to remove the original and let the new one be referenced
                        requestHandleBkp.statusCode = "Remove";
                    }
                    else {
                        // Itself. Break while
                        break;
                    }
                }
            }
        }
        else {
            if (requestHandle.requestStatus === "Redirected") {
                // When a redirect is needed we might have a different ip address to track
                if (requestHandle.destinationIp != eventDetails.ip) {
                    requestHandle.BeforeRedirectDestIp = requestHandle.detinationIp;
                }
            }
            requestHandle.destinationIp = eventDetails.ip;
        }
    }

    // Get event datails?
    logEvent("HeadersReceived", eventDetails, requestHandle);
}

/* onBeforeRedirect
   Fired when a request has completed. */
function logOnBeforeRedirect(eventDetails) {
    trace("logOnBeforeRedirect", eventDetails);

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
    logEvent("BeforeRedirect", eventDetails, requestHandle);
}

/* onResponseStarted
   Fired when the first byte of the response body is received. */
function logOnResponseStarted(eventDetails) {
    trace("BeforeRedirect", eventDetails);

    requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
    if (requestHandle === undefined) {
        // Should be an error
        // Even redirects get a new request id. 
        console.error("No request struct for id: " + eventDetails.requestId + " in logOnResponseStarted!!!");
    }

    // Get event datails?
    logEvent("ResponseStarted", eventDetails, requestHandle);
}

/* onCompleted
   Fired when a request has completed. */
async function logOnCompleted(eventDetails) {
    trace("logOnCompleted", eventDetails);

    // Log onCompleted time
    const requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
    if (requestHandle === undefined) {
        // why are we here without a request for this requestId?
        console.error("No request for id: " + eventDetails.requestId + " in logOnCompleted!!!");
    }
    else {
        requestHandle.completedTime = eventDetails.timeStamp;
        if (requestHandle.statusCode === "New") {
            requestHandle.statusCode = "Waiting";
        }

        // If the ip is null get it from destinationIp
        if (eventDetails.ip != null) {
            requestHandle.completedIp = eventDetails.ip;
        }
        else {
            requestHandle.completedIp = requestHandle.destinationIp;
        }

        if (!(eventDetails.method.toLowerCase() === "get" && eventDetails.type.toLowerCase() === "main_frame")) {
            // If it is not persitent look for the get main_frame reference
            if (requestHandle.persistent != "true" && requestHandle.userSelection === undefined) {
                console.log("*****************");
                console.log("NON-PERSISTENT request id : " + requestHandle.id);
                console.log("*****************");

                // If the request is non persistent then we should check if the user selection has been made
                referenceRequestHandle = requests.find(({ host }) => host === requestHandle.host);
                if (referenceRequestHandle === undefined) {
                    if (!(eventDetails.type.toLowerCase() === "main_frame" && eventDetails.method.toLowerCase() === "get")) {
                        console.error("No reference for host: " + requestHandle.host + " , requestId : " + requestHandle.id);
                    }
                    requestHandle.statusCode = "Unprocessed";
                }
                else {
                    if (referenceRequestHandle.userSelection != undefined) {
                        requestHandle.userSelection = referenceRequestHandle.userSelection;
                    }
                    else {
                        requestHandle.statusCode = "Unprocessed";
                    }
                }
            }

            // If the request is a different host altogether
            if (eventDetails.originUrl != null && requestHandle.userSelection === undefined && requestHandle.statusCode === "Waiting") {
                // Check if we can find user selection from origin url
                requestHandle.originUrl = eventDetails.originUrl;

                referenceRequestHandle = requests.find(({ url }) => url === requestHandle.originUrl);
                if (referenceRequestHandle === undefined) {
                    console.error("No reference origin url: " + requestHandle.originUrl + ", requestId : " + requestHandle.id);
                    requestHandle.statusCode = "Orphaned";
                }
                else {
                    if (referenceRequestHandle.userSelection != undefined) {
                        requestHandle.userSelection = referenceRequestHandle.userSelection;
                    }
                    else {
                        requestHandle.statusCode = "Orphaned";
                    }
                }
            }
        }
        else if (eventDetails.method.toLowerCase() === "get" && eventDetails.type.toLowerCase() === "main_frame") {
            requestHandle.statusCode = "GetMain";
            // Call pop up
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
                if (rqst.statusCode === "Remove") {
                    result = requests.findIndex(({ id }) => id === rqst.id);
                    if (result === -1) {
                        // why are we here without a request for this requestId?
                        console.error("No request for id: " + rqst.id + " in logOnCompleted!!!");
                    }
                    while (result != -1) {
                        console.log("delete id : " + rqst.id + " in onCompleted because it was marked remove!!!");
                        requests.splice(result, 1);
                        result = requests.findIndex(({ id }) => id === rqst.id);
                    }
                }
            }
            // Check for dupe get main_frame
            // destroy duplicate requests. LILO
            duplicate = requests.find(({ url }) => url === requestHandle.url);
            if (duplicate === undefined) {
                // This is bad because it should at least find itself in here.
                console.error("GET Main_Frame request url : " + requestHandle.url + " does not exist in delete dupes in onCompleted!")
            }

            while (duplicate != undefined) {
                if (duplicate.completedTime != requestHandle.completedTime) {
                    // Delete dupe
                    console.log("deleted dupe: rqst id : " + duplicate.id);
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
    // // check again
    for (let rqst of requests) {

        if (rqst.statusCode === "Waiting") {
            referenceRequestHandle = requests.find(({ host }) => host === rqst.host);
            if (referenceRequestHandle === undefined) {
                console.error("No reference for host: " + rqst.host + " , requestId : " + rqst.id);
                rqst.statusCode = "Unprocessed";
            }
            else {
                if (referenceRequestHandle.userSelection != undefined) {
                    rqst.userSelection = referenceRequestHandle.userSelection;
                    rqst.statusCode = "SentReady";
                }
                else {
                    rqst.statusCode = "Unprocessed";
                }
            }
        }
        if (rqst.statusCode === "Waiting") {
            referenceRequestHandle = requests.find(({ url }) => url === rqst.originUrl);
            if (referenceRequestHandle === undefined) {
                console.error("No reference origin url: " + rqst.originUrl + ", requestId : " + rqst.id);
                rqst.statusCode = "Orphaned";
            }
            else {
                if (referenceRequestHandle.userSelection != undefined) {
                    rqst.userSelection = referenceRequestHandle.userSelection;
                    rqst.statusCode = "SentReady";
                }
                else {
                    rqst.statusCode = "Orphaned";
                }
            }
        }
    }

    for (let rqst of requests) {
        if (rqst.statusCode === "SentReady") {
            message = {
                state: state,
                dataIn: [{
                    tabId: rqst.tabId,
                    destinationIp: rqst.destinationIp,
                    destinationPort: rqst.destinationPort,
                    userSelection: rqst.userSelection,
                    epochTime: rqst.timeStamp,
                    completedIp: rqst.completedIp,
                    requestId: rqst.id,
                    originalDestIp: rqst.originalDestIp,
                    extendedData: rqst.extendedData,
                    FirefoxPID: FirefoxPID,
                    os: os
                }],
                dataOut: [],
                optionsSendWith: optionsSendWith,
                exitMessage: ""
            };
            callNative();

            rqst.statusCode = "Remove";
        }
    }
    // Clean up
    for (let rqst of requests) {
        if (rqst.statusCode === "Remove") {
            deleteRequest(rqst.id);
        }
    }
    // Get event details?
    logEvent("Completed", eventDetails, requestHandle);
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
    // check operating system for native app
    // we cannot make this synchronous so we are going to have to do everything inside
    // this function because we need the os info before we can call native app.
    browser.runtime.getPlatformInfo().then((info) => {

        os = info.os;

        if (DEBUG === "ON") {
            console.log("Entrace to logCreatedTab");
            console.log(os);
            console.log(createdTab);
        }

        // Check if output file exists if not create it
        // Get the options
        state = "session_start";
        message = {
            state: state,
            dataIn: [{ os: os }],
            dataOut: [],
            exitMessage: ""
        };

        callNative();
    });

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
        return Promise.resolve(popupOptions);
    }

    // set_user_selection
    if (msg.type === "set_user_selection") {
        state = "add_connection"
        const requestHandle = requests.find(({ id }) => id === msg.requestId);
        if (requestHandle === undefined) {
            // why are we here without a request for this requestId?
            console.error("No request for id: " + msg.requestId + " in get_user_selection!!!");
        }
        else {
            // This is the request for the get main_frame
            requestHandle.userSelection = msg.response;
            message = {
                state: state,
                dataIn: [{
                    tabId: requestHandle.tabId,
                    destinationIp: requestHandle.destinationIp,
                    destinationPort: requestHandle.destinationPort,
                    userSelection: requestHandle.userSelection,
                    epochTime: requestHandle.timeStamp,
                    completedIp: requestHandle.completedIp,
                    requestId: requestHandle.id,
                    originalDestIp: requestHandle.originalDestIp,
                    extendedData: requestHandle.extendedData,
                    FirefoxPID: FirefoxPID,
                    os: os
                }],
                dataOut: [],
                optionsSendWith: optionsSendWith,
                exitMessage: ""
            };
            callNative();

            // All other unprocessed requests
            console.log("about to process unprocessed");
            for( let rqst of requests) {
                console.log("in for each");
                console.log(rqst);
                console.log(requests);
                if (rqst.statusCode === "Unprocessed" && rqst.host === requestHandle.host && rqst.tabId === requestHandle.tabId) {
                    rqst.userSelection = msg.response;
                    message = {
                        state: state,
                        dataIn: [{
                            tabId: rqst.tabId,
                            destinationIp: rqst.destinationIp,
                            destinationPort: rqst.destinationPort,
                            userSelection: rqst.userSelection,
                            epochTime: rqst.timeStamp,
                            completedIp: rqst.completedIp,
                            requestId: rqst.id,
                            originalDestIp: rqst.originalDestIp,
                            extendedData: rqst.extendedData,
                            FirefoxPID: FirefoxPID,
                            os: os
                        }],
                        dataOut: [],
                        optionsSendWith: optionsSendWith,
                        exitMessage: ""
                    };
                    callNative();

                    rqst.statusCode = "Remove";
                }
                else if (rqst.statusCode === "Orphaned" && rqst.originUrl === requestHandle.url && rqst.tabId === requestHandle.tabId) {
                    console.log("*****************");
                    console.log("Other HOST request id : " + rqst.id);
                    console.log("*****************");
                    // If the request is non persistent then we should check if the user selection has been made
                    rqst.userSelection = requestHandle.userSelection;
                    // Off with it
                    message = {
                        state: state,
                        dataIn: [{
                            tabId: rqst.tabId,
                            destinationIp: rqst.destinationIp,
                            destinationPort: rqst.destinationPort,
                            userSelection: rqst.userSelection,
                            epochTime: rqst.timeStamp,
                            completedIp: rqst.completedIp,
                            requestId: rqst.id,
                            originalDestIp: rqst.originalDestIp,
                            extendedData: rqst.extendedData,
                            FirefoxPID: FirefoxPID,
                            os: os
                        }],
                        dataOut: [],
                        optionsSendWith: optionsSendWith,
                        exitMessage: ""
                    };
                    callNative();

                    rqst.statusCode = "Remove";
                }
            }
            // Clean up
            for (let rqst of requests) {
                if (rqst.statusCode === "Remove") {
                    deleteRequest(rqst.id);
                }
            }
        }
        return Promise.resolve(true);
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

function logEvent(source, eventDetails, requestHandle) {
    // Get event datails?
    if (optionsExtendedWith === "All" || optionsExtendedWith.includes(source)) {
        extendedData = { source: source, eventDetails: eventDetails };
        requestHandle.extendedData.push(extendedData);
    }
}

function trace(source, eventDetails) {
    if (DEBUG === "ON") {
        console.log("Entrace to " + source);
        console.log(eventDetails);
        console.log(requests);
    }
}

function deleteRequest(requestId) {
    // Delete processed rqst 
    result = requests.findIndex(({ id }) => id === requestId);
    if (result === -1) {
        // why are we here without a request for this requestId?
        console.error("No request for id: " + requestId + " in deleteRequest!!!");
    }

    while (result != -1) {
        requests.splice(result, 1);
        result = requests.findIndex(({ id }) => id === requestId);
    }
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
