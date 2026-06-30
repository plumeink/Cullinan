(function () {
  function render() {
    var el = document.getElementById('route');
    if (el) {
      el.textContent = 'window.location.pathname = ' + window.location.pathname;
    }
  }
  window.addEventListener('popstate', render);
  render();
})();
