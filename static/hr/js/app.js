/* Staff salary — live total (basic + other); used by inline oninput on form fields */
window.recalcStaffTotal = function (el) {
    const form = el && el.closest ? el.closest('form') : null;
    if (!form) return;
    const basic = form.querySelector('[name="basic_salary"]');
    const other = form.querySelector('[name="other_salary"]');
    const total = form.querySelector('[name="total_salary"]');
    if (!basic || !other || !total) return;
    const sum = (parseFloat(basic.value) || 0) + (parseFloat(other.value) || 0);
    total.value = Number.isInteger(sum) ? String(sum) : sum.toFixed(2);
};

/* Theme */
function toggleTheme() {
    const html = document.documentElement;
    html.dataset.theme = html.dataset.theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('nexusTheme', html.dataset.theme);
    reinitCharts();
}

(function () {
    const saved = localStorage.getItem('nexusTheme') || 'light';
    document.documentElement.dataset.theme = saved;
})();

/* Sidebar */
let sidebarCollapsed = false;

function applySidebarCollapsed(collapsed) {
    sidebarCollapsed = collapsed;
    const sidebar = document.getElementById('sidebar');
    const body = document.body;
    const icon = document.getElementById('sidebar-toggle-icon');
    if (!sidebar) return;
    if (collapsed) {
        sidebar.classList.add('collapsed');
        body.classList.add('sidebar-collapsed');
        if (icon) icon.classList.replace('bi-chevron-left', 'bi-chevron-right');
    } else {
        sidebar.classList.remove('collapsed');
        body.classList.remove('sidebar-collapsed');
        if (icon) icon.classList.replace('bi-chevron-right', 'bi-chevron-left');
    }
    try {
        localStorage.setItem('takhleesSidebarCollapsed', collapsed ? '1' : '0');
    } catch (e) {}
}

function restoreSidebarState() {
    try {
        if (localStorage.getItem('takhleesSidebarCollapsed') === '1') {
            applySidebarCollapsed(true);
        }
    } catch (e) {}
    document.documentElement.classList.remove('sidebar-collapsed-init');
}

function toggleSidebar() {
    applySidebarCollapsed(!sidebarCollapsed);
}

/* Page transitions */
const PAGE_LEAVE_MS = 200;

function ensureTransitionBar() {
    let bar = document.getElementById('page-transition-bar');
    if (!bar) {
        bar = document.createElement('div');
        bar.id = 'page-transition-bar';
        bar.setAttribute('aria-hidden', 'true');
        document.body.appendChild(bar);
    }
    return bar;
}

function startPageEnter() {
    if ('scrollRestoration' in history) {
        history.scrollRestoration = 'manual';
    }
    window.scrollTo(0, 0);
    if (prefersReducedMotion()) {
        document.body.classList.remove('page-leaving', 'page-entering');
        document.body.classList.add('page-loaded');
        return;
    }
    const bar = ensureTransitionBar();
    bar.classList.remove('is-done');
    bar.classList.add('is-active');
    requestAnimationFrame(() => {
        document.body.classList.remove('page-leaving', 'page-entering');
        document.body.classList.add('page-loaded');
        bar.classList.add('is-done');
        window.setTimeout(() => {
            bar.classList.remove('is-active', 'is-done');
        }, 400);
    });
}

function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function shouldPageTransition(link) {
    if (!link || link.dataset.noTransition !== undefined) return false;
    if (link.target === '_blank' || link.hasAttribute('download')) return false;
    if (link.dataset.bsToggle || link.getAttribute('data-bs-toggle')) return false;
    if (link.getAttribute('role') === 'button') return false;
    if (link.closest('.dataTables_wrapper, .pagination, .paginate_button, .dropdown-menu, .modal')) return false;
    const href = link.getAttribute('href');
    if (!href || href === '#' || href.startsWith('javascript:') || href.startsWith('mailto:') || href.startsWith('tel:')) {
        return false;
    }
    try {
        const url = new URL(href, window.location.href);
        if (url.origin !== window.location.origin) return false;
        if (url.pathname.includes('/logout')) return false;
        if (url.pathname === window.location.pathname && url.search === window.location.search) return false;
        return true;
    } catch (e) {
        return false;
    }
}

function navigateWithTransition(url) {
    if (prefersReducedMotion()) {
        window.location.href = url;
        return;
    }
    const bar = ensureTransitionBar();
    document.body.classList.remove('page-loaded');
    document.body.classList.add('page-leaving');
    bar.classList.remove('is-done');
    bar.classList.add('is-active');
    window.setTimeout(() => {
        window.location.href = url;
    }, PAGE_LEAVE_MS);
}

function initPageTransitions() {
    ensureTransitionBar();
    restoreSidebarState();
    startPageEnter();

    document.addEventListener('click', (event) => {
        if (event.defaultPrevented || event.button !== 0) return;
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        const link = event.target.closest('a[href]');
        if (!shouldPageTransition(link)) return;
        event.preventDefault();
        navigateWithTransition(link.href);
    });

    window.addEventListener('pageshow', (event) => {
        if (event.persisted) {
            document.body.classList.remove('page-leaving');
            startPageEnter();
        }
    });
}

function openSidebarMobile() {
    document.getElementById('sidebar').classList.add('mobile-open');
}

function closeSidebarMobile() {
    document.getElementById('sidebar').classList.remove('mobile-open');
}

/* Charts */
let charts = {};

function getChartColors() {
    const isDark = document.documentElement.dataset.theme === 'dark';
    return {
        text: isDark ? '#94a3b8' : '#64748b',
        grid: isDark ? '#262626' : '#eef2f7',
        green: '#00843D',
        greenSoft: 'rgba(0,132,61,.75)',
        teal: '#0d9488',
        blue: '#2563eb',
        amber: '#d97706',
        palette: ['#00843D', '#0d9488', '#2563eb', '#7c3aed', '#d97706', '#0891b2', '#059669', '#6366f1'],
    };
}

function destroyChart(key) {
    if (charts[key]) {
        charts[key].destroy();
        delete charts[key];
    }
}

function readHrDashboardChartData() {
    const el = document.getElementById('hr-dashboard-chart-data');
    if (!el) return null;
    try {
        return JSON.parse(el.textContent || '{}');
    } catch (e) {
        return null;
    }
}

function initDashboardCharts() {
    const cc = getChartColors();
    const chartData = readHrDashboardChartData();
    const monthly = chartData?.monthly || {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        leads: [0, 0, 0, 0, 0, 0],
        revenue: [0, 0, 0, 0, 0, 0],
    };
    const sources = chartData?.sources || { labels: ['No data'], values: [0] };
    const sourceColors = cc.palette;

    destroyChart('revenue');
    const rCtx = document.getElementById('revenueChart');
    if (rCtx) {
        const barGradient = rCtx.getContext('2d').createLinearGradient(0, 0, 0, 280);
        barGradient.addColorStop(0, 'rgba(0,132,61,.92)');
        barGradient.addColorStop(1, 'rgba(13,148,136,.72)');

        charts.revenue = new Chart(rCtx, {
            type: 'bar',
            data: {
                labels: monthly.labels,
                datasets: [
                    {
                        label: 'Revenue (₹L)',
                        data: monthly.revenue,
                        backgroundColor: barGradient,
                        borderRadius: 10,
                        borderSkipped: false,
                        yAxisID: 'y',
                    },
                    {
                        label: 'Leads',
                        data: monthly.leads,
                        type: 'line',
                        borderColor: cc.teal,
                        backgroundColor: 'rgba(13,148,136,.08)',
                        fill: true,
                        tension: 0.42,
                        borderWidth: 2.5,
                        pointRadius: 4,
                        pointBackgroundColor: '#fff',
                        pointBorderColor: cc.teal,
                        pointBorderWidth: 2,
                        pointHoverRadius: 6,
                        yAxisID: 'y1',
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        labels: {
                            color: cc.text,
                            font: { family: 'Plus Jakarta Sans', size: 12, weight: '600' },
                            padding: 18,
                            usePointStyle: true,
                            pointStyle: 'circle',
                        },
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15,23,42,.92)',
                        titleFont: { family: 'Plus Jakarta Sans', size: 13, weight: '700' },
                        bodyFont: { family: 'Plus Jakarta Sans', size: 12 },
                        padding: 12,
                        cornerRadius: 10,
                        displayColors: true,
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: cc.text, font: { family: 'Plus Jakarta Sans', size: 11 } },
                        border: { display: false },
                    },
                    y: {
                        grid: { color: cc.grid },
                        ticks: { color: cc.text, font: { family: 'Plus Jakarta Sans', size: 11 }, callback: (v) => '₹' + v + 'L' },
                        border: { display: false },
                    },
                    y1: {
                        position: 'right',
                        grid: { display: false },
                        ticks: { color: cc.text, font: { family: 'Plus Jakarta Sans', size: 11 } },
                        border: { display: false },
                    },
                },
            },
        });
    }

    destroyChart('leadSource');
    const lCtx = document.getElementById('leadSourceChart');
    if (lCtx) {
        charts.leadSource = new Chart(lCtx, {
            type: 'doughnut',
            data: {
                labels: sources.labels,
                datasets: [{
                    data: sources.values,
                    backgroundColor: sources.labels.map((_, i) => sourceColors[i % sourceColors.length]),
                    borderWidth: 3,
                    borderColor: document.documentElement.dataset.theme === 'dark' ? '#1a1a1a' : '#ffffff',
                    hoverOffset: 10,
                    hoverBorderWidth: 0,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '72%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: cc.text,
                            font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' },
                            boxWidth: 10,
                            padding: 14,
                            usePointStyle: true,
                        },
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15,23,42,.92)',
                        cornerRadius: 10,
                        padding: 12,
                    },
                },
            },
        });
    }
}

function reinitCharts() {
    if (document.body.dataset.page === 'dashboard') {
        initDashboardCharts();
    }
}

/* Leads table — HTML rows already in template; only DataTable + search */
let leadsTableInst = null;

function initLeadMonitorFilters() {
    const form = document.getElementById('leadMonitorFilterForm');
    const period = document.getElementById('leadMonitorPeriod');
    const customDates = document.getElementById('leadMonitorCustomDates');
    if (!form || !period) return;

    const toggleCustom = () => {
        if (customDates) {
            customDates.classList.toggle('d-none', period.value !== 'custom');
        }
    };
    period.addEventListener('change', toggleCustom);
    toggleCustom();
}

function initLeadMonitorRows() {
    document.querySelectorAll('[data-lead-row]').forEach((row) => {
        const main = row.querySelector('.lead-monitor-row__main');
        const detail = row.querySelector('.lead-monitor-row__detail');
        const toggle = row.querySelector('.lead-monitor-row__toggle');
        if (!main || !detail) return;

        const openRow = () => {
            const isOpen = row.classList.contains('is-open');
            document.querySelectorAll('[data-lead-row].is-open').forEach((other) => {
                if (other === row) return;
                other.classList.remove('is-open');
                const d = other.querySelector('.lead-monitor-row__detail');
                const t = other.querySelector('.lead-monitor-row__toggle');
                if (d) d.hidden = true;
                if (t) t.setAttribute('aria-expanded', 'false');
            });
            row.classList.toggle('is-open', !isOpen);
            detail.hidden = isOpen;
            if (toggle) toggle.setAttribute('aria-expanded', String(!isOpen));
        };

        main.addEventListener('click', openRow);
    });
}

function initLeadsTable() {
    const table = document.getElementById('leadsTable');
    if (!table) return;

    if (leadsTableInst) {
        leadsTableInst.destroy();
        leadsTableInst = null;
    }

    leadsTableInst = $('#leadsTable').DataTable({
        pageLength: 7,
        responsive: true,
        dom: 'tp',
        language: { paginate: { previous: '‹', next: '›' } },
    });

    const search = document.getElementById('leadSearch');
    if (search) {
        search.addEventListener('keyup', function () {
            leadsTableInst.search(this.value).draw();
        });
    }
}

/* Toast */
function showToast(msg, type = 'info') {
    const icons = {
        success: 'bi-check-circle-fill',
        info: 'bi-info-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        error: 'bi-x-circle-fill',
    };
    const colors = { success: '#00843D', info: '#E01E26', warning: '#b45309', error: '#E01E26' };
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const id = 'toast-' + Date.now();
    const el = document.createElement('div');
    el.className = 'toast-custom';
    el.id = id;
    el.innerHTML =
        '<i class="bi ' + (icons[type] || icons.info) + ' toast-icon" style="color:' + (colors[type] || colors.info) + '"></i>' +
        '<div><div class="toast-title">' + type.charAt(0).toUpperCase() + type.slice(1) + '</div>' +
        '<div class="toast-body">' + msg + '</div></div>' +
        '<i class="bi bi-x toast-close" onclick="removeToast(\'' + id + '\')"></i>';
    container.appendChild(el);
    setTimeout(() => removeToast(id), 4000);
}

function removeToast(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

/* Table status filter — rows stay in DOM; filter only hides visually */
window._hrTableStatusFilter = {
    branchesTable: 'all',
    branchManagersTable: 'all',
    staffTable: 'all',
    followupTable: 'all',
    backofficeTable: 'all',
};

if (!window._hrStatusSearchInstalled && $.fn.dataTable) {
    window._hrStatusSearchInstalled = true;
    $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
        const tableId = settings.nTable.id;
        if (tableId !== 'branchesTable' && tableId !== 'branchManagersTable' && tableId !== 'staffTable') {
            return true;
        }
        const filter = window._hrTableStatusFilter[tableId];
        if (!filter || filter === 'all') {
            return true;
        }
        const api = new $.fn.dataTable.Api(settings);
        const node = api.row(dataIndex).node();
        if (!node) {
            return true;
        }
        return node.getAttribute('data-status') === filter;
    });
}

function applyTableStatusFilter(tableId, tableInst, filterValue) {
    window._hrTableStatusFilter[tableId] = filterValue;
    if (tableInst) {
        tableInst.draw();
    }
}

/* Branches */
let branchesTableInst = null;

function initBranchesTable() {
    const table = document.getElementById('branchesTable');
    if (!table) return;

    if (branchesTableInst) {
        branchesTableInst.destroy();
        branchesTableInst = null;
    }

    branchesTableInst = $('#branchesTable').DataTable({
        pageLength: 10,
        responsive: true,
        dom: 'tp',
        order: [[0, 'asc']],
        language: { paginate: { previous: '‹', next: '›' }, emptyTable: 'No branches found' },
    });

    const statusFilter = document.getElementById('branchStatusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function () {
            applyTableStatusFilter('branchesTable', branchesTableInst, this.value);
        });
        applyTableStatusFilter('branchesTable', branchesTableInst, statusFilter.value);
    }

    const search = document.getElementById('branchSearch');
    if (search) {
        search.addEventListener('keyup', function () {
            branchesTableInst.search(this.value).draw();
        });
    }

    const stateFilter = document.getElementById('branchStateFilter');
    if (stateFilter) {
        const seen = new Set();
        Array.from(stateFilter.options).forEach((opt, i) => {
            if (i === 0 || seen.has(opt.value)) {
                if (i > 0) opt.remove();
            } else {
                seen.add(opt.value);
            }
        });
        stateFilter.addEventListener('change', function () {
            const val = this.value;
            branchesTableInst.column(2).search(val ? '^' + val + '$' : '', true, false).draw();
        });
    }
}

function setBranchNationalityValue(inputId, value) {
    const el = document.getElementById(inputId);
    if (el) el.value = value || '';
}

function showAddBranchModal() {
    const el = document.getElementById('addBranchModal');
    if (el) new bootstrap.Modal(el).show();
}

function showAddManagerModal() {
    const el = document.getElementById('addBranchManagerModal');
    if (el) new bootstrap.Modal(el).show();
}

function initBranchManagerToggle() {
    const checkbox = document.getElementById('add_manager');
    const fields = document.getElementById('branchManagerFields');
    if (!checkbox || !fields) return;

    const sync = () => {
        fields.classList.toggle('d-none', !checkbox.checked);
        fields.querySelectorAll('input, select, textarea').forEach((input) => {
            if (input.type === 'checkbox') return;
            input.required = checkbox.checked;
        });
    };
    checkbox.addEventListener('change', sync);
    sync();
}

function openEditBranchModal(btn) {
    const form = document.getElementById('editBranchForm');
    if (!form) return;
    form.action = btn.dataset.url;
    const set = (id, key) => {
        const el = document.getElementById(id);
        if (el) el.value = btn.dataset[key] || '';
    };
    set('edit_name', 'name');
    set('edit_email', 'email');
    set('edit_phone', 'phone');
    set('edit_opening_date', 'openingDate');
    setBranchNationalityValue('edit_nationality', btn.dataset.nationality);
    set('edit_address', 'address');
    set('edit_city', 'city');
    set('edit_state', 'state');
    const el = document.getElementById('editBranchModal');
    if (el) new bootstrap.Modal(el).show();
}

function submitBranchStatusForm(url) {
    const form = document.getElementById('branchStatusForm');
    if (form && url) {
        form.action = url;
        form.submit();
    }
}

function confirmDeactivateBranch(btn) {
    const name = btn.dataset.name || 'this branch';
    Swal.fire({
        title: 'Deactivate branch?',
        text: `"${name}" and its active managers will be deactivated. The row stays in this table — use Activate to turn it back on.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#f59e0b',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Yes, deactivate',
    }).then((result) => {
        if (result.isConfirmed) submitBranchStatusForm(btn.dataset.url);
    });
}

function confirmReactivateBranch(btn) {
    const name = btn.dataset.name || 'this branch';
    Swal.fire({
        title: 'Activate branch?',
        text: `"${name}" will be active again. Branch managers stay deactivated until you activate them separately.`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#00843D',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Yes, activate',
    }).then((result) => {
        if (result.isConfirmed) submitBranchStatusForm(btn.dataset.url);
    });
}

function confirmDeactivateManager(btn) {
    const name = btn.dataset.name || 'this manager';
    Swal.fire({
        title: 'Deactivate manager?',
        text: `"${name}" will lose portal login access.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#f59e0b',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Yes, deactivate',
    }).then((result) => {
        if (result.isConfirmed) submitBranchStatusForm(btn.dataset.url);
    });
}

function confirmReactivateManager(btn) {
    const name = btn.dataset.name || 'this manager';
    Swal.fire({
        title: 'Activate manager?',
        text: `"${name}" will be able to sign in again. The row stays in this table.`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#00843D',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Yes, activate',
    }).then((result) => {
        if (result.isConfirmed) submitBranchStatusForm(btn.dataset.url);
    });
}

function initBranchActions() {
    document.querySelectorAll('.branch-edit-btn').forEach((btn) => {
        btn.addEventListener('click', () => openEditBranchModal(btn));
    });
    document.querySelectorAll('.branch-deactivate-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmDeactivateBranch(btn));
    });
    document.querySelectorAll('.branch-reactivate-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmReactivateBranch(btn));
    });
}

function initBranchManagerActions() {
    initTeamMemberActions();
    document.querySelectorAll('.branch-mgr-deactivate-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmDeactivateManager(btn));
    });
    document.querySelectorAll('.branch-mgr-reactivate-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmReactivateManager(btn));
    });
}

function showAddStaffModal() {
    const el = document.getElementById('addStaffModal');
    if (!el) return;
    const basic = el.querySelector('[name="basic_salary"]');
    if (basic) recalcStaffTotal(basic);
    new bootstrap.Modal(el).show();
}

function confirmDeactivateStaff(btn) {
    const name = btn.dataset.name || 'this staff member';
    Swal.fire({
        title: 'Deactivate staff?',
        text: `"${name}" will lose portal login. The row stays in this table.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#f59e0b',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Yes, deactivate',
    }).then((result) => {
        if (result.isConfirmed) submitBranchStatusForm(btn.dataset.url);
    });
}

function confirmReactivateStaff(btn) {
    const name = btn.dataset.name || 'this staff member';
    Swal.fire({
        title: 'Activate staff?',
        text: `"${name}" will be able to sign in again.`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#00843D',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Yes, activate',
    }).then((result) => {
        if (result.isConfirmed) submitBranchStatusForm(btn.dataset.url);
    });
}

function renderTeamViewDocuments(modal, btn) {
    const list = modal.querySelector('[data-view-documents-list]');
    if (!list) return;
    const raw = btn.dataset.documents;
    if (!raw) {
        list.innerHTML = '<p class="text-muted small mb-0">No documents uploaded.</p>';
        return;
    }
    let items;
    try {
        items = JSON.parse(raw);
    } catch (e) {
        list.innerHTML = '<p class="text-muted small mb-0">Unable to load documents.</p>';
        return;
    }
    if (!items.length) {
        list.innerHTML = '<p class="text-muted small mb-0">No documents uploaded.</p>';
        return;
    }
    list.innerHTML = items.map((item) => {
        const expiry = item.expiry
            ? `<div class="text-muted small">Expires: ${item.expiry}</div>`
            : '';
        return `
            <div class="team-view-doc-item d-flex justify-content-between align-items-center gap-3 py-2 border-bottom">
                <div class="min-w-0">
                    <div class="fw-semibold">${item.label}</div>
                    ${expiry}
                </div>
                <a href="${item.url}" target="_blank" rel="noopener" class="btn btn-sm btn-outline-primary flex-shrink-0">
                    <i class="bi bi-box-arrow-up-right me-1"></i> View
                </a>
            </div>
        `;
    }).join('');
}

function openTeamViewModal(btn) {
    const modalId = btn.dataset.viewModal;
    const el = document.getElementById(modalId);
    if (!el) return;
    const set = (field, value) => {
        const node = el.querySelector(`[data-view-field="${field}"]`);
        if (node) node.textContent = value || '—';
    };
    set('displayName', btn.dataset.displayName);
    set('username', btn.dataset.username ? `@${btn.dataset.username}` : '—');
    set('email', btn.dataset.email);
    if (btn.dataset.showBranch !== 'false') set('branch', btn.dataset.branch);
    set('phone', btn.dataset.phone);
    set('joinDate', btn.dataset.joinDate);
    set('dateOfBirth', btn.dataset.dateOfBirth);
    set('status', btn.dataset.status);
    if (btn.dataset.showSalary === 'true') {
        const fmt = (v) => (v !== undefined && v !== '' ? Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—');
        set('basicSalary', fmt(btn.dataset.basicSalary));
        set('otherSalary', fmt(btn.dataset.otherSalary));
        set('totalSalary', fmt(btn.dataset.totalSalary));
    }
    el.querySelectorAll('.date-of-birth-row').forEach((row) => {
        row.classList.toggle('d-none', btn.dataset.showDob !== 'true');
    });
    el.querySelectorAll('.salary-row').forEach((row) => {
        row.classList.toggle('d-none', btn.dataset.showSalary !== 'true');
    });
    renderTeamViewDocuments(el, btn);
    el._lastEditBtn = btn.closest('tr')?.querySelector('.team-edit-btn') || null;
    new bootstrap.Modal(el).show();
}

function openTeamEditModal(btn) {
    const form = document.getElementById(btn.dataset.formId);
    if (!form) return;
    form.action = btn.dataset.url;
    const set = (id, key) => {
        const node = document.getElementById(id);
        if (node) node.value = btn.dataset[key] || '';
    };
    if (btn.dataset.usernameDisplayId) {
        const u = document.getElementById(btn.dataset.usernameDisplayId);
        if (u) u.value = btn.dataset.username || '';
    }
    if (btn.dataset.branchFieldId) set(btn.dataset.branchFieldId, 'branchId');
    set(btn.dataset.emailFieldId, 'email');
    set(btn.dataset.phoneFieldId, 'phone');
    set(btn.dataset.joinFieldId, 'joinDate');
    if (btn.dataset.dobFieldId) set(btn.dataset.dobFieldId, 'dateOfBirth');
    if (btn.dataset.headFieldId) {
        const headEl = document.getElementById(btn.dataset.headFieldId);
        if (headEl) headEl.checked = btn.dataset.isBackofficeHead === '1';
    }
    if (btn.dataset.basicSalaryFieldId) set(btn.dataset.basicSalaryFieldId, 'basicSalary');
    if (btn.dataset.otherSalaryFieldId) set(btn.dataset.otherSalaryFieldId, 'otherSalary');
    if (btn.dataset.basicSalaryFieldId) {
        const basicEl = document.getElementById(btn.dataset.basicSalaryFieldId);
        if (basicEl) recalcStaffTotal(basicEl);
    }
    const modalId = btn.dataset.editModal;
    const el = document.getElementById(modalId);
    if (el) new bootstrap.Modal(el).show();
}

function initTeamMemberActions() {
    document.querySelectorAll('.team-view-btn').forEach((btn) => {
        btn.addEventListener('click', () => openTeamViewModal(btn));
    });
    document.querySelectorAll('.team-edit-btn').forEach((btn) => {
        btn.addEventListener('click', () => openTeamEditModal(btn));
    });
    document.querySelectorAll('.team-view-to-edit-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            const viewModal = btn.closest('.modal');
            const editBtn = viewModal?._lastEditBtn;
            if (editBtn) setTimeout(() => openTeamEditModal(editBtn), 300);
        });
    });
}

function initStaffActions() {
    initTeamMemberActions();
    document.querySelectorAll('.staff-deactivate-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmDeactivateStaff(btn));
    });
    document.querySelectorAll('.staff-reactivate-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmReactivateStaff(btn));
    });
}

function showAddFollowupModal() {
    const el = document.getElementById('addFollowupModal');
    if (el) new bootstrap.Modal(el).show();
}

function showAddBackofficeModal() {
    const el = document.getElementById('addBackofficeModal');
    if (el) new bootstrap.Modal(el).show();
}

function showAddFinanceModal() {
    const el = document.getElementById('addFinanceModal');
    if (el) new bootstrap.Modal(el).show();
}

function showAddMarketingModal() {
    const el = document.getElementById('addMarketingModal');
    if (el) new bootstrap.Modal(el).show();
}

function confirmDeactivateTeamMember(btn, label) {
    const name = btn.dataset.name || `this ${label}`;
    Swal.fire({
        title: `Deactivate ${label}?`,
        text: `"${name}" will lose portal login. The row stays in this table.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#f59e0b',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Yes, deactivate',
    }).then((result) => {
        if (result.isConfirmed) submitBranchStatusForm(btn.dataset.url);
    });
}

function confirmReactivateTeamMember(btn, label) {
    const name = btn.dataset.name || `this ${label}`;
    Swal.fire({
        title: `Activate ${label}?`,
        text: `"${name}" will be able to sign in again.`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#00843D',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Yes, activate',
    }).then((result) => {
        if (result.isConfirmed) submitBranchStatusForm(btn.dataset.url);
    });
}

function initFollowupActions() {
    initTeamMemberActions();
    document.querySelectorAll('.followup-deactivate-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmDeactivateTeamMember(btn, 'follow-up member'));
    });
    document.querySelectorAll('.followup-reactivate-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmReactivateTeamMember(btn, 'follow-up member'));
    });
}

function initBackofficeActions() {
    initTeamMemberActions();
    document.querySelectorAll('.backoffice-deactivate-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmDeactivateTeamMember(btn, 'back office member'));
    });
    document.querySelectorAll('.backoffice-reactivate-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmReactivateTeamMember(btn, 'back office member'));
    });
}

function initFinanceActions() {
    initTeamMemberActions();
    document.querySelectorAll('.finance-deactivate-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmDeactivateTeamMember(btn, 'finance member'));
    });
    document.querySelectorAll('.finance-reactivate-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmReactivateTeamMember(btn, 'finance member'));
    });
}

function initMarketingActions() {
    initTeamMemberActions();
    document.querySelectorAll('.marketing-deactivate-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmDeactivateTeamMember(btn, 'marketing member'));
    });
    document.querySelectorAll('.marketing-reactivate-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmReactivateTeamMember(btn, 'marketing member'));
    });
}

let staffTableInst = null;
let followupTableInst = null;
let backofficeTableInst = null;
let financeTableInst = null;
let marketingTableInst = null;

function initStaffTable() {
    const table = document.getElementById('staffTable');
    if (!table) return;

    if (staffTableInst) {
        staffTableInst.destroy();
        staffTableInst = null;
    }

    staffTableInst = $('#staffTable').DataTable({
        pageLength: 10,
        responsive: true,
        dom: 'tp',
        order: [[0, 'asc']],
        language: { paginate: { previous: '‹', next: '›' }, emptyTable: 'No staff found' },
    });

    const statusFilter = document.getElementById('staffStatusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function () {
            applyTableStatusFilter('staffTable', staffTableInst, this.value);
        });
        applyTableStatusFilter('staffTable', staffTableInst, statusFilter.value);
    }

    const search = document.getElementById('staffSearch');
    if (search) {
        search.addEventListener('keyup', function () {
            staffTableInst.search(this.value).draw();
        });
    }
}

function initFollowupTable() {
    const table = document.getElementById('followupTable');
    if (!table) return;

    if (followupTableInst) {
        followupTableInst.destroy();
        followupTableInst = null;
    }

    followupTableInst = $('#followupTable').DataTable({
        pageLength: 10,
        responsive: true,
        dom: 'tp',
        order: [[0, 'asc']],
        language: { paginate: { previous: '‹', next: '›' }, emptyTable: 'No follow-up profiles found' },
    });

    const statusFilter = document.getElementById('followupStatusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function () {
            applyTableStatusFilter('followupTable', followupTableInst, this.value);
        });
        applyTableStatusFilter('followupTable', followupTableInst, statusFilter.value);
    }

    const search = document.getElementById('followupSearch');
    if (search) {
        search.addEventListener('keyup', function () {
            followupTableInst.search(this.value).draw();
        });
    }
}

function initBackofficeTable() {
    const table = document.getElementById('backofficeTable');
    if (!table) return;

    if (backofficeTableInst) {
        backofficeTableInst.destroy();
        backofficeTableInst = null;
    }

    backofficeTableInst = $('#backofficeTable').DataTable({
        pageLength: 10,
        responsive: true,
        dom: 'tp',
        order: [[0, 'asc']],
        language: { paginate: { previous: '‹', next: '›' }, emptyTable: 'No back office profiles found' },
    });

    const statusFilter = document.getElementById('backofficeStatusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function () {
            applyTableStatusFilter('backofficeTable', backofficeTableInst, this.value);
        });
        applyTableStatusFilter('backofficeTable', backofficeTableInst, statusFilter.value);
    }

    const search = document.getElementById('backofficeSearch');
    if (search) {
        search.addEventListener('keyup', function () {
            backofficeTableInst.search(this.value).draw();
        });
    }
}

function initFinanceTable() {
    const table = document.getElementById('financeTable');
    if (!table) return;

    if (financeTableInst) {
        financeTableInst.destroy();
        financeTableInst = null;
    }

    financeTableInst = $('#financeTable').DataTable({
        pageLength: 10,
        responsive: true,
        dom: 'tp',
        order: [[0, 'asc']],
        language: { paginate: { previous: '‹', next: '›' }, emptyTable: 'No finance profiles found' },
    });

    const statusFilter = document.getElementById('financeStatusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function () {
            applyTableStatusFilter('financeTable', financeTableInst, this.value);
        });
        applyTableStatusFilter('financeTable', financeTableInst, statusFilter.value);
    }

    const search = document.getElementById('financeSearch');
    if (search) {
        search.addEventListener('keyup', function () {
            financeTableInst.search(this.value).draw();
        });
    }
}

function initMarketingTable() {
    const table = document.getElementById('marketingTable');
    if (!table) return;

    if (marketingTableInst) {
        marketingTableInst.destroy();
        marketingTableInst = null;
    }

    marketingTableInst = $('#marketingTable').DataTable({
        pageLength: 10,
        responsive: true,
        dom: 'tp',
        order: [[0, 'asc']],
        language: { paginate: { previous: '‹', next: '›' }, emptyTable: 'No marketing profiles found' },
    });

    const statusFilter = document.getElementById('marketingStatusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function () {
            applyTableStatusFilter('marketingTable', marketingTableInst, this.value);
        });
        applyTableStatusFilter('marketingTable', marketingTableInst, statusFilter.value);
    }

    const search = document.getElementById('marketingSearch');
    if (search) {
        search.addEventListener('keyup', function () {
            marketingTableInst.search(this.value).draw();
        });
    }
}

/* Branch managers list */
let branchManagersTableInst = null;

function initBranchManagersTable() {
    const table = document.getElementById('branchManagersTable');
    if (!table) return;

    if (branchManagersTableInst) {
        branchManagersTableInst.destroy();
        branchManagersTableInst = null;
    }

    branchManagersTableInst = $('#branchManagersTable').DataTable({
        pageLength: 10,
        responsive: true,
        dom: 'tp',
        order: [[0, 'asc']],
        language: { paginate: { previous: '‹', next: '›' }, emptyTable: 'No branch managers found' },
    });

    const mgrStatusFilter = document.getElementById('branchManagerStatusFilter');
    if (mgrStatusFilter) {
        mgrStatusFilter.addEventListener('change', function () {
            applyTableStatusFilter('branchManagersTable', branchManagersTableInst, this.value);
        });
        applyTableStatusFilter('branchManagersTable', branchManagersTableInst, mgrStatusFilter.value);
    }

    const search = document.getElementById('branchManagerSearch');
    if (search) {
        search.addEventListener('keyup', function () {
            branchManagersTableInst.search(this.value).draw();
        });
    }

    const branchFilter = document.getElementById('branchManagerBranchFilter');
    if (branchFilter) {
        const seen = new Set();
        Array.from(branchFilter.options).forEach((opt, i) => {
            if (i === 0 || seen.has(opt.value)) {
                if (i > 0) opt.remove();
            } else {
                seen.add(opt.value);
            }
        });
        branchFilter.addEventListener('change', function () {
            const val = this.value;
            branchManagersTableInst.column(4).search(val ? val : '', true, false).draw();
        });
    }
}

/* Profile photo preview */
function initProfilePhotoPreview() {
    const input = document.getElementById('profilePictureInput');
    const saveBtn = document.getElementById('profilePhotoSave');
    const previewWrap = document.getElementById('profileAvatarPreview');
    if (!input || !previewWrap) return;

    input.addEventListener('change', function () {
        const file = this.files && this.files[0];
        if (!file || !file.type.startsWith('image/')) return;

        const reader = new FileReader();
        reader.onload = function (e) {
            let img = document.getElementById('profileAvatarImg');
            if (img && img.tagName !== 'IMG') {
                const newImg = document.createElement('img');
                newImg.id = 'profileAvatarImg';
                newImg.className = 'profile-avatar profile-avatar--xl';
                newImg.alt = 'Profile preview';
                img.replaceWith(newImg);
                img = newImg;
            }
            if (!img) {
                img = document.createElement('img');
                img.id = 'profileAvatarImg';
                img.className = 'profile-avatar profile-avatar--xl';
                img.alt = 'Profile preview';
                previewWrap.innerHTML = '';
                previewWrap.appendChild(img);
            }
            img.src = e.target.result;
            if (saveBtn) saveBtn.hidden = false;
        };
        reader.readAsDataURL(file);
    });
}

/* HR leave requests */
let leaveRequestsTableInst = null;

function initLeaveRequestsTable() {
    const table = document.getElementById('leaveRequestsTable');
    if (!table) return;

    if (leaveRequestsTableInst) {
        leaveRequestsTableInst.destroy();
        leaveRequestsTableInst = null;
    }

    leaveRequestsTableInst = $('#leaveRequestsTable').DataTable({
        pageLength: 10,
        responsive: true,
        dom: 'tp',
        order: [[0, 'asc']],
        language: { paginate: { previous: '‹', next: '›' }, emptyTable: 'No leave requests found' },
    });

    const search = document.getElementById('leaveRequestSearch');
    if (search) {
        search.addEventListener('keyup', function () {
            leaveRequestsTableInst.search(this.value).draw();
        });
    }

    const statusFilter = document.getElementById('leaveRequestStatusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function () {
            const url = new URL(window.location.href);
            if (this.value === 'all') {
                url.searchParams.delete('status');
            } else {
                url.searchParams.set('status', this.value);
            }
            window.location.href = url.toString();
        });
    }
}

function confirmApproveLeave(btn) {
    const name = btn.dataset.name || 'this employee';
    Swal.fire({
        title: 'Approve leave?',
        text: `Approve leave request for "${name}"?`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#00843D',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Yes, approve',
    }).then((result) => {
        if (result.isConfirmed) submitBranchStatusForm(btn.dataset.url);
    });
}

function confirmRejectLeave(btn) {
    const name = btn.dataset.name || 'this employee';
    Swal.fire({
        title: 'Reject leave?',
        text: `Reject leave request for "${name}"?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Yes, reject',
    }).then((result) => {
        if (result.isConfirmed) submitBranchStatusForm(btn.dataset.url);
    });
}

function initLeaveRequestActions() {
    document.querySelectorAll('.leave-approve-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmApproveLeave(btn));
    });
    document.querySelectorAll('.leave-reject-btn').forEach((btn) => {
        btn.addEventListener('click', () => confirmRejectLeave(btn));
    });
}

function showAddLeaveTypeModal() {
    const el = document.getElementById('addLeaveTypeModal');
    if (el) new bootstrap.Modal(el).show();
}

/* Move modals to <body> so they are not trapped under backdrop (transform/stacking on #page-content) */
function moveModalsToBody() {
    document.querySelectorAll('#app-wrapper .modal, #page-content .modal').forEach((modal) => {
        if (modal.parentElement !== document.body) {
            document.body.appendChild(modal);
        }
    });
}

function hideSidebarOverlayForModal() {
    document.querySelectorAll('.modal').forEach((modal) => {
        modal.addEventListener('show.bs.modal', () => {
            const overlay = document.getElementById('sidebar-overlay');
            if (overlay) overlay.style.display = 'none';
        });
        modal.addEventListener('hidden.bs.modal', () => {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebar-overlay');
            if (overlay && sidebar && sidebar.classList.contains('mobile-open')) {
                overlay.style.display = '';
            }
        });
        modal.addEventListener('shown.bs.modal', () => initTeamDocumentFields(modal));
    });
}

function isIndiaNationality(value) {
    if (!value) return false;
    const normalized = value.trim().toLowerCase();
    return normalized === 'india' || normalized === 'republic of india';
}

function updateTeamDocumentSections(container) {
    if (!container) return;
    const form = container.closest('form');
    const india = container.querySelector('.team-documents-india');
    const gulf = container.querySelector('.team-documents-gulf');
    const common = container.querySelector('.team-documents-common');
    const hint = container.querySelector('.team-documents-hint');
    if (!india || !gulf || !common) return;

    let nationality = '';
    const branchSelect = form?.querySelector('select.team-branch-select');
    if (branchSelect && branchSelect.value) {
        const option = branchSelect.options[branchSelect.selectedIndex];
        nationality = option?.dataset?.nationality || '';
    }
    if (!nationality) {
        const natInput = form?.querySelector('input[name="nationality"]');
        if (natInput) nationality = natInput.value;
    }

    const showIndia = isIndiaNationality(nationality);
    const showGulf = Boolean(nationality) && !showIndia;
    const showDocs = showIndia || showGulf;

    india.classList.toggle('d-none', !showIndia);
    gulf.classList.toggle('d-none', !showGulf);
    common.classList.toggle('d-none', !showDocs);

    if (hint) {
        if (!nationality) {
            hint.textContent = 'Select a branch to see required uploads.';
        } else if (showIndia) {
            hint.textContent = 'Indian branch — upload Aadhaar card and offer letter.';
        } else {
            hint.textContent = 'Non-Indian branch — upload passport, Emirates ID, insurance, labour documents, and offer letter.';
        }
    }

    india.querySelectorAll('input').forEach((el) => {
        el.disabled = !showIndia;
        el.required = showIndia;
    });
    gulf.querySelectorAll('input').forEach((el) => {
        el.disabled = !showGulf;
        el.required = showGulf;
    });
    common.querySelectorAll('input').forEach((el) => {
        el.disabled = !showDocs;
        el.required = showDocs;
    });
}

function initTeamDocumentFields(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-team-documents]').forEach((container) => {
        const form = container.closest('form');
        if (container.dataset.docInit !== '1') {
            container.dataset.docInit = '1';
            const branchSelect = form?.querySelector('select.team-branch-select');
            const natInput = form?.querySelector('input[name="nationality"]');
            const refresh = () => updateTeamDocumentSections(container);
            if (branchSelect) branchSelect.addEventListener('change', refresh);
            if (natInput) natInput.addEventListener('input', refresh);
        }
        updateTeamDocumentSections(container);
    });
}

/* Page init */
document.addEventListener('DOMContentLoaded', () => {
    moveModalsToBody();
    hideSidebarOverlayForModal();
    initTeamDocumentFields();
    initPageTransitions();
    const page = document.body.dataset.page;
    if (page === 'profile') initProfilePhotoPreview();
    if (page === 'staff') {
        initStaffTable();
        initStaffActions();
        if (document.body.dataset.showStaffModal === 'true') showAddStaffModal();
        if (document.body.dataset.showStaffEditModal === 'true') {
            const el = document.getElementById('editStaffModal');
            if (el) {
                const basic = el.querySelector('[name="basic_salary"]');
                if (basic) recalcStaffTotal(basic);
                new bootstrap.Modal(el).show();
            }
        }
    }
    if (page === 'followup') {
        initFollowupTable();
        initFollowupActions();
        if (document.body.dataset.showTeamModal === 'true') showAddFollowupModal();
        if (document.body.dataset.showTeamEditModal === 'true') {
            const el = document.getElementById('editFollowupModal');
            if (el) new bootstrap.Modal(el).show();
        }
    }
    if (page === 'backoffice') {
        initBackofficeTable();
        initBackofficeActions();
        if (document.body.dataset.showTeamModal === 'true') showAddBackofficeModal();
        if (document.body.dataset.showTeamEditModal === 'true') {
            const el = document.getElementById('editBackofficeModal');
            if (el) new bootstrap.Modal(el).show();
        }
    }
    if (page === 'finance') {
        initFinanceTable();
        initFinanceActions();
        if (document.body.dataset.showTeamModal === 'true') showAddFinanceModal();
        if (document.body.dataset.showTeamEditModal === 'true') {
            const el = document.getElementById('editFinanceModal');
            if (el) new bootstrap.Modal(el).show();
        }
    }
    if (page === 'marketing') {
        initMarketingTable();
        initMarketingActions();
        if (document.body.dataset.showTeamModal === 'true') showAddMarketingModal();
        if (document.body.dataset.showTeamEditModal === 'true') {
            const el = document.getElementById('editMarketingModal');
            if (el) new bootstrap.Modal(el).show();
        }
    }
    if (page === 'dashboard') initDashboardCharts();
    if (document.querySelector('.lead-monitor-page')) {
        initLeadMonitorFilters();
        initLeadMonitorRows();
    }
    if (page === 'leads') {
        initLeadsTable();
    }
    if (page === 'branch_managers') {
        initBranchManagersTable();
        initBranchManagerActions();
        if (document.body.dataset.showManagerModal === 'true') showAddManagerModal();
        if (document.body.dataset.showManagerEditModal === 'true') {
            const el = document.getElementById('editBranchManagerModal');
            if (el) new bootstrap.Modal(el).show();
        }
    }
    if (page === 'branches') {
        initBranchesTable();
        initBranchActions();
        initBranchManagerToggle();
        if (document.body.dataset.showAddModal === 'true') showAddBranchModal();
        if (document.body.dataset.showEditModal === 'true') {
            const el = document.getElementById('editBranchModal');
            if (el) new bootstrap.Modal(el).show();
        }
        if (document.body.dataset.showManagerModal === 'true') showAddManagerModal();
    }
    if (page === 'leave_requests') {
        initLeaveRequestsTable();
        initLeaveRequestActions();
    }
    if (page === 'leave_types') {
        if (document.body.dataset.showLeaveTypeModal === 'true') showAddLeaveTypeModal();
    }
    if (page === 'leave_categories') {
        if (document.body.dataset.showLeaveCategoryModal === 'true') showAddLeaveCategoryModal();
    }
});

function showAddLeaveCategoryModal() {
    const el = document.getElementById('addLeaveCategoryModal');
    if (el) new bootstrap.Modal(el).show();
}
