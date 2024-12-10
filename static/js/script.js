//  Show Menu Bar//
var showMenu = document.querySelector(".openMenu");
var hideMenu = document.querySelector(".closeMenu");

var menuTl = gsap.timeline();

menuTl.to(".side-menu-bar", {
  opacity: 1,
  pointerEvents: "auto",
});
menuTl.from(".inner-menu-div", {
  x: 150,
  opacity: 0,
  stagger: 0.5,
});
menuTl.from(".menu-span", {
  x: 150,
  opacity: 0,
  stagger: 0.2,
});

menuTl.pause();

showMenu.addEventListener("click", function () {
  menuTl.play(); // Fixed typo here
});

hideMenu.addEventListener("click", function () {
  menuTl.reverse();
});
