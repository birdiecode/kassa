document.getElementById('inp_search').addEventListener('keydown', function(e) {
    if (e.keyCode === 13) {
        document.getElementById('frm_search').submit();
    }
});