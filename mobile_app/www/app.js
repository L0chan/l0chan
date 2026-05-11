const STORE_KEY = "npf.mobile.state.v2";
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

const seedState = {
  account: { name: "Guest", role: "customer" },
  users: [
    { id: 1, username: "admin", role: "admin" },
    { id: 2, username: "seller", role: "seller" },
    { id: 3, username: "customer", role: "customer" }
  ],
  products: [
    {
      id: 1,
      shopName: "City Mobile Hub",
      location: "MG Road",
      productName: "Type-C Fast Charger",
      price: 499,
      stock: 24,
      latitude: "12.9716",
      longitude: "77.5946",
      image: "assets/charger.jpg"
    },
    {
      id: 2,
      shopName: "Daily Carry Store",
      location: "Market Street",
      productName: "Black Laptop Bag",
      price: 899,
      stock: 11,
      latitude: "12.9751",
      longitude: "77.6052",
      image: "assets/bag.jpg"
    },
    {
      id: 3,
      shopName: "Smart Zone",
      location: "Station Road",
      productName: "Budget Mobile Phone",
      price: 7999,
      stock: 6,
      latitude: "12.9653",
      longitude: "77.5891",
      image: "assets/mobile.jpg"
    }
  ],
  orders: [
    {
      id: 1,
      productId: 1,
      productName: "Type-C Fast Charger",
      price: 499,
      customerName: "Demo Customer",
      address: "12 Market Road",
      paymentMethod: "Cash on Delivery",
      status: "Out For Delivery",
      riderName: "Arjun Kumar",
      riderPhone: "+91 98765 12001",
      deliveryOtp: "123456",
      otpVerified: "No",
      createdAt: new Date().toLocaleString()
    }
  ],
  chats: [
    { id: 1, sender: "seller", message: "Welcome. Ask about stock, delivery, or product availability.", createdAt: new Date().toLocaleString() }
  ]
};

function loadState() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORE_KEY));
    if (stored && Array.isArray(stored.products) && Array.isArray(stored.orders)) return stored;
  } catch (error) {
    console.warn("Could not load local state", error);
  }
  saveState(seedState);
  return structuredClone(seedState);
}

let state = loadState();

function saveState(nextState = state) {
  localStorage.setItem(STORE_KEY, JSON.stringify(nextState));
}

function setView(viewName) {
  const template = document.querySelector(`#${viewName}View`);
  if (!template) return;
  currentView = viewName;
  document.body.dataset.view = viewName;
  app.replaceChildren(template.content.cloneNode(true));
  document.querySelectorAll("[data-view]").forEach((button) => button.classList.toggle("active", button.dataset.view === viewName));
  accountChip.textContent = `${state.account.role}: ${state.account.name}`;
  app.focus({ preventScroll: true });

  ({
    home: renderHome,
    auth: renderAuth,
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
}

function renderAuth() {
  document.querySelector("#loginForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const username = form.get("username").trim() || "Guest";
    const role = form.get("role");
    state.account = { name: username, role };
    if (!state.users.some((user) => user.username.toLowerCase() === username.toLowerCase())) {
      state.users.push({ id: nextId(state.users), username, role });
    }
    saveState();
    showToast(`Logged in as ${role}.`);
    setView(role === "admin" ? "admin" : role === "seller" ? "seller" : "customer");
  });
}

function renderCustomer() {
  state.account = state.account.name === "Guest" ? { name: "Local Customer", role: "customer" } : state.account;
  saveState();
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
    saveState();
  }
  const stats = dashboardStats();
  document.querySelector("#sellerStats").innerHTML = statCards([
    ["Products", stats.products],
    ["Orders", stats.orders],
    ["Revenue", money(stats.revenue)]
  ]);
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

    state.products.unshift(...productsToAdd);
    saveState();
    showToast(`${productsToAdd.length} product${productsToAdd.length === 1 ? "" : "s"} added locally.`);
    setView("seller");
  });

  document.querySelector("#resetDemo").addEventListener("click", () => {
    state = structuredClone(seedState);
    saveState();
    showToast("Demo data reset.");
    setView("seller");
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
      <img src="${product.image}" alt="${escapeHtml(product.productName)}">
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

checkoutDialog.addEventListener("close", () => {
  if (checkoutDialog.returnValue !== "confirm" || !checkoutProductId) return;
  const product = state.products.find((item) => item.id === checkoutProductId);
  const form = new FormData(checkoutForm);
  const rider = riders[state.orders.length % riders.length];
  state.orders.unshift({
    id: nextId(state.orders),
    productId: product.id,
    productName: product.productName,
    price: product.price,
    customerName: form.get("customerName").trim(),
    address: form.get("address").trim(),
    paymentMethod: form.get("payment"),
    status: "Order Confirmed",
    riderName: rider[0],
    riderPhone: rider[1],
    deliveryOtp: String(Math.floor(100000 + Math.random() * 900000)),
    otpVerified: "No",
    createdAt: new Date().toLocaleString()
  });
  product.stock = Math.max(0, Number(product.stock || 0) - 1);
  saveState();
  checkoutForm.reset();
  checkoutProductId = null;
  showToast("Order placed successfully.");
  setView("orders");
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
