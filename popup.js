const statusElement = document.getElementById("status");
const startButton = document.getElementById("start");

function setStatus(message) {
  statusElement.textContent = message;
}

function getActiveInstagramTab() {
  return new Promise((resolve, reject) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs[0];
      if (!tab || !tab.url || !tab.url.startsWith("https://www.instagram.com/")) {
        reject(new Error("Open an Instagram profile first."));
        return;
      }
      resolve(tab);
    });
  });
}

function sendToTab(tabId, message) {
  return new Promise((resolve, reject) => {
    chrome.tabs.sendMessage(tabId, message, (response) => {
      if (chrome.runtime.lastError) {
        const messageText = chrome.runtime.lastError.message || "";
        if (!messageText.includes("Receiving end does not exist")) {
          reject(new Error(messageText));
          return;
        }
        chrome.scripting.executeScript({ target: { tabId }, files: ["content.js"] }, () => {
          if (chrome.runtime.lastError) {
            reject(new Error(`Could not connect to Instagram: ${chrome.runtime.lastError.message}`));
            return;
          }
          chrome.tabs.sendMessage(tabId, message, (retryResponse) => {
            if (chrome.runtime.lastError) reject(new Error(chrome.runtime.lastError.message));
            else resolve(retryResponse);
          });
        });
      }
      else resolve(response);
    });
  });
}

function setBusy(isBusy) {
  startButton.disabled = isBusy;
  document.getElementById("stop").disabled = !isBusy;
}

async function startCollection() {
  setBusy(true);
  try {
    const tab = await getActiveInstagramTab();
    setStatus("Connecting to the profile...");
    const response = await sendToTab(tab.id, { action: "startCollection" });
    if (!response?.ok) throw new Error(response?.error || "Collection failed.");
    if (response.stopped) {
      setStatus("Collection stopped.");
      return;
    }
    const collection = response.collection;
    setStatus(collection.complete
      ? `Saved ${collection.followers.length} followers and ${collection.following.length} following.`
      : "Collection stopped. The collected data was saved as a partial snapshot.");
  } catch (error) {
    setStatus(`Collection error: ${error.message}`);
  } finally {
    setBusy(false);
  }
}

startButton.addEventListener("click", startCollection);
document.getElementById("stop").addEventListener("click", async () => {
  try {
    const tab = await getActiveInstagramTab();
    await sendToTab(tab.id, { action: "stop" });
    setStatus("Stopping collection...");
  } catch (error) {
    setStatus(error.message);
  }
});
document.getElementById("feedback").addEventListener("click", () => {
  chrome.tabs.create({ url: "https://github.com/xxkyser-ctrl/IB_Circlio/issues/new" });
});
chrome.runtime.onMessage.addListener((message) => {
  if (message.action === "scanProgress" || message.action === "collectionProgress") {
    setStatus(message.message || `Scanning ${message.listType}: ${message.count} collected`);
  }
});
