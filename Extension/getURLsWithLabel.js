
/*****************************************************************
 * getURLsWithLabel.js
 *     This extenstion opens a dialog box to the
 *     user. On user selection the extension sends traffic info
 *     to storage via a navtive app called urlExport.py
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
 * 20230802 - Luis Vergara - We don't need before and after snapshots
 *                           because they take a lot of processing power
 *                           and plus we are not using the source ip & port
 *                           to make matches with pmacctd anymore.
 *                           We are trying to match with dest ip & port only.
 * 20230919 - Luis Vergara - Redirected pages were not creating a popup - Added redirected logic.
 * 20231012 - Herman Ramey - External hosts are those that have domain names that 
 *                           do not match the domain name of the webpage that 
 *                           fired the request.
 *     HOW IT WORKS FROM HERE ON OUT:
 *                           Get main_frame connections trigger the pop-up window.
 *                           The dest ip and port are saved with the user-selection.
 *                           An internal list of get main_frame hosts will keep multiple
 *                           requests on the same host to trigger the pop-up.
 *                           If a new host is created mid browsing with a domain name that does 
 *                           not match the domain name of the webpage that fired the request, 
 *                           it will logged as an external host. Otherwise, network operation.
 *                           External hosts can be useful to identify ads and other robots.
 * 20240102 - Herman Ramey - Implementing code to place user selections in array userSels
 ****************************************************************/

/*****************************************************************
 * Global Variables
 ****************************************************************/
let targetPage = "<all_urls>"; // Which pages trigger the dialog box

let globalHeaders = [];    // Used to pass message to popup window
let DEBUG = "ON";    //Turn to "ON" for messages
let optionsExtendedWith = "";
let FirefoxPID = "";
let logFile = "";
let popupOptionsList = [];
let redirectNeeded = undefined;  // If the request needs a redirection
let requests = [];               // Requests made so far
let userSels = [];
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
let getMainFrameRequests = [];      // List of get main_frame requests so far. This keeps us from multiple pop-ups
// id
// host 
// tabId
// url
// userSelection
let externalHosts = [];       // List of host request that are triggered hiden from the user
// id
// host
// tabId
// url
// class


/*****************************************************************
 * Event Handlers
 ****************************************************************/

/* onBeforeRequest Handler
   This event is triggered when a request is about to be made, and before headers are available.
   This is a good place to listen if you want to cancel or redirect the request. */
function logOnBeforeRequest(eventDetails) {

    // trace("logOnBeforeRequest", eventDetails);

    // Create an entry for this request
    // Check if there is an entry for this requestId
    let requestHandle = requests.find( ({ id }) => id === eventDetails.requestId);
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
        //
        if (Object.hasOwn(requestHandle, 'redirected')) {
            requestHandle.url4Popup = requestHandle.urlBeforeRedirection;
        }
        else
        {
              // Call the async function
            // let org = syncFunction(requestHandle.host);

            newGetMainFrameRequest = {
                id: requestHandle.id,
                url: requestHandle.url4Popup,
                tabId: requestHandle.tabId,
                host: requestHandle.host
            };
            getMainFrameRequests.push(newGetMainFrameRequest);

        }
    }

    logEvent("BeforeRequest", eventDetails, requestHandle);
}

/* onBeforeSendHeaders Handler
   This event is triggered before sending any HTTP data, but after all HTTP headers are available.
   This is a good place to listen if you want to modify HTTP request headers. */
function logOnBeforeSendHeaders(eventDetails) {
    // trace("logOnBeforeSendHeaders", eventDetails);

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

    // Only main_frame GET requests :
    //if (eventDetails.type.toLowerCase() === "main_frame" && eventDetails.method.toLowerCase() === "get") {
    //}

    // Get event datails?
    logEvent("BeforeSendHeaders", eventDetails, requestHandle);
}

/* onSendHeaders
   This event is fired just before sending headers.
   If your extension or some other extension modified headers in onBeforeSendHeaders,
   you'll see the modified version here. */
function logOnSendHeaders(eventDetails) {
    // trace("logOnSendHeaders", eventDetails);

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
    // trace("logOnHeadersReceived", eventDetails);
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
    // trace("logOnBeforeRedirect", eventDetails);

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
    // trace("OnResponseStarted", eventDetails);

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
    // trace("logOnCompleted", eventDetails);

    // Log onCompleted time
    const requestHandle = requests.find(({ id }) => id === eventDetails.requestId);
    if (requestHandle === undefined) {
        // why are we here without a request for this requestId?
        console.error("No request for id: " + eventDetails.requestId + " in logOnCompleted!");
    }
    else {
        requestHandle.completedTime = eventDetails.timeStamp;
        // console.log(requestHandle.host);
        // Let's log this
        message = {
            state: "logConnection",
            dataIn: requestHandle,
            logFile : logFile
        } 
        //LUIS V: TODO: callNative to log connection as a debugging option  
        //callNative(message);
        // Set to be deleted from request array
        requestHandle.requestStatus = "Logged"

        if (eventDetails.method.toLowerCase() === "get" && eventDetails.type.toLowerCase() === "main_frame") {
            requestHandle.requestStatus = "GetMain";

            // Find out if this host already prompted a popup
            let getMainFrameRequestHandle = getMainFrameRequests.find(({ host }) => host === requestHandle.host);
            if (getMainFrameRequestHandle === undefined) // Create the request 
            {
                // Add the host to getMainFrameRequestHandle to stop other get main connections with same host to 
                // start another popup
                let getMainFrameRequestHandleById = getMainFrameRequests.find(({ id }) => id === requestHandle.id);
                if (getMainFrameRequestHandleById === undefined) // Add host
                {
                    console.error("No getMainFrameRequestHandleById : " + eventDetails.requestId + " in logOnCompleted!");
                }
                else
                {
                    getMainFrameRequestHandleById.host = requestHandle.host;

                }
                // Call pop up
                try {
                    // pop up basics:
                    // the title of the pop up contains the request id in betwen % signs.
                    // Whenever the user selects something on the pop up we can 
                    // retrieve the request id from its titile.
                    browser.windows.create({
                        type: "popup", url: "/getHumanAppLabel.html",
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
        else{
            // TODO: Herman Ramey - Condense to one function that takes a flag 
            //                      as a parameter to decide which formatting 
            //                      technique to use.
            const requestDomain = extractDomain(requestHandle.host); // e.g., 'netflix' given www.netflix.com
            const requestDomain_TLD = extractDomain_TLD(requestHandle.originUrl); // e.g., 'www. netflix.com' given https url
            const origin_TLD = extractDomain_host(requestHandle.host) // e.g., 'netflix.com' 
            
            // Let's make sure the host on this request matches the user's intended host
            let getHostHandle = getMainFrameRequests.find(({ host }) => {
                if (host === undefined){
                    console.log("host is undefined in getHostHandle. Mainframe requests: ")
                    console.log(getMainFrameRequests);
                }
                else {
                const mainFrameDomain = extractDomain(host);
                return requestDomain.includes(mainFrameDomain);
                }
            });
            if (getHostHandle === undefined) // Not an intended host
            {
                requestHandle.requestStatus = "ExternalHost";

                // This is a request from a host that isn't the users intended host
                // Now let's check if the external host is already known
                let getExternalHostHandle = externalHosts.find(({ host }) => host === requestHandle.host);
                if (getExternalHostHandle === undefined){
                    // This is the first time encountering this host
                    newExternalHost = {
                        id: requestHandle.id,
                        url: requestHandle.url,
                        tabId: requestHandle.tabId,
                        host: requestHandle.host
                    };
                    externalHosts.push(newExternalHost);
                    // Log the external connections
                    state = "addMainConnection"
                    requestHandle.userSelection = "ExternalHost";
                    message = {
                        state: state,
                        dataIn: requestHandle,
                        logFile : logFile
                    };
                    callNative(message);
                }
            }
                // Request was triggered by intended host
            else {
                // Extract userSelection from dictionary
                const matchingObject = userSels.find(obj => {
                    // Extract domain from the 'host' property of the current object
                    const extractedDomain = extractDomain(obj.host);
                    
                    // Compare the extracted domain with the requestDomain variable
                    return extractedDomain === requestDomain;
                });

                requestHandle.requestStatus = "NetworkOperation";
                state = "addMainConnection"
                requestHandle.userSelection = matchingObject.selection;
                message = {
                    state: state,
                    dataIn: requestHandle,
                    logFile : logFile
                };
                callNative(message);
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


/*extractDomain
* Given a hostname like subdomain.domain.topleveldomain, 
* this function extracts domain name */
function extractDomain(hostname) {
    if (hostname !== undefined) {
        const parts = hostname.split('.');
        // Check if there are at least three parts (subdomain.domain.tld)
        if (parts.length >= 2) {
            return parts[parts.length - 2];
        }
        return null;
    }
    else {
        console.log("Host is undefined in extractDomain! Host: "+ hostname);
        return null;
    }
}

function extractDomain_TLD(hostname) {

    const parts = hostname.split('.');
    // Check if there are at least three parts (subdomain.domain.tld)
    if (parts.length >= 2) {
      
        const parsedUrl = new URL(hostname);
        const domainParts = parsedUrl.hostname.split('.');
        return domainParts.slice(-3).join('.');
      
    }
  
    return null;
  }

  function extractDomain_host(hostname) {

    const parts = hostname.split('.');
    // Check if there are at least three parts (subdomain.domain.tld)
    if (parts.length >= 2) {
        return parts.slice(-2).join('.');
      
    }
  
    return null;
  }
  

// On Installed
browser.runtime.onInstalled.addListener(() => {
    console.log("human_app_label running in background");
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
        // console.log("In callNative");
        // console.log("message is : " + JSON.stringify(message));
        // console.log(message);
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
        "urlExport",
        message);

    sending.then(onResponse, onError);
}

function onResponse(response) {
    if (DEBUG === "ON") {
        // console.log("In onResponse");
        // console.log(response);
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
                        // console.log("connection added :" + JSON.stringify(connection));
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
            console.log(msg)
            console.log(requestHandle)

            message_obj = {
                selection: msg.response,
                host: requestHandle.host
            };
            // Save user selection for future use
            userSels.push(message_obj);
            console.log(userSels); 

            message = {
                state: state,
                dataIn: requestHandle,
                logFile : logFile
            };
            callNative(message);

            // Let's also add it to getMainFrameRequests
            let getMainFrameRequestHandle = getMainFrameRequests.find(({ host }) => host === requestHandle.host);
            if (getMainFrameRequestHandle === undefined) // Create the request 
            {
                // why are we here without a getMainFrameRequest for this host?
                console.error("No getMainFrameRequest struct for host: " + requestHandle.host + " in set_user_selection.");                
            }
            else {
                getMainFrameRequestHandle.userSelection = msg.response;
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
    console.log("In OnError");
    console.log(`Error: ${error}`);
}

function logEvent(source, eventDetails, requestHandle) {
    // Get event datails?
    if (optionsExtendedWith === "All" || optionsExtendedWith.includes(source)) {
        extendedData = { source: source, eventDetails: eventDetails };
        requestHandle.extendedData.push(extendedData);
        console.log(requestHandle);
    }
}

function trace(source, eventDetails) {
    if (DEBUG === "ON") {
        console.log("Entrace to " + source);
        
        console.log(eventDetails);
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
