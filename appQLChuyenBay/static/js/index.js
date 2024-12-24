$(document).ready(function () {
    const today = new Date().toISOString().split('T')[0];
    $('#ThoiGian').attr('min', today);

    // Kiểm tra cookie và điền giá trị cho ô 'SanBayDi'
    if ($.cookie('SanBayDi')) {
        $('#SanBayDi').val($.cookie('SanBayDi'));
    } else {
        // Nếu không có cookie, kiểm tra nếu ô trống, nếu trống điền giá trị mặc định
        if ($('#SanBayDi').val() === '') {
            $('#SanBayDi').val('Tân Sơn Nhất (Thành phố Hồ Chí Minh)');
        }
    }

    // Kiểm tra cookie và điền giá trị cho ô 'SanBayDen'
    if ($.cookie('SanBayDen')) {
        $('#SanBayDen').val($.cookie('SanBayDen'));
    } else {
        // Nếu không có cookie, kiểm tra nếu ô trống, nếu trống điền giá trị mặc định
        if ($('#SanBayDen').val() === '') {
            $('#SanBayDen').val('Nội Bài (Hà Nội)');
        }
    }

    // Sự kiện khi người dùng click ra ngoài ô input
    $('#SanBayDi').on('blur', function() {
        // Kiểm tra nếu ô trống và tự điền giá trị mặc định
        if ($(this).val() === '') {
            $(this).val('Tân Sơn Nhất (Thành phố Hồ Chí Minh)');
        }
    });

    $('#SanBayDen').on('blur', function() {
        // Kiểm tra nếu ô trống và tự điền giá trị mặc định
        if ($(this).val() === '') {
            $(this).val('Nội Bài (Hà Nội)');
        }
    });
});

$(document).ready(function () {
            $("#btnSearchForFlights").click(function (event) {
                event.preventDefault();
                var flag = true;
                if ($("#ThoiGian").val() === '') {
                    flag = false;
                }
                if (flag) {
                    $('#btnSearchForFlights').empty();
                    $('#btnSearchForFlights').append('đang xử lý...');
                    $(".search-form").submit();
                    return true;
                } else {
                    alert("Vui lòng chọn ngày bay...");
                    return false;
                }
            });
        });

// script.js
$(document).ready(function () {
    const $input = $("#SanBayDi");
    const $dropdown = $("#dropdown-results");

    // Lấy dữ liệu từ API
    let sampleData = [];
    $.ajax({
        url: "/api/get_sanbay", // Địa chỉ API
        method: "GET",
        success: function (data) {
            // Dữ liệu trả về từ API
            sampleData = data.map(item => `${item.ten_SanBay}`);
        },
        error: function () {
            console.error("Không thể tải dữ liệu từ API.");
        }
    });

    // Function to filter results
    function filterResults(query) {
        return sampleData.filter(item =>
            item.toLowerCase().includes(query.toLowerCase())
        );
    }

    // Event listener for input
    $input.on("input", function () {
        const query = $(this).val();

        // Clear dropdown if query is empty
        if (!query) {
            $dropdown.empty().hide();
            return;
        }

        // Filter results and populate dropdown
        const results = filterResults(query);
        if (results.length) {
            $dropdown.empty().show();
            results.forEach(item => {
                $dropdown.append(`<li>${item}</li>`);
            });
        } else {
            $dropdown.empty().hide();
        }
    });

    // Event listener for selecting a dropdown item
    $dropdown.on("click", "li", function () {
        const selectedItem = $(this).text();
        $input.val(selectedItem);
        $dropdown.empty().hide();
    });

    // Hide dropdown when clicking outside
    $(document).on("click", function (e) {
        if (!$(e.target).closest(".search-container").length) {
            $dropdown.empty().hide();
        }
    });
});

$(document).ready(function () {
    const $input = $("#SanBayDen");
    const $dropdown = $("#dropdown-results-den");

    // Lấy dữ liệu từ API
    let sampleData = [];
    $.ajax({
        url: "/api/get_sanbay", // Địa chỉ API
        method: "GET",
        success: function (data) {
            // Dữ liệu trả về từ API
            sampleData = data.map(item => `${item.ten_SanBay}`);
        },
        error: function () {
            console.error("Không thể tải dữ liệu từ API.");
        }
    });

    // Function to filter results
    function filterResults(query) {
        return sampleData.filter(item =>
            item.toLowerCase().includes(query.toLowerCase())
        );
    }

    // Event listener for input
    $input.on("input", function () {
        const query = $(this).val();

        // Clear dropdown if query is empty
        if (!query) {
            $dropdown.empty().hide();
            return;
        }

        // Filter results and populate dropdown
        const results = filterResults(query);
        if (results.length) {
            $dropdown.empty().show();
            results.forEach(item => {
                $dropdown.append(`<li>${item}</li>`);
            });
        } else {
            $dropdown.empty().hide();
        }
    });

    // Event listener for selecting a dropdown item
    $dropdown.on("click", "li", function () {
        const selectedItem = $(this).text();
        $input.val(selectedItem);
        $dropdown.empty().hide();
    });

    // Hide dropdown when clicking outside
    $(document).on("click", function (e) {
        if (!$(e.target).closest(".search-container").length) {
            $dropdown.empty().hide();
        }
    });
});

document.addEventListener('DOMContentLoaded', function () {
    // Lấy tất cả các nút cộng và trừ
    const buttons = document.querySelectorAll('.signa');

    // Lặp qua các nút để thêm sự kiện
    buttons.forEach(button => {
        button.addEventListener('click', function () {
            // Tìm input gần nhất liên quan đến nút được bấm
            const input = this.parentElement.querySelector('input');
            let value = parseInt(input.value) || 0; // Lấy giá trị hiện tại, mặc định là 0 nếu không hợp lệ
            const parent = this.closest('.col-sm-3'); // Giả sử mỗi nhóm có class "col-sm-3" để phân biệt nhóm người lớn/trẻ em/em bé

            if (parent && parent.querySelector('.block-label').textContent.includes('Người lớn')) {
                // Nếu là người lớn, không cho phép giá trị nhỏ hơn 1
                if (this.classList.contains('plus')) {
                    input.value = value + 1;
                } else if (this.classList.contains('minus')) {
                    if (value > 1) {
                        input.value = value - 1;
                    }
                }
            } else if (parent && parent.querySelector('.block-label').textContent.includes('Trẻ em')) {
                // Nếu là trẻ em, cho phép giá trị giảm xuống 0 nhưng không âm
                if (this.classList.contains('plus')) {
                    input.value = value + 1;
                } else if (this.classList.contains('minus')) {
                    if (value > 0) {
                        input.value = value - 1;
                    }
                }
            } else if (parent && parent.querySelector('.block-label').textContent.includes('Em bé')) {
                // Nếu là em bé, cho phép giá trị giảm xuống 0 nhưng không âm
                if (this.classList.contains('plus')) {
                    input.value = value + 1;
                } else if (this.classList.contains('minus')) {
                    if (value > 0) {
                        input.value = value - 1;
                    }
                }
            }
        });
    });
});



//slides
const listImage = document.querySelector('.list-images');
const imgs = document.querySelectorAll('.list-images img');
const btnLeft = document.querySelector('.btn-left');
const btnRight = document.querySelector('.btn-right');
const length = imgs.length;
let current = 0;

// Lấy chiều rộng của ảnh tại chỉ số "current"
const getCurrentImageWidth = () => imgs[current].offsetWidth;

// Cập nhật vị trí slide
const updateSlidePosition = () => {
    let offset = 0;
    for (let i = 0; i < current; i++) {
        offset += imgs[i].offsetWidth; // Tính tổng chiều rộng các ảnh trước ảnh hiện tại
    }
    listImage.style.transform = `translateX(${-offset}px)`;
};

// Xử lý chuyển slide tự động
const handleChangeSlide = () => {
    if (current === length - 1) {
        current = 0; // Quay về ảnh đầu tiên
    } else {
        current++;
    }
    updateSlidePosition();
};

// Thiết lập tự động thay đổi slide
let handleEventChangeSlide = setInterval(handleChangeSlide, 4000);

// Khi bấm nút sang phải
btnRight.addEventListener('click', () => {
    clearInterval(handleEventChangeSlide); // Xóa setInterval cũ
    if (current === length - 1) {
        current = 0; // Quay về ảnh đầu tiên
    } else {
        current++;
    }
    updateSlidePosition();
    handleEventChangeSlide = setInterval(handleChangeSlide, 4000); // Thiết lập lại setInterval
});

// Khi bấm nút sang trái
btnLeft.addEventListener('click', () => {
    clearInterval(handleEventChangeSlide); // Xóa setInterval cũ
    if (current === 0) {
        current = length - 1; // Quay về ảnh cuối cùng
    } else {
        current--;
    }
    updateSlidePosition();
    handleEventChangeSlide = setInterval(handleChangeSlide, 4000); // Thiết lập lại setInterval
});

// Đảm bảo vị trí slide không bị thay đổi khi resize màn hình
window.addEventListener('resize', updateSlidePosition);

// Kiểm tra thông tin trang đặt vé
function kiemTraThongTin(event, nextStep) {
    // Ngăn chặn hành vi mặc định của form
    event.preventDefault();

    // Tạo biến giữ trạng thái thông tin hợp lệ
    let isValid = true;

    // Kiểm tra từng trường nhập liệu dựa trên lớp CSS
    const checkFields = (selector, errorSelector, validator, errorMessage) => {
        const fields = document.querySelectorAll(selector);
        const errors = document.querySelectorAll(errorSelector);

        fields.forEach((field, index) => {
            const value = field.value.trim();
            if (!validator(value)) {
                errors[index].textContent = errorMessage;
                isValid = false;
            } else {
                errors[index].textContent = '';
            }
        });
    };

    // Kiểm tra hạng ghế
    const hangGhe = document.getElementById('hangGhe');
    const hangGheError = document.getElementById('hangGheError');
    if (hangGhe.value.trim() === '') {
        hangGheError.textContent = 'Vui lòng chọn hạng ghế của bạn!';
        isValid = false;
        alert("Vui lòng chọn hạng ghế của bạn!")
    } else {
        hangGheError.textContent = '';
    }

    // Kiểm tra họ và tên
    checkFields(
        '.form-control.fullName',
        '.error-message.fullNameError',
        value => value !== '',
        'Họ và tên không được để trống.'
    );

    // Kiểm tra số điện thoại
    checkFields(
        '.form-control.phone',
        '.error-message.phoneError',
        value => /^[0-9]{10}$/.test(value),
        'Số điện thoại phải là 10 chữ số.'
    );

    // Kiểm tra email
    checkFields(
        '.form-control.email',
        '.error-message.emailError',
        value => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
        'Email không hợp lệ.'
    );

    // Kiểm tra căn cước công dân (CCCD)
    checkFields(
        '.form-control.cccd',
        '.error-message.cccdError',
        value => /^[0-9]{12}$/.test(value),
        'CCCD phải là 12 chữ số.'
    );

    // Nếu thông tin hợp lệ, tiến đến bước tiếp theo
    if (isValid) {
        document.getElementById('form1').submit(); // Gửi form hoặc di chuyển bước
    }

    if (!isValid) {
        field.classList.add('error'); // Thêm lớp 'error'
    } else {
        field.classList.remove('error'); // Xóa lớp 'error'
    }
}




