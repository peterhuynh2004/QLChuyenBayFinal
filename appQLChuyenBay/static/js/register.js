console.log("File JS đã được tải thành công!");
const myInput = document.getElementById("psw");
const letter = document.getElementById("letter");
const capital = document.getElementById("capital");
const number = document.getElementById("number");
const length = document.getElementById("length");

// When the user clicks on the password field, show the message box
myInput.onfocus = function () {
    document.getElementById("pass-error").style.display = "block";
};

// When the user clicks outside of the password field, hide the message box
myInput.onblur = function () {
    document.getElementById("pass-error").style.display = "none";
};

myInput.addEventListener("keyup", function () {
    validatePasswordComplexity();
});

function validatePasswordComplexity() {
    var lowerCaseLetters = /[a-z]/g;
    var upperCaseLetters = /[A-Z]/g;
    var numbers = /[0-9]/g;

    var hasLowerCase = myInput.value.match(lowerCaseLetters);
    var hasUpperCase = myInput.value.match(upperCaseLetters);
    var hasNumbers = myInput.value.match(numbers);
    var hasMinimumLength = myInput.value.length >= 8;

    letter.classList.toggle("valid", hasLowerCase);
    letter.classList.toggle("invalid", !hasLowerCase);
    capital.classList.toggle("valid", hasUpperCase);
    capital.classList.toggle("invalid", !hasUpperCase);
    number.classList.toggle("valid", hasNumbers);
    number.classList.toggle("invalid", !hasNumbers);
    length.classList.toggle("valid", hasMinimumLength);
    length.classList.toggle("invalid", !hasMinimumLength);
}

document.querySelector(".alert").classList.add("show");
