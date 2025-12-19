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
      <td>
        <input id=order-btn type="number" min="1" value="1" class="qty-input">
        <button class="order-btn" data-id="${b.id}">Commander</button>
      </td>
      <td class="admin-actions"></td>  
      <td class="admin-actions2"></td>  
    `;

      const adminActionsCell = tr.querySelector(".admin-actions");
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

      const adminActionsCell2 = tr.querySelector(".admin-actions2");
      const addDeleteBtn = document.createElement("button");
      addDeleteBtn.textContent = "Supprimer";
      addDeleteBtn.classList.add("btn-delete-stock");
      addDeleteBtn.id = `btn-delete-${b.id}`;
      addDeleteBtn.addEventListener("click", (e) => {
          e.preventDefault();
          const areUsure = prompt("Êtes vous sûre de vouloir supprimer ? \n Écrivez 'oui'")
          if (areUsure == "oui" || "Oui" || "OUI") {
            DeleteStock(b.id)
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

      adminActionsCell.appendChild(addStockBtn);
      adminActionsCell2.appendChild(addDeleteBtn);
      adminActionsCell3.appendChild(modifyPriceBtns);
      booksTableBody.appendChild(tr);
  });
  
  await checkAdminAndShowButton();
}

async function DeleteStock(id, quantity) {

  const result = await apiPost("/deletebooks", {
        book_id: id,
        quantity: quantity
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
    init();
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
