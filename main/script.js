// Navigation functionality
function showSection(sectionId) {
    // Hide all sections
    const sections = document.querySelectorAll('.section-content, .section');
    sections.forEach(section => {
        section.classList.add('hide');
    });
    // Show selected section
    const selectedSection = document.getElementById(sectionId);
    if (selectedSection) {
        selectedSection.classList.remove('hide');
    }
    // Update active nav link
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.classList.remove('active');
    });
    event.target.classList.add('active');
    // Update page title
    const titles = {
        'dashboard': 'Tableau de Bord',
        'products': 'Gestion des Produits',
        'low-stock': 'Stock Faible',
        'movements': 'Mouvements d\'Inventaire',
        'reports': 'Rapports'
    };
    document.getElementById('page-title').textContent = titles[sectionId] || 'Inventaire';
}
// Modal functions
function openAddProductModal() {
    document.getElementById('productModal').classList.add('show');
}
function closeAddProductModal() {
    document.getElementById('productModal').classList.remove('show');
    document.querySelector('form').reset();
}
function saveProduct() {
    const name = document.getElementById('productName').value;
    const category = document.getElementById('productCategory').value;
    const stock = document.getElementById('productStock').value;
    const minStock = document.getElementById('productMinStock').value;
    const price = document.getElementById('productPrice').value;
    if (name && stock && minStock && price) {
        alert(`✅ Produit sauvegardé!\n\n${name}\nCatégorie: ${category}\nStock: ${stock}\nPrix: €${price}`);
        closeAddProductModal();
    } else {
        alert('⚠️ Veuillez remplir tous les champs!');
    }
}
// Product management functions
function editProduct(id) {
    openAddProductModal();
    alert(`✏️ Édition du produit #${id}`);
}
function deleteProduct(id) {
    if (confirm(`Êtes-vous sûr de vouloir supprimer ce produit?`)) {
        alert(`🗑️ Produit #${id} supprimé!`);
    }
}
function reorderProduct(name) {
    alert(`📦 Commande de réapprovisionnement pour "${name}" créée!`);
}
function generateAlert() {
    alert(`📧 Alerte de stock faible envoyée aux responsables!`);
}
function exportMovements() {
    alert(`📥 Téléchargement du fichier CSV en cours...`);
}
function generateReport() {
    alert(`📊 Rapport généré et prêt à être téléchargé!`);
}
// Search functionality
document.getElementById('search').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        alert(`🔍 Recherche de: "${this.value}"`);
    }
});
// Close modal when clicking outside
document.getElementById('productModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeAddProductModal();
    }
});