/** Native font matching/layout: no separate preview metrics or synthesized styles. */
const root = document.documentElement;
const style = document.querySelector('#style');
const controls = [...document.querySelectorAll('[data-feature]')];
/** Apply the selected real font face and OpenType features to every specimen panel. */
function update() {
  const face = style.selectedOptions[0];
  root.style.setProperty('--cut-weight', face.dataset.weight);
  root.style.setProperty('--cut-slope', face.dataset.slope);
  root.style.setProperty('--cut-features', controls.map(input => `"${input.dataset.feature}" ${Number(input.checked)}`).join(', '));
}
style.addEventListener('change', update);
controls.forEach(input => input.addEventListener('change', update));
update();
