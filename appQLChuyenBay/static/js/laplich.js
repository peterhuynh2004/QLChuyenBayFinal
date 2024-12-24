let routeAirports = [];
$(document).ready(function () {
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

    // Event delegation for input events
    $(document).on("input", ".block-item.dropdown-input", function () {
        const $input = $(this);
        const $dropdown = $input.siblings(".dropdown");
        const query = $input.val();

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

    // Event delegation for selecting a dropdown item
    $(document).on("click", ".dropdownn li", function () {
        const $dropdownItem = $(this);
        const airportText = $dropdownItem.text(); // Chuỗi 'ten_SanBay (DiaChi)'

        // Phân tách tên sân bay (ten_SanBay) từ chuỗi
        const airportName = airportText.split(" (")[0]; // Tách tên sân bay trước dấu '('
        console.log("Dữ liệu sân bay:",airportName)
        console.log("Dữ liệu sân bay trùng:",routeAirports)
        // Kiểm tra tên sân bay có nằm trong danh sách sân bay của tuyến bay không
        if (routeAirports.includes(airportName)) {
            // Nếu có, hiển thị thông báo lỗi và dừng lại
            alert(`Sân bay bạn chọn trùng với tuyến bay: ${airportName}`);
            return;  // Dừng lại không tiếp tục thực hiện các thao tác sau
        }
        const $input = $dropdownItem.closest(".block-text").find(".block-item.dropdown-input");
        $input.val($dropdownItem.text());
        $dropdownItem.closest(".dropdownn").hide();
    });

    // Hide dropdown when clicking outside
    $(document).on("click", function (e) {
        if (!$(e.target).closest(".block-text").length) {
            $(".dropdownn").empty().hide();
        }
    });
});


$(document).ready(function () {
    // Lấy dữ liệu từ API tuyến bay
    let sampleData = [];
    $.ajax({
        url: "/api/get_tuyenbay", // Địa chỉ API để lấy danh sách tuyến bay
        method: "GET",
        success: function (data) {
            // Lưu danh sách tuyến bay vào biến
            console.log("Dữ liệu nhận từ API tuyến bay:", data);  // Debug dữ liệu trả về từ API
            sampleData = data.map(item => `${item.tenTuyen}`);  // Lưu trữ 'tenTuyen' vào sampleData
            console.log("Danh sách tuyến bay:", sampleData);  // Debug danh sách tuyến bay
        },
        error: function () {
            console.error("Không thể tải dữ liệu từ API tuyến bay.");
        }
    });

    // Function to filter results
    function filterResults(query) {
        console.log("Truy vấn tìm kiếm:", query);  // Debug giá trị query
        return sampleData.filter(item =>
            item.toLowerCase().includes(query.toLowerCase())
        );
    }

    // Event delegation for input events
    $(document).on("input", ".block-item.dropdown-inputlaplich", function () {
        const $input = $(this);
        const $dropdown = $input.siblings(".dropdown1"); // Tìm dropdown liệt kê kết quả
        const query = $input.val();

        console.log("Giá trị nhập vào:", query);  // Debug giá trị nhập vào trong input

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

    // Event delegation for selecting a dropdown item
    $(document).on("click", ".dropdown1 li", function () {
        const $dropdownItem = $(this);
        const selectedRoute = $dropdownItem.text();
        routeAirports = [];
        console.log("Phần tử dropdown đã chọn:", $dropdownItem.text());  // Debug phần tử được chọn từ dropdown
        routeAirports = selectedRoute.split(" - ");
         // Hiển thị các sân bay trong tuyến bay đã chọn
        console.log("Danh sách sân bay trong tuyến bay:", routeAirports);

        // Kiểm tra xem phần tử input có đúng không
        const $input = $dropdownItem.parent().parent().children(".dropdown-inputlaplich"); // Tìm input trong parent của li
        console.log("Input cần cập nhật:", $input);  // In ra giá trị của input cần tìm

        // Kiểm tra xem $input có đúng không
        if ($input.length === 0) {
            console.error("Không tìm thấy phần tử input!");
        } else {
            // Gán giá trị của dropdown item vào input
            $input.val($dropdownItem.text());
            // Ẩn dropdown sau khi chọn item
            $dropdownItem.closest(".dropdown").hide();

        }
    });

    // Hide dropdown when clicking outside
    $(document).on("click", function (e) {
        if (!$(e.target).closest(".block-text").length) {
            $(".dropdown1").empty().hide();
        }
    });
});



document.addEventListener("DOMContentLoaded", function() {
    // Lấy thời gian hiện tại
    let now = new Date();

    // Thêm 12 giờ vào thời gian hiện tại
    now.setHours(now.getHours() + 12);

    // Lấy ngày, giờ và phút trong định dạng yyyy-MM-ddTHH:mm
    let year = now.getFullYear();
    let month = (now.getMonth() + 1).toString().padStart(2, '0'); // Tháng bắt đầu từ 0, cần cộng thêm 1
    let day = now.getDate().toString().padStart(2, '0');
    let hours = now.getHours().toString().padStart(2, '0');
    let minutes = now.getMinutes().toString().padStart(2, '0');

    // Tạo chuỗi datetime theo định dạng yyyy-MM-ddTHH:mm
    let datetime = `${year}-${month}-${day}T${hours}:${minutes}`;

    // Thiết lập giá trị min của input
    document.getElementById("flight-date").setAttribute("min", datetime);
});

document.addEventListener("DOMContentLoaded", function() {
    // Lắng nghe sự kiện thay đổi giá trị của các input thời gian dừng tại sân bay trung gian
    $(document).on('input', '[name^="intermediate_airports"][name$="[duration]"]', function() {
        // Tính tổng thời gian dừng của các sân bay trung gian
        let totalIntermediateDuration = 0;
        $('[name^="intermediate_airports"][name$="[duration]"]').each(function() {
            totalIntermediateDuration += parseInt($(this).val()) || 0;  // Lấy giá trị, nếu không có thì lấy 0
        });

        // Lấy giá trị của input "flight-duration"
        let flightDuration = parseInt($('#flight-duration').val()) || 0;

        // Kiểm tra và thông báo lỗi nếu flight-duration không lớn hơn tổng thời gian dừng
        if (flightDuration <= totalIntermediateDuration) {
            alert('Thời gian bay phải lớn hơn tổng thời gian dừng tại các sân bay trung gian!');
            // Bạn có thể đặt lại giá trị hoặc đưa con trỏ vào trường flight-duration để người dùng nhập lại
            $('#flight-duration').val('');
        }
    });

    // Lắng nghe sự kiện thay đổi giá trị của input "flight-duration"
    $('#flight-duration').on('input', function() {
        // Lấy giá trị của input "flight-duration"
        let flightDuration = parseInt($(this).val()) || 0;

        // Tính tổng thời gian dừng của các sân bay trung gian
        let totalIntermediateDuration = 0;
        $('[name^="intermediate_airports"][name$="[duration]"]').each(function() {
            totalIntermediateDuration += parseInt($(this).val()) || 0;
        });

        // Kiểm tra nếu flight-duration nhỏ hơn hoặc bằng tổng thời gian dừng, thông báo lỗi
        if (flightDuration <= totalIntermediateDuration) {
            alert('Thời gian bay phải lớn hơn tổng thời gian dừng tại các sân bay trung gian!');
        }
    });
});

