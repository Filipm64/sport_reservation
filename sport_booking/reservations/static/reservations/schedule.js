(() => {
  const form = document.querySelector('#booking-form');
  if (!form) return;
  const boxes = [...form.querySelectorAll('input[name="selected_blocks"]')];
  const summary = form.querySelector('#slot-summary');
  const manual = form.querySelector('#manual-panel');
  const schedule = form.querySelector('#schedule-panel');
  const start = form.querySelector('[name="starts_at"]');
  const end = form.querySelector('[name="ends_at"]');
  const selected = () => boxes.filter(box => box.checked).sort((a, b) => Date.parse(a.dataset.start) - Date.parse(b.dataset.start));
  const valid = items => items.length <= 2 && (items.length < 2 || items[0].dataset.end === items[1].dataset.start && items[0].dataset.day === items[1].dataset.day);
  function updateSummary() {
    const items = selected();
    summary.textContent = items.length
      ? `Vybráno: ${items.map(item => item.dataset.label).join(' + ')} · ${items.length === 1 ? '1 hodina' : '2 hodiny'}`
      : 'Vyberte jeden nebo dva navazující bloky. Maximum jsou 2 hodiny.';
    summary.classList.toggle('has-selection', items.length > 0);
  }
  boxes.forEach(box => box.addEventListener('change', () => {
    if (!valid(selected())) {
      box.checked = false;
      summary.textContent = 'Vyberte nejvýše 2 bloky, které na sebe navazují.';
      return;
    }
    updateSummary();
  }));
  function changeMode() {
    const slots = form.querySelector('[name="selection_mode"]:checked')?.value === 'slots';
    manual.hidden = slots;
    schedule.hidden = !slots;
    start.disabled = slots;
    end.disabled = slots;
    start.required = !slots;
    end.required = !slots;
    boxes.forEach(box => {
      if (!box.closest('.week-slot-disabled')) box.disabled = !slots;
    });
    updateSummary();
  }
  form.querySelectorAll('[name="selection_mode"]').forEach(radio => radio.addEventListener('change', changeMode));
  form.addEventListener('submit', event => {
    const slots = form.querySelector('[name="selection_mode"]:checked')?.value === 'slots';
    if (slots && (!selected().length || !valid(selected()))) {
      event.preventDefault();
      summary.textContent = 'Nejprve vyberte 1 nebo 2 navazující hodinové bloky.';
      (boxes.find(box => !box.disabled) || summary).focus();
    }
  });
  const filter = document.querySelector('#schedule-filter');
  filter?.querySelectorAll('select, input').forEach(field => field.addEventListener('change', () => filter.requestSubmit()));
  changeMode();
})();
