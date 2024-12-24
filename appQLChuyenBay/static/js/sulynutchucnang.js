// Gọi API để kiểm tra vai trò người dùng
async function checkUserRole() {
    const response = await fetch('/api/user/roles');  // Gọi API kiểm tra vai trò
    const result = await response.json();  // Lấy kết quả trả về dưới dạng JSON

    if (result === true) {  // Nếu trả về true, hiển thị nút
        document.getElementById("change-info-btn").style.display = "block";
    } else {  // Nếu không, ẩn nút
        document.getElementById("change-info-btn").style.display = "none";
    }
}

// Chạy hàm kiểm tra vai trò khi trang tải
document.addEventListener("DOMContentLoaded", function() {
    checkUserRole();  // Kiểm tra vai trò người dùng ngay khi trang tải xong
});
