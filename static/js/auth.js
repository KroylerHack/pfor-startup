/**
 * PFOR Platform — Authentication Module
 * Handles JWT token storage, user session management,
 * and auth modal interactions (login / register tabs).
 */

const API_BASE = window.location.origin;
const TOKEN_KEY = 'pfor_access_token';
const USER_KEY = 'pfor_user';

function saveSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function getCurrentUser() {
  const raw = localStorage.getItem(USER_KEY);
  try {
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function isAuthenticated() {
  return !!getToken();
}

function updateNavbarAuthState() {
  const loginBtn = document.getElementById('nav-login-btn');
  const registerBtn = document.getElementById('nav-register-btn');
  const logoutBtn = document.getElementById('nav-logout-btn');
  const userBadge = document.getElementById('nav-user-badge');
  const userEmail = document.getElementById('nav-user-email');

  const user = getCurrentUser();

  if (user && isAuthenticated()) {
    loginBtn && loginBtn.classList.add('hidden');
    registerBtn && registerBtn.classList.add('hidden');
    logoutBtn && logoutBtn.classList.remove('hidden');
    userBadge && userBadge.classList.remove('hidden');
    if (userEmail) userEmail.textContent = user.email;
  } else {
    loginBtn && loginBtn.classList.remove('hidden');
    registerBtn && registerBtn.classList.remove('hidden');
    logoutBtn && logoutBtn.classList.add('hidden');
    userBadge && userBadge.classList.add('hidden');
  }
}

function openAuthModal(tab = 'login') {
  const overlay = document.getElementById('auth-modal-overlay');
  overlay && overlay.classList.remove('hidden');
  switchAuthTab(tab);
  clearAuthErrors();
}

function closeAuthModal() {
  const overlay = document.getElementById('auth-modal-overlay');
  overlay && overlay.classList.add('hidden');
  clearAuthErrors();
}

function switchAuthTab(tab) {
  const loginTab = document.getElementById('tab-login');
  const registerTab = document.getElementById('tab-register');
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');

  if (tab === 'login') {
    loginTab && loginTab.classList.add('active');
    registerTab && registerTab.classList.remove('active');
    loginForm && loginForm.classList.remove('hidden');
    registerForm && registerForm.classList.add('hidden');
  } else {
    registerTab && registerTab.classList.add('active');
    loginTab && loginTab.classList.remove('active');
    registerForm && registerForm.classList.remove('hidden');
    loginForm && loginForm.classList.add('hidden');
  }
}

function clearAuthErrors() {
  document.querySelectorAll('.form-error').forEach(el => el.classList.remove('visible'));
}

async function apiRegister(email, password) {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Registration failed.');
  }
  return data;
}

async function apiLogin(email, password) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Login failed.');
  }
  return data;
}

async function handleLogin(event) {
  event.preventDefault();
  clearAuthErrors();

  const emailInput = document.getElementById('login-email');
  const passInput = document.getElementById('login-password');
  const submitBtn = document.getElementById('login-submit');
  const errorEl = document.getElementById('login-error');

  const email = emailInput.value.trim();
  const password = passInput.value;

  if (!email || !password) {
    showFormError(errorEl, 'Please enter email and password.');
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Signing in…';

  try {
    const data = await apiLogin(email, password);
    saveSession(data.access_token, data.user);
    updateNavbarAuthState();
    closeAuthModal();
    showToast('Welcome back! 👋', 'success');
  } catch (err) {
    showFormError(errorEl, err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Sign In';
  }
}

async function handleRegister(event) {
  event.preventDefault();
  clearAuthErrors();

  const emailInput = document.getElementById('register-email');
  const passInput = document.getElementById('register-password');
  const submitBtn = document.getElementById('register-submit');
  const errorEl = document.getElementById('register-error');

  const email = emailInput.value.trim();
  const password = passInput.value;

  if (!email || !password) {
    showFormError(errorEl, 'Please enter email and password.');
    return;
  }

  if (password.length < 6) {
    showFormError(errorEl, 'Password must be at least 6 characters.');
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Creating account…';

  try {
    const data = await apiRegister(email, password);
    saveSession(data.access_token, data.user);
    updateNavbarAuthState();
    closeAuthModal();
    showToast('Account created successfully!', 'success');
  } catch (err) {
    showFormError(errorEl, err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Create account';
  }
}

function showFormError(el, message) {
  if (!el) return;
  el.textContent = message;
  el.classList.add('visible');
}

function bindAuthEvents() {
  document.getElementById('nav-login-btn')?.addEventListener('click', () => openAuthModal('login'));
  document.getElementById('nav-register-btn')?.addEventListener('click', () => openAuthModal('register'));
  document.getElementById('nav-logout-btn')?.addEventListener('click', () => {
    clearSession();
    updateNavbarAuthState();
    showToast('Logged out successfully.', 'info');
  });

  document.getElementById('tab-login')?.addEventListener('click', () => switchAuthTab('login'));
  document.getElementById('tab-register')?.addEventListener('click', () => switchAuthTab('register'));
  document.getElementById('login-form')?.addEventListener('submit', handleLogin);
  document.getElementById('register-form')?.addEventListener('submit', handleRegister);
  document.getElementById('modal-close-btn')?.addEventListener('click', closeAuthModal);
  document.getElementById('auth-modal-overlay')?.addEventListener('click', (event) => {
    if (event.target.id === 'auth-modal-overlay') closeAuthModal();
  });
}

document.addEventListener('DOMContentLoaded', () => {
  bindAuthEvents();
  updateNavbarAuthState();
});
