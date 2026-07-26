document.addEventListener('DOMContentLoaded', () => {
    // Staggered reveal
    const reveals = document.querySelectorAll('.reveal');
    reveals.forEach((el, idx) => {
        setTimeout(() => {
            el.classList.add('visible');
        }, 150 + idx * 100);
    });

    // Colab / Backend health check
    const colabBanner = document.getElementById('colab-banner');
    if (colabBanner) {
        fetch('/api/health-colab')
            .then(res => res.json())
            .then(data => {
                if (data.status !== 'online') {
                    colabBanner.classList.remove('hidden');
                }
            })
            .catch(() => {
                colabBanner.classList.remove('hidden');
            });
    }
});
