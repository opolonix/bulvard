const popup = document.querySelector(".popup")
const cover = document.querySelector(".cover")
const coffee_increment = document.querySelector('.coffee_increment')
cover.addEventListener("click", (e) => {
    popup.style.display = "none";
    cover.style.display = "none";
    document.body.style.overflow = "scroll"
})

let timeout;

const change_name = (clietn_id, name) => {
    clearInterval(timeout)
    timeout = setTimeout(() => {fetch(`/changeName?id=${clietn_id}&name=${encodeURI(name)}`)}, 500)
}
const profile = (element) => {
    const get_param = name => element.attributes[name].value

    popup.style.display = "flex"
    cover.style.display = "block"
    coffee_increment.value = 1
    popup.querySelector(".delete").style.display = "block"
    document.body.style.overflow = "hidden"

    popup.querySelector(".name").value = get_param("name")
    popup.querySelector(".name").oninput = (el) => {
        change_name(get_param("uuid"), el.target.value);
        element.querySelector(".name").innerText = el.target.value
    }
    popup.querySelector(".delete").onclick = (el) => {
        if (confirm('Точно хотите удалить эту запись?')){
            fetch(`/dropClient?id=${get_param("uuid")}`)
            element.remove()
            popup.style.display = "none";
            cover.style.display = "none";
            document.body.style.overflow = "scroll"
        }
    }
    popup.querySelector(".save-order").onclick = (el) => {
        let i = parseInt(coffee_increment.value)
        popup.querySelector(".coffee_count").innerText = `Покупок: ${parseInt(get_param("coffee_count"))+i} (${((parseInt(get_param("coffee_count"))+i)%coffee_limit)})`;
        element.attributes["coffee_count"].value = parseInt(get_param("coffee_count"))+i;
        fetch(`/newOrder?id=${get_param("uuid")}&count=${coffee_increment.value}`)
    }
    popup.querySelector(".phone").innerHTML = `Телефон: <a href="tel:+${get_param("phone")}">${format(get_param("phone"))}</a>`
    popup.querySelector(".uuid").innerText = `Код: ${get_param("uuid")}`
    popup.querySelector(".coffee_count").innerText = `Покупок: ${get_param("coffee_count")} (${(get_param("coffee_count")%coffee_limit)})`
}
document.querySelectorAll('.client').forEach(el => el.addEventListener("click", () => profile(el)))
document.querySelectorAll("input.numeric").forEach(el => el.addEventListener("input", e => {el.value = el.value.replace(/[^\d]/gi, '')}))