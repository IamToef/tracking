const API_URL = (window.location.protocol === "file:" || 
                 (!window.location.hostname.includes("localhost") && 
                  !window.location.hostname.includes("127.0.0.1") && 
                  !window.location.hostname.includes("onrender.com")))
    ? "https://tracking-suoc.onrender.com/api"
    : "/api";

// State
let rawData = { mentors: [], students: [] };
let overrides = { forced: [], blocked: [], skipped_students: [], skipped_mentors: [] };
let currentAssignments = [];
let currentUnassigned = [];
let matchCurrentPage = 1;
let unmatchedCurrentPage = 1;
const PAGE_SIZE = 50;

const TARGET_SELECTS = [
    "override_force_student",
    "override_force_mentor",
    "override_block_student",
    "override_block_mentor",
    "override_skip_student",
    "override_skip_mentor"
];

let loadingCount = 0;

function showLoading() {
    loadingCount++;
    if (loadingCount === 1) {
        const overlay = document.getElementById("loading_overlay");
        if (overlay) overlay.classList.add("active");
    }
}

function hideLoading() {
    loadingCount--;
    if (loadingCount <= 0) {
        loadingCount = 0;
        const overlay = document.getElementById("loading_overlay");
        if (overlay) overlay.classList.remove("active");
    }
}

// Remove Vietnamese tones for search function
function removeVietnameseTones(str) {
    str = str.replace(/à|á|ạ|ả|ã|â|ầ|ấ|ậ|ẩ|ẫ|ă|ằ|ắ|ặ|ẳ|ẵ/g, "a");
    str = str.replace(/è|é|ẹ|ẻ|ẽ|ê|ề|ế|ệ|ể|ễ/g, "e");
    str = str.replace(/ì|í|ị|ỉ|ĩ/g, "i");
    str = str.replace(/ò|ó|ọ|ỏ|õ|ô|ồ|ố|ộ|ổ|ỗ|ơ|ờ|ớ|ợ|ở|ỡ/g, "o");
    str = str.replace(/ù|ú|ụ|ủ|ũ|ư|ừ|ứ|ự|ử|ữ/g, "u");
    str = str.replace(/ỳ|ý|ỵ|ỷ|ỹ/g, "y");
    str = str.replace(/đ/g, "d");
    str = str.replace(/À|Á|Ạ|Ả|Ã|Â|Ầ|Ấ|Ậ|Ẩ|Ẫ|Ă|Ằ|Ắ|Ặ|Ẳ|Ẵ/g, "A");
    str = str.replace(/È|É|Ẹ|Ẻ|Ẽ|Ê|Ề|Ế|Ệ|Ể|Ễ/g, "E");
    str = str.replace(/Ì|Í|Ị|Ỉ|Ĩ/g, "I");
    str = str.replace(/Ò|Ó|Ọ|Ỏ|Õ|Ô|Ồ|Ố|Ộ|Ổ|Ỗ|Ơ|Ờ|Ớ|Ợ|Ở|Ỡ/g, "O");
    str = str.replace(/Ù|Ú|Ụ|Ủ|Ũ|Ư|Ừ|Ứ|Ự|Ử|Ữ/g, "U");
    str = str.replace(/Ỳ|Ý|Ỵ|Ỷ|Ỹ/g, "Y");
    str = str.replace(/Đ/g, "D");
    str = str.replace(/\u0300|\u0301|\u0303|\u0309|\u0323/g, ""); 
    str = str.replace(/\u02C6|\u0306|\u031B/g, ""); 
    str = str.replace(/ + /g, " ");
    return str.trim();
}

// Render Custom Dropdown options (limited & on-demand to optimize DOM performance)
function renderCustomSelectOptions(selectId, filterText = "") {
    const select = document.getElementById(selectId);
    const container = document.getElementById(`custom_${selectId}`);
    if (!select || !container) return;

    const trigger = container.querySelector(".custom-select-trigger");
    const optionsContainer = container.querySelector(".custom-select-options");
    optionsContainer.innerHTML = "";

    const query = removeVietnameseTones(filterText.toLowerCase());
    let renderedCount = 0;
    const MAX_RENDER = 50; // ponytail: limit elements in DOM to prevent freezing the browser

    // Render the default placeholder option if it matches
    const firstOpt = select.options[0];
    if (firstOpt && firstOpt.value === "") {
        const item = document.createElement("div");
        item.className = "custom-select-option";
        if (select.value === "") {
            item.classList.add("selected");
        }
        item.textContent = firstOpt.textContent;
        item.dataset.value = "";
        item.addEventListener("click", (e) => {
            e.stopPropagation();
            select.value = "";
            select.dispatchEvent(new Event("change"));
            trigger.textContent = firstOpt.textContent;
            container.classList.remove("open");
            renderCustomSelectOptions(selectId, "");
        });
        optionsContainer.appendChild(item);
    }

    // Render filtered options up to MAX_RENDER
    for (let i = 0; i < select.options.length; i++) {
        const opt = select.options[i];
        if (opt.value === "") continue;

        const text = opt.textContent;
        const normalizedText = removeVietnameseTones(text.toLowerCase());

        if (normalizedText.includes(query)) {
            const item = document.createElement("div");
            item.className = "custom-select-option";
            if (opt.selected) {
                item.classList.add("selected");
                trigger.textContent = text;
            }
            item.textContent = text;
            item.dataset.value = opt.value;

            item.addEventListener("click", (e) => {
                e.stopPropagation();
                select.value = opt.value;
                select.dispatchEvent(new Event("change"));

                trigger.textContent = text;
                container.classList.remove("open");
                renderCustomSelectOptions(selectId, "");
            });

            optionsContainer.appendChild(item);
            renderedCount++;
            if (renderedCount >= MAX_RENDER) break;
        }
    }
}

// Initialize Custom Searchable Dropdown
function initSearchableDropdown(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;

    select.style.display = 'none';

    const container = document.createElement("div");
    container.className = "custom-select-container";
    container.id = `custom_${selectId}`;

    const trigger = document.createElement("div");
    trigger.className = "custom-select-trigger";
    trigger.textContent = select.options[select.selectedIndex]?.textContent || "Chọn...";
    container.appendChild(trigger);

    const dropdown = document.createElement("div");
    dropdown.className = "custom-select-dropdown";

    const searchInput = document.createElement("input");
    searchInput.type = "text";
    searchInput.className = "custom-select-search";
    searchInput.placeholder = "Nhập để tìm kiếm...";
    dropdown.appendChild(searchInput);

    const optionsContainer = document.createElement("div");
    optionsContainer.className = "custom-select-options";
    dropdown.appendChild(optionsContainer);

    container.appendChild(dropdown);
    select.parentNode.insertBefore(container, select);

    trigger.addEventListener("click", (e) => {
        e.stopPropagation();
        document.querySelectorAll(".custom-select-container").forEach(c => {
            if (c !== container) c.classList.remove("open");
        });
        container.classList.toggle("open");
        if (container.classList.contains("open")) {
            searchInput.focus();
        }
    });

    searchInput.addEventListener("click", (e) => {
        e.stopPropagation();
    });

    searchInput.addEventListener("input", () => {
        renderCustomSelectOptions(selectId, searchInput.value);
    });
}

// Refresh Custom Dropdown options
function refreshCustomSelect(selectId) {
    const select = document.getElementById(selectId);
    const container = document.getElementById(`custom_${selectId}`);
    if (!select || !container) return;

    const trigger = container.querySelector(".custom-select-trigger");
    const searchInput = container.querySelector(".custom-select-search");

    searchInput.value = "";
    
    // Perform initial render (first 50 options)
    renderCustomSelectOptions(selectId, "");

    const selectedOpt = select.options[select.selectedIndex];
    trigger.textContent = selectedOpt ? selectedOpt.textContent : (select.options[0]?.textContent || "Chọn...");
}

// Initialize
document.addEventListener("DOMContentLoaded", async () => {
    TARGET_SELECTS.forEach(id => initSearchableDropdown(id));

    document.addEventListener("click", () => {
        document.querySelectorAll(".custom-select-container").forEach(c => c.classList.remove("open"));
    });

    await loadData();
    await loadOverrides();
    await runMatching();
});

// Load raw student/mentor data from API
async function loadData() {
    showLoading();
    try {
        const res = await fetch(`${API_URL}/data`);
        rawData = await res.json();
        populateSelectBoxes();
    } catch (err) {
        console.error("Error loading raw data:", err);
    } finally {
        hideLoading();
    }
}

// Load overrides configuration
async function loadOverrides() {
    showLoading();
    try {
        const res = await fetch(`${API_URL}/overrides`);
        overrides = await res.json();
        renderOverridesList();
    } catch (err) {
        console.error("Error loading overrides:", err);
    } finally {
        hideLoading();
    }
}

// Populate UI dropdown selects
function populateSelectBoxes() {
    const studentSelects = [
        document.getElementById("override_force_student"),
        document.getElementById("override_block_student"),
        document.getElementById("override_skip_student")
    ];
    
    const mentorSelects = [
        document.getElementById("override_force_mentor"),
        document.getElementById("override_block_mentor"),
        document.getElementById("override_skip_mentor")
    ];

    // Clear options except first
    studentSelects.forEach(sel => {
        if (sel) {
            sel.innerHTML = '<option value="">Chọn học sinh...</option>';
            rawData.students.forEach(s => {
                const opt = document.createElement("option");
                opt.value = s.id;
                opt.textContent = `${s.name} (${s.gender})`;
                sel.appendChild(opt);
            });
            refreshCustomSelect(sel.id);
        }
    });

    mentorSelects.forEach(sel => {
        if (sel) {
            sel.innerHTML = '<option value="">Chọn cố vấn...</option>';
            rawData.mentors.forEach(m => {
                const opt = document.createElement("option");
                opt.value = m.id;
                opt.textContent = `${m.name} (${m.gender})`;
                sel.appendChild(opt);
            });
            refreshCustomSelect(sel.id);
        }
    });
}

// Render current overrides lists
function renderOverridesList() {
    // 1. Forced pairs
    const forcedContainer = document.getElementById("forced_list");
    forcedContainer.innerHTML = "";
    if (overrides.forced.length === 0) {
        forcedContainer.innerHTML = '<div style="color: var(--text-secondary); font-size: 0.85rem; padding: 0.5rem;">Không có ghi đè cưỡng ép.</div>';
    } else {
        overrides.forced.forEach((pair, idx) => {
            const sName = getStudentName(pair[0]);
            const mName = getMentorName(pair[1]);
            const item = document.createElement("div");
            item.className = "override-item";
            item.innerHTML = `
                <span>${sName} 🤝 ${mName}</span>
                <button onclick="removeOverride('forced', ${idx})">✕</button>
            `;
            forcedContainer.appendChild(item);
        });
    }

    // 2. Blocked pairs
    const blockedContainer = document.getElementById("blocked_list");
    blockedContainer.innerHTML = "";
    if (overrides.blocked.length === 0) {
        blockedContainer.innerHTML = '<div style="color: var(--text-secondary); font-size: 0.85rem; padding: 0.5rem;">Không có ghi đè chặn.</div>';
    } else {
        overrides.blocked.forEach((pair, idx) => {
            const sName = getStudentName(pair[0]);
            const mName = getMentorName(pair[1]);
            const item = document.createElement("div");
            item.className = "override-item";
            item.innerHTML = `
                <span>${sName} 🚫 ${mName}</span>
                <button onclick="removeOverride('blocked', ${idx})">✕</button>
            `;
            blockedContainer.appendChild(item);
        });
    }

    // 3. Skipped pool
    const skippedContainer = document.getElementById("skipped_list");
    skippedContainer.innerHTML = "";
    const hasSkips = overrides.skipped_students.length > 0 || overrides.skipped_mentors.length > 0;
    if (!hasSkips) {
        skippedContainer.innerHTML = '<div style="color: var(--text-secondary); font-size: 0.85rem; padding: 0.5rem;">Không có ai bị bỏ qua.</div>';
    } else {
        overrides.skipped_students.forEach((sid, idx) => {
            const sName = getStudentName(sid);
            const item = document.createElement("div");
            item.className = "override-item";
            item.innerHTML = `
                <span>Học sinh: ${sName} (Skip)</span>
                <button onclick="removeOverride('skipped_students', ${idx})">✕</button>
            `;
            skippedContainer.appendChild(item);
        });

        overrides.skipped_mentors.forEach((mid, idx) => {
            const mName = getMentorName(mid);
            const item = document.createElement("div");
            item.className = "override-item";
            item.innerHTML = `
                <span>Cố vấn: ${mName} (Skip)</span>
                <button onclick="removeOverride('skipped_mentors', ${idx})">✕</button>
            `;
            skippedContainer.appendChild(item);
        });
    }
}

// Add forced pair override
async function addForceOverride() {
    const sSelect = document.getElementById("override_force_student");
    const mSelect = document.getElementById("override_force_mentor");
    const sId = sSelect.value;
    const mId = mSelect.value;
    if (!sId || !mId) return alert("Vui lòng chọn cả học sinh và cố vấn!");
    
    // Check if student already forced or blocked
    if (overrides.forced.some(pair => pair[0] === sId)) {
        return alert("Học sinh này đã được cưỡng ép ghép với người khác!");
    }
    
    overrides.forced.push([sId, mId]);
    await saveOverrides();

    // Reset select inputs
    sSelect.value = "";
    mSelect.value = "";
    refreshCustomSelect("override_force_student");
    refreshCustomSelect("override_force_mentor");
}

// Add blocked pair override
async function addBlockOverride() {
    const sSelect = document.getElementById("override_block_student");
    const mSelect = document.getElementById("override_block_mentor");
    const sId = sSelect.value;
    const mId = mSelect.value;
    if (!sId || !mId) return alert("Vui lòng chọn cả học sinh và cố vấn!");
    
    if (overrides.blocked.some(pair => pair[0] === sId && pair[1] === mId)) {
        return alert("Cặp đôi này đã được cấu hình chặn từ trước!");
    }
    
    overrides.blocked.push([sId, mId]);
    await saveOverrides();

    // Reset select inputs
    sSelect.value = "";
    mSelect.value = "";
    refreshCustomSelect("override_block_student");
    refreshCustomSelect("override_block_mentor");
}

// Add skip pool override
async function addSkipOverride(type) {
    if (type === 'student') {
        const sSelect = document.getElementById("override_skip_student");
        const sId = sSelect.value;
        if (!sId) return alert("Vui lòng chọn học sinh!");
        if (overrides.skipped_students.includes(sId)) return alert("Học sinh này đã nằm trong danh sách bỏ qua!");
        overrides.skipped_students.push(sId);
        await saveOverrides();
        sSelect.value = "";
        refreshCustomSelect("override_skip_student");
    } else {
        const mSelect = document.getElementById("override_skip_mentor");
        const mId = mSelect.value;
        if (!mId) return alert("Vui lòng chọn cố vấn!");
        if (overrides.skipped_mentors.includes(mId)) return alert("Cố vấn này đã nằm trong danh sách bỏ qua!");
        overrides.skipped_mentors.push(mId);
        await saveOverrides();
        mSelect.value = "";
        refreshCustomSelect("override_skip_mentor");
    }
}

// Remove override and save
async function removeOverride(key, idx) {
    overrides[key].splice(idx, 1);
    await saveOverrides();
}

// Save overrides configuration to backend
async function saveOverrides() {
    showLoading();
    try {
        const res = await fetch(`${API_URL}/overrides`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(overrides)
        });
        const result = await res.json();
        if (result.status === "success") {
            renderOverridesList();
            // Automatically re-run matching
            await runMatching();
        }
    } catch (err) {
        console.error("Failed to save overrides:", err);
    } finally {
        hideLoading();
    }
}

// Run matching algorithm
async function runMatching() {
    showLoading();
    const config = getMatchConfig();
    try {
        const res = await fetch(`${API_URL}/match`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ config, overrides })
        });
        const data = await res.json();
        
        currentAssignments = data.assignments;
        currentUnassigned = data.unassigned;
        
        // Reset pagination pages
        matchCurrentPage = 1;
        unmatchedCurrentPage = 1;
        
        updateMetrics(data.report);
        renderMatchesTable();
        renderUnmatchedTable();
    } catch (err) {
        console.error("Error running matching:", err);
    } finally {
        hideLoading();
    }
}

// Run Q4 Rejection Simulation
async function runRejectionSimulation() {
    if (currentAssignments.length === 0) {
        return alert("Vui lòng nhấn 'Chạy đối sánh' trước khi thực hiện mô phỏng từ chối!");
    }
    showLoading();
    const config = getMatchConfig();
    try {
        const res = await fetch(`${API_URL}/simulate-rejection`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                assignments: currentAssignments,
                config,
                overrides,
                seed: 42 // Seed fixed for consistent result presentation
            })
        });
        const data = await res.json();
        
        // Show simulation tab
        switchTab('tab-simulation');
        renderSimulationPanel(data);
    } catch (err) {
        console.error("Error running rejection simulation:", err);
    } finally {
        hideLoading();
    }
}

// Helper to get configuration values from UI
function getMatchConfig() {
    return {
        session_duration: parseInt(document.getElementById("session_duration").value),
        default_same_gender: document.getElementById("default_same_gender").checked,
        weight_theme: parseFloat(document.getElementById("weight_theme").value),
        weight_jaccard: parseFloat(document.getElementById("weight_jaccard").value),
        poor_fit_threshold: parseFloat(document.getElementById("poor_fit_threshold").value)
    };
}

// Update DOM elements with metrics
function updateMetrics(report) {
    document.getElementById("metric_match_rate").textContent = `${report.match_rate}%`;
    document.getElementById("metric_matched_count").textContent = `${report.matched_count} / ${report.total_students} học sinh`;
    document.getElementById("metric_avg_score").textContent = report.avg_score.toFixed(3);
    document.getElementById("metric_poor_fit_count").textContent = report.poor_fit_count;
    document.getElementById("metric_poor_fit_rate").textContent = `${report.poor_fit_rate}%`;
    document.getElementById("metric_baseline_match_rate").textContent = `${report.baseline_match_rate}%`;
    
    const diff = (report.match_rate - report.baseline_match_rate).toFixed(1);
    const improvementText = diff >= 0 ? `Cải thiện: +${diff}%` : `Hụt: ${diff}%`;
    document.getElementById("metric_improvement").textContent = improvementText;
}

// Render Pagination Controls
function updatePaginationControls(type, totalItems, currentPage, onPageChange) {
    const container = document.getElementById(`${type}_pagination`);
    if (!container) return;

    if (totalItems <= PAGE_SIZE) {
        container.innerHTML = "";
        return;
    }

    const totalPages = Math.ceil(totalItems / PAGE_SIZE);

    container.innerHTML = `
        <div class="pagination">
            <button class="btn btn-secondary btn-sm" ${currentPage === 1 ? "disabled" : ""} id="${type}_prev">⬅️ Trước</button>
            <span class="pagination-info">Trang ${currentPage} / ${totalPages} (Tổng: ${totalItems})</span>
            <button class="btn btn-secondary btn-sm" ${currentPage === totalPages ? "disabled" : ""} id="${type}_next">Sau ➡️</button>
        </div>
    `;

    const prevBtn = container.querySelector(`#${type}_prev`);
    const nextBtn = container.querySelector(`#${type}_next`);

    if (prevBtn) {
        prevBtn.addEventListener("click", () => {
            if (currentPage > 1) {
                onPageChange(currentPage - 1);
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener("click", () => {
            if (currentPage < totalPages) {
                onPageChange(currentPage + 1);
            }
        });
    }
}

// Render Assignments Table with pagination to optimize DOM performance
function renderMatchesTable() {
    const tbody = document.querySelector("#matches_table tbody");
    tbody.innerHTML = "";
    
    if (currentAssignments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-secondary);">Chưa có dữ liệu ghép cặp. Nhấn "Chạy đối sánh".</td></tr>';
        updatePaginationControls("matches", 0, 1, () => {});
        return;
    }

    const totalItems = currentAssignments.length;
    const totalPages = Math.ceil(totalItems / PAGE_SIZE);
    
    if (matchCurrentPage > totalPages) matchCurrentPage = totalPages;
    if (matchCurrentPage < 1) matchCurrentPage = 1;

    const start = (matchCurrentPage - 1) * PAGE_SIZE;
    const end = Math.min(start + PAGE_SIZE, totalItems);
    
    const pageAssignments = currentAssignments.slice(start, end);

    pageAssignments.forEach(a => {
        const tr = document.createElement("tr");
        
        // Badges
        const genderSBadge = `<span class="badge badge-gender-${a.student_gender.toLowerCase()}">${a.student_gender}</span>`;
        const genderMBadge = `<span class="badge badge-gender-${a.mentor_gender.toLowerCase()}">${a.mentor_gender}</span>`;
        
        let typeBadge = "";
        if (a.is_forced) {
            typeBadge = '<span class="badge badge-forced">Cưỡng ép (Admin)</span>';
        } else if (a.is_rematched) {
            typeBadge = '<span class="badge badge-rematched">Ghép lại</span>';
        }

        const fitBadgeClass = a.is_poor_fit ? 'badge-poor-fit' : 'badge-good-fit';
        const fitText = a.is_poor_fit ? 'Poor Fit ⚠️' : 'Khớp Tốt';
        const scoreBadge = `<span class="badge ${fitBadgeClass}">${a.score.toFixed(3)} (${fitText})</span>`;

        tr.innerHTML = `
            <td><strong>${a.student_name}</strong> ${typeBadge}</td>
            <td>${genderSBadge}</td>
            <td><strong>${a.mentor_name}</strong></td>
            <td>${genderMBadge}</td>
            <td><span style="text-transform: capitalize;">${translateDay(a.day)}</span> ${a.start_time}-${a.end_time}</td>
            <td>${scoreBadge}</td>
            <td style="color: var(--text-secondary); max-width: 320px; font-size: 0.85rem;">${a.explanation}</td>
        `;
        tbody.appendChild(tr);
    });

    updatePaginationControls("matches", totalItems, matchCurrentPage, (newPage) => {
        matchCurrentPage = newPage;
        renderMatchesTable();
    });
}

// Render Unmatched Table with pagination to optimize DOM performance
function renderUnmatchedTable() {
    const tbody = document.querySelector("#unmatched_table tbody");
    tbody.innerHTML = "";
    
    if (currentUnassigned.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--success-color); font-weight: 500;">Hoàn hảo! 100% học sinh đã được đối sánh thành công.</td></tr>';
        updatePaginationControls("unmatched", 0, 1, () => {});
        return;
    }

    const totalItems = currentUnassigned.length;
    const totalPages = Math.ceil(totalItems / PAGE_SIZE);

    if (unmatchedCurrentPage > totalPages) unmatchedCurrentPage = totalPages;
    if (unmatchedCurrentPage < 1) unmatchedCurrentPage = 1;

    const start = (unmatchedCurrentPage - 1) * PAGE_SIZE;
    const end = Math.min(start + PAGE_SIZE, totalItems);

    const pageUnassigned = currentUnassigned.slice(start, end);

    pageUnassigned.forEach(u => {
        const tr = document.createElement("tr");
        const slotsText = u.slots ? u.slots.map(s => `${translateDay(s.day)} ${s.start_time}`).join(", ") : "N/A";
        const genderBadge = `<span class="badge badge-gender-${u.student_gender.toLowerCase()}">${u.student_gender}</span>`;
        
        tr.innerHTML = `
            <td><strong>${u.student_name}</strong></td>
            <td>${genderBadge}</td>
            <td style="max-width: 250px;">${slotsText}</td>
            <td style="color: var(--error-color); font-weight: 500;">${u.reason}</td>
        `;
        tbody.appendChild(tr);
    });

    updatePaginationControls("unmatched", totalItems, unmatchedCurrentPage, (newPage) => {
        unmatchedCurrentPage = newPage;
        renderUnmatchedTable();
    });
}

// Render Simulation panel results
function renderSimulationPanel(data) {
    const report = data.rejection_report;
    
    // Fill stats
    document.getElementById("sim_match_rate_before").textContent = `${document.getElementById("metric_match_rate").textContent}`;
    document.getElementById("sim_avg_score_before").textContent = `${document.getElementById("metric_avg_score").textContent}`;
    document.getElementById("sim_count_before").textContent = `${currentAssignments.length} / ${rawData.students.length - overrides.skipped_students.length}`;
    
    document.getElementById("sim_rejected_count").textContent = report.rejected_count;
    document.getElementById("sim_rematch_success").textContent = report.rematched_success_count;
    document.getElementById("sim_rematch_fail").textContent = report.rematched_fail_count;
    document.getElementById("sim_match_rate_after").textContent = `${report.match_rate_after}%`;
    document.getElementById("sim_avg_score_after").textContent = report.avg_score_after.toFixed(3);

    // Render table
    const tbody = document.querySelector("#simulation_table tbody");
    tbody.innerHTML = "";
    
    const reMatches = data.assignments.filter(a => a.is_rematched);
    const fails = data.unassigned;

    if (reMatches.length === 0 && fails.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-secondary);">Không có dữ liệu thay đổi.</td></tr>';
        return;
    }

    // Success rematches
    reMatches.forEach(a => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${a.student_name}</strong></td>
            <td style="color: var(--text-secondary); text-decoration: line-through;">${a.old_mentor_name}</td>
            <td><strong style="color: var(--success-color);">${a.mentor_name}</strong></td>
            <td>${translateDay(a.day)} ${a.start_time}</td>
            <td><span class="badge badge-good-fit">${a.score.toFixed(3)}</span></td>
            <td><span class="badge badge-good-fit">Ghép lại thành công</span></td>
        `;
        tbody.appendChild(tr);
    });

    // Fails to rematch
    fails.forEach(f => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${f.student_name}</strong></td>
            <td style="color: var(--text-secondary); text-decoration: line-through;">N/A</td>
            <td style="color: var(--error-color); font-weight: bold;">✕ Không thể ghép</td>
            <td>-</td>
            <td>-</td>
            <td><span class="badge badge-poor-fit" style="font-size:0.8rem;">${f.reason}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// Helpers
function getStudentName(sid) {
    const s = rawData.students.find(x => x.id === sid);
    return s ? s.name : sid.substring(0, 8);
}

// Helper for mentor name
function getMentorName(mid) {
    const m = rawData.mentors.find(x => x.id === mid);
    return m ? m.name : mid.substring(0, 8);
}

// Translate day names
function translateDay(day) {
    const days = {
        'monday': 'Thứ 2',
        'tuesday': 'Thứ 3',
        'wednesday': 'Thứ 4',
        'thursday': 'Thứ 5',
        'friday': 'Thứ 6',
        'saturday': 'Thứ 7',
        'sunday': 'Chủ nhật'
    };
    return days[day.toLowerCase()] || day;
}

// Tab Switching
function switchTab(tabId) {
    // Switch active class in tabs
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    
    // Find active tab and set active
    const tabs = Array.from(document.querySelectorAll(".tab"));
    const activeTab = tabs.find(t => t.getAttribute("onclick").includes(tabId));
    if (activeTab) activeTab.classList.add("active");

    // Hide all contents
    document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");
    
    // Show active content
    document.getElementById(tabId).style.display = "block";
}
