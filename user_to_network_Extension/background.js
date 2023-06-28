/*****************************************************************
 * Background.js
 *     This extenstion opens a dialog box to the
 *     user. On user selection the extension sends traffic info
 *     to storage via a navtive app called Transport.py
 *     This extension extends the various APIs provided by Firefox
 *     on the different events of a request. Each event is analized
 *     for important information on the request or response headers. 
 * 20230605 - Luis Vergara - Refactored
 *                           Let write out all of the connections 
 *                           And keep all of the matching logic out.
 * 20230609 - Luis Vergara - Snapshot of netstat before headers sent.
 *                           Snapshot of netstat on headers recieved.
 *                           Only snapshot for get main connections.
 * 20230620 - Luis Vergara - Let's have special logic for get main_frame.
 *                           To write specific fields to the log. 
 ****************************************************************/


/*****************************************************************
 * Global Variables
 ****************************************************************/
let targetPage = "<all_urls>"; // Which pages trigger the dialog box

let globalHeaders = [];    // Used to pass message to popup window
let DEBUG = "OFF";    //Turn to "ON" for messages
let optionsExtendedWith = "";
let FirefoxPID = "";
let logFile = "";
let popupOptionsList = [];
let redirectNeeded = undefined;  // If the request needs a redirection
let requests = [];               // Requests made so far
// {
// id: "", request id from request headers
// url: "", url from user
// method: "", get method from request headers
// type: "", type of object to fetch (in our case only main_frame)
// timeStamp: 0, epoch time from request headers. Used to match flow.
// tabId: "", the tab id that started the request
// destinationIp: "", the destination ip from response headers
// urlBeforeRedirection: "", the destination ip from response headers if there is redirection involved
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
            createdTimeStamp: eventDetails.timeStamp,
            tabId: eventDetails.tabId,
            requestStatus: "Created",
            FirefoxPID : FirefoxPID,
            originUrl : eventDetails.originUrl
        };
        requests.push(newRequest);

        requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
        if (requestHandle === undefined) {
            // Should be an error
            // Even redirects get a new request id. 
            console.error("No request struct for id: " + eventDetails.requestId + " in logOnBeforeRequest");
            console.log(eventDetails);
        }
    }
    else {
        //Redirected?
        if (!Object.hasOwn(requestHandle, 'redirected')) {
            console.error("Request " + eventDetails.requestId + " in logOnBeforeRequest again without redirection status");
            console.log(requestHandle);
        }
        else {
            // What could have changed during redirection?
            requestHandle.urlBeforeRedirection = requestHandle.url;
            requestHandle.urlAfterRedirection = eventDetails.url;
            requestHandle.url = eventDetails.url;
        }
    }

    // Only main_frame GET requests can invoke a popup window.
    if (eventDetails.type.toLowerCase() === "main_frame" && eventDetails.method.toLowerCase() === "get") {
        // For get main_frame types we assume the originUrl is themselves
        requestHandle.originUrl = eventDetails.url;
        // Save url to send to popup
        requestHandle.url4Popup = eventDetails.url;
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
        console.error("No request struct for id: " + eventDetails.requestId + " in logOnBeforeSendHeaders");
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
        // Knowing the persistence of the connection can help
        // determine if one or more connections will be sent out
        // by the same site. 
        if (hdr.name.toLowerCase() === "connection") {
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

    // If we didn't find the "stay-alive" value let's set persistent to false
    if (requestHandle.persistent === undefined) {
        // default to non persistent
        requestHandle.persistent = "false";
    }

    // Only main_frame GET requests will check netstat before their headers are sent.
    if (eventDetails.type.toLowerCase() === "main_frame" && eventDetails.method.toLowerCase() === "get") {
        //Let's get a snapshot of netstat before we send these hdrs
        message = {
            state: "snapBefore",
            dataIn: {
                id : requestHandle.id,
                FirefoxPID : FirefoxPID
            },
            logFile : logFile
        }   
        callNative(message);
    }

    // Get event datails?
    logEvent("BeforeSendHeaders", eventDetails, requestHandle);
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
        console.error("No request struct for id: " + eventDetails.requestId + " in logOnSendHeaders");
        console.log(eventDetails);
    }

    // This timestamp is the closes to the flow.
    requestHandle.sendHeadersTimeStamp = eventDetails.timeStamp;

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
        console.error("No request struct for id: " + eventDetails.requestId + " in lonOnHeadersReceived.");
    }
    else {
            // This is where we want to check for destination ip
            // But the ip could be null. And then what?
            // We'll have the native app worry about such things.
        if (eventDetails.ip != null) {
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
        console.error("No request struct for id: " + eventDetails.requestId + " in logOnBeforeRedirect.");
    }
    else {
        requestHandle.redirected = "true";
    }

    // Get event datails?
    logEvent("BeforeRedirect", eventDetails, requestHandle);
}

/* onResponseStarted
   Fired when the first byte of the response body is received. */
function logOnResponseStarted(eventDetails) {
    trace("OnResponseStarted", eventDetails);

    requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
    if (requestHandle === undefined) {
        // Should be an error
        // Even redirects get a new request id. 
        console.error("No request struct for id: " + eventDetails.requestId + " in logOnResponseStarted!");
    }
    else {
        // For get main_frame types let's get the netstat after snapshot
	if (eventDetails.type.toLowerCase() === "main_frame" && eventDetails.method.toLowerCase() === "get") {
	    //Let's get a snapshot of netstat before we send these hdrs
	    message = {
            state: "snapAfter",
            dataIn: {
                id : requestHandle.id,
                sendHeadersTimeStamp : requestHandle.sendHeadersTimeStamp,
                destinationIp : requestHandle.destinationIp,
                destinationPort : requestHandle.destinationPort,
                FirefoxPID : FirefoxPID
            },
            logFile : logFile
	    }   
	    callNative(message);
	}
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
        console.error("No request for id: " + eventDetails.requestId + " in logOnCompleted!");
    }
    else {
        requestHandle.completedTime = eventDetails.timeStamp;
        // Let's log this
        message = {
            state: "logConnection",
            dataIn: requestHandle,
            logFile : logFile
        }   
        callNative(message);
        // Set to be deleted from request array
        requestHandle.requestStatus = "Logged" // set to delete

        if (eventDetails.method.toLowerCase() === "get" && eventDetails.type.toLowerCase() === "main_frame") {
            requestHandle.requestStatus = "GetMain";
            // Call pop up
            try {
                    // pop up basics:
                    // the title of the pop up contains the request id in betwen % signs.
                    // Whenever the user selects something on the pop up we can 
                    // retrieve the request id from its titile.
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
        }
    }

    // Remove from requests if logged, except GetMain connections
    if(requestHandle.requestStatus === "Logged")
    {
        deleteRequest(requestHandle.id);
    }
    // Get event details?
    logEvent("Completed", eventDetails, requestHandle);
}

function handleStartup() {
    // This function is not called when we manually load
    // Moving all of the code that would be in handleStartup to onInstalled
}

/* Tab
   This is a good place to start the app.
   Send an init message to the app. */
// Window
function logCreatedTab(createdTab) {


}

// On Installed
browser.runtime.onInstalled.addListener(() => {
    console.log("user_to_network running in background");
    // check operating system for native app
    // we cannot make this synchronous so we are going to have to do everything inside
    // this function because we need the os info before we can call native app.
    browser.runtime.getPlatformInfo().then((info) => {

        if (DEBUG === "ON") {
            console.log("Entrace to onInstalled");
        }

        // Check if output file exists if not create it
        // Get the options
        state = "session_start";
        message = {
            state: state
        };

        callNative(message);
    });
});


/* callNative
 * This function is called when the user makes a selection or when new request need to be saved
 * the selection along with netstat data is ready to be sent to database */

function callNative(message) {
    
    if (DEBUG === "ON") {
        console.log("In callNative");
        console.log("message is : " + JSON.stringify(message));
        console.log(message);
    }

    if (message.state != "session_start" && (FirefoxPID === "" || FirefoxPID === undefined)){
        // !! We shouldn't be here without the FirefoxPID 
        // !! Let's try to start the session manually
        // !! We'll lose whatever the message was.
        state = "session_start";
        message = {
            state: state
        };
    }
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

    if (response.state === "session_start") {
        // Default to 
        optionsExtendedWith = "";
        popupOptionsList = [];

        // Get set options
        for (var i = 0; i < response.dataOut.length; i++) {
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
            if (response.dataOut[i][0] === "logFile") {
                console.log("option " + response.dataOut[i][0] + " with : " + response.dataOut[i][1]);
                logFile = response.dataOut[i][1];
            }
        }
    }

    if (response.state === "addMainConnection") {
        if( response.exitMessage === "Success"){
            if (response.dataOut.connections.length > 0) {
                for (let connection of response.dataOut.connections) {
                        console.log("connection added :" + JSON.stringify(connection));
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
        let hdrs = [];
        const requestHandle = requests.find(({ id }) => id === msg.requestId);
        if (requestHandle === undefined) {
            // why are we here without a request for this requestId?
            console.error("No request for id: " + eventDetails.requestId + " in get_hdrs!!!");
        }
        else {
            hdrs.push({ name: "url", value: requestHandle.url4Popup });
        }
        return Promise.resolve(hdrs);
    }

    /* get_options  */
    if (msg.type === "get_options") {
        popupOptions = popupOptionsList;
        return Promise.resolve(popupOptions);
    }

    // set_user_selection
    if (msg.type === "set_user_selection") {
        state = "addMainConnection"
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
                dataIn: requestHandle,
                logFile : logFile
            };
            callNative(message);
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
