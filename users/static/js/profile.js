// Функция для получения CSRF-токена из cookie
function getCSRFToken() {
    let cookieValue = null;
    let cookies = document.cookie.split(";");

    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.startsWith("csrftoken=")) {
            cookieValue = cookie.substring("csrftoken=".length);
            break;
        }
    }
    return cookieValue;
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".cancel-booking").forEach(button => {
        button.addEventListener("click", function () {
            let bookingId = this.dataset.id;
            console.log("Нажата кнопка отмены для бронирования ID:", bookingId);

            if (confirm("Вы уверены, что хотите отменить бронирование?")) {
                let csrfToken = getCSRFToken();
                let requestData = JSON.stringify({ booking_id: bookingId });

                console.log("Отправляемый JSON:", requestData);
                console.log("CSRF-токен:", csrfToken);

                fetch("/api/cancel_booking/", {
                    method: "DELETE",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken,
                    },
                    body: requestData,
                })
                .then(response => response.json())
                .then(data => {
                    console.log("Ответ сервера:", data);
                    if (data.success) {
                        document.getElementById(`booking-${bookingId}`).remove();
                        alert("Бронирование отменено!");
                    } else {
                        alert("Ошибка: " + data.error);
                    }
                })
                .catch(error => console.error("Ошибка:", error));
            }
        });
    });
});
