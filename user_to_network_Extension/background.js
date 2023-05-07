/*****************************************************************
 * Background.js
 *     This extenstion opens a dialog box to the
 *     user. On user selection the extension sends traffic info
 *     to storage via a navtive app called Transport.py
 *     This extension extends the various APIs provided by Firefox
 *     on the different events of a request. Each event is analized
 *     for important information on the request or response headers. 
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
//let message = [];                // Message to be passed to native application {state "" , dataIn [] , dataOut [] , errorMessage ""}
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
            timeStamp: eventDetails.timeStamp,
            tabId: eventDetails.tabId,
            destinationIp: "",
            destinationPort: "",
            urlBeforeRedirection: "",
            globalHdrs: [],
            completedIp: "",
            requestStatus: "",
            extendedData: [],
            statusCode: "New",
            originalUrl: undefined,
            userSelection: undefined,
            originUrl: undefined,
            completedTime: undefined
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
        if (requestHandle.requestStatus != "Redirected") {
            console.error("Request " + eventDetails.requestId + " in logOnBeforeRequest again without redirection status");
            console.log(requestHandle);
        }
        else {
            // What could have changed during redirection?
            requestHandle.urlBeforeRedirection = requestHandle.url;
            requestHandle.url = eventDetails.url;
        }
    }

    // Save headers to send to popup
    // Only main_frame GET requests can invoke a popup window.
    if (eventDetails.type.toLowerCase() === "main_frame" && eventDetails.method.toLowerCase() === "get") {

        try {
            // This url header will be passed to the popup window.
            // Could it already by there if redirected?
            const urlHdr = requestHandle.globalHdrs.find(({ name }) => name === "url");
            if (urlHdr === undefined) {
                // If not there, added it.
                requestHandle.globalHdrs.push({ name: "url", value: eventDetails.url });
            }
            else {
                // If there, update it in case of redirect change.
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
        // determine if one or more main requests will be sent out
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

    // If the request connection is "stay-alive" we assume that the connection will create a single flow.
    // If the request connection in turn is "close" we will assume that subsequent http requests will create unique flows.
    if (requestHandle.persistent === undefined) {
        // default to non persistent
        requestHandle.persistent = "false";
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
        console.error("No request struct for id: " + eventDetails.requestId + " in lonOnHeadersReceived.");
    }
    else {
        // Check if it got response from cache
        if (eventDetails.ip === null) {
            for (let requestHandleBkp of requests.filter(({ url }) => url === eventDetails.url)) {
                if (requestHandleBkp.id != requestHandle.id) {
                    requestHandle.destinationIp = requestHandleBkp.destinationIp;
                    // Mark to remove the original and let the new one be referenced
                    requestHandleBkp.statusCode = "Remove";
                }
                else {
                    continue;
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
        console.error("No request struct for id: " + eventDetails.requestId + " in logOnBeforeRedirect.");
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
        console.error("No request struct for id: " + eventDetails.requestId + " in logOnResponseStarted!");
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
        // The New to Waiting statuses are going to help
        // know which pages have received user selection. 
        // for it is possible for the popup to go unanswered 
        // and the user must be able to keep browsing. 
        if (requestHandle.statusCode === "New") {
            requestHandle.statusCode = "Waiting";
        }

        // If the ip is null get it from destinationIp
        // This watches out for cases when requested ip could be different
        // than the final ip. If that is a thing.
        if (eventDetails.ip != null) {
            requestHandle.completedIp = eventDetails.ip;
        }
        else {
            requestHandle.completedIp = requestHandle.destinationIp;
        }

        // For all connections that are not get main_frame.
        if (!(eventDetails.method.toLowerCase() === "get" && eventDetails.type.toLowerCase() === "main_frame")) {
                // A non get main_frame connection could be matched to a user selection
                // if the connection that started it has a user selection. 
            if (requestHandle.userSelection === undefined) {
                    // Let's check if this host has a user selection from a get main_frame request. 
                    // Look at all of the hosts in our requests list for a match
                    // on this request's host.
                for (let referenceRequestHandle of requests.filter(({ host }) => host === requestHandle.host)) {
                        // If there is another entry in the requests list for this host
                    if (referenceRequestHandle.id != requestHandle.id && referenceRequestHandle.tabId === requestHandle.tabId) {
                            // If that other entry has a user selection
                        if (referenceRequestHandle.userSelection != undefined) {
                                // Let's copy the user selection to our request
                            requestHandle.userSelection = referenceRequestHandle.userSelection;
                                // NOTE: Persistent status refers to a connection that is made to the host
                                // to request all the content that is needed in one connection.
                                // Non-persistent status refers to a connection that creates a new connection
                                // for each of the items it needs from the host.
                            if (requestHandle.persistent != "true") {
                                // In here we have a connection likely as a result
                                // of a  non-persistent get main_frame connection.
                                
                                // This connection will be logged as a child to a "parent" 
                                // connetion: the actual get main_frame connection that started it.
                                console.log("*****************");
                                console.log("NON-PERSISTENT request id : " + requestHandle.id);
                                console.log("*****************");
                                // ChildSentReady status is so that we can log this connection
                                // in our connections file as a child to a non-persistent 
                                // get main_frame connection. 
                                requestHandle.statusCode = "ChildSentReady";
                            }
                            else {
                                // If this is not a connection from a non-persistent parent
                                // let's remove it from our requests list and forget it
                                requestHandle.statusCode = "Remove";
                            }
                            break;
                        }
                        else if (referenceRequestHandle.userSelection === undefined) {
                                // This is the same as above but in this case
                                // if don't find a user selection for the parent
                                // then we mark the status as Child to remember
                                // that once the parent gets the selection 
                                // then this one should also get it. 
                            if (requestHandle.persistent != "true") {
                                requestHandle.statusCode = "Child";
                            }
                            else {
                                requestHandle.statusCode = "Remove";
                            }
                        }
                    }
                }
            }

                // Different hosts
                // This connection is not get main_frame and is not the child of a get main_frame connection
                // It might be a new host that is fired off independently. 
                // The originUrl can tell use which host triggered this connection, which might or might not be
                // a get main_frame url.
            if (requestHandle.userSelection === undefined && requestHandle.statusCode === "Waiting" && eventDetails.originUrl != null) {
                requestHandle.originUrl = eventDetails.originUrl;
                console.log("*****************");
                console.log("Different host request id : " + requestHandle.id + ", host: " + requestHandle.host);
                console.log("*****************");

                    // Let's look for the origin url in our requests to see what infor we can find
                for (let referenceRequestHandle of requests.filter(({ url }) => url === requestHandle.originUrl)) {
                    if (referenceRequestHandle.id != requestHandle.id && referenceRequestHandle.tabId === requestHandle.tabId) {
                        if (referenceRequestHandle.userSelection != undefined) {
                                // What we have here is an external host triggered
                                // by one other host that does have a user selection.
                                // We can log this as having the same user selection.
                            requestHandle.userSelection = referenceRequestHandle.userSelection;
                                // HoseSentReady: Different host with a user selection from the origin url
                                // ready to be written out to file.
                            requestHandle.statusCode = "HostSentReady";
                            break;
                        }
                        else if (referenceRequestHandle.userSelection === undefined) {
                                // Orphaned host -- which we can adopt once the origin url
                                // receives a user selection.
                            requestHandle.statusCode = "Orphaned";
                        }
                    }
                }

            }
        }
            // Now let's take a look at get main_frames which are our target connections.
        else if (eventDetails.method.toLowerCase() === "get" && eventDetails.type.toLowerCase() === "main_frame") {
            requestHandle.statusCode = "GetMain";
            // Call pop up
            try {
                    // pop up basics:
                    // the title of the pop up contains the request id in betwen % signs.
                    // Whenever the user selects somethings on the pop up we can 
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

            // Check for dupe get main_frame
            // destroy duplicate requests. LILO - Last In Last Out
            duplicate = requests.find(({ url }) => url === requestHandle.url);
            if (duplicate === undefined) {
                // This is bad because it should at least find itself in here.
                console.error("GET Main_Frame request url : " + requestHandle.url + " does not exist in delete dupes in onCompleted!")
            }

            while (duplicate != undefined) {
                if (duplicate.id != requestHandle.id) {
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

        // This is the for loop to process the connections.
        // Connections that were waiting for parent to get a user selection?
        // Maybe this connection does have a user selection already.
        // Let's loop our requests list to see what can be written out.
        // We enter this loop every single time the browser completes a 
        // request. That means we do this a lot.
    for (let rqst of requests) {
            // Starting off with children that are ready to file
            // Or host's that were triggered that we are ready to file
        if (rqst.statusCode === "ChildSentReady" || rqst.statusCode === "HostSentReady") {
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
                // We are shutting this down to start off light // UNCOMMENT below for extra connections
            //callNative(message);

            if (rqst.statusCode === "ChildSentReady") {
                    // Child connections can be removed after we write them out. 
                rqst.statusCode = "Remove";
            }
            else {
                    // Triggered hosts are kept in the requests list
                    // because they might be a parent to other connections later on.
                rqst.statusCode = "ExternalHost"
            }
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

        os = info.os;

        if (DEBUG === "ON") {
            console.log("Entrace to onInstalled");
            console.log(os);
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

        callNative(message);
    });
});


/* callNative
 * This function is called when the user makes a selection or when new request need to be saved
 * the selection along with netstat data is ready to be sent to database */

function callNative(message) {
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
        console.log(requests);
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
            // Try to find a connection again 
        if( response.exitMessage === "connection to netstat connection not found"){
            for(var i = 0; i < response.dataOut.length; i++) {
                if (response.dataOut[i][0] === "ConnectionTry") {
                    ConnectionTry = response.dataOut[i][1];
                    if (ConnectionTry < 2)
                    {
                        message = {
                            state: response.state,
                            dataIn: [{
                                tabId: response.dataIn[0].tabId,
                                destinationIp: response.dataIn[0].destinationIp,
                                destinationPort: response.dataIn[0].destinationPort,
                                userSelection: response.dataIn[0].userSelection,
                                epochTime: response.dataIn[0].epochTime,
                                completedIp: response.dataIn[0].completedIp,
                                requestId: response.dataIn[0].requestId,
                                originalDestIp: response.dataIn[0].originalDestIp,
                                extendedData: response.dataIn[0].extendedData,
                                FirefoxPID: response.dataIn[0].FirefoxPID,
                                os: response.dataIn[0].os,
                                ConnectionTry : ConnectionTry
                            }],
                            dataOut: [],
                            optionsSendWith: response.optionsSendWith,
                            exitMessage: ""
                        };
                        callNative(message);
                    }
                    else {
                        console.log("RequestId : " + response.dataIn[0].requestId + " netstat not found");
                    }
                }
            }
        }

        if( response.exitMessage === "Success"){
            console.log("options sendwith is " + optionsSendWith);
            if (response.dataOut.connections.length > 0) {
                for (let connection of response.dataOut.connections) {
                        // You can decide to send the connection via http.
                        // NOTE: We are using pythong to write out connections.
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
            if (requestHandle.statusCode != "ExternalHost") {
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
                        os: os,
                        ConnectionTry : 0
                    }],
                    dataOut: [],
                    optionsSendWith: optionsSendWith,
                    exitMessage: ""
                };
                callNative(message);
            }

            // This would be a good place to update child and external hosts with 
            // this user selection.
            for (let rqst of requests) {
                if (rqst.statusCode === "Child" && rqst.host === requestHandle.host && rqst.tabId === requestHandle.tabId) {
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
                    // We are commenting this out // UNCOMMENT BELOW FOR EXTRA CONNECTIONS
                    //callNative(message);

                    rqst.statusCode = "Remove";
                }
                    // Remember that orphaned connections are external hosts that were triggered
                    // by some other connection. We can check if this user selection can be given
                    // to any of them.
                else if (rqst.statusCode === "Orphaned" && rqst.originUrl === requestHandle.url && rqst.tabId === requestHandle.tabId) {
                    console.log("*****************");
                    console.log("Other HOST request id : " + rqst.id);
                    console.log("*****************");
                    rqst.userSelection = requestHandle.userSelection;
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
                    // We are commenting this out // UNCOMMENT BELOW FOR EXTRA CONNECTIONS
                    //callNative(message);
                    // You don't want to remove and external host because it might be needed for its children if any
                    // UNCOMMENT BELOW FOR EXTRA CONNECTIONS
                    //rqst.statusCode = "ExternalHost";
                    rqst.statusCode = "Remove";
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

// Local Storage
//set
// browser.storage.local.set({ variable: variableInformation });
//get
//browser.storage.local.get(['variable'], (result) => {
//let someVariable = result.variable;
  // Do something with someVariable
//});
