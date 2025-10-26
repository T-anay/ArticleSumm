document.addEventListener("DOMContentLoaded", function () {
  // Header'ı yükle ve header içindeki özellikleri (tema butonu gibi) başlat
  fetch("/header.html") // header.html dosyasının doğru yolda olduğundan emin olun
    .then(res => {
      if (!res.ok) {
        throw new Error(`Header yüklenemedi: ${res.status}`);
      }
      return res.text();
    })
    .then(data => {
      // Header'ı body'nin en başına ekle
      document.body.insertAdjacentHTML("afterbegin", data);
      // Header eklendikten sonra içindeki butonları vb. etkinleştir
      initializeHeaderFeatures();
    })
    .catch(error => console.error("Header yüklenirken hata:", error));

  // Geri Bildirim kutusu (isteğe bağlı, kaldırılabilir)
  initializeFeedbackWidget();

  // --- Aktif Sayfa Vurgusu ---
    highlightActiveNav();

    // --- Giriş/Çıkış butonlarının yönetimi ---
    updateAuthUI(); // Kullanıcı giriş durumuna göre butonları ayarla
    setupLogoutButton(); // Çıkış yap butonu olayını ekle

  // --- YENİ EKLENECEK KODLAR İÇİN YER TUTUCULAR ---
  // Sayfa yüklendiğinde kullanıcının giriş durumunu kontrol et
  // checkLoginStatus();

  // Eğer ana özetleme sayfasındaysak ilgili form olaylarını dinle
  // if (document.getElementById('summary-form')) { // ID'yi kendi HTML'inize göre ayarlayın
  //   setupSummaryPageListeners();
  // }

  // Eğer geçmiş sayfasındaysak geçmiş özetleri yükle
  // if (document.getElementById('history-list')) { // ID'yi kendi HTML'inize göre ayarlayın
  //   loadHistoryPage();
  // }
  // --- --- --- --- --- --- --- --- --- --- --- --- ---
});

// Header içindeki tema değiştirme butonu gibi özellikleri etkinleştirir
function initializeHeaderFeatures() {
    const themeToggle = document.getElementById("theme-toggle");
    // Butonun içindeki SVG elementini alıyoruz
    const themeIconSvg = document.getElementById("theme-icon-svg");

    if (themeToggle && themeIconSvg) {
        // Feather Icons SVG path verileri
        const sunPath = '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>';
        const moonPath = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';

        // SVG'nin içeriğini güncelleyen fonksiyon
        function updateIcon(isDark) {
            themeIconSvg.innerHTML = isDark ? sunPath : moonPath;
            // Erişilebilirlik için aria-label'ı da güncelleyebiliriz (opsiyonel)
            themeToggle.setAttribute('aria-label', isDark ? 'Gündüz Moduna Geç' : 'Gece Moduna Geç');
        }

        // Sayfa yüklendiğinde localStorage'ı kontrol et
        const savedTheme = localStorage.getItem("theme");
        let isDark = savedTheme === "dark";

        // Başlangıç ikonunu ve body class'ını ayarla
        document.body.classList.toggle("dark-mode", isDark);
        updateIcon(isDark); // Başlangıç ikonunu ayarla

        // Butona tıklama olayını dinle
        themeToggle.addEventListener("click", () => {
            // Mevcut tema durumunu tersine çevir
            isDark = document.body.classList.toggle("dark-mode");

            // Yeni duruma göre ikonu güncelle
            updateIcon(isDark);

            // Yeni tema tercihini localStorage'a kaydet
            localStorage.setItem("theme", isDark ? "dark" : "light");
        });
    } else {
        console.warn("Tema değiştirme butonu ('theme-toggle') veya SVG ikonu ('theme-icon-svg') bulunamadı.");
    }

    // --- Giriş/Çıkış butonlarının yönetimi ---
    // updateAuthUI();
    // --- --- --- --- --- --- --- --- --- ---
}

// Geri Bildirim kutusu işlevselliği (isteğe bağlı)
function initializeFeedbackWidget() {
    const feedbackToggle = document.getElementById('feedback-toggle');
    const feedbackBox = document.getElementById('feedback-box');
    const submitButton = document.getElementById('submit-feedback');
    const thankYouMessage = document.getElementById('thankYou');
    const stars = document.querySelectorAll('.star');
    let selectedRating = 0;

    if (!feedbackToggle || !feedbackBox || !submitButton || !thankYouMessage || stars.length === 0) {
        console.warn("Geri bildirim widget elemanlarından bazıları bulunamadı.");
        // İsteğe bağlı: Geri bildirim widget'ını gizle
        // const widget = document.getElementById('feedback-widget');
        // if (widget) widget.style.display = 'none';
        return; // Fonksiyonun geri kalanını çalıştırma
    }

    feedbackToggle.addEventListener('click', () => {
        feedbackBox.classList.toggle('hidden');
    });

    stars.forEach(star => {
        star.addEventListener('click', function () {
            selectedRating = +this.dataset.value;
            stars.forEach(s => s.classList.toggle('selected', +s.dataset.value <= selectedRating));
        });
    });

    submitButton.addEventListener('click', () => {
        if (!selectedRating) {
            alert("Lütfen bir puan seçin.");
            return;
        }
        // Yıldızları, yorum alanını ve gönder butonunu gizle
        ['star-rating', 'comment', 'submit-feedback'].forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = 'none';
        });
        // Teşekkür mesajını göster
        if (thankYouMessage) thankYouMessage.classList.remove('hidden');

        // TODO: Geri bildirimi backend'e gönderme işlemi eklenebilir (opsiyonel)
        // const commentElement = document.getElementById('comment');
        // const comment = commentElement ? commentElement.value : '';
        // sendFeedbackToAPI(selectedRating, comment);
    });
    // --- YENİ EKLENEN FONKSİYONLAR ---

// Aktif navigasyon linkini vurgulayan fonksiyon
function highlightActiveNav() {
    const currentPage = window.location.pathname; // Mevcut sayfanın yolu (örn: /summary.html)
    const navLinks = document.querySelectorAll('.main-nav a');

    navLinks.forEach(link => {
        // Linkin href'i mevcut sayfa yoluyla bitiyorsa veya
        // ana sayfadaysak ve linkin href'i /summary.html ise aktif yap
        if (link.getAttribute('href') === currentPage ||
            (currentPage === '/' && link.getAttribute('href') === '/summary.html')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Header'daki kimlik doğrulama arayüzünü güncelleyen fonksiyon
function updateAuthUI() {
    const userInfo = document.getElementById('user-info');
    const usernameDisplay = document.getElementById('username-display');
    const authLinks = document.getElementById('auth-links');
    const loginLink = document.getElementById('login-link');
    const registerLink = document.getElementById('register-link');
    const logoutButton = document.getElementById('logout-button');

    // Şimdilik sahte kullanıcı adı ve token kontrolü (localStorage'dan)
    const token = localStorage.getItem('accessToken');
    const username = localStorage.getItem('username'); // Girişte kullanıcı adını da sakladığımızı varsayalım

    if (token && username && userInfo && usernameDisplay && authLinks && logoutButton && loginLink && registerLink) {
        // Kullanıcı giriş yapmışsa
        userInfo.style.display = 'flex'; // Kullanıcı adı bölümünü göster
        usernameDisplay.textContent = username;
        loginLink.style.display = 'none'; // Giriş linkini gizle
        registerLink.style.display = 'none'; // Kayıt linkini gizle
        logoutButton.style.display = 'inline-block'; // Çıkış butonunu göster
    } else if (userInfo && authLinks && logoutButton && loginLink && registerLink) {
        // Kullanıcı giriş yapmamışsa
        userInfo.style.display = 'none'; // Kullanıcı adı bölümünü gizle
        loginLink.style.display = 'inline-block'; // Giriş linkini göster
        registerLink.style.display = 'inline-block'; // Kayıt linkini göster
        logoutButton.style.display = 'none'; // Çıkış butonunu gizle
    }
}

// Çıkış Yap butonu için olay dinleyici ekleyen fonksiyon
function setupLogoutButton() {
     const logoutButton = document.getElementById('logout-button');
     if(logoutButton) {
         logoutButton.addEventListener('click', () => {
             // Saklanan token ve kullanıcı adını temizle
             localStorage.removeItem('accessToken');
             localStorage.removeItem('tokenType');
             localStorage.removeItem('username'); // Kullanıcı adını da temizle

             // Header'ı güncelle
             updateAuthUI();

             // Giriş sayfasına yönlendir
             window.location.href = '/login.html';
         });
     }
}

// Header kaydırma efekti için olay dinleyici
window.addEventListener('scroll', () => {
    const header = document.querySelector('header');
    if (header) {
        if (window.scrollY > 10) { // 10 pikselden fazla kaydırıldıysa
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    }
});

// --- Mevcut Fonksiyonlar (initializeFeedbackWidget vb.) ---
// ... (initializeFeedbackWidget fonksiyonu ve diğerleri burada kalır) ...
}


// --- YENİ EKLENECEK FONKSİYONLAR ---

// async function checkLoginStatus() {
//   // Token'ı localStorage'dan al
//   // Token geçerli mi diye backend'e bir istek at (örn: /api/users/me)
//   // Sonuca göre updateAuthUI() çağır
// }

// function updateAuthUI() {
//   // Kullanıcı giriş yapmışsa header'da "Çıkış Yap" butonu göster
//   // Giriş yapmamışsa "Giriş Yap" / "Kayıt Ol" butonlarını göster
// }

// function setupSummaryPageListeners() {
//   // Metin gönderme formu, dosya yükleme formu olaylarını dinle
//   // Form gönderildiğinde ilgili API endpoint'ine istek at (handleSummarySubmit, handleFileUpload)
//   // Sonucu ekranda göster (displaySummaryResult)
// }

// async function handleSummarySubmit(event) {
//   // event.preventDefault();
//   // Formdan metni ve başlığı al
//   // Token'ı al
//   // /api/ozetler/metin endpoint'ine fetch ile POST isteği at
//   // Gelen sonucu displaySummaryResult ile göster
// }

// async function handleFileUpload(event) {
//   // event.preventDefault();
//   // Formdan dosyayı ve başlığı al (FormData kullanarak)
//   // Token'ı al
//   // /api/ozetler/dosya endpoint'ine fetch ile POST isteği at
//   // Gelen sonucu displaySummaryResult ile göster
// }

// function displaySummaryResult(result) {
//   // Özet metnini ve etiketleri ilgili HTML elementlerine yazdır
// }

// async function loadHistoryPage() {
//   // Token'ı al
//   // /api/ozetler endpoint'ine fetch ile GET isteği at
//   // Gelen özet listesini HTML'de oluştur (displayHistoryList)
//   // Silme butonlarına olay dinleyicileri ekle (addDeleteListeners)
// }

// function displayHistoryList(historyItems) {
//   // Gelen her bir özet için HTML elementi oluştur ve listeye ekle
// }

// function addDeleteListeners() {
//   // Tüm silme butonlarına tıklandığında handleDeletion fonksiyonunu çağıracak olay dinleyicileri ekle
// }

// async function handleDeletion(ozetId) {
//   // Token'ı al
//   // /api/ozetler/{ozetId} endpoint'ine fetch ile DELETE isteği at
//   // Başarılı olursa ilgili HTML elementini sayfadan kaldır
// }

// --- --- --- --- --- --- --- --- --- ---