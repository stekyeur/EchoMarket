document.addEventListener("DOMContentLoaded", () => {
    const themeBtn = document.getElementById("themeToggle");
    const body = document.body;

    // 1. Sayfa Yüklenince: Kayıtlı temayı kontrol et
    const savedTheme = localStorage.getItem("theme");

    // Eğer kayıtlı tema 'light' ise sınıfı ekle
    if (savedTheme === 'light') {
        body.classList.add('light-mode');
        updateButtonText(true);
    } else {
        updateButtonText(false);
    }

    // 2. Butona Tıklanınca
    if (themeBtn) {
        themeBtn.addEventListener("click", () => {
            // Sınıfı varsa sil, yoksa ekle (toggle)
            body.classList.toggle('light-mode');

            const isLight = body.classList.contains('light-mode');

            // Tercihi kaydet
            localStorage.setItem('theme', isLight ? 'light' : 'dark');

            // Buton yazısını güncelle
            updateButtonText(isLight);
        });
    }

    // Buton ikonunu ve yazısını güncelleme fonksiyonu
    function updateButtonText(isLight) {
        if (!themeBtn) return;
        // FontAwesome ikonları kullanıyorsun, ona uygun yapalım:
        if (isLight) {
            themeBtn.innerHTML = '<i class="fas fa-sun"></i> Aydınlık';
        } else {
            themeBtn.innerHTML = '<i class="fas fa-moon"></i> Karanlık';
        }
    }
});