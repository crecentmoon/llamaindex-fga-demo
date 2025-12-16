// State
let selectedUserId = null;
let users = [];
let permissions = {};

// DOM Elements
const userCardsContainer = document.getElementById('userCards');
const questionInput = document.getElementById('questionInput');
const submitBtn = document.getElementById('submitBtn');
const resultsSection = document.getElementById('resultsSection');
const documentsList = document.getElementById('documentsList');
const answerContent = document.getElementById('answerContent');
const permissionSummary = document.getElementById('permissionSummary');
const permissionPanel = document.getElementById('permissionPanel');
const accessibleDocuments = document.getElementById('accessibleDocuments');
const loadingOverlay = document.getElementById('loadingOverlay');
const scenarioButtons = document.querySelectorAll('.scenario-btn');

// Initialize
async function init() {
    await loadUsers();
    await loadDocuments();
    setupEventListeners();
}

// Load users from API
async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        users = await response.json();
        renderUserCards();
    } catch (error) {
        console.error('Failed to load users:', error);
    }
}

// Render user cards
function renderUserCards() {
    userCardsContainer.innerHTML = '';
    users.forEach(user => {
        const card = document.createElement('div');
        card.className = 'user-card';
        card.dataset.userId = user.id;
        
        const groupsHtml = user.groups.map(g => 
            `<span class="group-badge">${g}</span>`
        ).join('');
        
        card.innerHTML = `
            <h3>${user.name}</h3>
            <div class="role">${user.role}</div>
            <div class="groups">${groupsHtml}</div>
        `;
        
        card.addEventListener('click', () => selectUser(user.id));
        userCardsContainer.appendChild(card);
    });
}

// Select user
async function selectUser(userId) {
    selectedUserId = userId;
    
    // Update UI
    document.querySelectorAll('.user-card').forEach(card => {
        card.classList.remove('selected');
        if (card.dataset.userId === userId) {
            card.classList.add('selected');
        }
    });
    
    // Enable submit button
    submitBtn.disabled = false;
    
    // Load permissions
    await loadPermissions(userId);
    
    // Update permission panel
    updatePermissionPanel(userId);
}

// Load permissions for user
async function loadPermissions(userId) {
    try {
        const response = await fetch(`/api/permissions/${userId}`);
        permissions[userId] = await response.json();
    } catch (error) {
        console.error('Failed to load permissions:', error);
    }
}

// Update permission panel
function updatePermissionPanel(userId) {
    if (!permissions[userId]) return;
    
    const perm = permissions[userId];
    const folders = {};
    
    // Group documents by folder
    perm.accessible_documents.forEach(doc => {
        if (!folders[doc.folder]) {
            folders[doc.folder] = [];
        }
        folders[doc.folder].push(doc);
    });
    
    // Get all documents
    const allDocs = [
        {id: "1", title: "Engineering Roadmap 2025", folder: "engineering"},
        {id: "2", title: "Sales Targets 2025", folder: "sales"},
        {id: "3", title: "Holiday Notice", folder: "general"},
        {id: "4", title: "Project Alpha Specs", folder: "engineering"},
        {id: "5", title: "Q4 Sales Report JP", folder: "sales"},
        {id: "6", title: "Remote Work Policy", folder: "general"},
        {id: "7", title: "Merger Strategy", folder: "executive"},
    ];
    
    const folderNames = {
        engineering: "Engineering",
        sales: "Sales",
        general: "General",
        executive: "Executive"
    };
    
    let html = '';
    Object.keys(folderNames).forEach(folderKey => {
        const folderName = folderNames[folderKey];
        const accessibleDocIds = new Set(
            (folders[folderKey] || []).map(d => d.id)
        );
        
        html += `<div class="folder-group">`;
        html += `<div class="folder-title">${folderName}</div>`;
        
        allDocs.filter(d => d.folder === folderKey).forEach(doc => {
            const isAccessible = accessibleDocIds.has(doc.id);
            html += `<div class="accessible-doc-item ${isAccessible ? '' : 'disabled'}">`;
            html += doc.title;
            html += `</div>`;
        });
        
        html += `</div>`;
    });
    
    accessibleDocuments.innerHTML = html;
}

// Setup event listeners
function setupEventListeners() {
    // Submit button
    submitBtn.addEventListener('click', handleSubmit);
    
    // Enter key in textarea
    questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            handleSubmit();
        }
    });
    
    // Scenario buttons
    scenarioButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const question = btn.dataset.question;
            questionInput.value = question;
            questionInput.focus();
        });
    });
}

// Handle submit
async function handleSubmit() {
    if (!selectedUserId || !questionInput.value.trim()) {
        return;
    }
    
    const question = questionInput.value.trim();
    
    // Show loading
    loadingOverlay.style.display = 'flex';
    resultsSection.style.display = 'none';
    
    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: selectedUserId,
                question: question
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        console.error('Query failed:', error);
        alert('エラーが発生しました: ' + error.message);
    } finally {
        loadingOverlay.style.display = 'none';
    }
}

// Display results
function displayResults(data) {
    // Show results section
    resultsSection.style.display = 'block';
    
    // Update permission summary
    permissionSummary.textContent = 
        `${data.allowed_count} / ${data.total_count} 件のドキュメントが許可されました`;
    
    // Display documents with animation
    documentsList.innerHTML = '';
    data.documents.forEach((doc, index) => {
        setTimeout(() => {
            const docItem = document.createElement('div');
            docItem.className = `document-item ${doc.allowed ? 'allowed' : 'denied'}`;
            
            const statusIcon = doc.allowed ? '✅' : '❌';
            const statusText = doc.allowed ? '許可' : '拒否';
            const statusClass = doc.allowed ? 'allowed' : 'denied';
            
            docItem.innerHTML = `
                <div class="document-header">
                    <div class="document-title">${doc.title}</div>
                    <div class="document-status ${statusClass}">
                        ${statusIcon} ${statusText}
                    </div>
                </div>
                <div class="document-meta">
                    <span>カテゴリ: ${doc.category}</span>
                    <span>スコア: ${doc.score.toFixed(2)}</span>
                </div>
                <div class="document-text">${doc.text}</div>
            `;
            
            documentsList.appendChild(docItem);
        }, index * 200); // Stagger animation
    });
    
    // Display answer
    answerContent.textContent = data.answer;
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Load documents (for reference)
async function loadDocuments() {
    try {
        const response = await fetch('/api/documents');
        const docs = await response.json();
        // Store for future use if needed
        console.log('Loaded documents:', docs);
    } catch (error) {
        console.error('Failed to load documents:', error);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);

