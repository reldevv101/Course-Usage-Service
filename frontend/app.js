(() => {
  const root = document.getElementById("app");
  const API = (window.COURSE_USAGE_API_URL || "").replace(/\/$/, "");
  const TOKEN_KEY = "course_usage_access_token";
  const icons = { dashboard: "▦", courses: "▤", usage: "◷", invoices: "▧", students: "♙", account: "⚙" };
  const titles = { dashboard: "Ringkasan", courses: "Course", usage: "Penggunaan", invoices: "Tagihan", students: "Akun Mahasiswa", account: "Akun Saya" };
  let token = sessionStorage.getItem(TOKEN_KEY) || "";
  let currentUser = null;
  let notice = "";
  let noticeIsError = false;

  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
  const idr = (value) => new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(Number(value || 0));
  const date = (value) => value ? new Date(value).toLocaleString("id-ID", { dateStyle: "medium", timeStyle: "short" }) : "-";
  const isAdmin = () => currentUser?.role === "admin";
  const showNotice = (message, error = false) => { notice = message; noticeIsError = error; };
  const clearNotice = () => { notice = ""; noticeIsError = false; };

  async function api(path, options = {}) {
    const headers = { Accept: "application/json", ...(options.headers || {}) };
    if (token) headers.Authorization = `Bearer ${token}`;
    if (options.body !== undefined) headers["Content-Type"] = "application/json";
    const response = await fetch(`${API}${path}`, { ...options, headers, body: options.body === undefined ? undefined : JSON.stringify(options.body) });
    if (response.status === 401 && token) {
      logout(false);
      throw new Error("Sesi berakhir. Silakan login kembali.");
    }
    if (!response.ok) {
      let message = `Permintaan gagal (${response.status})`;
      try { message = (await response.json()).detail || message; } catch (_) { /* Keep the generic message. */ }
      throw new Error(message);
    }
    if (response.status === 204) return null;
    return response.json();
  }

  function renderLogin() {
    root.innerHTML = `
      <section class="login-wrap">
        <aside class="login-aside">
          <div class="brand"><span class="brand-mark">C</span><span>Course Usage Service</span></div>
          <div><h1>Belajar, tercatat dengan jelas.</h1><p>Catat pemakaian belajar, pantau aktivitas course, dan lihat rincian tagihan dalam satu tempat.</p></div>
          <div class="aside-foot">Layanan pembelajaran digital · Demo Cloud Computing</div>
        </aside>
        <section class="login-panel"><form id="login-form" class="login-card">
          <h2>Selamat datang</h2><p>Masuk memakai akun yang diberikan admin.</p>
          <div id="notice" class="notice ${noticeIsError ? "error" : ""}">${esc(notice)}</div>
          <div class="field"><label for="username">Username</label><input id="username" name="username" autocomplete="username" required minlength="3" /></div>
          <div class="field"><label for="password">Password</label><input id="password" name="password" type="password" autocomplete="current-password" required /></div>
          <button class="btn btn-primary btn-block" type="submit">Masuk</button>
          <p class="hint">Belum memiliki akun? Hubungi admin untuk dibuatkan akun.</p>
        </form></section>
      </section>`;
  }

  function navItems() {
    const items = ["dashboard", "courses", "usage", "invoices"];
    if (isAdmin()) items.push("students");
    items.push("account");
    return items;
  }

  function renderShell(page, body) {
    const nav = navItems().map((item) => `<button class="nav-item ${item === page ? "active" : ""}" data-nav="${item}"><span class="nav-icon">${icons[item]}</span>${titles[item]}</button>`).join("");
    root.innerHTML = `
      <div class="shell">
        <aside class="sidebar">
          <div class="brand"><span class="brand-mark">C</span><span>Course Usage</span></div>
          <div class="nav-label">Menu utama</div>
          <nav class="nav-list">${nav}</nav>
          <div class="sidebar-user"><div class="user-name">${esc(currentUser.username)}</div><div class="user-role">${esc(currentUser.role)}${currentUser.student_id ? ` · ${esc(currentUser.student_id)}` : ""}</div><button class="btn btn-secondary btn-small" data-action="logout">Keluar</button></div>
        </aside>
        <section class="main-area">
          <header class="topbar"><div><h1>${titles[page]}</h1><span class="topbar-sub">Course Usage Service</span></div><button class="btn btn-secondary btn-small" data-action="logout">Keluar</button></header>
          <main class="content"><div id="notice" class="notice ${noticeIsError ? "error" : ""}">${esc(notice)}</div>${body}</main>
        </section>
      </div>`;
  }

  function table(headers, rows, emptyText = "Belum ada data.") {
    if (!rows.length) return `<div class="empty">${esc(emptyText)}</div>`;
    return `<div class="table-wrap"><table><thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>`;
  }

  function stat(label, value) { return `<article class="stat-card"><div class="stat-label">${label}</div><div class="stat-value">${value}</div></article>`; }

  async function loadPage(page = "dashboard") {
    root.innerHTML = `<div class="loading-card">Memuat data…</div>`;
    try {
      let body = "";
      if (page === "dashboard") body = await dashboardPage();
      else if (page === "courses") body = await coursesPage();
      else if (page === "usage") body = await usagePage();
      else if (page === "invoices") body = await invoicesPage();
      else if (page === "students" && isAdmin()) body = studentsPage();
      else if (page === "account") body = accountPage();
      else body = await dashboardPage();
      renderShell(page, body);
    } catch (error) {
      showNotice(error.message, true);
      renderShell(page, `<section class="panel"><h2>Data belum dapat dimuat</h2><p>${esc(error.message)}</p><button class="btn btn-secondary" data-action="reload">Coba lagi</button></section>`);
    }
  }

  async function dashboardPage() {
    const [courses, usage, invoices] = await Promise.all([
      api("/api/v1/courses"), api("/api/v1/usage-records"), api("/api/v1/invoices"),
    ]);
    const totalCost = invoices.reduce((sum, invoice) => sum + Number(invoice.total_cost), 0);
    const title = isAdmin() ? "Selamat datang, Admin" : `Halo, ${esc(currentUser.username)}`;
    const subtitle = isAdmin() ? "Berikut ringkasan aktivitas seluruh course." : "Berikut ringkasan aktivitas dan tagihan Anda.";
    const recent = [...usage].sort((a, b) => new Date(b.recorded_at) - new Date(a.recorded_at)).slice(0, 5);
    const recentRows = recent.map((item) => `<tr><td>${esc(item.student_id)}</td><td>${esc(item.study_hours)} jam</td><td>${date(item.recorded_at)}</td><td>${esc(item.course_id.slice(0, 8))}…</td></tr>`);
    return `<section class="welcome"><h2>${title}</h2><p>${subtitle}</p></section>
      <section class="stats-grid">${stat("Course", courses.length)}${stat("Catatan penggunaan", usage.length)}${stat("Total tagihan", idr(totalCost))}</section>
      <section class="panel"><div class="panel-head"><h2>Penggunaan terbaru</h2><button class="btn btn-secondary btn-small" data-nav="usage">Lihat semua</button></div>
      ${table(["Mahasiswa", "Durasi belajar", "Waktu dicatat", "ID course"], recentRows, "Belum ada catatan penggunaan.")}</section>`;
  }

  async function coursesPage() {
    const courses = await api("/api/v1/courses");
    const rows = courses.map((course) => `<tr><td><strong>${esc(course.course_code)}</strong><div class="hint">${esc(course.name)}</div></td><td>${esc(course.description || "-")}</td><td><span class="badge ${course.is_active ? "" : "inactive"}">${course.is_active ? "Aktif" : "Nonaktif"}</span></td><td>${isAdmin() ? `<div class="table-actions"><button class="btn btn-secondary btn-small" data-action="edit-course" data-id="${esc(course.id)}">Ubah</button><button class="btn btn-danger btn-small" data-action="delete-course" data-id="${esc(course.id)}">Hapus</button></div>` : ""}</td></tr>`);
    const form = isAdmin() ? `<section class="panel"><div class="panel-head"><h2>Tambah course</h2></div><form id="course-form" class="inline-form">
      <div class="field"><label>Kode course</label><input name="course_code" maxlength="30" pattern="[A-Za-z0-9_-]+" required /></div>
      <div class="field"><label>Nama course</label><input name="name" maxlength="150" required /></div>
      <div class="field wide"><label>Deskripsi</label><textarea name="description"></textarea></div>
      <button class="btn btn-primary" type="submit">Simpan course</button></form></section>` : "";
    return `${form}<section class="panel"><div class="panel-head"><h2>Daftar course</h2><span class="hint">${courses.length} course</span></div>${table(["Course", "Deskripsi", "Status", "Aksi"], rows, "Belum ada course.")}</section>`;
  }

  async function usagePage() {
    const [usage, courses] = await Promise.all([api("/api/v1/usage-records"), api("/api/v1/courses?active=true")]);
    const invoices = isAdmin() ? await api("/api/v1/invoices") : [];
    const invoiced = new Set(invoices.map((item) => item.usage_record_id));
    const courseName = new Map(courses.map((item) => [item.id, item.name]));
    const rows = usage.map((item) => `<tr><td>${esc(item.student_id)}</td><td>${esc(courseName.get(item.course_id) || item.course_id.slice(0, 8))}</td><td>${esc(item.study_hours)} jam</td><td>${esc(item.material_accesses)}</td><td>${esc(item.quizzes_completed)}</td><td>${date(item.recorded_at)}</td><td>${isAdmin() && !invoiced.has(item.id) ? `<button class="btn btn-primary btn-small" data-action="make-invoice" data-id="${esc(item.id)}">Buat invoice</button>` : invoiced.has(item.id) ? `<span class="badge">Ditagihkan</span>` : ""}</td></tr>`);
    const courseOptions = courses.map((item) => `<option value="${esc(item.id)}">${esc(item.course_code)} · ${esc(item.name)}</option>`).join("");
    const studentField = isAdmin() ? `<div class="field"><label>ID mahasiswa</label><input name="student_id" placeholder="S001" required /></div>` : "";
    const form = `<section class="panel"><div class="panel-head"><h2>Catat penggunaan</h2></div><form id="usage-form" class="inline-form">
      ${studentField}<div class="field"><label>Course</label><select name="course_id" required><option value="">Pilih course</option>${courseOptions}</select></div>
      <div class="field"><label>Durasi belajar (jam)</label><input name="study_hours" type="number" min="0" step="0.01" value="0" required /></div>
      <div class="field"><label>Akses materi premium</label><input name="material_accesses" type="number" min="0" step="1" value="0" required /></div>
      <div class="field"><label>Kuis diselesaikan</label><input name="quizzes_completed" type="number" min="0" step="1" value="0" required /></div>
      <button class="btn btn-primary" type="submit">Simpan penggunaan</button></form></section>`;
    return `${form}<section class="panel"><div class="panel-head"><h2>${isAdmin() ? "Semua penggunaan" : "Riwayat penggunaan saya"}</h2><span class="hint">${usage.length} catatan</span></div>${table(["Mahasiswa", "Course", "Jam", "Materi", "Kuis", "Waktu", "Invoice"], rows, "Belum ada catatan penggunaan.")}</section>`;
  }

  async function invoicesPage() {
    const invoices = await api("/api/v1/invoices");
    const rows = invoices.map((item) => `<tr><td>${esc(item.student_id)}</td><td>${esc(item.course_id.slice(0, 8))}…</td><td>${esc(item.study_hours)} jam</td><td>${esc(item.material_accesses)}</td><td>${esc(item.quizzes_completed)}</td><td><strong>${idr(item.total_cost)}</strong></td><td>${date(item.created_at)}</td></tr>`);
    return `<section class="panel"><div class="panel-head"><h2>${isAdmin() ? "Semua invoice" : "Tagihan saya"}</h2><span class="hint">${invoices.length} invoice</span></div>${table(["Mahasiswa", "Course ID", "Jam", "Materi", "Kuis", "Total", "Dibuat"], rows, "Belum ada invoice.")}</section>`;
  }

  function studentsPage() {
    return `<section class="panel"><div class="panel-head"><h2>Buat akun mahasiswa</h2></div>
      <p>Akun mahasiswa akan dikaitkan dengan ID mahasiswa. Berikan password awal secara pribadi dan minta mahasiswa menggantinya setelah login.</p>
      <form id="student-form" class="inline-form">
        <div class="field"><label>Username</label><input name="username" minlength="3" maxlength="50" pattern="[A-Za-z0-9_.-]+" required /></div>
        <div class="field"><label>ID mahasiswa</label><input name="student_id" placeholder="S001" required /></div>
        <div class="field wide"><label>Password awal</label><input name="password" type="password" minlength="12" maxlength="128" required /><span class="hint">Minimal 12 karakter.</span></div>
        <button class="btn btn-primary" type="submit">Buat akun</button>
      </form></section>`;
  }

  function accountPage() {
    return `<section class="panel"><div class="panel-head"><h2>Informasi akun</h2></div>
      <p><strong>Username:</strong> ${esc(currentUser.username)}</p><p><strong>Role:</strong> ${esc(currentUser.role)}</p>
      ${currentUser.student_id ? `<p><strong>ID mahasiswa:</strong> ${esc(currentUser.student_id)}</p>` : ""}</section>
      <section class="panel"><div class="panel-head"><h2>Ganti password</h2></div><form id="password-form" class="inline-form">
        <div class="field wide"><label>Password saat ini</label><input name="current_password" type="password" autocomplete="current-password" required /></div>
        <div class="field wide"><label>Password baru</label><input name="new_password" type="password" minlength="12" autocomplete="new-password" required /><span class="hint">Minimal 12 karakter.</span></div>
        <button class="btn btn-primary" type="submit">Perbarui password</button>
      </form></section>`;
  }

  function logout(render = true) {
    token = "";
    currentUser = null;
    sessionStorage.removeItem(TOKEN_KEY);
    showNotice("Anda telah keluar.");
    if (render) renderLogin();
  }

  function formValue(form, name) { return form.elements.namedItem(name)?.value?.trim() || ""; }
  function intValue(form, name) { return Number.parseInt(formValue(form, name), 10) || 0; }

  root.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.target;
    try {
      clearNotice();
      if (form.id === "login-form") {
        const result = await api("/api/v1/auth/login", { method: "POST", body: { username: formValue(form, "username"), password: form.elements.password.value } });
        token = result.access_token;
        sessionStorage.setItem(TOKEN_KEY, token);
        currentUser = await api("/api/v1/auth/me");
        await loadPage("dashboard");
      } else if (form.id === "course-form") {
        await api("/api/v1/courses", { method: "POST", body: { course_code: formValue(form, "course_code"), name: formValue(form, "name"), description: formValue(form, "description") || null, is_active: true } });
        showNotice("Course berhasil ditambahkan."); await loadPage("courses");
      } else if (form.id === "usage-form") {
        const body = { course_id: formValue(form, "course_id"), study_hours: Number(formValue(form, "study_hours")), material_accesses: intValue(form, "material_accesses"), quizzes_completed: intValue(form, "quizzes_completed") };
        if (isAdmin()) body.student_id = formValue(form, "student_id");
        await api("/api/v1/usage-records", { method: "POST", body });
        showNotice("Penggunaan berhasil dicatat."); await loadPage("usage");
      } else if (form.id === "student-form") {
        await api("/api/v1/admin/students", { method: "POST", body: { username: formValue(form, "username"), student_id: formValue(form, "student_id"), password: form.elements.password.value } });
        showNotice("Akun mahasiswa berhasil dibuat."); await loadPage("students");
      } else if (form.id === "password-form") {
        await api("/api/v1/auth/password", { method: "PUT", body: { current_password: form.elements.current_password.value, new_password: form.elements.new_password.value } });
        showNotice("Password berhasil diperbarui."); await loadPage("account");
      }
    } catch (error) {
      showNotice(error.message, true);
      if (currentUser) await loadPage(form.id === "login-form" ? "dashboard" : document.querySelector(".nav-item.active")?.dataset.nav || "dashboard");
      else renderLogin();
    }
  });

  root.addEventListener("click", async (event) => {
    const nav = event.target.closest("[data-nav]");
    const actionButton = event.target.closest("[data-action]");
    if (nav) { clearNotice(); await loadPage(nav.dataset.nav); return; }
    if (!actionButton) return;
    const { action, id } = actionButton.dataset;
    if (action === "logout") { logout(); return; }
    if (action === "reload") { await loadPage(document.querySelector(".nav-item.active")?.dataset.nav || "dashboard"); return; }
    try {
      clearNotice();
      if (action === "delete-course") {
        if (!confirm("Hapus course ini? Course yang sudah memiliki riwayat penggunaan tidak dapat dihapus.")) return;
        await api(`/api/v1/courses/${encodeURIComponent(id)}`, { method: "DELETE" });
        showNotice("Course berhasil dihapus."); await loadPage("courses");
      } else if (action === "edit-course") {
        const courses = await api("/api/v1/courses");
        const course = courses.find((item) => item.id === id);
        if (!course) throw new Error("Course tidak ditemukan.");
        const name = prompt("Nama course:", course.name);
        if (name === null) return;
        const description = prompt("Deskripsi course:", course.description || "");
        if (description === null) return;
        const is_active = confirm("Pilih OK untuk mengaktifkan course. Pilih Cancel untuk menonaktifkan.");
        await api(`/api/v1/courses/${encodeURIComponent(id)}`, { method: "PATCH", body: { name, description, is_active } });
        showNotice("Course berhasil diperbarui."); await loadPage("courses");
      } else if (action === "make-invoice") {
        if (!confirm("Buat invoice untuk catatan penggunaan ini?")) return;
        await api("/api/v1/invoices", { method: "POST", body: { usage_record_id: id } });
        showNotice("Invoice berhasil dibuat."); await loadPage("usage");
      }
    } catch (error) {
      showNotice(error.message, true);
      await loadPage(document.querySelector(".nav-item.active")?.dataset.nav || "dashboard");
    }
  });

  async function start() {
    if (!API) { showNotice("Alamat API belum diatur di frontend/config.js.", true); renderLogin(); return; }
    if (!token) { renderLogin(); return; }
    try {
      currentUser = await api("/api/v1/auth/me");
      await loadPage("dashboard");
    } catch (_) {
      logout();
    }
  }

  start();
})();
