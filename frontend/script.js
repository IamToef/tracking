const API_URL = window.location.protocol === "file:"
    ? "https://tracking-suoc.onrender.com/api"
    : "/api";

// State
let rawData = { mentors: [], students: [] };
let overrides = { forced: [], blocked: [], skipped_students: [], skipped_mentors: [] };
let currentAssignments = [];
let currentUnassigned = [];

// Initialize
document.addEventListener("DOMContentLoaded", async () => {
    await loadData();
    await loadOverrides();
    // Run initial match
    await runMatching();
});

// Load raw student/mentor data from API
async function loadData() {
    try {
        const res = await fetch(`${API_URL}/data`);
        rawData = await res.json();
        populateSelectBoxes();
    } catch (err) {
        console.error("Error loading raw data:", err);
    }
}

// Load overrides configuration
async function loadOverrides() {
    try {
        const res = await fetch(`${API_URL}/overrides`);
        overrides = await res.json();
        renderOverridesList();
    } catch (err) {
        console.error("Error loading overrides:", err);
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
    const sId = document.getElementById("override_force_student").value;
    const mId = document.getElementById("override_force_mentor").value;
    if (!sId || !mId) return alert("Vui lòng chọn cả học sinh và cố vấn!");
    
    // Check if student already forced or blocked
    if (overrides.forced.some(pair => pair[0] === sId)) {
        return alert("Học sinh này đã được cưỡng ép ghép với người khác!");
    }
    
    overrides.forced.push([sId, mId]);
    await saveOverrides();
}

// Add blocked pair override
async function addBlockOverride() {
    const sId = document.getElementById("override_block_student").value;
    const mId = document.getElementById("override_block_mentor").value;
    if (!sId || !mId) return alert("Vui lòng chọn cả học sinh và cố vấn!");
    
    if (overrides.blocked.some(pair => pair[0] === sId && pair[1] === mId)) {
        return alert("Cặp đôi này đã được cấu hình chặn từ trước!");
    }
    
    overrides.blocked.push([sId, mId]);
    await saveOverrides();
}

// Add skip pool override
async function addSkipOverride(type) {
    if (type === 'student') {
        const sId = document.getElementById("override_skip_student").value;
        if (!sId) return alert("Vui lòng chọn học sinh!");
        if (overrides.skipped_students.includes(sId)) return alert("Học sinh này đã nằm trong danh sách bỏ qua!");
        overrides.skipped_students.push(sId);
    } else {
        const mId = document.getElementById("override_skip_mentor").value;
        if (!mId) return alert("Vui lòng chọn cố vấn!");
        if (overrides.skipped_mentors.includes(mId)) return alert("Cố vấn này đã nằm trong danh sách bỏ qua!");
        overrides.skipped_mentors.push(mId);
    }
    await saveOverrides();
}

// Remove override and save
async function removeOverride(key, idx) {
    overrides[key].splice(idx, 1);
    await saveOverrides();
}

// Save overrides configuration to backend
async function saveOverrides() {
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
    }
}

// Run matching algorithm
async function runMatching() {
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
        
        updateMetrics(data.report);
        renderMatchesTable();
        renderUnmatchedTable();
    } catch (err) {
        console.error("Error running matching:", err);
    }
}

// Run Q4 Rejection Simulation
async function runRejectionSimulation() {
    if (currentAssignments.length === 0) {
        return alert("Vui lòng nhấn 'Chạy đối sánh' trước khi thực hiện mô phỏng từ chối!");
    }
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

// Render Assignments Table
function renderMatchesTable() {
    const tbody = document.querySelector("#matches_table tbody");
    tbody.innerHTML = "";
    
    if (currentAssignments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-secondary);">Chưa có dữ liệu ghép cặp. Nhấn "Chạy đối sánh".</td></tr>';
        return;
    }

    currentAssignments.forEach(a => {
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
}

// Render Unmatched Table
function renderUnmatchedTable() {
    const tbody = document.querySelector("#unmatched_table tbody");
    tbody.innerHTML = "";
    
    if (currentUnassigned.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--success-color); font-weight: 500;">Hoàn hảo! 100% học sinh đã được đối sánh thành công.</td></tr>';
        return;
    }

    currentUnassigned.forEach(u => {
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
