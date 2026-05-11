let deferredInstallPrompt = null;

function isProbablyAndroidChrome() {
  const ua = navigator.userAgent || "";
  return /Android/i.test(ua) && /Chrome/i.test(ua);
}

function explainInstallBlock() {
  if (!isProbablyAndroidChrome()) {
    return "If the install prompt is not visible, open this site in Chrome or Edge and use the browser install option.";
  }

  if (!window.isSecureContext) {
    return "Android Chrome needs HTTPS before it can show Install App. Open the app from an HTTPS link, then refresh this page.";
  }

  return "Chrome has not made the install prompt available yet. Refresh once, then open the Chrome menu and choose Add to Home screen.";
}

function createInstallButton() {
  if (document.getElementById("npf-install-app")) {
    return;
  }

  const button = document.createElement("button");
  button.id = "npf-install-app";
  button.type = "button";
  button.textContent = "Install App";
  button.style.cssText = [
    "position:fixed",
    "left:18px",
    "bottom:18px",
    "z-index:10000",
    "border:0",
    "border-radius:999px",
    "padding:12px 18px",
    "background:#16a34a",
    "color:#fff",
    "font:600 14px Arial,sans-serif",
    "box-shadow:0 12px 30px rgba(0,0,0,.24)",
    "cursor:pointer"
  ].join(";");

  button.addEventListener("click", async () => {
    if (!deferredInstallPrompt) {
      alert(explainInstallBlock());
      return;
    }

    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    button.remove();
  });

  document.body.appendChild(button);
}

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js").catch(() => {
      // The app still works normally if service worker registration is blocked.
    });
  });
}

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  createInstallButton();
});

window.addEventListener("appinstalled", () => {
  deferredInstallPrompt = null;

  const button = document.getElementById("npf-install-app");
  if (button) {
    button.remove();
  }
});

window.NPF_PWA = {
  getCanPromptInstall: () => Boolean(deferredInstallPrompt),
  explainInstallBlock,
  promptInstall: () => {
    const button = document.getElementById("npf-install-app");

    if (button) {
      button.click();
      return true;
    }

    alert(explainInstallBlock());
    return false;
  }
};
