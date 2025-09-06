document.addEventListener("keydown", (e) => {
  if (e.code === "Space") {
    e.preventDefault();
    e.stopPropagation();
    document.activeElement.blur();
  }
});
