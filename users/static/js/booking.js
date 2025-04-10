$(document).ready(function () {
    function loadServices() {
        $("#service-spinner").removeClass("d-none");
        $.get("/api/services/", function (data) {
            $("#service").html('<option value="">Выберите услугу</option>');
            data.forEach(service => {
                $("#service").append(`<option value="${service.id}">${service.name}</option>`);
            });
        }).fail(() => {
            $("#service").html('<option value="">Ошибка загрузки услуг</option>');
        }).always(() => {
            $("#service-spinner").addClass("d-none");
        });
    }

    function loadMasters(serviceId) {
        if (!serviceId) return;
        $("#master-spinner").removeClass("d-none");
        $.get(`/api/masters/?service_id=${serviceId}`, function (data) {
            $("#master").html('<option value="">Выберите мастера</option>');
            data.forEach(master => {
                $("#master").append(`<option value="${master.id}">${master.name}</option>`);
            });
        }).fail(() => {
            $("#master").html('<option value="">Ошибка загрузки мастеров</option>');
        }).always(() => {
            $("#master-spinner").addClass("d-none");
        });
    }

    function loadSlots(serviceId, masterId, date) {
        if (!serviceId || !masterId || !date) return;
        $("#time-spinner").removeClass("d-none");
        $.get(`/api/available-slots/?service_id=${serviceId}&master_id=${masterId}&date=${date}`, function (data) {
            $("#time").html("");
            if (data.available_slots.length > 0) {
                data.available_slots.forEach(slot => {
                    $("#time").append(`<option value="${slot}">${slot}</option>`);
                });
            } else {
                $("#time").html('<option value="">Нет доступных слотов</option>');
            }
        }).fail(() => {
            $("#time").html('<option value="">Ошибка загрузки слотов</option>');
        }).always(() => {
            $("#time-spinner").addClass("d-none");
        });
    }

    function submitBooking(event) {
        event.preventDefault();

        let masterId = $("#master").val();
        let serviceId = $("#service").val();
        let date = $("#date").val();
        let time = $("#time").val();

        if (!masterId || !serviceId || !date || !time) {
            $("#message").html("<p class='text-danger'>Заполните все поля!</p>");
            return;
        }

        let submitButton = $("button[type='submit']");
        submitButton.prop("disabled", true).text("Загрузка...");

        $.ajax({
            url: "/api/create_booking/",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ service_id: serviceId, master_id: masterId, date: date, time: time }),
            success: function () {
                $("#message").html("<p class='text-success'>Бронирование успешно!</p>");
            },
            error: function (xhr) {
                let errorMessage = xhr.responseJSON?.error || "Ошибка бронирования!";
                $("#message").html(`<p class='text-danger'>${errorMessage}</p>`);
            },
            complete: function () {
                submitButton.prop("disabled", false).text("Забронировать");
            }
        });
    }

    function loadTopBarbers() {
        fetch("/top-masters/")
            .then(response => response.json())
            .then(data => {
                const container = $("#top-barbers");
                container.empty();

                data.forEach(master => {
                    const masterCard = `
                        <div class="card m-2 shadow-sm text-center p-3" style="width: 12rem;">
                            <h5 class="card-title">${master.name}</h5>
                            <p class="card-text">⭐ ${master.rating.toFixed(1)}</p>
                        </div>`;
                    container.append(masterCard);
                });
            })
            .catch(() => console.error("Ошибка загрузки топ-мастеров"));
    }

    // Инициализация
    loadServices();
    loadTopBarbers();

    // Обработчики событий
    $("#service").change(() => loadMasters($("#service").val()));
    $("#master, #date").change(() => loadSlots($("#service").val(), $("#master").val(), $("#date").val()));
    $("#booking-form").submit(submitBooking);
});
