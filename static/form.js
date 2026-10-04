const form = document.querySelector('form[data-request-form]');
if (form) {
  const problem = form.querySelector('[name="problem"]');
  const count = document.querySelector('#problem-count');
  const updateCount = () => { count.textContent = `${problem.value.length} / 2000`; };
  problem.addEventListener('input', updateCount);
  updateCount();
  form.addEventListener('submit', () => {
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = 'Сохранение…';
  });
  window.addEventListener('pageshow', () => {
    const button = form.querySelector('button[type="submit"]');
    button.disabled = false;
    button.textContent = button.dataset.label;
  });
}
