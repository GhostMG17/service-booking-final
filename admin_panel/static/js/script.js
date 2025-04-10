document.addEventListener("DOMContentLoaded", function () {
    console.log("JavaScript загружен!"); // Проверяем загрузку

    function confirmStatusChange(button, status) {
        const messages = {
            "confirmed": "Вы уверены, что хотите подтвердить бронирование?",
            "completed": "Вы уверены, что хотите завершить бронирование?",
            "canceled": "Вы уверены, что хотите отменить бронирование?"
        };

        if (confirm(messages[status])) {
            const form = button.closest("form");
            form.querySelector("input[name='status']").value = status;
            form.submit();

            // ❌ Если статус "отменено", скрываем кнопки
            if (status === "canceled") {
                const actionsContainer = form.closest("td");
                actionsContainer.innerHTML = `<span class="canceled-text">❌ Отменено</span>`;
            }
        }
    }

    document.querySelectorAll(".status-form button").forEach(button => {
        button.addEventListener("click", function () {
            const status = this.classList.contains("btn-confirmed") ? "confirmed" :
                           this.classList.contains("btn-completed") ? "completed" :
                           "canceled";
            confirmStatusChange(this, status);
        });
    });
});
