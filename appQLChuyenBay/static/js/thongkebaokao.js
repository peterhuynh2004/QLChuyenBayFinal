//let ctx = document.getElementById('myChart');
//let myChart;
//let Jsondata;
//
//// Kiểm tra nếu phần tử canvas tồn tại
//if (!ctx) {
//    console.error("Canvas element with ID 'myChart' not found.");
//} else {
//    fetch("/static/data/datachart.json")
//    .then(function(response){
//        if (response.ok) {
//            return response.json();
//        } else {
//            throw new Error(`HTTP error! status: ${response.status}`);
//        }
//    })
//    .then(function(data){
//        if (Array.isArray(data)) {
//            Jsondata = data;
//            createChart(Jsondata, 'bar');
//        } else {
//            console.error("Data format is not an array:", data);
//        }
//    })
//    .catch(function(error) {
//        console.error("Fetch error:", error);
//    });
//}
//
//function createChart(data, type) {
//    if (!Array.isArray(data)) {
//        console.error("Invalid data for chart:", data);
//        return;
//    }
//    myChart = new Chart(ctx, {
//        type: type,
//        data: {
//            labels: data.map(row => row.month),
//            datasets: [{
//                label: '# of Income',
//                data: data.map(row => row.income),
//                borderWidth: 1
//            }]
//        },
//        options: {
//            scales: {
//                y: {
//                    beginAtZero: true
//                }
//            },
//            responsive: true,
//            maintainAspectRatio: false,
//        }
//    });
//}
//
//function setChartType(chartType) {
//    if (myChart) {
//        myChart.destroy();
//        createChart(Jsondata, chartType);
//    } else {
//        console.error("Chart not initialized.");
//    }
//}
