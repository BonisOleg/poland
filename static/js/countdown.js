document.querySelectorAll("[data-countdown]").forEach(function (el) {
    var target = new Date(el.dataset.countdown).getTime();

    function update() {
        var now = Date.now();
        var diff = target - now;

        if (diff <= 0) {
            el.querySelectorAll(".countdown__number").forEach(function (n) {
                n.textContent = "0";
            });
            return;
        }

        var days = Math.floor(diff / 86400000);
        var hours = Math.floor((diff % 86400000) / 3600000);
        var minutes = Math.floor((diff % 3600000) / 60000);
        var seconds = Math.floor((diff % 60000) / 1000);

        var d = el.querySelector("[data-days]");
        var h = el.querySelector("[data-hours]");
        var m = el.querySelector("[data-minutes]");
        var s = el.querySelector("[data-seconds]");

        if (d) d.textContent = days;
        if (h) h.textContent = hours;
        if (m) m.textContent = minutes;
        if (s) s.textContent = seconds;
    }

    update();
    setInterval(update, 1000);
});
