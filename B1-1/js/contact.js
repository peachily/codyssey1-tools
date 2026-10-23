import { config } from './config.js';
export function validateField(name, value) {
  const text = value.trim();
  if (!text) return { name: '이름을 입력해 주세요.', email: '이메일을 입력해 주세요.', message: '메시지를 입력해 주세요.' }[name];
  if (name === 'name' && text.length > 80) return '이름은 80자 이하로 입력해 주세요.';
  if (name === 'email' && (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(text) || text.length > 254)) return '올바른 이메일 주소를 입력해 주세요.';
  if (name === 'message' && (text.length < 10 || text.length > 5000)) return '메시지는 10자 이상 5,000자 이하로 입력해 주세요.';
  return '';
}
export function isFormEndpoint(value) {
  try { const url = new URL(value); return url.origin === 'https://formspree.io' && /^\/f\/[a-zA-Z0-9]+$/.test(url.pathname) && !url.search && !url.hash && !url.username && !url.password; }
  catch { return false; }
}
export function initContact() {
  const form = document.querySelector('#contact-form');
  const status = document.querySelector('#contact-status');
  const button = form.querySelector('[type="submit"]');
  const fields = [...form.querySelectorAll('input, textarea')];
  const state = { phase: 'idle', errors: {}, message: '' };
  function render() {
    fields.forEach(field => {
      const error = state.errors[field.name] || '';
      field.setAttribute('aria-invalid', String(Boolean(error)));
      document.querySelector(`#${field.name}-error`).textContent = error;
      field.disabled = state.phase === 'sending';
    });
    button.disabled = state.phase === 'sending';
    form.setAttribute('aria-busy', String(state.phase === 'sending'));
    status.dataset.state = state.phase;
    status.textContent = state.message;
  }
  fields.forEach(field => {
    field.addEventListener('input', () => {
      state.errors[field.name] = validateField(field.name, field.value);
      if (state.phase === 'success') { state.phase = 'idle'; state.message = ''; }
      render();
    });
    field.addEventListener('blur', () => { state.errors[field.name] = validateField(field.name, field.value); render(); });
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (state.phase === 'sending') return;
    fields.forEach(field => { state.errors[field.name] = validateField(field.name, field.value); });
    const invalid = fields.find(field => state.errors[field.name]);
    if (invalid) {
      state.phase = 'error'; state.message = '입력 내용을 확인해 주세요.'; render(); invalid.focus(); return;
    }
    if (!isFormEndpoint(config.formEndpoint)) {
      state.phase = 'error'; state.message = '메시지가 전송되지 않았습니다. 잠시 후 다시 시도해 주세요.'; render(); return;
    }
    const body = Object.fromEntries(fields.map(field => [field.name, field.value.trim()]));
    state.phase = 'sending'; state.message = '메시지를 보내고 있습니다…'; render();
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(config.formEndpoint, { method: 'POST', headers: { Accept: 'application/json', 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal: controller.signal });
      if (!response.ok) throw new Error('send-failed');
      state.phase = 'success'; state.message = '메시지가 전송되었습니다.';
      state.errors = {}; form.reset();
    } catch (error) {
      state.phase = 'error'; state.message = error.name === 'AbortError' ? '전송 응답을 확인하지 못했습니다. 중복 전송을 피하려면 잠시 후 확인하거나 이메일로 연락해 주세요.' : '전송하지 못했습니다. 입력 내용은 보존됩니다. 잠시 후 다시 시도하거나 이메일로 연락해 주세요.';
    } finally { clearTimeout(timeout); render(); }
  });
  render();
}
