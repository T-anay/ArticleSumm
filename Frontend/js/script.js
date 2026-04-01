let API_URL = "";
const GOOGLE_CLIENT_ID = "703815846089-k7oqhi4o4qge65i64q2a9lpd1q654fp0.apps.googleusercontent.com";

function getApiCandidates() {
    const host = window.location.hostname || "localhost";
    const protocol = window.location.protocol || "http:";
    const stored = localStorage.getItem("apiUrl") || "";

    return [
        "",
        stored,
        `${protocol}//${host}:8010`,
        `${protocol}//${host}:8001`,
        `${protocol}//${host}:8000`,
        "http://localhost:8010",
        "http://localhost:8001",
        "http://localhost:8000",
    ].filter((v, i, arr) => v !== null && arr.indexOf(v) === i);
}

async function resolveApiUrl() {
    const candidates = getApiCandidates();

    for (const candidate of candidates) {
        const base = candidate === "" ? "" : candidate.replace(/\/$/, "");
        const healthUrl = `${base}/health`;
        try {
            const res = await fetch(healthUrl, { method: "GET" });
            if (!res.ok) {
                continue;
            }

            const data = await res.json().catch(() => null);
            if (data?.status === "ok") {
                API_URL = base;
                localStorage.setItem("apiUrl", API_URL);
                console.info("[API] Connected:", API_URL || "same-origin");
                return;
            }
        } catch (_) {
        }
    }

    API_URL = "http://localhost:8010";
    localStorage.setItem("apiUrl", API_URL);
    console.warn("[API] Could not auto-detect backend, fallback:", API_URL);
}

// ==============================================
// === 1. TEMA VE GÖRÜNÜM YÖNETİMİ ===
// ==============================================

function applySavedPreferences() {
  const theme = localStorage.getItem("theme") || "light";
  setTheme(theme, false);
  
  const fontSize = localStorage.getItem("fontSize") || "medium";
  document.body.classList.remove("font-small", "font-medium", "font-large");
  if(fontSize !== "medium") document.body.classList.add(`font-${fontSize}`);
}

function setTheme(mode, save = true) {
  document.body.classList.remove("dark-mode", "sepia-mode");
  if (mode === "dark") document.body.classList.add("dark-mode");
  if (mode === "sepia") document.body.classList.add("sepia-mode");

  if (save) localStorage.setItem("theme", mode);
  updateActiveThemeButtons(mode);
}

function updateActiveThemeButtons(mode) {
  const allThemeBtns = document.querySelectorAll('.theme-btn');
  allThemeBtns.forEach(btn => {
    btn.classList.remove('active');
    if (btn.getAttribute('data-mode') === mode) {
      btn.classList.add('active');
    }
  });
}

// ==============================================
// === 2. ANİMASYONLAR VE EFEKTLER (DÜZELTİLMİŞ) ===
// ==============================================
function initBackgroundAnimation() {
  // 1. Kareleri HTML'e ekle
  if (!document.querySelector('.site-background-animation')) {
      const html = `
        <div class="site-background-animation">
          <div class="squares">
            <div class="square"></div><div class="square"></div><div class="square"></div>
            <div class="square"></div><div class="square"></div><div class="square"></div>
            <div class="square"></div><div class="square"></div><div class="square"></div>
            <div class="square"></div>
          </div>
        </div>`;
      document.body.insertAdjacentHTML('afterbegin', html);
  }

  // 2. Mouse ile Parallax
  const squares = document.querySelector('.squares');
  if (squares) {
      document.addEventListener('mousemove', (e) => {
          const x = (window.innerWidth / 2 - e.clientX) / 40;
          const y = (window.innerHeight / 2 - e.clientY) / 40;
          squares.style.transform = `translate(${x}px, ${y}px)`;
      });
  }

  // 3. PATLAMA VE GİZLEME (CLASS YÖNTEMİ)
  window.addEventListener('click', function(e) {
      if (e.target.classList.contains('square')) {
          const clickedSquare = e.target;

          // --- A) Rengi Al ---
          const computedStyle = window.getComputedStyle(clickedSquare);
          const dynamicColor = computedStyle.backgroundColor;

          // --- B) Patlamayı Yarat ---
          createExplosion(e.clientX, e.clientY, dynamicColor);

          // --- C) Kareyi Gizle (Class Ekleyerek) ---
          // Bu sınıf CSS'teki animasyonu ezer ve kareyi yok eder
          clickedSquare.classList.add('exploded');

          // --- D) Kareyi Geri Getir ---
          // 3 saniye sonra sınıfı kaldırıp döngüye sokuyoruz
          setTimeout(() => {
              clickedSquare.classList.remove('exploded');
          }, 3000);
      }
  });
}

// Patlama parçacığı fonksiyonu (Aynı kalabilir)
function createExplosion(x, y, color) {
    const particle = document.createElement('div');
    particle.classList.add('explosion-particle');
    particle.style.left = x + 'px';
    particle.style.top = y + 'px';
    particle.style.backgroundColor = color;
    particle.style.boxShadow = `0 0 30px ${color}, 0 0 60px white`;
    
    document.body.appendChild(particle);
    setTimeout(() => { particle.remove(); }, 600);
} 

// Patlama parçacığını oluşturan yardımcı fonksiyon (Renk parametresi eklendi)
function createExplosion(x, y, color) {
    const particle = document.createElement('div');
    particle.classList.add('explosion-particle');
    
    // Pozisyonu ayarla (CSS'teki translate(-50%, -50%) ile tam ortalanacak)
    particle.style.left = x + 'px';
    particle.style.top = y + 'px';

    // --- DİNAMİK RENK UYGULAMA ---
    // Gönderilen rengi arka plan ve gölge olarak ayarla
    particle.style.backgroundColor = color;
    // Ana renk gölgesi ve ortasında beyaz bir parlama
    particle.style.boxShadow = `0 0 30px ${color}, 0 0 60px white`;
    
    document.body.appendChild(particle);
    
    // Animasyon süresi bitince (0.6s) elemanı sil
    setTimeout(() => {
        particle.remove();
    }, 600);
}

// Patlama parçacığını oluşturan yardımcı fonksiyon
function createExplosion(x, y) {
    const particle = document.createElement('div');
    particle.classList.add('explosion-particle');
    
    // Pozisyonu ayarla (Ortalamak için 25px çıkarıyoruz)
    particle.style.left = (x - 25) + 'px';
    particle.style.top = (y - 25) + 'px';
    
    document.body.appendChild(particle);
    
    // Animasyon bitince sil (0.6 saniye sonra)
    setTimeout(() => {
        particle.remove();
    }, 600);
}

// ==============================================
// === 3. HEADER VE NAVİGASYON ===
// ==============================================
async function loadHeader() {
  const placeholder = document.getElementById("header-placeholder");
  if (!placeholder) return;

  try {
      const res = await fetch("header.html");
      if (res.ok) {
        placeholder.innerHTML = await res.text();
        
        const token = localStorage.getItem("token");
        const loggedOutLinks = document.getElementById("auth-links-logged-out");
        const profileContainer = document.getElementById("profile-dropdown-container");

        if (token) {
            if(loggedOutLinks) loggedOutLinks.style.display = "none";
            if(profileContainer) profileContainer.style.display = "block";
        } else {
            if(loggedOutLinks) loggedOutLinks.style.display = "block";
            if(profileContainer) profileContainer.style.display = "none";
        }

        const headerThemeBtns = document.querySelectorAll('.theme-switcher-group .theme-btn');
        const currentTheme = localStorage.getItem("theme") || "light";
        updateActiveThemeButtons(currentTheme);

        headerThemeBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const mode = btn.getAttribute('data-mode');
                setTheme(mode);
            });
        });

        // Profil Menüsü ve Modal Tetikleyici
        const profileBtn = document.getElementById("profile-button");
        const profileMenu = document.getElementById("profile-dropdown-menu");
        
        if(profileBtn && profileMenu) {
            profileBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                profileMenu.classList.toggle("show");
            });

            document.addEventListener("click", (e) => {
                if (!profileMenu.contains(e.target) && !profileBtn.contains(e.target)) {
                    profileMenu.classList.remove("show");
                }
            });

            const logoutBtn = document.getElementById("dropdown-logout-btn");
            if(logoutBtn) {
                logoutBtn.addEventListener("click", (e) => {
                    e.preventDefault();
                    localStorage.removeItem("token");
                    window.location.href = "index.html";
                });
            }

            // AYARLAR BUTONU -> MODALI AÇAR
            const settingsBtn = document.getElementById("open-settings-modal-btn");
            if (settingsBtn) {
                settingsBtn.addEventListener("click", (e) => {
                    e.preventDefault();
                    profileMenu.classList.remove("show"); // Menüyü kapat
                    
                    const modal = document.getElementById("settings-modal");
                    if(modal) {
                        modal.style.display = "flex";
                        initSettingsModal(); // Modalı başlat
                    }
                });
            }
        }
      }
  } catch(e) { console.error("Header yükleme hatası", e); }
}

// ==============================================
// === 4. AYARLAR MODALI MANTIĞI ===
// ==============================================
function initSettingsModal() {
    const modal = document.getElementById("settings-modal");
    const closeBtn = document.getElementById("close-settings-btn");
    
    if (!modal) return;

    const closeModal = () => modal.style.display = "none";
    if(closeBtn) closeBtn.onclick = closeModal;
    modal.onclick = (e) => { if (e.target === modal) closeModal(); };

    // Sekme Geçişleri
    const tabs = document.querySelectorAll(".settings-tab");
    const panels = document.querySelectorAll(".settings-panel");

    tabs.forEach(tab => {
        tab.onclick = () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            const targetId = tab.getAttribute("data-target");
            panels.forEach(panel => {
                panel.classList.remove("active");
                if(panel.id === targetId) {
                    panel.classList.add("active");
                }
            });
        };
    });

    // Font Boyutu
    const fontBtns = document.querySelectorAll(".font-btn");
    const currentSize = localStorage.getItem("fontSize") || "medium";
    
    fontBtns.forEach(btn => {
        if(btn.getAttribute("data-size") === currentSize) btn.classList.add("active");
        else btn.classList.remove("active");

        btn.onclick = () => {
            fontBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            const size = btn.getAttribute("data-size");
            document.body.classList.remove("font-small", "font-medium", "font-large");
            if(size !== "medium") document.body.classList.add(`font-${size}`);
            localStorage.setItem("fontSize", size);
        };
    });

    // Tehlikeli Bölge
    const btnDelHist = document.getElementById("btn-delete-history");
    if(btnDelHist) {
        btnDelHist.onclick = () => {
            if(confirm("Tüm özet geçmişiniz silinecek. Emin misiniz?")) {
                localStorage.removeItem("history"); 
                const list = document.getElementById("summaryList");
                if(list) list.innerHTML = '<li class="placeholder">Geçmiş temizlendi.</li>';
                alert("Geçmiş temizlendi.");
            }
        };
    }

    const btnDelAcc = document.getElementById("btn-delete-account");
    if(btnDelAcc) {
        btnDelAcc.onclick = () => {
            const input = prompt("Hesabınızı silmek için 'SIL' yazın:");
            if(input === "SIL") {
                localStorage.clear();
                alert("Hesabınız silindi.");
                window.location.href = "index.html";
            }
        };
    }
}

// ==============================================
// === 5. SAYFA YÜKLEME ===
// ==============================================
document.addEventListener("DOMContentLoaded", async () => {
    await resolveApiUrl();
  applySavedPreferences();
  initBackgroundAnimation(); 
  await loadHeader();
  
  const page = window.location.pathname.split("/").pop() || "index.html";
  
  if (page === "summary.html") initSummaryPage();
  else if (["index.html", "register.html", "reset-password.html"].includes(page)) initAuthPage();
});

// ==============================================
// === 6. AUTH SAYFASI ===
// ==============================================
function initAuthPage() {
  const container = document.querySelector('.auth-flipper-container');
  const toRegister = document.getElementById('to-register');
  const toLogin = document.getElementById('to-login');
  
  if(toRegister && container) toRegister.onclick = (e) => {
      e.preventDefault();
      container.classList.add('is-flipped');
  };
  if(toLogin && container) toLogin.onclick = (e) => {
      e.preventDefault();
      container.classList.remove('is-flipped');
  };
  
  const loginForm = document.getElementById('login-form');
  if(loginForm) {
      loginForm.onsubmit = async (e) => {
          e.preventDefault();
          const email = document.getElementById('loginEmail')?.value || "";
          const password = document.getElementById('loginPassword')?.value || "";
          const errorBox = document.getElementById("error-message-login");
          if (errorBox) errorBox.textContent = "";

          try {
              const res = await fetch(`${API_URL}/api/auth/token`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ email, password })
              });

              const data = await res.json().catch(() => ({}));
              if (!res.ok) {
                  const msg = data.detail || "Giris basarisiz.";
                  if (errorBox) errorBox.textContent = msg;
                  return;
              }

              if (data.access_token) {
                  localStorage.setItem("token", data.access_token);
                  window.location.href = "summary.html";
              } else {
                  if (errorBox) errorBox.textContent = "Token alinamadi.";
              }
          } catch (err) {
              if (errorBox) errorBox.textContent = `Sunucuya baglanilamadi. API: ${API_URL || 'same-origin'}`;
              console.error(err);
          }
      };
  }

  const registerForm = document.getElementById('register-form');
  if (registerForm) {
      registerForm.onsubmit = async (e) => {
          e.preventDefault();
          const errorBox = document.getElementById("error-message-register");
          if (errorBox) errorBox.textContent = "";

          const payload = {
              first_name: document.getElementById('firstName')?.value || "",
              last_name: document.getElementById('lastName')?.value || "",
              email: document.getElementById('email')?.value || "",
              password: document.getElementById('password')?.value || "",
          };

          try {
              const res = await fetch(`${API_URL}/api/auth/kayit`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(payload)
              });
              const data = await res.json().catch(() => ({}));
              if (!res.ok) {
                  const msg = data.detail || "Kayit basarisiz.";
                  if (errorBox) errorBox.textContent = msg;
                  return;
              }
              alert("Kayit basarili. Giris yapabilirsiniz.");
              const container = document.querySelector('.auth-flipper-container');
              if (container) container.classList.remove('is-flipped');
          } catch (err) {
              if (errorBox) errorBox.textContent = `Sunucuya baglanilamadi. API: ${API_URL || 'same-origin'}`;
              console.error(err);
          }
      };
  }
}

// ==============================================
// === 7. ÖZET SAYFASI ===
// ==============================================
function initSummaryPage() {
  const token = localStorage.getItem("token");
  if (!token) { window.location.href = "index.html"; return; }
  
  const dropZone = document.getElementById('drop-zone');
  const pdfInput = document.getElementById('pdfInput');
  const btn = document.getElementById("summarizeBtn");
  
  if(dropZone && pdfInput) {
      dropZone.onclick = () => pdfInput.click();
      pdfInput.onchange = () => {
          if(pdfInput.files.length) {
              document.getElementById('file-name-display').textContent = pdfInput.files[0].name;
              document.getElementById('file-name-display').style.display = 'block';
          }
      };
  }

  if(btn) {
      btn.addEventListener("click", async () => {
          const file = pdfInput.files[0];
          if (!file) { alert("Lütfen dosya seçin"); return; }
          
          document.getElementById("loading").style.display = "block";
          document.getElementById("result-wrapper").style.display = "none";
          btn.disabled = true;
          
          try {
              const formData = new FormData();
              formData.append("file", file);
              formData.append("baslik", file.name.replace(".pdf", ""));
              
              const selectEl = document.getElementById("summaryLength");
              const mode = selectEl ? selectEl.value : "medium";
              formData.append("length_option", mode);
              
              const langEl = document.getElementById("targetLanguage");
              const targetLang = langEl ? langEl.value : "turkish";
              formData.append("target_language", targetLang);
              
              const res = await fetch(`${API_URL}/api/ozetler/pdf_yukle`, {
                  method: "POST",
                  headers: { 'Authorization': `Bearer ${token}` },
                  body: formData
              });
              const data = await res.json().catch(() => ({}));

              if (!res.ok) {
                  const errorBox = document.getElementById("form-error-message");
                  const msg = data.detail || "Sunucu hatasi olustu.";
                  if (errorBox) {
                      errorBox.textContent = msg;
                      errorBox.style.display = "block";
                  }
                  if (res.status === 401) {
                      localStorage.removeItem("token");
                      window.location.href = "index.html";
                      return;
                  }
                  throw new Error(msg);
              }
              
              document.getElementById("loading").style.display = "none";
              document.getElementById("result-wrapper").style.display = "block";
              document.getElementById("resultArea").style.display = "block";
              document.getElementById("summaryOutput").innerHTML = data.ozet_metin || "";
              
              // Rozet (Badge) Gösterimi
              const badge = document.getElementById("active-mode-badge");
              if(badge) {
                  badge.style.display = "inline-block";
                  badge.className = "mode-badge"; 
                  let label = "";
                  if(mode === "short") {
                      label = '<i class="fas fa-bolt"></i> Kısa (30-60 kelime)';
                      badge.classList.add("badge-short");
                  } else if(mode === "medium") {
                      label = '<i class="fas fa-layer-group"></i> Orta (150-400 kelime)';
                      badge.classList.add("badge-medium");
                  } else {
                      label = '<i class="fas fa-align-left"></i> Uzun (500-1500 kelime)';
                      badge.classList.add("badge-long");
                  }
                  badge.innerHTML = label;
              }

              // Font/ToC Ayarları
              document.body.classList.remove('font-mode-serif', 'font-mode-sans');
              if (mode === "long") {
                  document.body.classList.add('font-mode-serif');
                  setTimeout(generateToC, 500);
              } else {
                  document.body.classList.add('font-mode-sans');
                  const stickyToc = document.getElementById("sticky-toc");
                  if(stickyToc) stickyToc.style.display = "none";
              }
              
          } catch (e) {
              console.error(e);
              alert("Bir hata oluştu: " + e.message);
              document.getElementById("loading").style.display = "none";
          } finally {
              btn.disabled = false;
          }
      });
  }
  
  const toggle = document.getElementById("sidebar-toggle");
  if(toggle) toggle.onclick = () => document.body.classList.toggle("sidebar-collapsed");
}

function generateToC() {
  const output = document.getElementById("summaryOutput");
  const tocList = document.getElementById("toc-list");
  const tocCont = document.getElementById("sticky-toc");
  
  if (!output || !tocList || !tocCont) return;
  
  tocList.innerHTML = "";
  const headers = output.querySelectorAll("h2, h3");
  
  if (headers.length < 2) {
      tocCont.style.display = "none";
      return;
  }
  
  tocCont.style.display = "block";
  headers.forEach((h, i) => {
      const id = `toc-${i}`;
      h.id = id;
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = "#" + id;
      a.textContent = h.textContent;
      if (h.tagName === "H3") a.style.paddingLeft = "15px";
      
      a.onclick = (e) => {
          e.preventDefault();
          document.getElementById(id).scrollIntoView({behavior: "smooth"});
      };
      li.appendChild(a);
      tocList.appendChild(li);
  });
}