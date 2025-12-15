const API_BASE = "/api";

const token = localStorage.getItem("token");
if (!token) {
  globalThis.location.href = "index.html";
}

const logoutBtn = document.getElementById("logout-btn");
logoutBtn.addEventListener("click", () => {
  localStorage.removeItem("token");
  globalThis.location.href = "index.html";
});

const booksTableBody = document.querySelector("#books-table tbody");
const bookForm = document.getElementById("book-form");
const statItems = document.getElementById("stat-items");
const statRevenue = document.getElementById("stat-revenue");

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (res.status === 401) {
    localStorage.removeItem("token");
    globalThis.location.href = "index.html";
  }
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify(body)
  });
  if (res.status === 401) {
    localStorage.removeItem("token");
    globalThis.location.href = "index.html";
  }
  return res.json().then(data => ({ ok: res.ok, data }));
}


async function loadBooks() {
  const books = await apiGet("/books");
  booksTableBody.innerHTML = "";
  books.forEach(b => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${b.name}</td>
      <td>${b.author}</td>
      <td>${b.genre}</td>
      <td>${Number.parseFloat(b.price).toFixed(2)} €</td>
      <td>${b.stock}</td>
      <td>
        <input type="number" min="1" value="1" class="qty-input">
        <button class="order-btn" data-id="${b.id}">Commander</button>
      </td>
      <td>
        <input type="number" min="1" value="1" class="qty-input">
        <button class="addbooks-btn" data-id="${b.id}">Ajouter du stock</button>
      </td>      
    `;
    booksTableBody.appendChild(tr);
  });
}

bookForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("book-name").value;
  const author = document.getElementById("book-author").value;
  const genre = document.getElementById("book-genre").value;
  const price = document.getElementById("book-price").value;
  const stock = document.getElementById("book-stock").value;
  const { ok, data } = await apiPost("/books", { name, author, genre, price, stock });
  if (!ok) {
    alert(data.error || "Erreur ajout livre");
    return;
  }
  bookForm.reset();
  loadBooks();
});

booksTableBody.addEventListener("click", async (e) => {
  if (e.target.classList.contains("order-btn")) {
    const bookId = e.target.dataset.id;
    const qtyInput = e.target.parentElement.querySelector(".qty-input");
    const quantity = Number.parseInt(qtyInput.value, 10) || 1;
    const { ok, data } = await apiPost("/orders", { book_id: bookId, quantity });
    if (!ok) {
      alert(data.error || "Erreur commande");
      return;
    }
    alert("Commande enregistrée.");
    loadBooks();
    loadStats();
  }
  if (e.target.classList.contains("addbooks-btn")) {
    const bookId = e.target.dataset.id;
    const qtyInput = e.target.parentElement.querySelector(".qty-input");
    const quantity = Number.parseInt(qtyInput.value, 10) || 1;
    const { ok, data } = await apiPost("/books", { id: bookId, stock: quantity, add_stock: true });
    if (!ok) {
      alert(data.error || "Erreur ajout stock");
      return;
    }
  }
});

async function loadStats() {
  const stats = await apiGet("/stats");
  statItems.textContent = stats.total_items;
  statRevenue.textContent = stats.total_revenue.toFixed(2);
}

loadBooks();
loadStats();
