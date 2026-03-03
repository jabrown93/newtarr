document.addEventListener('DOMContentLoaded', function() {
    var el = document.getElementById('version-value');
    if (el) {
        fetch('/version.txt').then(function(r) { return r.text(); })
            .then(function(v) { el.textContent = v.trim(); })
            .catch(function() {});
    }
});
