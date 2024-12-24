// Tạo sự kiện thanh aside
const sideMenu = document.querySelector('aside');
const menuBtn = document.querySelector('#menu_bar');
const closeBtn = document.querySelector('#close_btn');
const themeToggler = document.querySelector('.theme-toggler');

//menuBtn.addEventListener('click', () => {
//    sideMenu.style.display = "block";
//});
//
//closeBtn.addEventListener('click', () => {
//    sideMenu.style.display = "none";
//});

 // Chuyển đổi Light/Dark Mode
    if (themeToggler) {
        themeToggler.addEventListener('click', () => {
            document.body.classList.toggle('dark-theme-variables');

            const span1 = themeToggler.querySelector('span:nth-child(1)');
            const span2 = themeToggler.querySelector('span:nth-child(2)');

            if (span1) span1.classList.toggle('active');
            if (span2) span2.classList.toggle('active');
        });
}

// Hàm cập nhật giờ tự động sau khi load lại page

window.onload = function() {
    var now = new Date();
    var localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString();
    localDateTime = localDateTime.slice(0, 16); // Cắt chuỗi để loại bỏ giây và phần mili giây
    document.getElementById('realtime-calendar').value = localDateTime;
};

// Hàm tạo animation cho các giá trị phần trăm
function animateValue(obj, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.textContent = (progress * (end - start) + start).toFixed(2) + '%';
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Hàm khởi tạo animation cho các giá trị phần trăm
function animatePercentages() {
    const revenuePct = document.querySelector('.sale .number');
    const flightsPct = document.querySelector('.expenses .number');
    const hoursPct = document.querySelector('.income .number');


    // Lấy giá trị phần trăm thực từ các biến Flask đã được tính toán và truyền vào
    animateValue(revenuePct, 0, 80, 2000);
    animateValue(flightsPct, 0, 100 , 2000);
    animateValue(hoursPct, 0, 100, 2000);
}