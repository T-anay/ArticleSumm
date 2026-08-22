let API_URL = "";
const GOOGLE_CLIENT_ID = "703815846089-k7oqhi4o4qge65i64q2a9lpd1q654fp0.apps.googleusercontent.com";
const SUMMARY_ICON_OPTIONS = [
    { value: "fa-file-lines", label: "Belge" },
    { value: "fa-book", label: "Kitap" },
    { value: "fa-flask", label: "Bilim" },
    { value: "fa-chart-pie", label: "Grafik" },
    { value: "fa-newspaper", label: "Makale" },
    { value: "fa-lightbulb", label: "Fikir" },
    { value: "fa-microscope", label: "Araştırma" },
    { value: "fa-scale-balanced", label: "Hukuk" },
    { value: "fa-briefcase", label: "İş" },
    { value: "fa-graduation-cap", label: "Eğitim" },
];
const expandedWorkspaceIds = new Set();
let currentSummaryId = null;
let currentSummaryData = null;
let isSummaryEditing = false;
let summaryEditSnapshot = "";

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

function getToken() {
    return localStorage.getItem("token") || "";
}

function getActiveWorkspaceId() {
    const value = Number(localStorage.getItem("activeWorkspaceId") || "0");
    return Number.isFinite(value) && value > 0 ? value : null;
}

function setActiveWorkspaceId(workspaceId) {
    if (workspaceId) {
        localStorage.setItem("activeWorkspaceId", String(workspaceId));
    } else {
        localStorage.removeItem("activeWorkspaceId");
    }
}

async function apiFetch(path, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = getToken();
    if (token && !headers.has("Authorization")) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers,
    });

    return response;
}

async function loadWorkspaces() {
    const response = await apiFetch("/api/ozetler/calismalar");
    if (!response.ok) {
        throw new Error("Çalışma listesi alınamadı.");
    }
    return response.json();
}

async function createWorkspace(title) {
    const response = await apiFetch("/api/ozetler/calismalar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ baslik: title }),
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Çalışma oluşturulamadı.");
    }

    return response.json();
}

async function updateWorkspace(workspaceId, payload) {
    const response = await apiFetch(`/api/ozetler/calismalar/${workspaceId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Çalışma güncellenemedi.");
    }

    return response.json();
}

async function updateWorkspaceTitle(workspaceId, title) {
    return updateWorkspace(workspaceId, { baslik: title });
}

async function deleteWorkspace(workspaceId) {
    const response = await apiFetch(`/api/ozetler/calismalar/${workspaceId}`, {
        method: "DELETE",
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Çalışma silinemedi.");
    }

    return response.json();
}

async function loadWorkspaceSummaries(workspaceId) {
    const response = await apiFetch(`/api/ozetler/calismalar/${workspaceId}/ozetler`);
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Özetler alınamadı.");
    }
    return response.json();
}

async function loadSummaryById(summaryId) {
    const response = await apiFetch(`/api/ozetler/${summaryId}`);
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Özet alınamadı.");
    }
    return response.json();
}

function getSummaryIdFromUrl() {
    const params = new URLSearchParams(window.location.search || "");
    const summaryId = Number(params.get("id") || "0");
    return Number.isFinite(summaryId) && summaryId > 0 ? summaryId : null;
}

function renderSummaryDetails(data) {
    currentSummaryId = data?.id || null;
    currentSummaryData = data || null;
    isSummaryEditing = false;
    summaryEditSnapshot = "";

    const resultWrapper = document.getElementById("result-wrapper");
    const resultArea = document.getElementById("resultArea");
    const output = document.getElementById("summaryOutput");
    const title = document.getElementById("resultTitle");
    const tagsEl = document.getElementById("summaryTags");
    const badge = document.getElementById("active-mode-badge");
    const editBtn = document.getElementById("editSummaryBtn");
    const saveBtn = document.getElementById("saveSummaryBtn");
    const cancelBtn = document.getElementById("cancelEditSummaryBtn");
    const downloadBtn = document.getElementById("downloadSummaryBtn");
    const editorToolbar = document.getElementById("summaryEditorToolbar");
    const stickyToc = document.getElementById("sticky-toc");

    if (resultWrapper) resultWrapper.style.display = "block";
    if (resultArea) resultArea.style.display = "block";
    if (output) {
        output.contentEditable = "false";
        output.classList.remove("editing");
        output.innerHTML = data?.ozet_metin || "";
    }
    if (title) title.textContent = data?.baslik || "Sonuç";
    if (tagsEl) {
        const tags = (data?.etiketler || "")
            .split(",")
            .map((tag) => tag.trim())
            .filter(Boolean);
        tagsEl.innerHTML = tags.map((tag) => `<span>${tag}</span>`).join("");
    }
    if (badge) badge.style.display = "none";
    if (editBtn) editBtn.style.display = currentSummaryId ? "inline-flex" : "none";
    if (saveBtn) saveBtn.style.display = "none";
    if (cancelBtn) cancelBtn.style.display = "none";
    if (downloadBtn) downloadBtn.style.display = currentSummaryId ? "inline-flex" : "none";
    if (editorToolbar) editorToolbar.style.display = "none";

    document.body.classList.remove("font-mode-serif", "font-mode-sans");
    document.body.classList.add("font-mode-sans");
    if (stickyToc) stickyToc.style.display = "none";
}

function runEditorCommand(command, value = null) {
    const output = document.getElementById("summaryOutput");
    if (!output || !isSummaryEditing) return;

    output.focus();
    if (value) {
        document.execCommand(command, false, value);
    } else {
        document.execCommand(command, false, null);
    }
}

function setSummaryEditingMode(editing) {
    isSummaryEditing = editing;

    const output = document.getElementById("summaryOutput");
    const editBtn = document.getElementById("editSummaryBtn");
    const saveBtn = document.getElementById("saveSummaryBtn");
    const cancelBtn = document.getElementById("cancelEditSummaryBtn");
    const editorToolbar = document.getElementById("summaryEditorToolbar");

    if (!output) return;

    output.contentEditable = editing ? "true" : "false";
    output.classList.toggle("editing", editing);

    if (editing) {
        summaryEditSnapshot = output.innerHTML;
        output.focus();
    }

    if (editBtn) editBtn.style.display = editing ? "none" : (currentSummaryId ? "inline-flex" : "none");
    if (saveBtn) saveBtn.style.display = editing ? "inline-flex" : "none";
    if (cancelBtn) cancelBtn.style.display = editing ? "inline-flex" : "none";
    if (editorToolbar) editorToolbar.style.display = editing ? "flex" : "none";
}

async function updateSummary(summaryId, payload) {
    const response = await apiFetch(`/api/ozetler/${summaryId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Özet güncellenemedi.");
    }

    return response.json();
}

async function deleteSummary(summaryId) {
    const response = await apiFetch(`/api/ozetler/${summaryId}`, {
        method: "DELETE",
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Özet silinemedi.");
    }
}

async function downloadSummaryPdf(summaryId) {
    const response = await apiFetch(`/api/ozetler/${summaryId}/pdf`);

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "PDF indirilemedi.");
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `ozet-${summaryId}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
}

async function moveSummaryToWorkspace(summaryId, workspaceId) {
    const response = await apiFetch(`/api/ozetler/${summaryId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ calisma_id: workspaceId }),
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Özet taşınamadı.");
    }

    return response.json();
}

function requireLogin() {
    if (!getToken()) {
        window.location.href = "index.html";
        return false;
    }
    return true;
}

async function ensureWorkspaceSelection(selectElement) {
    const workspaces = await loadWorkspaces();
    if (!workspaces.length) {
        const created = await createWorkspace("Genel Çalışma");
        workspaces.push(created);
    }

    const savedId = getActiveWorkspaceId();
    const currentId = savedId && workspaces.some((item) => item.id === savedId) ? savedId : workspaces[0].id;
    setActiveWorkspaceId(currentId);

    if (selectElement) {
        selectElement.innerHTML = workspaces.map((workspace) => `<option value="${workspace.id}">${workspace.baslik}</option>`).join("");
        selectElement.value = String(currentId);
    }

    return { workspaces, currentId };
}

function escapeHtml(value) {
    return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

async function renderWorkspaceSidebar() {
    const list = document.getElementById("summaryList");
    if (!list) return;

    list.innerHTML = '<li class="placeholder">Yükleniyor...</li>';

    try {
        const workspaces = await loadWorkspaces();
        if (!workspaces.length) {
            const created = await createWorkspace("Genel Çalışma");
            workspaces.push(created);
        }

        const savedId = getActiveWorkspaceId();
        const activeWorkspaceId = savedId && workspaces.some((item) => item.id === savedId) ? savedId : workspaces[0].id;
        setActiveWorkspaceId(activeWorkspaceId);

        if (!expandedWorkspaceIds.size) {
            expandedWorkspaceIds.add(activeWorkspaceId);
        }

        const workspaceSummaries = new Map(
            await Promise.all(
                workspaces.map(async (workspace) => {
                    const summaries = await loadWorkspaceSummaries(workspace.id).catch(() => []);
                    return [workspace.id, summaries];
                })
            )
        );

        const newWorkspaceItem = `
            <li data-action="create-workspace-from-history">
                <a href="#">
                    <i class="fas fa-folder-plus"></i>
                    <span>Yeni Aktif Çalışma</span>
                </a>
            </li>
        `;

        const workspaceItems = workspaces.map((workspace) => {
            const workspaceId = workspace.id;
            const isExpanded = expandedWorkspaceIds.has(workspaceId);
            const isActive = workspaceId === activeWorkspaceId;
            const summaries = workspaceSummaries.get(workspaceId) || [];

            return `
                <li class="workspace-parent ${isActive ? 'active' : ''} ${workspace.is_pinned ? 'is-pinned' : ''}" data-workspace-id="${workspaceId}">
                    <a href="#" class="workspace-row-link" data-action="toggle-workspace" data-workspace-id="${workspaceId}">
                        <i class="fas fa-chevron-right workspace-expand-icon ${isExpanded ? 'expanded' : ''}"></i>
                        <i class="fas ${isExpanded ? 'fa-folder-open' : 'fa-folder'}"></i>
                        <span class="history-item-text">${escapeHtml(workspace.baslik)}</span>
                        ${workspace.is_pinned ? '<span class="workspace-pinned-badge" title="Yıldızlı Çalışma"><i class="fas fa-star"></i></span>' : ''}
                    </a>
                    <div class="history-item-actions">
                        <button type="button" class="action-btn" data-action="workspace-more" data-workspace-id="${workspaceId}" title="Diğer İşlemler">
                            <i class="fas fa-ellipsis-vertical"></i>
                        </button>
                    </div>
                    <ul class="workspace-summary-sublist ${isExpanded ? 'workspace-summary-sublist--expanded' : ''}">
                        <li class="workspace-create-summary-item">
                            <a class="history-item-link" href="#" data-action="create-summary-in-workspace" data-workspace-id="${workspaceId}">
                                <i class="fas fa-plus"></i>
                                <span class="history-item-text">Yeni Damıtma</span>
                            </a>
                        </li>
                        ${summaries.length ? summaries.map((item) => `
                            <li class="${item.id === currentSummaryId ? 'active' : ''}" data-summary-id="${item.id}" data-workspace-id="${workspaceId}">
                                <a class="history-item-link" href="summary.html?id=${item.id}">
                                    <i class="fas ${escapeHtml(item.icon_name || 'fa-file-lines')}"></i>
                                    <span class="history-item-text">${escapeHtml(item.baslik || 'Başlıksız Özet')}</span>
                                </a>
                                <div class="history-item-actions">
                                    <button type="button" class="action-btn" data-action="summary-more" data-summary-id="${item.id}" title="Diğer İşlemler">
                                        <i class="fas fa-ellipsis-vertical"></i>
                                    </button>
                                </div>
                            </li>
                        `).join("") : '<li><p class="workspace-summary-empty">Bu çalışmada özet yok.</p></li>'}
                    </ul>
                </li>
            `;
        }).join("");

        list.innerHTML = `${newWorkspaceItem}${workspaceItems}`;

        const createBtn = list.querySelector('[data-action="create-workspace-from-history"] a');
        if (createBtn) {
            createBtn.addEventListener("click", async (event) => {
                event.preventDefault();
                const title = await appPrompt("Yeni çalışma adı:", "Yeni Çalışma", "Yeni Aktif Çalışma");
                if (!title) return;
                try {
                    const workspace = await createWorkspace(title);
                    setActiveWorkspaceId(workspace.id);
                    await renderWorkspaceSidebar();
                    showInAppToast("Yeni çalışma oluşturuldu.", "success");
                } catch (error) {
                    await appAlert(error.message || "Çalışma oluşturulamadı.", "Hata");
                }
            });
        }

        list.querySelectorAll('[data-action="create-summary-in-workspace"]').forEach((link) => {
            link.addEventListener("click", (event) => {
                event.preventDefault();
                const workspaceId = Number(link.getAttribute("data-workspace-id"));
                if (!workspaceId) return;
                setActiveWorkspaceId(workspaceId);
                window.location.href = "summary.html";
            });
        });

        list.querySelectorAll('[data-action="toggle-workspace"]').forEach((button) => {
            button.addEventListener("click", async (event) => {
                event.preventDefault();
                const workspaceId = Number(button.getAttribute("data-workspace-id"));
                if (!workspaceId) return;

                const workspaceItem = button.closest(".workspace-parent");
                const workspaceSublist = workspaceItem?.querySelector(".workspace-summary-sublist");
                const workspaceArrow = workspaceItem?.querySelector(".workspace-expand-icon");
                const isExpanded = workspaceSublist?.classList.contains("workspace-summary-sublist--expanded");

                list.querySelectorAll(".workspace-parent").forEach((item) => {
                    if (item !== workspaceItem) item.classList.remove("active");
                });

                list.querySelectorAll(".workspace-summary-sublist").forEach((sublist) => {
                    if (sublist !== workspaceSublist) {
                        sublist.classList.remove("workspace-summary-sublist--expanded");
                    }
                });

                list.querySelectorAll(".workspace-expand-icon").forEach((icon) => {
                    if (icon !== workspaceArrow) icon.classList.remove("expanded");
                });

                if (workspaceItem) {
                    workspaceItem.classList.add("active");
                }

                if (isExpanded) {
                    expandedWorkspaceIds.delete(workspaceId);
                    workspaceSublist?.classList.remove("workspace-summary-sublist--expanded");
                    workspaceArrow?.classList.remove("expanded");
                } else {
                    expandedWorkspaceIds.clear();
                    expandedWorkspaceIds.add(workspaceId);
                    workspaceSublist?.classList.add("workspace-summary-sublist--expanded");
                    workspaceArrow?.classList.add("expanded");
                }

                setActiveWorkspaceId(workspaceId);
            });
        });

        list.querySelectorAll('[data-action="workspace-more"]').forEach((button) => {
            button.addEventListener("click", async (event) => {
                event.preventDefault();
                event.stopPropagation();

                const workspaceId = Number(button.getAttribute("data-workspace-id"));
                const workspace = workspaces.find((item) => item.id === workspaceId);
                if (!workspace) return;

                const action = await appSelectOption(
                    "Çalışma için işlem seçin:",
                    [
                        { value: "", label: "İşlem seçin..." },
                        { value: "pin", label: workspace.is_pinned ? "Yıldızı Kaldır" : "Yıldızla" },
                        { value: "edit", label: "Adını Düzenle" },
                        { value: "delete", label: "Çalışmayı Sil" },
                    ],
                    "",
                    "Çalışma Menüsü"
                );
                if (!action) return;

                if (action === "pin") {
                    try {
                        await updateWorkspace(workspaceId, { is_pinned: !workspace.is_pinned });
                        await renderWorkspaceSidebar();
                        showInAppToast(workspace.is_pinned ? "Çalışma yıldızı kaldırıldı." : "Çalışma yıldızlandı.", "success");
                    } catch (error) {
                        await appAlert(error.message || "Çalışma güncellenemedi.", "Hata");
                    }
                    return;
                }

                if (action === "edit") {
                    const newTitle = await appPrompt("Çalışma adını değiştirin:", workspace.baslik || "", "Çalışma Düzenle");
                    if (newTitle === null) return;

                    try {
                        await updateWorkspaceTitle(workspaceId, newTitle);
                        setActiveWorkspaceId(workspaceId);
                        await renderWorkspaceSidebar();
                        showInAppToast("Çalışma adı güncellendi.", "success");
                    } catch (error) {
                        await appAlert(error.message || "Çalışma adı güncellenemedi.", "Hata");
                    }
                    return;
                }

                const confirmed = await appConfirm(
                    "Bu çalışmayı silmek istediğinizden emin misiniz? İçindeki özetler başka bir çalışmaya taşınacaktır.",
                    "Çalışmayı Sil"
                );
                if (!confirmed) return;

                try {
                    const result = await deleteWorkspace(workspaceId);
                    const fallbackId = Number(result?.fallback_calisma_id || 0);
                    if (fallbackId) {
                        setActiveWorkspaceId(fallbackId);
                        expandedWorkspaceIds.add(fallbackId);
                    }
                    expandedWorkspaceIds.delete(workspaceId);
                    await renderWorkspaceSidebar();
                    showInAppToast("Çalışma silindi.", "success");
                } catch (error) {
                    await appAlert(error.message || "Çalışma silinemedi.", "Hata");
                }
            });
        });

        list.querySelectorAll('[data-action="summary-more"]').forEach((button) => {
            button.addEventListener("click", async (event) => {
                event.preventDefault();
                event.stopPropagation();

                const summaryId = Number(button.getAttribute("data-summary-id"));
                const summary = summaries.find((item) => item.id === summaryId);
                if (!summary) return;

                const action = await appSelectOption(
                    "Özet için işlem seçin:",
                    [
                        { value: "", label: "İşlem seçin..." },
                        { value: "pin", label: summary.is_pinned ? "Yıldızı Kaldır" : "Yıldızla" },
                        { value: "edit", label: "Başlık ve Simge Düzenle" },
                        { value: "delete", label: "Özeti Sil" },
                    ],
                    "",
                    "Özet Menüsü"
                );
                if (!action) return;

                if (action === "pin") {
                    try {
                        const updated = await updateSummary(summaryId, { is_pinned: !summary.is_pinned });
                        if (currentSummaryId === summaryId) {
                            renderSummaryDetails(updated);
                        }
                        await renderWorkspaceSidebar();
                        showInAppToast(summary.is_pinned ? "Özet yıldızı kaldırıldı." : "Özet yıldızlandı.", "success");
                    } catch (error) {
                        await appAlert(error.message || "Özet güncellenemedi.", "Hata");
                    }
                    return;
                }

                if (action === "delete") {
                    const confirmed = await appConfirm("Bu özeti silmek istediğinizden emin misiniz?", "Özet Sil");
                    if (!confirmed) return;

                    try {
                        await deleteSummary(summaryId);
                        if (currentSummaryId === summaryId) {
                            currentSummaryId = null;
                            currentSummaryData = null;
                            const resultWrapper = document.getElementById("result-wrapper");
                            if (resultWrapper) resultWrapper.style.display = "none";
                            const url = new URL(window.location.href);
                            url.searchParams.delete("id");
                            window.history.replaceState({}, "", url.toString());
                        }
                        await renderWorkspaceSidebar();
                        showInAppToast("Özet silindi.", "success");
                    } catch (error) {
                        await appAlert(error.message || "Özet silinemedi.", "Hata");
                    }
                    return;
                }

                const newTitle = await appPrompt("Özet başlığını düzenleyin:", summary.baslik || "", "Başlık Düzenle");
                if (newTitle === null) return;

                const newIcon = await appSelectOption(
                    "Özet simgesini seçin:",
                    SUMMARY_ICON_OPTIONS,
                    normalizeIconClass(summary.icon_name || "fa-file-lines"),
                    "Simge Seç"
                );
                if (newIcon === null) return;

                try {
                    const updated = await updateSummary(summaryId, {
                        baslik: (newTitle || "").trim() || summary.baslik,
                        icon_name: normalizeIconClass(newIcon),
                    });

                    if (currentSummaryId === summaryId) {
                        renderSummaryDetails(updated);
                    }
                    await renderWorkspaceSidebar();
                    showInAppToast("Özet başlığı güncellendi.", "success");
                } catch (error) {
                    await appAlert(error.message || "Özet güncellenemedi.", "Hata");
                }
            });
        });


    } catch (error) {
        list.innerHTML = `<li class="placeholder">${error.message || 'Geçmiş yüklenemedi.'}</li>`;
    }
}

function formatWorkspaceDate(value) {
    try {
        return new Date(value).toLocaleDateString("tr-TR", {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    } catch (_) {
        return "";
    }
}

function ensureInAppFeedbackUi() {
    if (!document.getElementById("app-toast-stack")) {
        const toastStack = document.createElement("div");
        toastStack.id = "app-toast-stack";
        toastStack.className = "app-toast-stack";
        document.body.appendChild(toastStack);
    }

    if (!document.getElementById("app-dialog-overlay")) {
        const overlay = document.createElement("div");
        overlay.id = "app-dialog-overlay";
        overlay.className = "app-dialog-overlay";
        overlay.innerHTML = `
            <div class="app-dialog" role="dialog" aria-modal="true">
                <h3 id="app-dialog-title" class="app-dialog-title"></h3>
                <p id="app-dialog-message" class="app-dialog-message"></p>
                <input id="app-dialog-input" class="modal-input" style="display:none;" />
                <select id="app-dialog-select" class="modal-input" style="display:none;"></select>
                <div class="app-dialog-actions">
                    <button type="button" id="app-dialog-cancel" class="secondary-btn">Vazgeç</button>
                    <button type="button" id="app-dialog-confirm" class="secondary-btn">Tamam</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
    }
}

function showInAppToast(message, type = "info", timeoutMs = 2600) {
    ensureInAppFeedbackUi();
    const stack = document.getElementById("app-toast-stack");
    if (!stack) return;

    const toast = document.createElement("div");
    toast.className = `app-toast ${type}`;
    toast.textContent = message;
    stack.appendChild(toast);

    window.setTimeout(() => {
        toast.classList.add("leaving");
        window.setTimeout(() => toast.remove(), 220);
    }, timeoutMs);
}

function showInAppDialog({
    title = "Bilgi",
    message = "",
    confirmText = "Tamam",
    cancelText = "Vazgeç",
    showCancel = true,
    inputValue = "",
    showInput = false,
    showSelect = false,
    selectOptions = [],
    selectValue = "",
}) {
    ensureInAppFeedbackUi();
    const overlay = document.getElementById("app-dialog-overlay");
    const titleEl = document.getElementById("app-dialog-title");
    const msgEl = document.getElementById("app-dialog-message");
    const inputEl = document.getElementById("app-dialog-input");
    const selectEl = document.getElementById("app-dialog-select");
    const cancelBtn = document.getElementById("app-dialog-cancel");
    const confirmBtn = document.getElementById("app-dialog-confirm");

    if (!overlay || !titleEl || !msgEl || !inputEl || !selectEl || !cancelBtn || !confirmBtn) {
        return Promise.resolve({ confirmed: false, value: null });
    }

    titleEl.textContent = title;
    msgEl.textContent = message;
    confirmBtn.textContent = confirmText;
    cancelBtn.textContent = cancelText;
    cancelBtn.style.display = showCancel ? "inline-flex" : "none";
    inputEl.style.display = showInput ? "block" : "none";
    inputEl.value = inputValue || "";
    selectEl.style.display = showSelect ? "block" : "none";
    if (showSelect) {
        selectEl.innerHTML = (selectOptions || [])
            .map((option) => `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`)
            .join("");
        selectEl.value = selectValue || (selectOptions[0]?.value || "");
    }

    overlay.classList.add("show");
    if (showInput) {
        window.setTimeout(() => inputEl.focus(), 0);
    } else if (showSelect) {
        window.setTimeout(() => selectEl.focus(), 0);
    } else {
        window.setTimeout(() => confirmBtn.focus(), 0);
    }

    return new Promise((resolve) => {
        let finished = false;

        const cleanup = (result) => {
            if (finished) return;
            finished = true;
            overlay.classList.remove("show");
            confirmBtn.removeEventListener("click", onConfirm);
            cancelBtn.removeEventListener("click", onCancel);
            overlay.removeEventListener("click", onOverlayClick);
            resolve(result);
        };

        const onConfirm = () => {
            const value = showInput ? inputEl.value : (showSelect ? selectEl.value : null);
            cleanup({ confirmed: true, value });
        };
        const onCancel = () => cleanup({ confirmed: false, value: null });
        const onOverlayClick = (event) => {
            if (event.target === overlay) onCancel();
        };

        confirmBtn.addEventListener("click", onConfirm);
        cancelBtn.addEventListener("click", onCancel);
        overlay.addEventListener("click", onOverlayClick);
    });
}

async function appAlert(message, title = "Bilgi") {
    await showInAppDialog({
        title,
        message,
        showCancel: false,
        confirmText: "Tamam",
    });
}

async function appConfirm(message, title = "Onay") {
    const result = await showInAppDialog({
        title,
        message,
        showCancel: true,
        confirmText: "Evet",
        cancelText: "Vazgeç",
    });
    return result.confirmed;
}

async function appPrompt(message, defaultValue = "", title = "Bilgi") {
    const result = await showInAppDialog({
        title,
        message,
        showCancel: true,
        confirmText: "Kaydet",
        cancelText: "Vazgeç",
        showInput: true,
        inputValue: defaultValue,
    });
    return result.confirmed ? result.value : null;
}

async function appSelectOption(message, options, selectedValue = "", title = "Seçim") {
    const result = await showInAppDialog({
        title,
        message,
        showCancel: true,
        confirmText: "Seç",
        cancelText: "Vazgeç",
        showSelect: true,
        selectOptions: options,
        selectValue: selectedValue,
    });
    return result.confirmed ? result.value : null;
}

// ==============================================
// === 1. TEMA VE GÖRÜNÜM YÖNETİMİ ===
// ==============================================

function applySavedPreferences() {
  const theme = localStorage.getItem("theme") || "light";
  setTheme(theme, false);
  
  const fontSize = localStorage.getItem("fontSize") || "medium";
    applyFontSize(fontSize);
}

function applyFontSize(size) {
    document.body.classList.remove("font-small", "font-medium", "font-large");
    if (size && size !== "medium") {
        document.body.classList.add(`font-${size}`);
    }
}

function setFontSize(size, save = true) {
    applyFontSize(size);
    if (save) localStorage.setItem("fontSize", size);
    updateActiveFontButtons(size);
}

function updateActiveFontButtons(size) {
    const fontBtns = document.querySelectorAll(".font-btn");
    fontBtns.forEach((btn) => {
        btn.classList.toggle("active", btn.getAttribute("data-size") === size);
    });
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

    const themeBtns = modal.querySelectorAll(".theme-btn");
    const currentTheme = localStorage.getItem("theme") || "light";
    updateActiveThemeButtons(currentTheme);
    themeBtns.forEach((btn) => {
        btn.onclick = () => {
            const mode = btn.getAttribute("data-mode");
            setTheme(mode);
        };
    });

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
            const size = btn.getAttribute("data-size");
            setFontSize(size);
        };
    });

    // Tehlikeli Bölge
    const btnDelHist = document.getElementById("btn-delete-history");
    if(btnDelHist) {
        btnDelHist.onclick = async () => {
            const confirmed = await appConfirm("Tüm özet geçmişiniz silinecek. Emin misiniz?", "Geçmişi Sil");
            if(confirmed) {
                localStorage.removeItem("history"); 
                const list = document.getElementById("summaryList");
                if(list) list.innerHTML = '<li class="placeholder">Geçmiş temizlendi.</li>';
                showInAppToast("Geçmiş temizlendi.", "success");
            }
        };
    }

    const btnDelAcc = document.getElementById("btn-delete-account");
    if(btnDelAcc) {
        btnDelAcc.onclick = async () => {
            const input = await appPrompt("Hesabınızı silmek için 'SIL' yazın:", "", "Hesabı Sil");
            if(input === "SIL") {
                localStorage.clear();
                await appAlert("Hesabınız silindi.", "Bilgi");
                window.location.href = "index.html";
            }
        };
    }
}

function initSettingsPage() {
    const tabs = document.querySelectorAll(".settings-page-tab");
    const panels = document.querySelectorAll(".settings-panel-page");
    const themeBtns = document.querySelectorAll(".page-theme-select .theme-btn, .settings-page-content .theme-btn");
    const fontBtns = document.querySelectorAll(".settings-page-content .font-btn");

    const currentTheme = localStorage.getItem("theme") || "light";
    updateActiveThemeButtons(currentTheme);
    themeBtns.forEach((btn) => {
        btn.onclick = () => {
            const mode = btn.getAttribute("data-mode");
            setTheme(mode);
        };
    });

    const currentSize = localStorage.getItem("fontSize") || "medium";
    fontBtns.forEach((btn) => {
        btn.classList.toggle("active", btn.getAttribute("data-size") === currentSize);
        btn.onclick = () => {
            setFontSize(btn.getAttribute("data-size"));
            fontBtns.forEach((other) => other.classList.toggle("active", other === btn));
        };
    });

    tabs.forEach((tab) => {
        tab.onclick = () => {
            tabs.forEach((other) => other.classList.remove("active"));
            tab.classList.add("active");
            const targetId = tab.getAttribute("data-target");
            panels.forEach((panel) => panel.classList.toggle("active", panel.id === targetId));
        };
    });

    const historyBtn = document.getElementById("btn-delete-history-page");
    if (historyBtn) {
        historyBtn.onclick = async () => {
            const confirmed = await appConfirm("Tüm özet geçmişiniz silinecek. Emin misiniz?", "Geçmişi Sil");
            if (confirmed) {
                localStorage.removeItem("history");
                showInAppToast("Geçmiş temizlendi.", "success");
            }
        };
    }

    const accountBtn = document.getElementById("btn-delete-account-page");
    if (accountBtn) {
        accountBtn.onclick = async () => {
            const input = await appPrompt("Hesabınızı silmek için 'SIL' yazın:", "", "Hesabı Sil");
            if (input === "SIL") {
                localStorage.clear();
                await appAlert("Hesabınız silindi.", "Bilgi");
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
    ensureInAppFeedbackUi();
  applySavedPreferences();
  initBackgroundAnimation(); 
  await loadHeader();
  
  const page = window.location.pathname.split("/").pop() || "index.html";
  
    if (page === "summary.html") initSummaryPage();
        else if (page === "history.html") initHistoryPage();
        else if (page === "settings.html") initSettingsPage();
        else if (["index.html", "register.html", "reset-password.html"].includes(page)) initAuthPage();
});

// ==============================================
// === 6. AUTH SAYFASI ===
// ==============================================
function initAuthPage() {
  const container = document.querySelector('.auth-flipper-container');
  const showRegisterBtn = document.getElementById('show-register-btn');
  const showLoginBtn = document.getElementById('show-login-btn');
  const showForgotBtn = document.getElementById('show-forgot-btn');
  const showLoginFromForgotBtn = document.getElementById('show-login-btn-from-forgot');

  if (showRegisterBtn && container) {
      showRegisterBtn.onclick = (e) => {
          e.preventDefault();
          container.classList.remove('is-forgot');
          container.classList.add('is-flipped');
      };
  }

  if (showLoginBtn && container) {
      showLoginBtn.onclick = (e) => {
          e.preventDefault();
          container.classList.remove('is-flipped', 'is-forgot');
      };
  }

  if (showForgotBtn && container) {
      showForgotBtn.onclick = (e) => {
          e.preventDefault();
          container.classList.remove('is-flipped');
          container.classList.add('is-forgot');
      };
  }

  if (showLoginFromForgotBtn && container) {
      showLoginFromForgotBtn.onclick = (e) => {
          e.preventDefault();
          container.classList.remove('is-flipped', 'is-forgot');
      };
  }
  
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
              showInAppToast("Kayıt başarılı. Giriş yapabilirsiniz.", "success");
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
  if (!requireLogin()) return;
  
  const dropZone = document.getElementById('drop-zone');
  const pdfInput = document.getElementById('pdfInput');
  const btn = document.getElementById("summarizeBtn");
    const editSummaryBtn = document.getElementById("editSummaryBtn");
    const saveSummaryBtn = document.getElementById("saveSummaryBtn");
    const cancelEditSummaryBtn = document.getElementById("cancelEditSummaryBtn");
        const downloadSummaryBtn = document.getElementById("downloadSummaryBtn");
    const editorToolbar = document.getElementById("summaryEditorToolbar");
    const urlSummaryId = getSummaryIdFromUrl();

  renderWorkspaceSidebar().catch((error) => console.error(error));

  if (editSummaryBtn) {
      editSummaryBtn.addEventListener("click", () => {
          if (!currentSummaryId || !currentSummaryData) return;
          setSummaryEditingMode(true);
      });
  }

  if (saveSummaryBtn) {
      saveSummaryBtn.addEventListener("click", async () => {
          if (!currentSummaryId) return;
          const output = document.getElementById("summaryOutput");
          if (!output) return;

          try {
              const updated = await updateSummary(currentSummaryId, {
                  ozet_metin: output.innerHTML,
              });
              renderSummaryDetails(updated);
              await renderWorkspaceSidebar();
              showInAppToast("Özet metni güncellendi.", "success");
          } catch (error) {
              await appAlert(error.message || "Özet metni güncellenemedi.", "Hata");
          }
      });
  }

  if (cancelEditSummaryBtn) {
      cancelEditSummaryBtn.addEventListener("click", () => {
          const output = document.getElementById("summaryOutput");
          if (output && isSummaryEditing) {
              output.innerHTML = summaryEditSnapshot;
          }
          setSummaryEditingMode(false);
      });
  }

  if (downloadSummaryBtn) {
      downloadSummaryBtn.addEventListener("click", async () => {
          if (!currentSummaryId) return;
          try {
              await downloadSummaryPdf(currentSummaryId);
              showInAppToast("PDF indiriliyor.", "success");
          } catch (error) {
              await appAlert(error.message || "PDF indirilemedi.", "Hata");
          }
      });
  }

  if (editorToolbar) {
      editorToolbar.querySelectorAll(".editor-tool-btn").forEach((button) => {
          button.addEventListener("click", () => {
              const command = button.getAttribute("data-cmd");
              const value = button.getAttribute("data-value");
              if (!command) return;
              runEditorCommand(command, value);
          });
      });
  }

  if (urlSummaryId) {
      loadSummaryById(urlSummaryId)
          .then((data) => {
              renderSummaryDetails(data);
              if (data?.calisma_id) {
                  setActiveWorkspaceId(data.calisma_id);
                  renderWorkspaceSidebar().catch((error) => console.error(error));
              }
          })
          .catch(async (error) => {
              await appAlert(error.message || "Özet detayı yüklenemedi.", "Hata");
          });
  }

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
          if (!file) { await appAlert("Lütfen dosya seçin", "Uyarı"); return; }
          
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
              const targetLang = langEl ? langEl.value : "en";
              formData.append("target_language", targetLang);

              const workspaceId = getActiveWorkspaceId();
              if (workspaceId) {
                  formData.append("calisma_id", String(workspaceId));
              }
              
              const res = await fetch(`${API_URL}/api/ozetler/pdf_yukle`, {
                  method: "POST",
                  headers: { 'Authorization': `Bearer ${getToken()}` },
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
              renderSummaryDetails(data);
              renderWorkspaceSidebar().catch((error) => console.error(error));
              
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
              await appAlert("Bir hata oluştu: " + e.message, "Hata");
              document.getElementById("loading").style.display = "none";
          } finally {
              btn.disabled = false;
          }
      });
  }
  
  const toggle = document.getElementById("sidebar-toggle");
  if(toggle) toggle.onclick = () => document.body.classList.toggle("sidebar-collapsed");
}

function initHistoryPage() {
  if (!requireLogin()) return;

  const workspaceList = document.getElementById("workspace-history-list");
  const createWorkspaceForm = document.getElementById("create-workspace-form");
  const workspaceTitleInput = document.getElementById("workspace-title-input");
  const workspaceDetailTitle = document.getElementById("workspace-detail-title");
  const workspaceDetailMeta = document.getElementById("workspace-detail-meta");
  const workspaceSummaryList = document.getElementById("workspace-summary-list");

  async function renderHistory(selectedId = null) {
      const workspaces = await loadWorkspaces();
      if (!workspaces.length) {
          const created = await createWorkspace("Genel Çalışma");
          workspaces.push(created);
      }

      const activeId = selectedId || getActiveWorkspaceId() || workspaces[0].id;
      setActiveWorkspaceId(activeId);

      const currentWorkspace = workspaces.find((workspace) => workspace.id === activeId) || workspaces[0];
      const summaries = await loadWorkspaceSummaries(currentWorkspace.id);

      if (workspaceList) {
          workspaceList.innerHTML = workspaces.map((workspace) => {
              const inlineItems = workspace.id === currentWorkspace.id
                  ? (summaries.length
                      ? `<div class="workspace-inline-summaries">${summaries.map((item) => `
                              <a href="summary.html?id=${item.id}" class="workspace-inline-summary-link">
                                  <span class="workspace-inline-summary-title">${item.baslik || "Başlıksız Özet"}</span>
                                  <span class="workspace-inline-summary-excerpt">${(item.ozet_metin || "").slice(0, 110)}${(item.ozet_metin || "").length > 110 ? "..." : ""}</span>
                              </a>
                          `).join("")}</div>`
                      : '<p class="workspace-inline-empty">Bu çalışma altında henüz özet yok.</p>')
                  : "";

              return `
                  <div class="workspace-list-item">
                      <button class="workspace-chip ${workspace.id === activeId ? 'active' : ''}" data-id="${workspace.id}">
                          <span>${workspace.baslik}</span>
                      </button>
                      ${inlineItems}
                  </div>
              `;
          }).join("");

          workspaceList.querySelectorAll("[data-id]").forEach((button) => {
              button.addEventListener("click", async () => {
                  const workspaceId = Number(button.getAttribute("data-id"));
                  setActiveWorkspaceId(workspaceId);
                  await renderHistory(workspaceId);
              });
          });
      }

      if (workspaceDetailTitle) workspaceDetailTitle.textContent = currentWorkspace.baslik;
      if (workspaceDetailMeta) workspaceDetailMeta.textContent = `${workspaces.length} çalışma mevcut • ${formatWorkspaceDate(currentWorkspace.created_at)}`;
      if (workspaceSummaryList) {
          if (!summaries.length) {
              workspaceSummaryList.innerHTML = '<p class="empty-state">Bu çalışma altında henüz özet yok.</p>';
          } else {
              workspaceSummaryList.innerHTML = summaries.map((item) => `
                  <article class="workspace-summary-card">
                      <div class="workspace-summary-card-header">
                          <h3>${item.baslik || 'Başlıksız Özet'}</h3>
                          <div class="workspace-card-actions">
                              <a href="summary.html?id=${item.id}" class="secondary-link">Aç</a>
                              <a href="summary.html?id=${item.id}" class="secondary-link">Düzenle</a>
                          </div>
                      </div>
                      <p>${item.ozet_metin || ''}</p>
                      <div class="summary-tags">
                          ${(item.etiketler || '').split(',').filter(Boolean).map((tag) => `<span>${tag.trim()}</span>`).join('')}
                      </div>
                      <div class="workspace-move-row">
                          <select class="modal-input summary-move-select" data-summary-id="${item.id}">
                              ${workspaces.map((workspace) => `<option value="${workspace.id}" ${workspace.id === currentWorkspace.id ? 'selected' : ''}>${workspace.baslik}</option>`).join("")}
                          </select>
                          <button type="button" class="secondary-btn summary-move-btn" data-summary-id="${item.id}">Taşı</button>
                      </div>
                  </article>
              `).join("");

              workspaceSummaryList.querySelectorAll(".summary-move-btn").forEach((button) => {
                  button.addEventListener("click", async () => {
                      const summaryId = Number(button.getAttribute("data-summary-id"));
                      const select = workspaceSummaryList.querySelector(`.summary-move-select[data-summary-id="${summaryId}"]`);
                      const targetWorkspaceId = Number(select?.value || currentWorkspace.id);
                      if (!summaryId || !targetWorkspaceId || targetWorkspaceId === currentWorkspace.id) return;

                      try {
                          await moveSummaryToWorkspace(summaryId, targetWorkspaceId);
                          await renderHistory(currentWorkspace.id);
                          showInAppToast("Özet başka çalışmaya taşındı.", "success");
                      } catch (error) {
                          await appAlert(error.message || "Özet taşınamadı.", "Hata");
                      }
                  });
              });
          }
      }
  }

  if (createWorkspaceForm) {
      createWorkspaceForm.addEventListener("submit", async (event) => {
          event.preventDefault();
          const title = (workspaceTitleInput?.value || "").trim();
          if (!title) return;

          try {
              const workspace = await createWorkspace(title);
              if (workspaceTitleInput) workspaceTitleInput.value = "";
              setActiveWorkspaceId(workspace.id);
              await renderHistory(workspace.id);
              showInAppToast("Çalışma oluşturuldu.", "success");
          } catch (error) {
              await appAlert(error.message || "Çalışma oluşturulamadı.", "Hata");
          }
      });
  }

  renderHistory().catch((error) => {
      const errorBox = document.getElementById("history-error-message");
      if (errorBox) {
          errorBox.textContent = error.message || "Geçmiş yüklenemedi.";
          errorBox.style.display = "block";
      }
  });
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

function normalizeIconClass(value) {
    const cleaned = String(value || "").trim().replace(/^fa[srlbd]?\s+/i, "");
    if (!cleaned) return "fa-file-lines";
    return cleaned.startsWith("fa-") ? cleaned : `fa-${cleaned}`;
}
