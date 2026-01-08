const API_BASE = "/api";
const token = localStorage.getItem("token");
let allBooks = [];

if (!token) {
  window.location.href = "/";
}

const booksTableBody = document.querySelector("#books-table tbody");
const bookForm = document.getElementById("book-form");
const statItems = document.getElementById("stat-items");
const statRevenue = document.getElementById("stat-revenue");
const logoutBtn = document.getElementById("logout-btn");
const searchInput = document.getElementById("search-btn");

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    localStorage.removeItem("token");
    window.location.href = "/";
  });
}

if (searchInput) {
  searchInput.addEventListener("input", () => {
    const q = searchInput.value.toLowerCase().trim();

    const filtered = allBooks.filter((b) =>
      b.name.toLowerCase().includes(q) ||
      b.author.toLowerCase().includes(q) ||
      b.genre.toLowerCase().includes(q)
    );

    renderBooksTable(filtered);
  });
}


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

async function apiPut(path, body) {
  const res = await fetch(API_BASE + path, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + token,
    },
    body: JSON.stringify(body),
  });
  if (res.status === 401) {
    localStorage.removeItem("token");
    globalThis.location.href = "index.html";
    return res.json().then(data => ({ ok: false, data }));
  }
  const data = await res.json();
  return { ok: res.ok, data };
}

function getToken() {
    return localStorage.getItem("token") || "";
}

async function addToCart(bookId, quantity = 1) {
    const token = getToken();
    const res = await fetch("/api/cart", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({ book_id: String(bookId), quantity })
    });
    if (res.ok) {
        await fetchCart();
      if (typeof loadBooks === "function") {
        await loadBooks();
      }
    } else {
        const err = await res.json();
        alert(err.error || "Erreur ajout au panier");
    }
}

async function fetchCart() {
    const token = getToken();
    const res = await fetch("/api/cart", {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) return;
    const items = await res.json();
    renderCart(items);
}

function renderCart(items) {
    const container = document.getElementById("cart-items");
    const count = document.getElementById("cart-count");
    container.innerHTML = "";
    if (!items || items.length === 0) {
        container.innerHTML = "<p>Panier vide</p>";
        count.textContent = "0";
        return;
    }
    count.textContent = String(items.length);
    items.forEach(item => {
        const el = document.createElement("div");
        el.className = "cart-item";
        const name = item.book_name || ("Livre ID " + item.book_id);
        el.innerHTML = `
            <div class="cart-item-left">
                <strong>${name}</strong>
                <div>Quantité: ${item.quantity}</div>
            </div>
            <div class="cart-item-right">
                <button class="remove-cart-btn" data-id="${item.id}">Supprimer</button>
            </div>
        `;
        container.appendChild(el);
    });
    document.querySelectorAll(".remove-cart-btn").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            const id = e.currentTarget.dataset.id;
            await removeFromCart(id);
        });
    });
}

async function removeFromCart(cartId) {
    const token = getToken();
    const res = await fetch(`/api/cart/${cartId}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + token }
    });
    if (res.ok) {
        await fetchCart();
      if (typeof loadBooks === "function") {
        await loadBooks();
      }
    } else {
        const err = await res.json();
        alert(err.error || "Impossible de supprimer");
    }
}

async function fetchOrders() {
    const token = getToken();
    const res = await fetch("/api/orders", {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) return;
    const orders = await res.json();
    renderOrders(orders);
}

function renderOrders(orders) {
    const container = document.querySelector("#orders-table tbody");
    container.innerHTML = "";
    if (!orders || orders.length === 0) {
        container.innerHTML = "<tr><td colspan='3' style='text-align:center;'>Aucun achat</td></tr>";
        return;
    }
    orders.forEach(order => {
        const tr = document.createElement("tr");
    // supporte plusieurs noms de champ de date selon le backend
    const dateStr = order.date || order.date_achat || order.date_added || order.date_achat;
    let dateText = "";
    try {
      const d = new Date(dateStr);
      if (!isNaN(d)) dateText = d.toLocaleDateString('fr-FR');
    } catch (e) {
      dateText = "";
    }
    tr.innerHTML = `
      <td>${order.book_name || "Livre introuvable"}</td>
      <td>${order.quantity}</td>
      <td>${dateText}</td>
    `;
        container.appendChild(tr);
    });
}

async function checkoutCart() {
    const token = getToken();
    const res = await fetch("/api/cart/checkout", {
        method: "POST",
        headers: { "Authorization": "Bearer " + token }
    });
    if (res.ok) {
        alert("Achat finalisé");
        // Vider immédiatement l'affichage du panier
        renderCart([]);
      if (typeof loadBooks === "function") await loadBooks();
      await fetchCart();
      // Mettre à jour la liste des achats récents après un checkout
      if (typeof fetchOrders === "function") await fetchOrders();
        document.getElementById("cart-panel").classList.add("cart-closed");
    } else {
        const err = await res.json();
        alert(err.error || "Erreur lors du paiement");
    }
    await fetchCart();
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("open-cart-btn").addEventListener("click", () => {
        document.getElementById("cart-panel").classList.remove("cart-closed");
    });
    document.getElementById("close-cart-btn").addEventListener("click", () => {
        document.getElementById("cart-panel").classList.add("cart-closed");
    });
    document.getElementById("checkout-btn").addEventListener("click", () => {
        if (confirm("Confirmer la commande de tous les articles du panier ?")) {
            checkoutCart();
        }
    });
    // Tab navigation: basique, affiche le panneau lié au bouton cliqué
    const tabButtons = document.querySelectorAll('.tabs button');
    if (tabButtons && tabButtons.length) {
      tabButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
          tabButtons.forEach(b => b.classList.remove('active'));
          e.currentTarget.classList.add('active');
          const target = e.currentTarget.dataset.tab;
          document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
          const panel = document.getElementById(`tab-${target}`);
          if (panel) panel.classList.add('active');
        });
      });
    }
    if (typeof loadBooks === "function") {
      loadBooks().then(() => fetchCart()).then(() => fetchOrders());
    } else {
      fetchCart().then(() => fetchOrders());
    }
});

document.addEventListener("click", (e) => {
    const btn = e.target.closest(".order-btn");
    if (!btn) return;
    const id = btn.dataset.id;
    addToCart(id, 1);
});

async function loadBooks() {
  const books = await apiGet("/books");
  allBooks = books;
  renderBooksTable(books);
}

async function renderBooksTable(books) {
  booksTableBody.innerHTML = "";
  books.forEach((b) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${b.name}</td>
      <td>${b.author}</td>
      <td>${b.genre}</td>
      <td class="admin-actions3">
        ${b.price} €
      </td>
      <td>${b.stock}</td>
      <td class="actions-col">
        <div class="order-wrap">
          <input type="number" min="1" value="1" class="qty-input">
          <button class="order-btn" data-id="${b.id}">Commander</button>
        </div>
        <div class="admin-controls"></div>
      </td>
    `;

      const actionsCell = tr.querySelector(".actions-col");
      const adminControls = actionsCell.querySelector(".admin-controls");

      const addStockBtn = document.createElement("button");
      addStockBtn.textContent = "Ajouter stock";
      addStockBtn.classList.add("btn-add-stock");
      addStockBtn.id = `btn-stock-${b.id}`;
      addStockBtn.addEventListener("click", (e) => {
          e.preventDefault();
          const quantity = prompt("Quantité à ajouter :");
          if (quantity && !isNaN(quantity) && parseInt(quantity) > 0) {
              addStock(b.id, parseInt(quantity));
          }
      });

      const addDeleteBtn = document.createElement("button");
      addDeleteBtn.textContent = "Supprimer";
      addDeleteBtn.classList.add("btn-delete-stock");
      addDeleteBtn.id = `btn-delete-${b.id}`;
      addDeleteBtn.addEventListener("click", (e) => {
        e.preventDefault();
        const areUsure = prompt("Êtes vous sûre de vouloir supprimer cet article ? \n Écrivez 'oui' pour valider : ");
        if (areUsure === "Oui" || areUsure === "oui" || areUsure === "OUI"){
          DeleteStock(b.id, b.name);
        }
      });

      const adminActionsCell3 = tr.querySelector(".admin-actions3");
      const modifyPriceBtns = document.createElement("button");
      modifyPriceBtns.textContent = "modifier le prix";
      modifyPriceBtns.classList.add("btn-modify-price");
      modifyPriceBtns.id = `btn-stock-${b.id}`;
      modifyPriceBtns.addEventListener("click", (e) => {
          e.preventDefault();
          const newPrice = prompt("Nouveau prix :");
          if (newPrice && !isNaN(newPrice) && parseFloat(newPrice) > 0) {
              modifyPrice(b.id, parseFloat(newPrice));
          }
      });

      adminControls.appendChild(addStockBtn);
      adminControls.appendChild(addDeleteBtn);
      adminActionsCell3.appendChild(modifyPriceBtns);
      booksTableBody.appendChild(tr);
  });
  
  await checkAdminAndShowButton();
}

async function DeleteStock(bookId, bookname) {

  const result = await apiPost("/deletebooks", {
    book_id: bookId,
    book_name: bookname
    });

  if (result.ok) {
        alert("Stock mis à jour !");
        await loadBooks();
        await loadStats();
    } else {
        alert("Erreur : " + (result.data.error || "Erreur inconnue"));
    }

}

async function addStock(bookId, quantity) {
    console.log("Envoi requête addStock:", { book_id: bookId, quantity: quantity });
    
    const result = await apiPost("/addbooks", {
        book_id: bookId,
        quantity: quantity
    });
    
    console.log("Réponse du serveur:", result);
    
    if (result.ok) {
        alert("Stock mis à jour !");
        await loadBooks();
        await loadStats();
    } else {
        alert("Erreur : " + (result.data.error || "Erreur inconnue"));
    }
}

async function checkAdminAndShowButton() {
    const user = await apiGet("/me");
    const adminEmail = "admin@admin.com";
    
    const addDeleteBtns = document.querySelectorAll(".btn-delete-stock")    
    const modifyPriceBtns = document.querySelectorAll(".btn-modify-price");
    const addStockBtns = document.querySelectorAll(".btn-add-stock");
    const addBookForm = document.getElementById("add-book-section");
    const statSection = document.getElementById("stat-section");
    
    if (user.email !== adminEmail) {
        modifyPriceBtns.forEach(btn => btn.style.display = "none");
        addDeleteBtns.forEach(btn => btn.style.display = "none");
        addStockBtns.forEach(btn => btn.style.display = "none");
        addBookForm.style.display = "none";
        statSection.style.display = "none";
    }
}

async function modifyPrice(bookId, newPrice) {
    console.log("Envoi requête addStock:", { book_id: bookId, new_price: newPrice });
    
      const result = await apiPut(`/books/${bookId}/price`, {
      price: newPrice  
    });
    
    console.log("Réponse du serveur:", result);
    
    if (result.ok) {
        alert("Prix modifié !");
        await loadBooks();
        await loadStats();
    } else {
        alert("Erreur : " + (result.data.error || "Erreur inconnue"));
    }
    init();
}

async function loadStats() {
    const stats = await apiGet("/stats");
    statItems.textContent = stats.total_items;
    statRevenue.textContent = stats.total_revenue.toFixed(2);
}

bookForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("book-name").value;
  const author = document.getElementById("book-author").value;
  const genre = document.getElementById("book-genre").value;
  const price = document.getElementById("book-price").value;
  const stock = document.getElementById("book-stock").value;
  const result = await apiPost("/books", { name, author, genre, price, stock });
    
    if (result.ok) {
        bookForm.reset();
        init();
    } else {
        alert("Erreur : " + result.data.error);
    }
});

booksTableBody.addEventListener("click", async (e) => {
  // Les boutons de commande ajoutent maintenant au panier via le gestionnaire global;
  // n'envoyez pas directement une requête /orders ici pour éviter les doublons.
  // (Le click sur .order-btn est traité par le listener global plus haut.)
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


function sortTable(n) {
  var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
  table = document.getElementById("books-table");
  switching = true;
  dir = "asc";
  while (switching) {
    switching = false;
    rows = table.rows;
    for (i = 1; i < (rows.length - 1); i++) {
      shouldSwitch = false;
      x = rows[i].getElementsByTagName("TD")[n];
      y = rows[i + 1].getElementsByTagName("TD")[n];
      if (dir == "asc") {
        if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
          shouldSwitch = true;
          break;
        }
      } else if (dir == "desc") {
        if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
          shouldSwitch = true;
          break;
        }
      }
    }
    if (shouldSwitch) {
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
      switchcount ++;
    } else {
      if (switchcount == 0 && dir == "asc") {
        dir = "desc";
        switching = true;
      }
    }
  }
}

async function init() {
    await loadBooks();
    await checkAdminAndShowButton();
    await loadStats();
}

init();
