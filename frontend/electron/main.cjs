const { app, BrowserWindow, shell } = require("electron");
const path = require("node:path");

const startUrl = process.env.ELECTRON_START_URL;

function createWindow() {
  const window = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    backgroundColor: "#f4f6fa",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (startUrl) {
    window.loadURL(startUrl).catch((error) => {
      showLoadError(window, error);
    });
  } else {
    window.loadFile(path.join(__dirname, "..", "dist", "index.html")).catch((error) => {
      showLoadError(window, error);
    });
  }

  window.webContents.on("did-fail-load", (_event, errorCode, errorDescription) => {
    showLoadError(window, new Error(`${errorDescription} (${errorCode})`));
  });
  window.webContents.on("render-process-gone", (_event, details) => {
    showLoadError(window, new Error(`Renderer stopped: ${details.reason}`));
  });

  window.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
}

function showLoadError(window, error) {
  const message = String(error?.message || error);
  window.loadURL(
    `data:text/html;charset=utf-8,${encodeURIComponent(`
      <!doctype html>
      <html><body style="font-family:Arial;padding:40px;color:#172338">
        <h1>SmartERP could not load</h1>
        <p>Close this window, make sure the application was completely extracted, and try again.</p>
        <pre style="white-space:pre-wrap;background:#f4f6fa;padding:16px;border-radius:8px">${message}</pre>
      </body></html>
    `)}`,
  );
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
