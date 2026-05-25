const API_URL = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" || window.location.protocol === "file:")
  ? "http://127.0.0.1:5000"
  : "https://dealradar-kvsp.onrender.com";
const STORE_KEY = "c2s.mobile.state.v2";

function dataURLtoFile(dataurl, filename = "file.png") {
  if (!dataurl || !dataurl.startsWith("data:")) return null;
  try {
    const arr = dataurl.split(',');
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, { type: mime });
  } catch (e) {
    console.error("Failed to convert dataURL to file:", e);
    return null;
  }
}

function getPlaceholderFile(filename = "placeholder.png") {
  const dummyBytes = new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82, 0, 0, 0, 1, 0, 0, 0, 1, 8, 6, 0, 0, 0, 31, 21, 108, 137, 0, 0, 0, 10, 73, 68, 65, 84, 120, 156, 99, 0, 1, 0, 0, 2, 0, 1, 10, 48, 12, 168, 0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130]);
  const blob = new Blob([dummyBytes], { type: "image/png" });
  return new File([blob], filename, { type: "image/png" });
}
const app = document.querySelector("#app");
const accountChip = document.querySelector("#accountChip");
const checkoutDialog = document.querySelector("#checkoutDialog");
const checkoutForm = document.querySelector("#checkoutForm");
const toast = document.querySelector("#toast");

let checkoutProductId = null;
let currentView = "home";

const riders = [
  ["Arjun Kumar", "+91 98765 12001"],
  ["Meera Singh", "+91 98765 12002"],
  ["Ravi Patel", "+91 98765 12003"],
  ["Ananya Rao", "+91 98765 12004"]
];

let state = {
  account: JSON.parse(localStorage.getItem("c2s.account")) || { name: "Guest", role: "customer" },
  products: [],
  orders: [],
  chats: [
    { id: 1, sender: "seller", message: "Welcome. Ask about stock, delivery, or product availability.", createdAt: new Date().toLocaleString() }
  ]
};

async function migrateOldData(manual = false) {
  const oldData = JSON.parse(localStorage.getItem(STORE_KEY));
  if (!oldData || !oldData.products || oldData.products.length === 0) {
    if (manual) showToast("No offline data found on this phone.");
    return;
  }

  if (manual || confirm(`Found ${oldData.products.length} items saved on this phone. Would you like to upload them to the live website?`)) {
    if (state.account.name === "Guest") {
      showToast("Please log in first to upload items.");
      setView("auth");
      return;
    }

    showToast("Syncing old items...");
    for (const p of oldData.products) {
      try {
        const formData = new FormData();
        formData.append("shop_name", p.shopName);
        formData.append("location", p.location);
        formData.append("latitude", p.latitude);
        formData.append("longitude", p.longitude);
        formData.append("product_name", p.productName);
        formData.append("price", p.price);
        formData.append("stock", p.stock);
        formData.append("unit", p.unit || "unit");

        const fileObj = dataURLtoFile(p.image, `${p.productName.replace(/[^a-zA-Z0-9]/g, "_")}.png`);
        if (fileObj) {
          formData.append("product_image", fileObj);
          formData.append("shop_image", fileObj);
        } else {
          formData.append("product_image", getPlaceholderFile("product_placeholder.png"));
          formData.append("shop_image", getPlaceholderFile("shop_placeholder.png"));
        }

        await fetch(`${API_URL}/add_product`, {
          method: "POST",
          body: formData,
          credentials: "include"
        });
      } catch (err) {
        console.error("Migration error for product:", p.productName, err);
      }
    }
    // Clear old data after migration
    localStorage.removeItem(STORE_KEY);
    showToast("Sync complete!");
    await syncState();
  }
}

async function syncState() {
  try {
    const pRes = await fetch(`${API_URL}/api/products`);
    const pData = await pRes.json();
    state.products = pData.products || [];

    if (state.account.name !== "Guest") {
      const oRes = await fetch(`${API_URL}/api/orders`, { credentials: "include" });
      const oData = await oRes.json();
      state.orders = oData.orders || [];
    }

    // Check for migration
    await migrateOldData();
  } catch (err) {
    console.error("Sync error:", err);
  }
}

function saveLocalAccount() {
  localStorage.setItem("c2s.account", JSON.stringify(state.account));
}

async function setView(viewName) {
  const template = document.querySelector(`#${viewName}View`);
  if (!template) return;
  currentView = viewName;
  document.body.dataset.view = viewName;
  app.replaceChildren(template.content.cloneNode(true));
  document.querySelectorAll("[data-view]").forEach((button) => button.classList.toggle("active", button.dataset.view === viewName));
  accountChip.textContent = `${state.account.role}: ${state.account.name}`;
  app.focus({ preventScroll: true });

  await syncState();
  updateNavVisibility();

  ({
    home: renderHome,
    auth: renderAuth,
    otp: renderOtp,
    customer: renderCustomer,
    seller: renderSeller,
    orders: renderOrders,
    analytics: renderAnalytics,
    admin: renderAdmin,
    chat: renderChat
  })[viewName]?.();
}

function renderHome() {
  renderProductGrid(document.querySelector("#featuredProducts"), state.products.slice(0, 6));
  
  // Hide seller buttons if customer
  const sellerBtns = document.querySelectorAll("[data-view='seller'], [data-view='analytics'], [data-view='admin']");
  sellerBtns.forEach(btn => {
    if (state.account.role === 'customer') {
      // If it's a quick card or hero button, hide it
      if (btn.classList.contains('quick-card') || btn.closest('.hero-actions')) {
        btn.style.display = 'none';
      }
    } else {
      btn.style.display = '';
    }
  });
}

function updateNavVisibility() {
  const role = state.account.role;
  const navLinks = document.querySelectorAll(".nav-links [data-view], .tabs [data-view]");
  
  navLinks.forEach(link => {
    const view = link.dataset.view;
    if (role === 'customer') {
      if (['seller', 'analytics', 'admin'].includes(view)) {
        link.style.display = 'none';
      } else {
        link.style.display = '';
      }
    } else if (role === 'seller') {
      if (['admin'].includes(view)) {
        link.style.display = 'none';
      } else {
        link.style.display = '';
      }
    } else {
      link.style.display = '';
    }
  });
}

function renderAuth() {
  const form = document.querySelector("#loginForm");
  const title = document.querySelector("#authTitle");
  const subtitle = document.querySelector("#authSubtitle");
  const toggleLogin = document.querySelector("#toggleLogin");
  const toggleSignup = document.querySelector("#toggleSignup");
  const gotoSignup = document.querySelector("#gotoSignup");
  const submitBtn = form.querySelector(".auth-submit span");

  let isLogin = true;

  const updateUI = () => {
    title.textContent = isLogin ? "Welcome Back" : "Create Account";
    subtitle.textContent = isLogin ? "Login to your account to continue" : "Join our local marketplace today";
    submitBtn.textContent = isLogin ? "Continue" : "Create Account";
    toggleLogin.classList.toggle("active", isLogin);
    toggleSignup.classList.toggle("active", !isLogin);
  };

  toggleLogin.onclick = () => { isLogin = true; updateUI(); };
  toggleSignup.onclick = () => { isLogin = false; updateUI(); };
  gotoSignup.onclick = (e) => { e.preventDefault(); isLogin = false; updateUI(); };
  document.querySelector("#gotoOtp").onclick = (e) => { e.preventDefault(); setView("otp"); };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const username = formData.get("username").trim();
    const role = formData.get("role");

    try {
      showToast(isLogin ? "Signing in..." : "Creating account...");
      const endpoint = isLogin ? "/api/login" : "/api/register";
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password: "password123", role })
      });
      const data = await res.json();
      if (data.success) {
        state.account = { name: data.user, role: data.role };
        saveLocalAccount();
        showToast(isLogin ? `Welcome, ${data.user}!` : `Account created! Welcome, ${data.user}!`);
        setView(data.role === "admin" ? "admin" : data.role === "seller" ? "seller" : "customer");
      } else {
        showToast(data.message || "Authentication failed");
      }
    } catch (err) {
      console.error("Auth error:", err);
      // Fallback for offline testing
      state.account = { name: username || "Guest", role };
      saveLocalAccount();
      setView(role === "admin" ? "admin" : role === "seller" ? "seller" : "customer");
    }
  });
}

function renderOtp() {
  const sendForm = document.querySelector("#otpSendForm");
  const verifyForm = document.querySelector("#otpVerifyForm");

  sendForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const phone = new FormData(sendForm).get("phone");
    showToast("Sending OTP...");
    try {
      const res = await fetch(`${API_URL}/send_otp`, {
        method: "POST",
        body: new URLSearchParams({ phone }),
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });
      if (res.ok) {
        showToast("Code sent to " + phone);
        sendForm.style.display = "none";
        verifyForm.style.display = "grid";
      } else {
        showToast("Failed to send OTP.");
      }
    } catch (err) {
      showToast("Server error.");
    }
  });

  verifyForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const otp = new FormData(verifyForm).get("otp");
    showToast("Verifying...");
    try {
      const res = await fetch(`${API_URL}/verify_otp`, {
        method: "POST",
        body: new URLSearchParams({ otp }),
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });
      if (res.ok) {
        showToast("Login Successful!");
        state.account = { name: "Phone User", role: "customer" };
        saveLocalAccount();
        setView("customer");
      } else {
        showToast("Invalid OTP code.");
      }
    } catch (err) {
      showToast("Verification error.");
    }
  });
}

function renderCustomer() {
  state.account = state.account.name === "Guest" ? { name: "Local Customer", role: "customer" } : state.account;
  saveLocalAccount();
  accountChip.textContent = `${state.account.role}: ${state.account.name}`;
  const form = document.querySelector("#searchForm");
  const input = document.querySelector("#searchInput");
  const results = document.querySelector("#searchResults");
  renderProductGrid(results, state.products);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const query = input.value.trim().toLowerCase();
    const filtered = state.products.filter((product) => [product.productName, product.shopName, product.location].some((value) => String(value).toLowerCase().includes(query)));
    renderProductGrid(results, filtered);
  });
}

function renderSeller() {
  if (state.account.role === "customer" || state.account.name === "Guest") {
    state.account = { name: "Local Seller", role: "seller" };
    saveLocalAccount();
  }
  const stats = dashboardStats();
  document.querySelector("#sellerStats").innerHTML = statCards([
    ["Products", stats.products],
    ["Orders", stats.orders],
    ["Revenue", money(stats.revenue)]
  ]);

  const syncBtn = document.createElement("button");
  syncBtn.className = "wide";
  syncBtn.style.marginBottom = "20px";
  syncBtn.textContent = "🔄 Sync Offline Data from Phone";
  syncBtn.onclick = () => migrateOldData(true);
  document.querySelector("#sellerStats").after(syncBtn);

  renderProductGrid(document.querySelector("#sellerProducts"), state.products, "seller");

  const productRows = document.querySelector("#productRows");
  const addRowButtons = [document.querySelector("#addProductRow"), document.querySelector("#addProductRowBottom")];
  addProductRow(productRows);
  addProductRow(productRows);
  addRowButtons.forEach((button) => button.addEventListener("click", () => addProductRow(productRows)));

  document.querySelector("#productForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const shopName = form.get("shopName").trim();
    const location = form.get("location").trim();
    const latitude = form.get("latitude").trim();
    const longitude = form.get("longitude").trim();
    const rows = [...document.querySelectorAll(".product-row")];
    const productsToAdd = [];

    for (const row of rows) {
      const productName = row.querySelector("[name='productName']").value.trim();
      const price = Number(row.querySelector("[name='price']").value);
      const stock = Number(row.querySelector("[name='stock']").value);
      const imageFile = row.querySelector("[name='image']").files[0];

      if (!productName && !price && !stock && !imageFile) continue;
      if (!productName || !price || Number.isNaN(price)) {
        showToast("Each filled row needs a product name and price.");
        return;
      }

      productsToAdd.push({
        id: nextId([...state.products, ...productsToAdd]),
        shopName,
        location,
        productName,
        price,
        stock: Number.isNaN(stock) ? 0 : stock,
        latitude,
        longitude,
        image: imageFile ? await fileToDataUrl(imageFile) : "assets/shop.png"
      });
    }

    if (!productsToAdd.length) {
      showToast("Add at least one product row.");
      return;
    }

    try {
      const formData = new FormData();
      formData.append("shop_name", shopName);
      formData.append("location", location);
      formData.append("latitude", latitude);
      formData.append("longitude", longitude);

      // Note: Backend expects getlist for product_name, price, stock, unit
      rows.forEach(row => {
        const pName = row.querySelector("[name='productName']").value.trim();
        const pPrice = row.querySelector("[name='price']").value;
        const pStock = row.querySelector("[name='stock']").value;
        const pUnit = "unit"; // default
        const pImage = row.querySelector("[name='image']").files[0];

        if (pName && pPrice) {
          formData.append("product_name", pName);
          formData.append("price", pPrice);
          formData.append("stock", pStock || "0");
          formData.append("unit", pUnit);
          if (pImage) {
            formData.append("product_image", pImage);
          } else {
            formData.append("product_image", getPlaceholderFile("product_placeholder.png"));
          }
        }
      });

      // We also need shop_image (for simplicity use the first product image or a placeholder)
      const firstImage = rows.find(r => r.querySelector("[name='image']").files[0])?.querySelector("[name='image']").files[0];
      if (firstImage) {
        formData.append("shop_image", firstImage);
      } else {
        formData.append("shop_image", getPlaceholderFile("shop_placeholder.png"));
      }

      const res = await fetch(`${API_URL}/add_product`, {
        method: "POST",
        body: formData,
        credentials: "include"
      });

      showToast("Products submitted to live server.");
      setView("seller");
    } catch (err) {
      console.error("Upload error:", err);
      showToast("Failed to connect to live server.");
    }
  });

  document.querySelector("#resetDemo").addEventListener("click", () => {
    showToast("Demo reset is disabled in live mode.");
  });
}

function addProductRow(container) {
  const row = document.createElement("div");
  row.className = "product-row";
  row.innerHTML = `
    <div class="row-number">${container.children.length + 1}</div>
    <input name="productName" placeholder="Product name">
    <input name="price" type="number" min="1" placeholder="Price">
    <input name="stock" type="number" min="0" placeholder="Stock">
    <input name="image" type="file" accept="image/*">
    <button type="button" class="row-remove" aria-label="Remove product row">Remove</button>
  `;
  row.querySelector(".row-remove").addEventListener("click", () => {
    if (container.children.length <= 1) {
      row.querySelectorAll("input").forEach((input) => {
        if (input.type === "file") input.value = "";
        else input.value = "";
      });
      return;
    }
    row.remove();
    [...container.children].forEach((child, index) => {
      child.querySelector(".row-number").textContent = index + 1;
    });
  });
  container.append(row);
}

function renderOrders() {
  const stats = dashboardStats();
  document.querySelector("#orderStats").innerHTML = statCards([
    ["Total Orders", stats.orders],
    ["Delivered", stats.delivered],
    ["Revenue", money(stats.revenue)]
  ]);

  const list = document.querySelector("#ordersList");
  list.replaceChildren();
  if (!state.orders.length) {
    list.innerHTML = `<div class="empty">No orders yet. Buy a product to create a local order.</div>`;
    return;
  }

  state.orders.forEach((order) => {
    const card = document.createElement("article");
    card.className = "order-card";
    card.innerHTML = `
      <div class="order-top">
        <div>
          <h3>Order #${order.id}</h3>
          <p class="price">${escapeHtml(order.productName)} - ${money(order.price)}</p>
        </div>
        <span class="tag">${escapeHtml(order.status)}</span>
      </div>
      <div class="meta">
        <span>Customer: ${escapeHtml(order.customerName)}</span>
        <span>Address: ${escapeHtml(order.address)}</span>
        <span>Payment: ${escapeHtml(order.paymentMethod)}</span>
        <span>Rider: ${escapeHtml(order.riderName)} | ${escapeHtml(order.riderPhone)}</span>
        <span>Delivery OTP: ${escapeHtml(order.deliveryOtp)} | Verified: ${escapeHtml(order.otpVerified)}</span>
      </div>
      <div class="status-row">
        <select>${["Order Confirmed", "Preparing", "Packed", "Out For Delivery", "Delivered"].map((status) => `<option ${status === order.status ? "selected" : ""}>${status}</option>`).join("")}</select>
        <button type="button">Update Status</button>
      </div>
      <div class="status-row">
        <input inputmode="numeric" maxlength="6" placeholder="Enter delivery OTP">
        <button type="button">Confirm Delivered</button>
      </div>
    `;
    const statusSelect = card.querySelector("select");
    const otpInput = card.querySelector("input");
    const [updateButton, confirmButton] = card.querySelectorAll("button");
    updateButton.addEventListener("click", () => {
      if (statusSelect.value === "Delivered" && order.otpVerified !== "Yes") {
        showToast("Confirm the delivery OTP first.");
        return;
      }
      order.status = statusSelect.value;
      saveState();
      showToast("Order status updated.");
      setView("orders");
    });
    confirmButton.addEventListener("click", () => {
      if (otpInput.value.trim() !== order.deliveryOtp) {
        showToast("Wrong delivery OTP.");
        return;
      }
      order.otpVerified = "Yes";
      order.status = "Delivered";
      saveState();
      showToast("Delivery confirmed with OTP.");
      setView("orders");
    });
    list.append(card);
  });
}

function renderAnalytics() {
  const stats = dashboardStats();
  document.querySelector("#analyticsStats").innerHTML = statCards([
    ["Products", stats.products],
    ["Users", stats.users],
    ["Orders", stats.orders],
    ["Revenue", money(stats.revenue)]
  ]);
  document.querySelector("#topProducts").innerHTML = state.products
    .slice()
    .sort((a, b) => Number(b.price) - Number(a.price))
    .map((product) => rowItem(product.productName, `${money(product.price)} | Stock ${product.stock}`))
    .join("");
  document.querySelector("#activityList").innerHTML = [
    rowItem("Latest order", state.orders[0] ? `${state.orders[0].productName} | ${state.orders[0].status}` : "No orders yet"),
    rowItem("Low stock", state.products.filter((product) => Number(product.stock) <= 6).length),
    rowItem("Active chats", state.chats.length),
    rowItem("Local storage", "Enabled")
  ].join("");
}

function renderAdmin() {
  state.account = state.account.name === "Guest" ? { name: "admin", role: "admin" } : state.account;
  saveState();
  const stats = dashboardStats();
  document.querySelector("#adminStats").innerHTML = statCards([
    ["Products", stats.products],
    ["Orders", stats.orders],
    ["Users", stats.users],
    ["Delivered", stats.delivered]
  ]);
  document.querySelector("#adminProducts").innerHTML = state.products.map((product) => rowItem(product.productName, `${product.shopName} | ${money(product.price)} | Stock ${product.stock}`)).join("");
  document.querySelector("#adminOrders").innerHTML = state.orders.map((order) => rowItem(`#${order.id} ${order.productName}`, `${order.customerName} | ${order.status} | OTP ${order.deliveryOtp}`)).join("") || rowItem("No orders", "Place an order from customer panel");
}

function renderChat() {
  const messages = document.querySelector("#chatMessages");
  const form = document.querySelector("#chatForm");
  drawMessages(messages);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    sendChat(formData.get("sender"), formData.get("message"));
    form.reset();
    drawMessages(messages);
  });
  document.querySelectorAll("[data-chat]").forEach((button) => {
    button.addEventListener("click", () => {
      sendChat("customer", button.dataset.chat);
      drawMessages(messages);
    });
  });
}

function sendChat(sender, message) {
  const clean = String(message || "").trim();
  if (!clean) return;
  state.chats.push({ id: nextId(state.chats), sender, message: clean, createdAt: new Date().toLocaleString() });
  const reply = localAssistantReply(clean);
  if (reply) state.chats.push({ id: nextId(state.chats), sender: "assistant", message: reply, createdAt: new Date().toLocaleString() });
  saveState();
}

function localAssistantReply(message) {
  const clean = message.toLowerCase();
  const matches = state.products.filter((product) => clean.split(/\s+/).some((word) => word.length > 2 && product.productName.toLowerCase().includes(word))).slice(0, 3);
  if (matches.length) return `I found ${matches.map((product) => `${product.productName} at ${money(product.price)}`).join(", ")}.`;
  if (clean.includes("track") || clean.includes("order")) return "Open Orders to view rider details, status, and delivery OTP.";
  if (clean.includes("seller") || clean.includes("shop")) return "Open Seller to add products, images, stock, location, and price.";
  if (clean.includes("cheap") || clean.includes("lowest")) return "Use Customer Search and compare the price shown on each product card.";
  return "Tell me a product name like charger, bag, or mobile and I will search the local catalog.";
}

function productCard(product, mode = "customer") {
  const card = document.createElement("article");
  card.className = "product-card";
  card.innerHTML = `
    <div class="image-wrap">
      <img src="${product.image.startsWith('http') ? product.image : API_URL + product.image}" alt="${escapeHtml(product.productName)}">
      <span class="badge">Trending</span>
    </div>
    <div class="product-body">
      <span class="tag">${escapeHtml(product.shopName)}</span>
      <h3>${escapeHtml(product.productName)}</h3>
      <div class="price">${money(product.price)}</div>
      <div class="meta">
        <span>Stock Left: ${escapeHtml(product.stock)}</span>
        <span>Location: ${escapeHtml(product.location)}</span>
        <span>Map: ${escapeHtml(product.latitude || "0")}, ${escapeHtml(product.longitude || "0")}</span>
      </div>
      <div class="delivery">Fast delivery available</div>
      <div class="actions"></div>
    </div>
  `;
  const actions = card.querySelector(".actions");
  if (mode === "seller") {
    actions.append(actionButton("Edit", () => editProduct(product.id)), actionButton("Delete", () => deleteProduct(product.id), "danger"));
  } else {
    actions.append(
      actionButton("3D View", () => showToast("Offline 3D preview placeholder for this product.")),
      actionButton("Live Map", () => showToast(`Location: ${product.location} (${product.latitude || "0"}, ${product.longitude || "0"})`)),
      actionButton("Buy Now", () => openCheckout(product.id), "wide")
    );
  }
  return card;
}

function renderProductGrid(target, products, mode = "customer") {
  target.replaceChildren();
  if (!products.length) {
    target.innerHTML = `<div class="empty">No products found yet. Add products from the seller panel.</div>`;
    return;
  }
  products.forEach((product) => target.append(productCard(product, mode)));
}

function openCheckout(productId) {
  checkoutProductId = productId;
  const product = state.products.find((item) => item.id === productId);
  document.querySelector("#checkoutTitle").textContent = `Checkout: ${product.productName}`;
  checkoutDialog.showModal();
}

checkoutDialog.addEventListener("close", async () => {
  if (checkoutDialog.returnValue !== "confirm" || !checkoutProductId) return;
  const product = state.products.find((item) => item.id === checkoutProductId);
  const form = new FormData(checkoutForm);

  try {
    const res = await fetch(`${API_URL}/place_order`, {
      method: "POST",
      credentials: "include",
      body: new URLSearchParams({
        product_name: product.productName,
        price: product.price,
        product_image: product.image.split("/").pop(), // just the filename
        customerName: form.get("customerName"),
        phone: "+91 98765 43210", // placeholder or get from form if exists
        address: form.get("address"),
        payment: form.get("payment")
      })
    });

    if (res.ok) {
      showToast("Order placed on live server!");
      setView("orders");
    } else {
      showToast("Failed to place order.");
    }
  } catch (err) {
    console.error("Checkout error:", err);
    showToast("Server connection error.");
  }

  checkoutForm.reset();
  checkoutProductId = null;
});

function editProduct(id) {
  const product = state.products.find((item) => item.id === id);
  if (!product) return;
  const productName = prompt("Product name", product.productName);
  const price = prompt("Price", product.price);
  const stock = prompt("Stock", product.stock);
  if (productName === null || price === null || stock === null) return;
  product.productName = productName.trim() || product.productName;
  product.price = Number(price);
  product.stock = Number(stock);
  saveState();
  showToast("Product updated.");
  setView("seller");
}

function deleteProduct(id) {
  state.products = state.products.filter((item) => item.id !== id);
  saveState();
  showToast("Product deleted.");
  setView("seller");
}

function actionButton(label, handler, className = "") {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.textContent = label;
  button.addEventListener("click", handler);
  return button;
}

function drawMessages(target) {
  target.replaceChildren();
  state.chats.forEach((chat) => {
    const bubble = document.createElement("div");
    bubble.className = `message ${chat.sender}`;
    bubble.innerHTML = `<small>${escapeHtml(chat.sender)} - ${escapeHtml(chat.createdAt)}</small>${escapeHtml(chat.message)}`;
    target.append(bubble);
  });
  target.scrollTop = target.scrollHeight;
}

function dashboardStats() {
  return {
    products: state.products.length,
    orders: state.orders.length,
    users: state.users.length,
    revenue: state.orders.reduce((sum, order) => sum + Number(order.price || 0), 0),
    delivered: state.orders.filter((order) => order.status === "Delivered").length
  };
}

function statCards(items) {
  return items.map(([label, value]) => `<article class="stat-card"><strong>${escapeHtml(value)}</strong><span>${escapeHtml(label)}</span></article>`).join("");
}

function rowItem(title, detail) {
  return `<div class="row-item"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(detail)}</span></div>`;
}

function money(value) {
  return `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;
}

function nextId(items) {
  return items.reduce((max, item) => Math.max(max, Number(item.id) || 0), 0) + 1;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 2400);
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  })[char]);
}

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-view]");
  if (!button) return;
  setView(button.dataset.view);
});

if ("serviceWorker" in navigator && location.protocol !== "file:") {
  navigator.serviceWorker.register("./service-worker.js").catch((error) => console.warn("Service worker registration failed", error));
}

setView("home");
