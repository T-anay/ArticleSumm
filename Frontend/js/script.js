const API_URL = ""; 
const GOOGLE_CLIENT_ID = "703815846089-k7oqhi4o4qge65i64q2a9lpd1q654fp0.apps.googleusercontent.com";
const ICON_LIST = [
  "fa-file-lines", "fa-book", "fa-flask", "fa-briefcase", "fa-code",
  "fa-newspaper", "fa-lightbulb", "fa-chart-pie", "fa-landmark", "fa-atom",
  "fa-gavel", "fa-microchip", "fa-notes-medical", "fa-brain", "fa-earth-americas"
];

function applySavedPreferences() {
  if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark-mode");
  }
  const savedFont = localStorage.getItem("font-size");
  if (savedFont && savedFont !== 'medium') {
      document.body.classList.add(`font-size-${savedFont}`);
  }
}

async function handleGoogleCredentialResponse(response) {
    const googleToken = response.credential; 
    const loginError = document.getElementById('error-message-login');
    const registerError = document.getElementById('error-message-register');
    
    try {
        const res = await fetch(`${API_URL}/api/auth/google-login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: googleToken })
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || 'Google girişi başarısız oldu.');
        }

        const data = await res.json();
        localStorage.setItem("token", data.access_token);
        window.location.href = "summary.html"; 

    } catch (err) {
        if (loginError) loginError.textContent = err.message;
        if (registerError) registerError.textContent = err.message;
    }
}

function initializeGoogleSignIn() {
  if (typeof google === 'undefined' || !google.accounts) {
    setTimeout(initializeGoogleSignIn, 100);
    return;
  }

  google.accounts.id.initialize({
    client_id: GOOGLE_CLIENT_ID,
    callback: handleGoogleCredentialResponse
  });

  const loginBtnContainer = document.getElementById('google-login-button-container-login');
  if (loginBtnContainer) {
    google.accounts.id.renderButton(
      loginBtnContainer,
      { theme: "outline", size: "large", type: "standard", text: "signin_with", width: "100%" } 
    );
  }
  
  const registerBtnContainer = document.getElementById('google-login-button-container-register');
  if (registerBtnContainer) {
    google.accounts.id.renderButton(
      registerBtnContainer,
      { theme: "outline", size: "large", type: "standard", text: "signup_with", width: "100%" } 
    );
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  applySavedPreferences(); 
  await loadHeader(); 
  initThemeToggle(); 
  initAuthButtons();
  
  const currentPage = window.location.pathname.split("/").pop() || "index.html";
  
  if (currentPage === "index.html") {
    initAuthPage();
    initializeGoogleSignIn(); 
  } else if (currentPage === "summary.html") {
    initSummaryPage();
  }
});

async function loadHeader() {
  const headerPlaceholder = document.getElementById("header-placeholder");
  const target = headerPlaceholder || document.getElementById("header");
  if (!target) return;

  try {
    const response = await fetch("header.html");
    if (!response.ok) throw new Error("Header yüklenemedi.");
    const headerHTML = await response.text();
    target.innerHTML = headerHTML;
    applyThemeIcon();
  } catch (error) {
    console.error("Header yüklenirken hata:", error);
    target.innerHTML = "<p style='text-align:center; color:red;'>Header yüklenemedi.</p>";
  }
}

function applyThemeIcon() {
    const themeIcon = document.getElementById("theme-icon-svg");
    if (!themeIcon) return;
    const moonPath = "M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z";
    const sunPath = "M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4M12 7a5 5 0 1 0 5 5 5 5 0 0 0-5-5z";
    if (localStorage.getItem("theme") === "dark") {
        themeIcon.innerHTML = `<path d="${sunPath}"></path>`;
    } else {
        themeIcon.innerHTML = `<path d="${moonPath}"></path>`;
    }
}


function initThemeToggle() {
  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");
      const isDark = document.body.classList.contains("dark-mode");
      localStorage.setItem("theme", isDark ? "dark" : "light");
      applyThemeIcon(); 
    });
  }
}

function initAuthButtons() {
  const token = localStorage.getItem("token");
  const authLinks = document.getElementById("auth-links-logged-out");
  const profileContainer = document.getElementById("profile-dropdown-container");
  const profileButton = document.getElementById("profile-button");
  const profileMenu = document.getElementById("profile-dropdown-menu");
  const dropdownLogoutBtn = document.getElementById("dropdown-logout-btn");
  const loginLink = document.getElementById("login-link");
  const openSettingsBtn = document.getElementById("open-settings-modal-btn");

  if (token) {
    if (authLinks) authLinks.style.display = "none";
    if (profileContainer) profileContainer.style.display = "list-item"; 

    if (profileButton && profileMenu) {
      profileButton.addEventListener("click", (e) => {
        e.stopPropagation(); 
        profileMenu.classList.toggle("show");
      });
    }

    if (dropdownLogoutBtn) {
      dropdownLogoutBtn.addEventListener("click", (e) => {
        e.preventDefault();
        localStorage.removeItem("token");
        window.location.href = "index.html";
      });
    }

    if (openSettingsBtn) {
        openSettingsBtn.addEventListener("click", (e) => {
            e.preventDefault();
            const modal = document.getElementById("settingsModal");
            if (modal) {
                 modal.style.display = "flex";
                 if (window.loadSettingsData) window.loadSettingsData();
            }
            if (profileMenu) profileMenu.classList.remove("show");
        });
    }

  } else {
    if (authLinks) authLinks.style.display = "list-item";
    if (profileContainer) profileContainer.style.display = "none";
    if (loginLink) loginLink.style.display = "block";
  }
  
  window.addEventListener("click", (e) => {
    if (profileMenu && profileMenu.classList.contains("show")) {
      if (profileButton && !profileButton.contains(e.target)) {
        profileMenu.classList.remove("show");
      }
    }
  });
}

function setActiveSidebarItem(activeItem) {
    const summaryList = document.getElementById("summaryList");
    const newSummaryLink = document.querySelector('.sidebar-menu a[href="summary.html"]');
    
    if (summaryList) {
       summaryList.querySelectorAll('li.active').forEach(li => li.classList.remove('active'));
    }
    if (newSummaryLink) {
       newSummaryLink.parentElement.classList.remove('active');
    }
    
    if (activeItem) {
        activeItem.classList.add('active');
    }
}

async function loadSummaries() {
    const summaryList = document.getElementById("summaryList");
    if (!summaryList) return; 

    try {
        summaryList.innerHTML = "<li class='placeholder'>Yükleniyor...</li>";
        
        const token = localStorage.getItem("token");
        if (!token) {
            throw new Error("Lütfen giriş yapın.");
        }
        const headers = { 'Authorization': `Bearer ${token}` };

        const res = await fetch(`${API_URL}/api/ozetler/`, { headers: headers });
        
        if (!res.ok) {
             if (res.status === 401) { 
                 throw new Error("Oturum süreniz doldu. Lütfen tekrar giriş yapın.");
             }
             throw new Error("Geçmiş yüklenemedi.");
        }
        
        const data = await res.json();
        summaryList.innerHTML = "";

        if (data.length === 0) {
            summaryList.innerHTML = "<li class='placeholder'>Henüz özetiniz yok.</li>";
            return;
        }
        
        data.forEach((s) => {
            const li = document.createElement("li");
            li.dataset.id = s.id;
            if (s.is_pinned) li.classList.add("pinned");
            
            const a = document.createElement("a");
            a.href = "#";
            a.title = s.baslik;
            
            const icon = document.createElement("i");
            icon.className = `fas ${s.icon_name || 'fa-file-lines'}`; 
            
            const span = document.createElement("span");
            span.textContent = s.baslik || (s.ozet_metin.slice(0, 30) + "...");
            
            a.appendChild(icon);
            a.appendChild(span);
            li.appendChild(a);

            if (typeof window.handleDeleteSummary === 'function') {
                const actions = document.createElement("div");
                actions.className = "history-item-actions";
                const pinBtnClass = s.is_pinned ? "action-btn pin-btn active" : "action-btn pin-btn";
                
                actions.innerHTML = `
                  <button class="${pinBtnClass}" title="Sabitle"><i class="fas fa-thumbtack"></i></button>
                  <button class="action-btn edit-btn" title="Yeniden adlandır"><i class="fas fa-pen"></i></button>
                  <button class="action-btn delete-btn" title="Sil"><i class="fas fa-trash"></i></button>
                `;
                
                actions.querySelector('.delete-btn').addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (window.handleDeleteSummary) window.handleDeleteSummary(s.id, s.baslik);
                });
                actions.querySelector('.edit-btn').addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (window.handleOpenEditModal) window.handleOpenEditModal(s);
                });
                actions.querySelector('.pin-btn').addEventListener('click', (e) => {
                    e.stopPropagation();
                     if (window.handleTogglePin) window.handleTogglePin(s.id, !s.is_pinned, e.currentTarget);
                });
                
                li.appendChild(actions);
            }

            a.addEventListener("click", (e) => {
              e.preventDefault();
              const inputAreaCard = document.getElementById("inputArea");
              
              if (inputAreaCard && window.displaySummary) {
                const resultArea = document.getElementById("resultArea");
                inputAreaCard.style.display = "none";
                window.displaySummary(s);
                setActiveSidebarItem(li);
                
                if (window.innerWidth < 992) {
                   document.body.classList.add("sidebar-collapsed");
                   resultArea.scrollIntoView({ behavior: 'smooth' });
                }
              } else {
                  window.location.href = `summary.html?id=${s.id}`;
              }
            });
            
            summaryList.appendChild(li);
        });
    } catch (err) {
        if (summaryList) {
           summaryList.innerHTML = `<li class='placeholder' style='color: red;'>${err.message}</li>`;
        }
        if (err.message.includes("giriş yapın") || err.message.includes("Oturum")) {
            setTimeout(() => {
               localStorage.removeItem("token");
               window.location.href = "index.html";
            }, 2000);
        }
    }
}


function initAuthPage() {
  const flipperContainer = document.querySelector('.auth-flipper-container');
  if (!flipperContainer) return; 

  const showRegisterBtn = document.getElementById('show-register-btn');
  const showLoginBtn = document.getElementById('show-login-btn');
  const showForgotBtn = document.getElementById('show-forgot-btn'); 
  const showLoginBtnFromForgot = document.getElementById('show-login-btn-from-forgot'); 

  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  const forgotPasswordForm = document.getElementById('forgot-password-form'); 

  const loginError = document.getElementById('error-message-login');
  const registerError = document.getElementById('error-message-register');
  const forgotError = document.getElementById('error-message-forgot'); 

  const loginContainer = document.querySelector('.auth-front');
  const registerContainer = document.querySelector('.auth-back');
  const forgotContainer = document.querySelector('.auth-forgot'); 

  function setFlipperHeight() {
      let height;
      if (flipperContainer.classList.contains('is-flipped')) {
          height = registerContainer.scrollHeight;
      } else if (flipperContainer.classList.contains('is-forgot')) { 
          height = forgotContainer.scrollHeight;
      } else {
          height = loginContainer.scrollHeight;
      }
      flipperContainer.style.height = `${height}px`;
  }
  setTimeout(setFlipperHeight, 100); 
  window.addEventListener('resize', setFlipperHeight);

  showRegisterBtn.addEventListener('click', (e) => {
    e.preventDefault();
    flipperContainer.classList.remove('is-forgot');
    flipperContainer.classList.add('is-flipped');
    setFlipperHeight(); 
  });
  
  const showLogin = (e) => {
    e.preventDefault();
    flipperContainer.classList.remove('is-flipped');
    flipperContainer.classList.remove('is-forgot');
    setFlipperHeight();
  };
  showLoginBtn.addEventListener('click', showLogin);
  showLoginBtnFromForgot.addEventListener('click', showLogin); 

  showForgotBtn.addEventListener('click', (e) => {
    e.preventDefault();
    flipperContainer.classList.remove('is-flipped');
    flipperContainer.classList.add('is-forgot');
    setFlipperHeight();
  });

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    loginError.textContent = "";
    loginError.style.color = "#ff6b6b"; 
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    try {
      const res = await fetch(`${API_URL}/api/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Giriş başarısız!");
      }
      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      window.location.href = "summary.html";
    } catch (err) {
      loginError.textContent = err.message;
    }
  });

  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    registerError.textContent = "";
    const first_name = document.getElementById("firstName").value.trim();
    const last_name = document.getElementById("lastName").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirm = document.getElementById("confirmPassword").value;

    if (password !== confirm) {
      registerError.textContent = "Şifreler eşleşmiyor!";
      return;
    }
    try {
      const res = await fetch(`${API_URL}/api/auth/kayit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ first_name, last_name, email, password }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Kayıt başarısız.");
      }
      
      loginError.textContent = "Kayıt başarılı! Lütfen giriş yapın.";
      loginError.style.color = "green"; 
      flipperContainer.classList.remove('is-flipped');
      setFlipperHeight();
    } catch (err) {
      registerError.textContent = err.message;
    }
  });

  forgotPasswordForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    forgotError.textContent = "";
    forgotError.style.color = "#ff6b6b";
    
    const email = document.getElementById('forgotEmail').value.trim();
    const button = forgotPasswordForm.querySelector('button');
    
    button.textContent = "Gönderiliyor...";
    button.disabled = true;

    try {
      const res = await fetch(`${API_URL}/api/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email }),
      });

      const data = await res.json(); 

      if (!res.ok) {
        throw new Error(data.detail || "Bir hata oluştu.");
      }
      
      forgotError.textContent = data.message;
      forgotError.style.color = "green";

    } catch (err) {
      forgotError.textContent = err.message;
    } finally {
      button.textContent = "Gönder";
      button.disabled = false;
    }
  });

}

function initSummaryPage() {
  const token = localStorage.getItem("token");
  if (!token) {
    window.location.href = "index.html";
    return;
  }
  
  const headers = { 
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json" 
  };

  const body = document.body;
  const sidebarToggle = document.getElementById("sidebar-toggle");
  const dropZone = document.getElementById("drop-zone");
  const pdfInput = document.getElementById("pdfInput");
  const fileNameDisplay = document.getElementById("file-name-display");
  const summarizeBtn = document.getElementById("summarizeBtn");
  const loading = document.getElementById("loading");
  const errorBox = document.getElementById("form-error-message");
  const resultArea = document.getElementById("resultArea");
  const summaryOutput = document.getElementById("summaryOutput");
  const summaryTags = document.getElementById("summaryTags");
  const mainContent = document.getElementById("main-content-container");
  const inputAreaCard = document.getElementById("inputArea");
  const newSummaryLink = document.querySelector('.sidebar-menu a[href="summary.html"]');
  const editModal = document.getElementById("editModal");
  const editForm = document.getElementById("editForm");
  const cancelEditBtn = document.getElementById("cancelEditBtn");
  const closeModalBtn = document.getElementById("closeModalBtn");
  const iconPicker = document.getElementById("iconPicker");
  const modalError = document.getElementById("modal-error-message");
  const settingsModal = document.getElementById("settingsModal"); 

  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      body.classList.toggle("sidebar-collapsed");
    });
  }
  if (mainContent) {
    mainContent.addEventListener("click", () => {
        if (window.innerWidth < 992 && !body.classList.contains("sidebar-collapsed")) {
            body.classList.add("sidebar-collapsed");
        }
    });
  }

  if (newSummaryLink) {
    newSummaryLink.addEventListener("click", (e) => {
      e.preventDefault();
      inputAreaCard.style.display = "block";
      resultArea.style.display = "none"; 
      setActiveSidebarItem(newSummaryLink.parentElement); 
      resetForm();
    });
  }

  if (dropZone && pdfInput) {
    dropZone.addEventListener("click", () => pdfInput.click());
    pdfInput.addEventListener("change", () => {
      if (pdfInput.files.length > 0) handleFileSelect(pdfInput.files[0]);
    });
    dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("drag-over"); });
    dropZone.addEventListener("dragleave", () => { dropZone.classList.remove("drag-over"); });
    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("drag-over");
      if (e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        if (file.type === "application/pdf") {
          handleFileSelect(file);
        } else {
          showError("Lütfen sadece PDF dosyası yükleyin.");
        }
      }
    });
  }

  function handleFileSelect(file) {
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    pdfInput.files = dataTransfer.files;
    fileNameDisplay.textContent = file.name;
    fileNameDisplay.style.display = "block";
    dropZone.querySelector("p").style.display = "none";
    dropZone.querySelector("i").style.display = "none";
  }

  if (summarizeBtn) {
    summarizeBtn.addEventListener("click", async () => {
      const file = pdfInput.files[0];
      if (!file) {
        showError("Lütfen bir PDF dosyası seçin.");
        return;
      }
      showError(null);
      loading.style.display = "block";
      summarizeBtn.disabled = true;

      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("baslik", file.name.replace('.pdf', ''));
        
        const res = await fetch(`${API_URL}/api/ozetler/pdf_yukle`, {
          method: "POST",
          headers: { 'Authorization': `Bearer ${token}` },
          body: formData,
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || "Özetleme başarısız oldu.");
        }

        const data = await res.json();
        window.displaySummary(data); 
        inputAreaCard.style.display = "none";
        await loadSummaries(); 
        resetForm();

        setTimeout(() => {
          const summaryList = document.getElementById("summaryList");
          const newItem = summaryList.querySelector(`li[data-id="${data.id}"]`);
          if(newItem) setActiveSidebarItem(newItem); 
        }, 100); 

      } catch (err) {
        showError(err.message);
      } finally {
        loading.style.display = "none";
        summarizeBtn.disabled = false;
      }
    });
  }

  window.handleDeleteSummary = async function(ozetId, ozetBaslik) {
      const li = document.querySelector(`#summaryList li[data-id="${ozetId}"]`);
      if (!li) return;
      
      const deleteBtn = li.querySelector('.delete-btn');
      if (!deleteBtn) return;

      if (deleteBtn.dataset.confirm !== 'true') {
          const originalIcon = deleteBtn.innerHTML;
          deleteBtn.innerHTML = '<i class="fas fa-check"></i>'; 
          deleteBtn.dataset.confirm = 'true';
          
          setTimeout(() => {
              if (deleteBtn.dataset.confirm === 'true') {
                  deleteBtn.innerHTML = originalIcon;
                  deleteBtn.dataset.confirm = 'false';
              }
          }, 3000);
          return;
      }

      try {
          const res = await fetch(`${API_URL}/api/ozetler/${ozetId}`, {
              method: 'DELETE',
              headers: { 'Authorization': `Bearer ${token}` }
          });
          if (!res.ok) {
              const errData = await res.json().catch(() => ({}));
              throw new Error(errData.detail || "Silme başarısız.");
          }
          
          const summaryList = document.getElementById("summaryList");
          li.remove(); 
          
          if (summaryList.children.length === 0) {
              summaryList.innerHTML = "<li class='placeholder'>Henüz özetiniz yok.</li>";
          }
          if (resultArea.style.display === "block" && summaryOutput.dataset.currentId === String(ozetId)) {
              newSummaryLink.click();
          }
      } catch (err) {
          showError(err.detail || err.message); 
      }
  }

  window.handleTogglePin = async function(ozetId, newPinState, buttonElement) {
      try {
          buttonElement.disabled = true;
          const res = await fetch(`${API_URL}/api/ozetler/${ozetId}`, {
              method: 'PUT',
              headers: headers,
              body: JSON.stringify({ is_pinned: newPinState })
          });
          
          if (!res.ok) throw new Error("Sabitleme durumu güncellenemedi.");

          const activeItem = document.querySelector("#summaryList li.active");
          const activeId = activeItem ? activeItem.dataset.id : null;
          
          await loadSummaries(); 
          
          if (activeId) {
              const summaryList = document.getElementById("summaryList");
              const newActiveItem = summaryList.querySelector(`li[data-id="${activeId}"]`);
              if (newActiveItem) setActiveSidebarItem(newActiveItem); 
          }
          
      } catch (err) {
          showError(`Hata: ${err.message}`); 
          buttonElement.disabled = false;
      }
  }

  window.handleOpenEditModal = function(summaryData) {
      modalError.style.display = "none";
      document.getElementById("editOzetId").value = summaryData.id;
      document.getElementById("editBaslik").value = summaryData.baslik;
      document.getElementById("editOzetMetin").value = summaryData.ozet_metin;
      document.getElementById("editEtiketler").value = summaryData.etiketler || "";
      
      window.populateIconPicker(summaryData.icon_name || 'fa-file-lines');
      
      editModal.style.display = "flex";
  }

  window.populateIconPicker = function(currentIcon) {
      if (!iconPicker) return; 
      iconPicker.innerHTML = "";
      
      ICON_LIST.forEach(iconClass => {
          const iconEl = document.createElement("div");
          iconEl.className = "icon-option";
          iconEl.dataset.icon = iconClass;
          iconEl.innerHTML = `<i class="fas ${iconClass}"></i>`;
          
          if (iconClass === currentIcon) {
              iconEl.classList.add("selected");
          }
          
          iconEl.addEventListener("click", () => {
              iconPicker.querySelectorAll(".icon-option.selected").forEach(el => el.classList.remove("selected"));
              iconEl.classList.add("selected");
          });
          
          iconPicker.appendChild(iconEl);
      });
  }

  window.displaySummary = function(summaryData) {
    if (!resultArea) return; 
    resultArea.style.display = "block";
    summaryOutput.textContent = summaryData.ozet_metin;
    summaryOutput.dataset.currentId = summaryData.id;
    
    summaryTags.innerHTML = "";
    if (summaryData.etiketler) {
      summaryData.etiketler.split(',').forEach(tag => {
        const tagEl = document.createElement("span");
        tagEl.textContent = tag.trim();
        summaryTags.appendChild(tagEl);
      });
    }
  }

  function initEditModal() {
      if (!editModal) return; 

      cancelEditBtn.addEventListener("click", () => editModal.style.display = "none");
      closeModalBtn.addEventListener("click", () => editModal.style.display = "none");
      editModal.addEventListener("click", (e) => {
          if (e.target === editModal) {
              editModal.style.display = "none";
          }
      });
      
      editForm.addEventListener("submit", async (e) => {
          e.preventDefault();
          modalError.style.display = "none";
          
          const ozetId = document.getElementById("editOzetId").value;
          const newBaslik = document.getElementById("editBaslik").value.trim();
          const newOzetMetin = document.getElementById("editOzetMetin").value.trim();
          const newEtiketler = document.getElementById("editEtiketler").value.trim();
          const selectedIconEl = iconPicker.querySelector(".icon-option.selected");
          const newIconName = selectedIconEl ? selectedIconEl.dataset.icon : 'fa-file-lines';
          
          if (!newBaslik || !newOzetMetin) {
              modalError.textContent = "Başlık ve Özet Metni boş olamaz.";
              modalError.style.display = "block";
              return;
          }
          
          try {
              const res = await fetch(`${API_URL}/api/ozetler/${ozetId}`, {
                  method: 'PUT',
                  headers: headers, 
                  body: JSON.stringify({
                      baslik: newBaslik,
                      icon_name: newIconName,
                      ozet_metin: newOzetMetin,
                      etiketler: newEtiketler
                  })
              });
              
              if (!res.ok) {
                  const errData = await res.json().catch(() => ({}));
                  throw new Error(errData.detail || "Güncelleme başarısız.");
              }
              
              const updatedSummary = await res.json();
              
              await loadSummaries();
              editModal.style.display = "none";
              
              const summaryList = document.getElementById("summaryList");
              const newActiveItem = summaryList.querySelector(`li[data-id="${updatedSummary.id}"]`);
              if (newActiveItem) {
                  setActiveSidebarItem(newActiveItem);
              }

              if (resultArea.style.display === "block" && summaryOutput.dataset.currentId === String(ozetId)) {
                  window.displaySummary(updatedSummary);
              }
              
          } catch (err) {
              modalError.textContent = `Hata: ${err.detail || err.message}`;
              modalError.style.display = "block";
          }
      });
  }
  
  function initSettingsModal() {
    if (!settingsModal) return;
    
    const navTabs = settingsModal.querySelectorAll('.nav-tab');
    const tabPanes = settingsModal.querySelectorAll('.tab-pane');

    navTabs.forEach(tab => {
      tab.addEventListener('click', (e) => {
        e.preventDefault();
        const targetTabId = tab.dataset.tab;
        navTabs.forEach(t => t.classList.remove('active'));
        tabPanes.forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(targetTabId).classList.add('active');
      });
    });

    const closeSettingsBtn = document.getElementById("closeSettingsModalBtn");
    closeSettingsBtn.addEventListener("click", () => settingsModal.style.display = "none");
    settingsModal.addEventListener("click", (e) => {
        if (e.target === settingsModal) { 
             settingsModal.style.display = "none";
        }
    });

    function showModalMessage(type, elementId, text) {
        const el = document.getElementById(elementId);
        if (!el) return;
        el.textContent = text;
        el.className = `modal-message ${type}`;
        el.style.display = text ? "block" : "none"; 
    }

    window.loadSettingsData = async function() {
        settingsModal.querySelectorAll('.modal-message').forEach(el => {
            el.style.display = "none";
            el.textContent = "";
            el.className = "modal-message";
        });
        settingsModal.querySelectorAll('input[type="password"]').forEach(el => el.value = "");
        
        try {
            const res = await fetch(`${API_URL}/api/auth/users/me`, {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Kullanıcı verisi alınamadı.');
            }
            
            const userData = await res.json();
            document.getElementById("editFirstName").value = userData.first_name || '';
            document.getElementById("editLastName").value = userData.last_name || '';
            document.getElementById("editEmail").value = userData.email || ''; 

        } catch (err) {
            showModalMessage('error', 'profile-message', `Hata: ${err.message}`);
        }

        navTabs.forEach(t => t.classList.remove('active'));
        tabPanes.forEach(p => p.classList.remove('active'));
        settingsModal.querySelector('.nav-tab[data-tab="tab-gorunum"]').classList.add('active');
        settingsModal.querySelector('#tab-gorunum').classList.add('active');
    }

    const fontButtons = settingsModal.querySelectorAll('.font-btn');
    const currentFont = localStorage.getItem('font-size') || 'medium';
    fontButtons.forEach(btn => btn.classList.toggle('active', btn.dataset.size === currentFont));
    fontButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        const newSize = btn.dataset.size;
        localStorage.setItem('font-size', newSize);
        document.body.classList.remove('font-size-small', 'font-size-large');
        if (newSize !== 'medium') {
          document.body.classList.add(`font-size-${newSize}`);
        }
        fontButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });

    const profileForm = document.getElementById("profile-update-form");
    if (profileForm) {
        profileForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn = document.getElementById("save-profile-btn");
            const msgEl = "profile-message";
            btn.textContent = "Güncelleniyor...";
            btn.disabled = true;

            const newFirstName = document.getElementById("editFirstName").value;
            const newLastName = document.getElementById("editLastName").value;

            try {
                const res = await fetch(`${API_URL}/api/auth/users/me`, {
                    method: 'PUT',
                    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        first_name: newFirstName,
                        last_name: newLastName
                    })
                });
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Profil güncellenemedi.');
                }
                showModalMessage('success', msgEl, "Profil başarıyla güncellendi!");
            } catch (err) {
                showModalMessage('error', msgEl, `Hata: ${err.message}`);
            } finally {
                btn.textContent = "Profili Güncelle";
                btn.disabled = false;
            }
        });
    }

    const emailForm = document.getElementById("email-change-form");
    if (emailForm) {
        emailForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn = document.getElementById("save-email-btn");
            const msgEl = "email-message";
            btn.textContent = "Güncelleniyor...";
            btn.disabled = true;

            const newEmail = document.getElementById("editEmail").value;
            const currentPassword = document.getElementById("emailCurrentPass").value;

            try {
                const res = await fetch(`${API_URL}/api/auth/change-email`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        new_email: newEmail,
                        current_password: currentPassword
                    })
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'E-posta güncellenemedi.');
                }
                
                showModalMessage('success', msgEl, "E-posta başarıyla güncellendi! Güvenlik nedeniyle çıkış yapılıyor...");
                btn.textContent = "Başarılı!";

                setTimeout(() => {
                    localStorage.removeItem("token");
                    window.location.href = "index.html";
                }, 2500);

            } catch (err) {
                showModalMessage('error', msgEl, `Hata: ${err.message}`);
                btn.textContent = "E-postayı Güncelle";
                btn.disabled = false;
            }
        });
    }

    const passwordForm = document.getElementById("password-change-form");
    if (passwordForm) {
        passwordForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn = document.getElementById("save-password-btn");
            const msgEl = "password-message";
            btn.textContent = "Değiştiriliyor...";
            btn.disabled = true;

            const passCurrent = document.getElementById("passCurrent").value;
            const passNew = document.getElementById("passNew").value;
            const passConfirm = document.getElementById("passConfirm").value;

            if (passNew !== passConfirm) {
                showModalMessage('error', msgEl, "Yeni şifreler eşleşmiyor.");
                btn.textContent = "Şifreyi Değiştir";
                btn.disabled = false;
                return;
            }

            try {
                const res = await fetch(`${API_URL}/api/auth/change-password`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        current_password: passCurrent,
                        new_password: passNew
                    })
                });
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Şifre değiştirilemedi.');
                }
                showModalMessage('success', msgEl, "Şifre başarıyla değiştirildi.");
                passwordForm.reset();
            } catch (err) {
                showModalMessage('error', msgEl, `Hata: ${err.message}`);
            } finally {
                btn.textContent = "Şifreyi Değiştir";
                btn.disabled = false;
            }
        });
    }

    const deleteAllBtn = document.getElementById("delete-all-summaries-btn");
    const deleteAccountBtn = document.getElementById("delete-account-btn");
    const deleteAccountForm = document.getElementById("delete-account-form");
    const cancelDeleteAccountBtn = document.getElementById("cancel-delete-account-btn");

    if (deleteAllBtn) {
        deleteAllBtn.addEventListener("click", async () => {
            const isConfirming = deleteAllBtn.dataset.confirm === "true";
            
            if (!isConfirming) {
                deleteAllBtn.textContent = "EMİN MİSİNİZ? (Onay için tekrar tıklayın)";
                deleteAllBtn.dataset.confirm = "true";
                showModalMessage('error', 'danger-message-1', 'Tüm özetler kalıcı olarak silinecek!');
                
                setTimeout(() => {
                    if (deleteAllBtn.dataset.confirm === "true") {
                        deleteAllBtn.textContent = "Tüm Özetleri Sil";
                        deleteAllBtn.dataset.confirm = "false";
                        showModalMessage('error', 'danger-message-1', ''); 
                    }
                }, 5000);
                return;
            }

            deleteAllBtn.textContent = "Siliniyor...";
            deleteAllBtn.disabled = true;

            try {
                const res = await fetch(`${API_URL}/api/ozetler/all`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                
                if (!res.ok) {
                    let errorDetail = 'Özetler silinemedi.';
                    try {
                        const errData = await res.json();
                        errorDetail = errData.detail || errorDetail;
                    } catch (e) { }
                    throw new Error(errorDetail);
                }
                
                const result = await res.json();
                showModalMessage('success', 'danger-message-1', result.message);
                await loadSummaries();
            } catch (err) {
                showModalMessage('error', 'danger-message-1', `Hata: ${err.message}`);
            } finally {
                deleteAllBtn.textContent = "Tüm Özetleri Sil";
                deleteAllBtn.disabled = false;
                deleteAllBtn.dataset.confirm = "false";
            }
        });
    }

    if (deleteAccountBtn && deleteAccountForm && cancelDeleteAccountBtn) {
        deleteAccountBtn.addEventListener("click", () => {
            deleteAccountBtn.style.display = "none";
            deleteAccountForm.style.display = "block";
            showModalMessage('error', 'danger-message-2', 'Hesabınızı silmek için şifrenizi girin.');
        });

        cancelDeleteAccountBtn.addEventListener("click", () => {
            deleteAccountForm.style.display = "none";
            deleteAccountBtn.style.display = "block";
            showModalMessage('error', 'danger-message-2', ''); 
        });

        deleteAccountForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const confirmationPassword = document.getElementById("deleteAccountPass").value;

            if (!confirmationPassword) {
                showModalMessage('error', 'danger-message-2', 'Lütfen şifrenizi girin.');
                return;
            }
            
            const submitBtn = document.getElementById("confirm-delete-account-btn");
            submitBtn.textContent = "Hesap Siliniyor...";
            submitBtn.disabled = true;

            try {
                const res = await fetch(`${API_URL}/api/auth/users/delete`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password: confirmationPassword })
                });
                
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Hesap silinemedi.');
                }
                
               showModalMessage('success', 'danger-message-2', 'Hesabınız başarıyla silindi. Çıkış yapılıyor...');
               submitBtn.textContent = "Başarıyla Silindi";
               document.getElementById("cancel-delete-account-btn").disabled = true;

                setTimeout(() => {
                    localStorage.removeItem("token");
                    window.location.href = "index.html"; 
                }, 2500);

            } catch (err) {
                showModalMessage('error', 'danger-message-2', `Hata: ${err.message}`);
                submitBtn.textContent = "Hesabı Kalıcı Olarak Sil";
                submitBtn.disabled = false;
            }
        });
    }
  } 
  function resetForm() {
    pdfInput.value = null;
    fileNameDisplay.style.display = "none";
    dropZone.querySelector("p").style.display = "block";
    dropZone.querySelector("i").style.display = "block";
  }
  function showError(message) {
    if (message) {
      errorBox.textContent = message;
      errorBox.style.display = "block";
    } else {
      errorBox.textContent = "";
      errorBox.style.display = "none";
    }
  }
  
  loadSummaries();
  initEditModal(); 
  initSettingsModal(); 
  
  const urlParams = new URLSearchParams(window.location.search);
  const ozetIdToOpen = urlParams.get('id');
  if (ozetIdToOpen) {
      async function fetchAndOpenOzet(id) {
          try {
              const res = await fetch(`${API_URL}/api/ozetler/${id}`, { headers: { 'Authorization': `Bearer ${token}` } });
              if (!res.ok) throw new Error("Özet bulunamadı.");
              const data = await res.json();
              
              inputAreaCard.style.display = "none";
              window.displaySummary(data);
              
              const trySetActive = () => {
                const summaryList = document.getElementById("summaryList");
                const activeItem = summaryList.querySelector(`li[data-id="${id}"]`);
                if (activeItem) {
                    setActiveSidebarItem(activeItem);
                } else {
                    setTimeout(trySetActive, 1000);
                }
              };
              trySetActive();
              
          } catch (err) {
              showError(err.message);
          }
      }
      fetchAndOpenOzet(ozetIdToOpen);
  }
}