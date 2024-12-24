$(document).ready(function () {
    const today = new Date().toISOString().split('T')[0];
    $('#ThoiGian').attr('min', today);

    if ($.cookie('SanBayDi')) {
        $('#SanBayDi').val($.cookie('SanBayDi'));
    } else {
        $('#SanBayDi').val('Hồ Chí Minh (SGN)');
    }

    if ($.cookie('SanBayDen')) {
        $('#SanBayDen').val($.cookie('SanBayDen'));
    } else {
        $('#SanBayDen').val('Hà Nội (HAN)');
    }
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
    const sampleData = [
        "Apple",
        "Banana",
        "Cherry",
        "Date",
        "Elderberry",
        "Fig",
        "Grape",
        "Honeydew",
        "Kiwi",
        "Lemon"
    ];

    const $input = $("#SanBayDi");
    const $dropdown = $("#dropdown-results");

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

            if (this.classList.contains('plus')) {
                // Nếu là nút cộng
                input.value = value + 1;
            } else if (this.classList.contains('minus')) {
                // Nếu là nút trừ
                if (value > 1) {
                    input.value = value - 1;
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

