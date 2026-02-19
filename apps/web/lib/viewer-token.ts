const KEY = "wishlist_viewer_token";

function uuidv4(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function getViewerToken(): string {
  if (typeof window === "undefined") {
    return "server-viewer-token-placeholder";
  }
  let token = localStorage.getItem(KEY);
  if (!token) {
    token = uuidv4();
    localStorage.setItem(KEY, token);
  }
  return token;
}
