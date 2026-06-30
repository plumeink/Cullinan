(function () {
  const root = document.querySelector(".md-version-switcher");
  if (!root) {
    return;
  }

  const select = root.querySelector("#version-switcher");
  const current = root.querySelector(".md-version-switcher__current");
  if (!select || !current) {
    return;
  }

  const path = window.location.pathname || "/";
  const isZh = /(^|\/)zh(\/|$)/.test(path);
  const labels = isZh
    ? {
        title: "文档版本",
        current: "当前",
        stable: "正式版",
        pre: "测试版",
      }
    : {
        title: "Docs version",
        current: "Current",
        stable: "Stable",
        pre: "Pre-release",
      };

  const normalizeTarget = (baseUrl) => {
    if (!baseUrl) {
      return null;
    }

    let target = baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
    if (isZh && !/(^|\/)zh\/?$/.test(target)) {
      target = `${target}zh/`;
    }
    return target;
  };

  const currentChannel = root.dataset.currentChannel || "stable";
  const currentVersion = root.dataset.currentVersion || "";
  const stableVersion = root.dataset.stableVersion || "";
  const stableUrl = normalizeTarget(root.dataset.stableUrl || "/");
  const preVersion = root.dataset.preVersion || "";
  const preUrl = normalizeTarget(root.dataset.preUrl || "/pre/");
  const preAvailable = (root.dataset.preAvailable || "false").toLowerCase() === "true";

  const options = [];

  if (stableVersion && stableUrl) {
    options.push({
      value: stableUrl,
      label: `${labels.stable} ${stableVersion}`,
      selected: currentChannel === "stable",
    });
  }

  if (preAvailable && preVersion && preUrl) {
    options.push({
      value: preUrl,
      label: `${labels.pre} ${preVersion}`,
      selected: currentChannel === "pre",
    });
  }

  if (!options.length) {
    root.style.display = "none";
    return;
  }

  select.innerHTML = "";
  options.forEach((option) => {
    const node = document.createElement("option");
    node.value = option.value;
    node.textContent = option.label;
    node.selected = option.selected;
    select.appendChild(node);
  });

  select.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLSelectElement)) {
      return;
    }
    if (target.value) {
      window.location.href = target.value;
    }
  });

  const currentLabel = currentChannel === "pre" ? labels.pre : labels.stable;
  current.textContent = `${labels.current}: ${currentLabel} ${currentVersion}`.trim();
  root.setAttribute("aria-label", labels.title);
})();
