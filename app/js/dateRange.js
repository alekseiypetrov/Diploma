// установка диапазона дат
document.addEventListener('DOMContentLoaded', function () {
    const rangeFields = document.querySelector('.range-fields');
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');

    // Установить диапазон дат
    const today = new Date();
    const currentYear = today.getFullYear();
    const currentMonth = today.getMonth() + 1;
    const minYear = currentYear - 1;
    const maxYear = currentYear;

    const formatDate = (year, month) => `${year}-${month.toString().padStart(2, '0')}`;

    const minDate = formatDate(minYear, 1);
    const maxDate = formatDate(maxYear, currentMonth);

    startDateInput.setAttribute('min', minDate);
    startDateInput.setAttribute('max', maxDate);
    endDateInput.setAttribute('min', minDate);
    endDateInput.setAttribute('max', maxDate);

    // Скрыть rangeFields по умолчанию
    rangeFields.style.display = 'none';
});