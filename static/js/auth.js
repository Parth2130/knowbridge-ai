// Authentication Handling for KnowBridge AI

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');
  const authAlert = document.getElementById('authAlert');

  function showAlert(msg, type = 'danger') {
    if (authAlert) {
      authAlert.className = `alert alert-${type}`;
      authAlert.innerText = msg;
      authAlert.classList.remove('d-none');
    }
  }

  function hideAlert() {
    if (authAlert) {
      authAlert.classList.add('d-none');
    }
  }

  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert();

      const email = document.getElementById('loginEmail').value.trim();
      const password = document.getElementById('loginPassword').value;
      const submitBtn = loginForm.querySelector('button[type="submit"]');

      if (!email || !password) {
        showAlert('Please provide both your email address and password.');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Signing In...';

      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (res.ok) {
          showAlert('Login successful! Redirecting...', 'success');
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 600);
        } else {
          showAlert(data.error || 'Failed to authenticate. Please check your credentials.');
          submitBtn.disabled = false;
          submitBtn.innerHTML = 'Sign In';
        }
      } catch (err) {
        showAlert('Network error: ' + err.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Sign In';
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert();

      const full_name = document.getElementById('regName').value.trim();
      const email = document.getElementById('regEmail').value.trim();
      const organisation = document.getElementById('regOrg').value.trim();
      const password = document.getElementById('regPassword').value;
      const confirm_password = document.getElementById('regConfirmPassword').value;
      const role = document.getElementById('regRole') ? document.getElementById('regRole').value : 'Project Manager';
      const submitBtn = registerForm.querySelector('button[type="submit"]');

      if (!full_name || !email || !organisation || !password) {
        showAlert('All fields are required.');
        return;
      }

      if (password !== confirm_password) {
        showAlert('Passwords do not match. Please re-enter.');
        return;
      }

      if (password.length < 6) {
        showAlert('Password must contain at least 6 characters.');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating Account...';

      try {
        const res = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            full_name,
            email,
            organisation,
            password,
            confirm_password,
            role
          })
        });
        const data = await res.json();

        if (res.ok) {
          showAlert('Account created successfully! Redirecting to dashboard...', 'success');
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 800);
        } else {
          showAlert(data.error || 'Registration failed.');
          submitBtn.disabled = false;
          submitBtn.innerHTML = 'Create Account';
        }
      } catch (err) {
        showAlert('Network error: ' + err.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Create Account';
      }
    });
  }
});
