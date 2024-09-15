const format = (string) => {
    matrix = "+7(___) ___-__-__";
    i = 0;
    def = matrix.replace(/\D/g, ""),
    val = string.replace(/\D/g, "");
    if (def.length >= val.length) val = def;
    string = matrix.replace(/./g, function (a) {
        return /[_\d]/.test(a) && i < val.length ? val.charAt(i++) : i >= val.length ? "" : a
    });
    return string
}