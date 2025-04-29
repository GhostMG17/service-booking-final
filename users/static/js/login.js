document.querySelectorAll('.toggle-password').forEach(button => {
    button.addEventListener('click', function() {
        const container = this.closest('.password-input-container');
        const input = container.querySelector('input');
        const icon = this.querySelector('i');

        // Переключаем тип поля
        input.type = input.type === 'password' ? 'text' : 'password';

        // Меняем иконку
        icon.classList.toggle('fa-eye');
        icon.classList.toggle('fa-eye-slash');

        // Добавляем анимацию
        this.style.transform = 'translateY(-50%) scale(1.1)';
        setTimeout(() => {
            this.style.transform = 'translateY(-50%)';
        }, 200);
    });
});