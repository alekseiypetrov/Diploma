// скрыть или показать поля с выбором дат
const radios = document.querySelectorAll('input[name="mode"]');
const rangeFields = document.querySelector('.range-fields');

radios.forEach(radio => {
    radio.addEventListener('change', () => {
        if (document.querySelector('input[name="mode"][value="range"]').checked) {
            rangeFields.style.display = 'block';
        } else {
            rangeFields.style.display = 'none';
        }
    });
});
