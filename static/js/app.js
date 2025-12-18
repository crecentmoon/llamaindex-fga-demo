// State
let selectedUserId = null;
let users = [];
let documents = [];
let permissions = {};
let flowAnimationTimer = null;

// DOM Elements
const userCardsContainer = document.getElementById("userCards");
const questionInput = document.getElementById("questionInput");
const submitBtn = document.getElementById("submitBtn");
const resultsSection = document.getElementById("resultsSection");
const documentsList = document.getElementById("documentsList");
const answerContent = document.getElementById("answerContent");
const permissionSummary = document.getElementById("permissionSummary");
const permissionPanel = document.getElementById("permissionPanel");
const accessibleDocuments = document.getElementById("accessibleDocuments");
const loadingOverlay = document.getElementById("loadingOverlay");
const scenarioButtons = document.querySelectorAll(".scenario-btn");

// Initialize
async function init() {
  await loadUsers();
  await loadDocuments();
  setupEventListeners();
}

// Load users from API
async function loadUsers() {
  try {
    const response = await fetch("/api/users");
    users = await response.json();
    renderUserCards();
  } catch (error) {
    console.error("Failed to load users:", error);
  }
}

// Get profile image path from user object
// Image mapping is now managed server-side via API
function getProfileImagePath(user) {
  return user.profile_image || `/static/img/${user.id.replace("user:", "").toLowerCase()}.png`;
}

// Render user cards
function renderUserCards() {
  userCardsContainer.innerHTML = "";
  users.forEach((user) => {
    const card = document.createElement("div");
    card.className = "user-card";
    card.dataset.userId = user.id;

    const groupsHtml = user.groups
      .map((g) => `<span class="group-badge">${g}</span>`)
      .join("");

    const profileImagePath = getProfileImagePath(user);

    card.innerHTML = `
            <div class="user-avatar">
              <img src="${profileImagePath}" alt="${user.name}" onerror="this.src='/static/img/default.png'; this.onerror=null;" />
            </div>
            <h3>${user.name}</h3>
            <div class="role">${user.role}</div>
            <div class="groups">${groupsHtml}</div>
        `;

    card.addEventListener("click", () => selectUser(user.id));
    userCardsContainer.appendChild(card);
  });
}

// Select user
async function selectUser(userId) {
  selectedUserId = userId;

  // Update UI
  document.querySelectorAll(".user-card").forEach((card) => {
    card.classList.remove("selected");
    if (card.dataset.userId === userId) {
      card.classList.add("selected");
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
    console.error("Failed to load permissions:", error);
  }
}

// Update permission panel
function updatePermissionPanel(userId) {
  if (!permissions[userId] || !documents.length) return;

  const perm = permissions[userId];
  const folders = {};

  // Group accessible documents by folder
  perm.accessible_documents.forEach((doc) => {
    if (!folders[doc.folder]) {
      folders[doc.folder] = [];
    }
    folders[doc.folder].push(doc);
  });

  // Group all documents by folder (from API)
  const allDocsByFolder = {};
  documents.forEach((doc) => {
    const folder = doc.folder || "general";
    if (!allDocsByFolder[folder]) {
      allDocsByFolder[folder] = [];
    }
    allDocsByFolder[folder].push(doc);
  });

  const folderNames = {
    engineering: "Engineering",
    se: "SE",
    sales: "Sales",
    product: "Product",
    corporate: "Corporate",
    scpm: "SC/PM",
    general: "General",
    executive: "Executive",
  };

  let html = "";
  Object.keys(folderNames).forEach((folderKey) => {
    const folderName = folderNames[folderKey];
    const accessibleDocIds = new Set(
      (folders[folderKey] || []).map((d) => d.id)
    );
    const folderDocs = allDocsByFolder[folderKey] || [];

    html += `<div class="folder-group">`;
    html += `<div class="folder-title">${folderName}</div>`;

    folderDocs.forEach((doc) => {
      const isAccessible = accessibleDocIds.has(doc.id);
      html += `<div class="accessible-doc-item ${
        isAccessible ? "" : "disabled"
      }">`;
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
  submitBtn.addEventListener("click", handleSubmit);

  // Enter key in textarea
  questionInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && e.ctrlKey) {
      handleSubmit();
    }
  });

  // Scenario buttons
  scenarioButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const question = btn.dataset.question;
      questionInput.value = question;
      questionInput.focus();
    });
  });
}

// Stop flow visualization animation
function stopFlowVisualization() {
  clearTimeout(flowAnimationTimer);
  const flowSteps = document.querySelectorAll(".flow-step");
  const flowArrows = document.querySelectorAll(".flow-arrow");
  flowSteps.forEach((step) => {
    step.classList.remove("active", "completed");
  });
  flowArrows.forEach((arrow) => {
    arrow.classList.remove("active", "completed");
  });
}

// Animate flow visualization with loop
function animateFlowVisualization(shouldLoop = false) {
  const flowSteps = document.querySelectorAll(".flow-step");
  const flowArrows = document.querySelectorAll(".flow-arrow");

  // Reset all steps
  flowSteps.forEach((step) => {
    step.classList.remove("active", "completed");
  });
  flowArrows.forEach((arrow) => {
    arrow.classList.remove("active", "completed");
  });

  // Animate each step sequentially
  flowSteps.forEach((step, index) => {
    setTimeout(() => {
      // Mark previous step as completed
      if (index > 0) {
        flowSteps[index - 1].classList.remove("active");
        flowSteps[index - 1].classList.add("completed");
        if (flowArrows[index - 1]) {
          flowArrows[index - 1].classList.remove("active");
          flowArrows[index - 1].classList.add("completed");
        }
      }

      // Activate current step
      step.classList.add("active");
      if (flowArrows[index]) {
        flowArrows[index].classList.add("active");
      }

      // If this is the last step, mark it as completed after a delay
      if (index === flowSteps.length - 1) {
        setTimeout(() => {
          step.classList.remove("active");
          step.classList.add("completed");
          if (flowArrows[index]) {
            flowArrows[index].classList.remove("active");
            flowArrows[index].classList.add("completed");
          }

          // If looping is enabled, restart animation after 5 seconds
          if (shouldLoop) {
            clearTimeout(flowAnimationTimer);
            flowAnimationTimer = setTimeout(() => {
              animateFlowVisualization(true);
            }, 5000); // 5 seconds delay before looping
          }
        }, 1000);
      }
    }, index * 800); // 800ms delay between each step
  });
}

// Handle submit
async function handleSubmit() {
  if (!selectedUserId || !questionInput.value.trim()) {
    return;
  }

  const question = questionInput.value.trim();

  // Disable submit button and show loading state
  submitBtn.disabled = true;
  submitBtn.innerHTML =
    '<span class="loading-spinner-small"></span> Processing...';

  // Show results section and flow visualization immediately
  resultsSection.style.display = "block";

  // Hide results content initially
  documentsList.innerHTML = "";
  answerContent.textContent = "";
  permissionSummary.textContent = "";

  // Start flow animation (without loop initially)
  animateFlowVisualization(false);

  try {
    const response = await fetch("/api/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: selectedUserId,
        question: question,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // Stop flow visualization when request completes
    stopFlowVisualization();

    // Display results immediately
    displayResults(data);

    // Re-enable submit button
    submitBtn.disabled = false;
    submitBtn.innerHTML = "Submit";
  } catch (error) {
    console.error("Query failed:", error);
    alert("An error occurred: " + error.message);

    // Stop animation and reset flow visualization on error
    stopFlowVisualization();

    // Re-enable submit button
    submitBtn.disabled = false;
    submitBtn.innerHTML = "Submit";
  }
}

// Display results
function displayResults(data) {
  // Mark all flow steps as completed
  const flowSteps = document.querySelectorAll(".flow-step");
  const flowArrows = document.querySelectorAll(".flow-arrow");
  flowSteps.forEach((step) => {
    step.classList.remove("active");
    step.classList.add("completed");
  });
  flowArrows.forEach((arrow) => {
    arrow.classList.remove("active");
    arrow.classList.add("completed");
  });

  // Update permission summary
  permissionSummary.textContent = `${data.allowed_count} / ${data.total_count} documents allowed`;

  // Display documents with animation
  documentsList.innerHTML = "";
  data.documents.forEach((doc, index) => {
    setTimeout(() => {
      const docItem = document.createElement("div");
      docItem.className = `document-item ${doc.allowed ? "allowed" : "denied"}`;

      const statusIcon = doc.allowed ? "✅" : "❌";
      const statusText = doc.allowed ? "Allowed" : "Denied";
      const statusClass = doc.allowed ? "allowed" : "denied";

      docItem.innerHTML = `
                <div class="document-header">
                    <div class="document-title">${doc.title}</div>
                    <div class="document-status ${statusClass}">
                        ${statusIcon} ${statusText}
                    </div>
                </div>
                <div class="document-meta">
                    <span>Category: ${doc.category}</span>
                    <span>Score: ${doc.score.toFixed(2)}</span>
                </div>
                <div class="document-text">${doc.text}</div>
            `;

      documentsList.appendChild(docItem);
    }, index * 200); // Stagger animation
  });

  // Display answer
  answerContent.textContent = data.answer;

  // Scroll to results
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

// Load documents from API
async function loadDocuments() {
  try {
    const response = await fetch("/api/documents");
    documents = await response.json();
    console.log("Loaded documents:", documents);
  } catch (error) {
    console.error("Failed to load documents:", error);
  }
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", init);
