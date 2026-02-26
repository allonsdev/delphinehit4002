(function ($) {
  "use strict";

  /*--------------------------------------------------------------
    RegisterPlugin, ScrollTrigger, SplitText
  --------------------------------------------------------------*/
  gsap.registerPlugin(ScrollTrigger, SplitText);
  gsap.config({
    nullTargetWarn: false,
    trialWarn: false
  });


  /*--------------------------------------------------------------
    FullHeight
  --------------------------------------------------------------*/
  function fullHeight() {
    $('.full-height').css("height", $(window).height());
  }


  /*--------------------------------------------------------------
    Preloader
  --------------------------------------------------------------*/
  function handlePreloader() {
    if ($('.loader-wrap').length) {
      $('.loader-wrap').delay(1000).fadeOut(1000);
    }
    TweenMax.to($(".loader-wrap .overlay"), 1.2, {
      force3D: true,
      left: "100%",
      ease: Expo.easeInOut,
    });
  }


  /*--------------------------------------------------------------
    Scroll To Top
  --------------------------------------------------------------*/
  function handleScrollbar() {
    const bHeight = $('body').height();
    const scrolled = $(window).innerHeight() + $(window).scrollTop();

    let percentage = ((scrolled / bHeight) * 100);

    if (percentage > 100) percentage = 100;

    $('.scroll-top-inner .bar-inner').css('width', percentage + '%');
  }


  // Banner Slider //Home One
  if ($(".banner-slider").length > 0) {
    var bannerSlider = new Swiper('.banner-slider', {
      spaceBetween: 0,
      slidesPerView: 1,
      mousewheel: false,
      height: 500,
      grabCursor: true,
      loop: true,
      speed: 1400,
      autoplay: {
        delay: 10000,
      },
      pagination: {
        el: '.swiper-pagination',
        type: 'progressbar',
      },
      navigation: {
        prevEl: '.banner-slider-button-prev',
        nextEl: '.banner-slider-button-next',
      },
    });
    bannerSlider.on('slideChange', function () {
      var csli = bannerSlider.realIndex + 1,
        curnum = $('#current');
      TweenMax.to(curnum, 0.2, {
        force3D: true,
        y: -10,
        opacity: 0,
        ease: Power2.easeOut,
        onComplete: function () {
          TweenMax.to(curnum, 0.1, {
            force3D: true,
            y: 10
          });
          curnum.html('0' + csli);
        }
      });
      TweenMax.to(curnum, 0.2, {
        force3D: true,
        y: 0,
        delay: 0.3,
        opacity: 1,
        ease: Power2.easeOut
      });
    });

    var totalSlides = bannerSlider.slides.length - 2;
    $('#total').html('0' + totalSlides);
  }


  // Banner Slider //Home One
  if ($(".banner-slider-two").length > 0) {
    var bannerSlider = new Swiper('.banner-slider-two', {
      spaceBetween: 0,
      effect: 'fade',
      slidesPerView: 1,
      mousewheel: false,
      height: 500,
      grabCursor: true,
      loop: true,
      speed: 1400,
      autoplay: {
        delay: 10000,
      },
      pagination: {
        el: '#main-slider-pagination',
        type: 'bullets',
      },
      navigation: {
        prevEl: '.banner-slider-button-prev',
        nextEl: '.banner-slider-button-next',
      },
    });
    bannerSlider.on('slideChange', function () {
      var csli = bannerSlider.realIndex + 1,
        curnum = $('#current');
      TweenMax.to(curnum, 0.2, {
        force3D: true,
        y: -10,
        opacity: 0,
        ease: Power2.easeOut,
        onComplete: function () {
          TweenMax.to(curnum, 0.1, {
            force3D: true,
            y: 10
          });
          curnum.html('0' + csli);
        }
      });
      TweenMax.to(curnum, 0.2, {
        force3D: true,
        y: 0,
        delay: 0.3,
        opacity: 1,
        ease: Power2.easeOut
      });
    });

    var totalSlides = bannerSlider.slides.length - 2;
    $('#total').html('0' + totalSlides);
  }


  /*--------------------------------------------------------------
    Owl Slider
  --------------------------------------------------------------*/
  function thmOwlInit() {
    if ($(".thm-owl__carousel").length) {
      $(".thm-owl__carousel").each(function () {
        let elm = $(this);
        let options = elm.data('owl-options');
        let thmOwlCarousel = elm.owlCarousel(options);
      });
    }

    if ($(".thm-owl__carousel--custom-nav").length) {
      $(".thm-owl__carousel--custom-nav").each(function () {
        let elm = $(this);
        let owlNavPrev = elm.data('owl-nav-prev');
        let owlNavNext = elm.data('owl-nav-next');
        $(owlNavPrev).on("click", function (e) {
          elm.trigger('prev.owl.carousel');
          e.preventDefault();
        })

        $(owlNavNext).on("click", function (e) {
          elm.trigger('next.owl.carousel');
          e.preventDefault();
        })
      });
    }
  }

  /*--------------------------------------------------------------
    Dynamic Current Menu Class selector
  --------------------------------------------------------------*/
  function dynamicCurrentMenuClass(selector) {
    let FileName = window.location.href.split("/").reverse()[0];

    selector.find("li").each(function () {
      let anchor = $(this).find("a");
      if ($(anchor).attr("href") == FileName) {
        $(this).addClass("current");
      }
    });
    // if any li has .current elmnt add class
    selector.children("li").each(function () {
      if ($(this).find(".current").length) {
        $(this).addClass("current");
      }
    });
    // if no file name return
    if ("" == FileName) {
      selector.find("li").eq(0).addClass("current");
    }
  }

  /*--------------------------------------------------------------
    Project / masonary Active
  --------------------------------------------------------------*/
  function projectMasonaryLayout() {
    if ($('.masonary-layout').length) {
      $('.masonary-layout').isotope({
        layoutMode: 'masonry'
      });
    }
    if ($('.post-filter').length) {
      $('.post-filter li').children('.filter-text').on('click', function () {
        var Self = $(this);
        var selector = Self.parent().attr('data-filter');
        $('.post-filter li').removeClass('active');
        Self.parent().addClass('active');
        $('.filter-layout').isotope({
          filter: selector,
          animationOptions: {
            duration: 500,
            easing: 'linear',
            queue: false
          }
        });
        return false;
      });
    }

    if ($('.post-filter.has-dynamic-filters-counter').length) {
      // var allItem = $('.single-filter-item').length;
      var activeFilterItem = $('.post-filter.has-dynamic-filters-counter').find('li');
      activeFilterItem.each(function () {
        var filterElement = $(this).data('filter');
        var count = $('.filter-layout').find(filterElement).length;
        $(this).children('.filter-text').append('<i class="count">' + count + '</i>');
      });
    };
  }

  /*--------------------------------------------------------------
   Smooth Menu Scroll Active
  --------------------------------------------------------------*/
  function SmoothMenuScroll() {
    var anchor = $(".scrollToLink");
    if (anchor.length) {
      anchor.children("a").bind("click", function (event) {
        if ($(window).scrollTop() > 10) {
          var headerH = "90";
        } else {
          var headerH = "90";
        }
        var target = $(this);
        $("html, body")
          .stop()
          .animate({
              scrollTop: $(target.attr("href")).offset().top - headerH + "px"
            },
            900,
            "easeInSine"
          );
        anchor.removeClass("current");
        anchor.removeClass("current-menu-ancestor");
        anchor.removeClass("current_page_item");
        anchor.removeClass("current-menu-parent");
        target.parent().addClass("current");
        event.preventDefault();
      });
    }
  }

  /*--------------------------------------------------------------
   One Page Menu Scroll Active
  --------------------------------------------------------------*/
  function OnePageMenuScroll() {
    var windscroll = $(window).scrollTop();
    if (windscroll >= 117) {
      var menuAnchor = $(".one-page-scroll-menu .scrollToLink").children("a");
      menuAnchor.each(function () {
        var sections = $(this).attr("href");
        $(sections).each(function () {
          if ($(this).offset().top <= windscroll + 100) {
            var Sectionid = $(sections).attr("id");
            $(".one-page-scroll-menu").find("li").removeClass("current");
            $(".one-page-scroll-menu").find("li").removeClass("current-menu-ancestor");
            $(".one-page-scroll-menu").find("li").removeClass("current_page_item");
            $(".one-page-scroll-menu").find("li").removeClass("current-menu-parent");
            $(".one-page-scroll-menu")
              .find("a[href*=\\#" + Sectionid + "]")
              .parent()
              .addClass("current");
          }
        });
      });
    } else {
      $(".one-page-scroll-menu li.current").removeClass("current");
      $(".one-page-scroll-menu li:first").addClass("current");
    }
  }

  // Testimonial Slider 
  if ($(".testimonial-slider").length > 0) {
    var testimonialSlider = new Swiper('.testimonial-slider', {
      spaceBetween: 0,
      slidesPerView: 1,
      mousewheel: false,
      height: 500,
      grabCursor: true,
      loop: true,
      speed: 1400,
      autoplay: {
        delay: 10000,
      },
      pagination: {
        el: '.swiper-pagination',
        type: 'progressbar',
      },
      navigation: {
        prevEl: '.testimonial-slider-button-prev',
        nextEl: '.testimonial-slider-button-next',
      },
    });
    testimonialSlider.on('slideChange', function () {
      var csli = testimonialSlider.realIndex + 1,
        curnum = $('#current');
      TweenMax.to(curnum, 0.2, {
        force3D: true,
        y: -10,
        opacity: 0,
        ease: Power2.easeOut,
        onComplete: function () {
          TweenMax.to(curnum, 0.1, {
            force3D: true,
            y: 10
          });
          curnum.html('0' + csli);
        }
      });
      TweenMax.to(curnum, 0.2, {
        force3D: true,
        y: 0,
        delay: 0.3,
        opacity: 1,
        ease: Power2.easeOut
      });
    });

    var totalSlides = testimonialSlider.slides.length - 2;
    $('#total').html('0' + totalSlides);
  }

  if ($("#shop-details-one__thumb").length) {
    let testimonialsThumb = new Swiper("#shop-details-one__thumb", {
      slidesPerView: 3,
      spaceBetween: 0,
      speed: 1400,
      watchSlidesVisibility: true,
      watchSlidesProgress: true,
      loop: true,
      autoplay: {
        delay: 5000
      }
    });

    let testimonialsCarousel = new Swiper("#shop-details-one__carousel", {
      observer: true,
      observeParents: true,
      loop: true,
      speed: 1400,
      mousewheel: false,
      slidesPerView: 1,
      autoplay: {
        delay: 5000
      },
      thumbs: {
        swiper: testimonialsThumb
      },
      pagination: {
        el: '#testimonials-one__carousel-pagination',
        type: 'bullets',
        clickable: true
      },

      "navigation": {
        "nextEl": "#product-details__swiper-button-next",
        "prevEl": "#product-details__swiper-button-prev"
      },
    });
  }

  // Products Details Tab Box
  if ($('.products-details-tab-box').length) {
    $('.products-details-tab-box .tabs-button-box .tab-btn-item').on('click', function (e) {
      e.preventDefault();
      var target = $($(this).attr('data-tab'));

      if ($(target).hasClass('actve-tab')) {
        return false;
      } else {
        $('.products-details-tab-box .tabs-button-box .tab-btn-item').removeClass('active-btn-item');
        $(this).addClass('active-btn-item');
        $('.products-details-tab-box .tabs-content-box .tab-content-box-item').removeClass('tab-content-box-item-active');
        $(target).addClass('tab-content-box-item-active');
      }
    });
  }

  /*--------------------------------------------------------------
    Main Menu For Mobile Nav Toogle Button Script
  --------------------------------------------------------------*/
  if ($(".mobile-nav__toggler").length) {
    $(".mobile-nav__toggler").on("click", function (e) {
      e.preventDefault();
      $(".mobile-nav__wrapper").toggleClass("expanded");
      $("body").toggleClass("locked");
    });
  }

  /*--------------------------------------------------------------
    Main Menu Mobile Nav Script
  --------------------------------------------------------------*/
  if ($(".main-menu__list").length && $(".mobile-nav__container").length) {
    let navContent = document.querySelector(".main-menu__list").outerHTML;
    let mobileNavContainer = document.querySelector(".mobile-nav__container");
    mobileNavContainer.innerHTML = navContent;
  }

  /*--------------------------------------------------------------
    Main Menu Mobile Nav Dropdown Script
  --------------------------------------------------------------*/
  if ($(".mobile-nav__container .main-menu__list").length) {
    let dropdownAnchor = $(
      ".mobile-nav__container .main-menu__list .dropdown > a"
    );
    dropdownAnchor.each(function () {
      let self = $(this);
      let toggleBtn = document.createElement("BUTTON");
      toggleBtn.setAttribute("aria-label", "dropdown toggler");
      toggleBtn.innerHTML = "<i class='fa fa-angle-down'></i>";
      self.append(function () {
        return toggleBtn;
      });
      self.find("button").on("click", function (e) {
        e.preventDefault();
        let self = $(this);
        self.toggleClass("expanded");
        self.parent().toggleClass("expanded");
        self.parent().parent().children("ul").slideToggle();
      });
    });
  }

  /*--------------------------------------------------------------
    Sticky Header Script
  --------------------------------------------------------------*/
  if ($(".sticky-header__content").length) {
    let navContent = document.querySelector(".main-menu").innerHTML;
    let mobileNavContainer = document.querySelector(".sticky-header__content");
    mobileNavContainer.innerHTML = navContent;
  }

  /*--------------------------------------------------------------
    Dynamic current Menu class Active Script
  --------------------------------------------------------------*/
  if ($(".main-menu__list").length) {
    let mainNavUL = $(".main-menu__list");
    dynamicCurrentMenuClass(mainNavUL);
  }

  /*--------------------------------------------------------------
    Dynamic Service Details Page Sidebar Menu class Active Script
  --------------------------------------------------------------*/
  if ($(".service-details__sidebar-service-list").length) {
    let mainNavUL = $(".service-details__sidebar-service-list");
    dynamicCurrentMenuClass(mainNavUL);
  }


  /*--------------------------------------------------------------
    Search Toggler Script Active
  --------------------------------------------------------------*/
  if ($(".search-toggler").length) {
    $(".search-toggler").on("click", function (e) {
      e.preventDefault();
      $(".search-popup").toggleClass("active");
      $(".mobile-nav__wrapper").removeClass("expanded");
      $("body").toggleClass("locked");
    });
  }

  /*--------------------------------------------------------------
    Odometer Script Active
  --------------------------------------------------------------*/
  if ($(".odometer").length) {
    var odo = $(".odometer");
    odo.each(function () {
      $(this).appear(function () {
        var countNumber = $(this).attr("data-count");
        $(this).html(countNumber);
      });
    });
  }

  /*--------------------------------------------------------------
    Wow Script Active
  --------------------------------------------------------------*/
  if ($(".wow").length) {
    var wow = new WOW({
      boxClass: "wow", // animated element css class (default is wow)
      animateClass: "animated", // animation css class (default is animated)
      mobile: true, // trigger animations on mobile devices (default is true)
      live: true // act on asynchronously loaded content (default is true)
    });
    wow.init();
  }

  // Filter by Price
  if ($('.price-ranger').length) {
    $('.price-ranger #slider-range').slider({
      range: true,
      min: 120,
      max: 405,
      values: [10.00, 200.00],
      slide: function (event, ui) {
        $('.price-ranger .ranger-min-max-block .min').val('$' + ui.values[0]);
        $('.price-ranger .ranger-min-max-block .max').val('$' + ui.values[1]);
      }
    });
    $('.price-ranger .ranger-min-max-block .min').val('$' + $('.price-ranger #slider-range').slider('values', 0));
    $('.price-ranger .ranger-min-max-block .max').val('$' + $('.price-ranger #slider-range').slider('values', 1));
  };

  //Fact Counter + Text Count
  if ($(".count-box").length) {
    $(".count-box").appear(
      function () {
        var $t = $(this),
          n = $t.find(".count-text").attr("data-stop"),
          r = parseInt($t.find(".count-text").attr("data-speed"), 10);

        if (!$t.hasClass("counted")) {
          $t.addClass("counted");
          $({
            countNum: $t.find(".count-text").text()
          }).animate({
            countNum: n
          }, {
            duration: r,
            easing: "linear",
            step: function () {
              $t.find(".count-text").text(Math.floor(this.countNum));
            },
            complete: function () {
              $t.find(".count-text").text(this.countNum);
            }
          });
        }
      }, {
        accY: 0
      }
    );
  }

  if ($('.time-countdown-two').length) {
    $('.time-countdown-two').each(function () {
      var Self = $(this);
      var countDate = Self.data('countdown-time'); // getting date

      Self.countdown(countDate, function (event) {
        $(this).html('<li> <div class="box"> <span class="days">' + event.strftime('%D') + '</span> <span class="timeRef">days</span> </div> </li> <li> <div class="box"> <span class="hours">' + event.strftime('%H') + '</span> <span class="timeRef clr-1">Hrs</span> </div> </li> <li> <div class="box"> <span class="minutes">' + event.strftime('%M') + '</span> <span class="timeRef clr-2">Mins</span> </div> </li> <li> <div class="box"> <span class="seconds">' + event.strftime('%S') + '</span> <span class="timeRef clr-3">Secs</span> </div> </li>');
      });
    });
  }

  // Cart Touch Spin
  if ($('.quantity-spinner').length) {
    $("input.quantity-spinner").TouchSpin({
      verticalbuttons: true
    });
  }

  //Progress Bar / Levels
  if ($('.progress-levels .progress-box .bar-fill').length) {
    $(".progress-box .bar-fill").each(function () {
      $('.progress-box .bar-fill').appear(function () {
        var progressWidth = $(this).attr('data-percent');
        $(this).css('width', progressWidth + '%');
      });

    }, {
      accY: 0
    });
  }

  //====== Magnific Popup
  if ($(".video-popup").length) {
    $(".video-popup").magnificPopup({
      type: "iframe",
      mainClass: "mfp-fade",
      removalDelay: 160,
      preloader: true,

      fixedContentPos: false
    });
  }

  if ($(".img-popup").length) {
    var groups = {};
    $(".img-popup").each(function () {
      var id = parseInt($(this).attr("data-group"), 10);

      if (!groups[id]) {
        groups[id] = [];
      }

      groups[id].push(this);
    });

    $.each(groups, function () {
      $(this).magnificPopup({
        type: "image",
        closeOnContentClick: true,
        closeBtnInside: false,
        gallery: {
          enabled: true
        }
      });
    });
  }

  //LightBox / Fancybox
  if ($('.lightbox-image').length) {
    $('.lightbox-image').fancybox({
      openEffect: 'fade',
      closeEffect: 'fade',

      youtube: {
        controls: 0,
        showinfo: 0
      },

      helpers: {
        media: {}
      }
    });
  }

  // AOS Animation
  if ($("[data-aos]").length) {
    AOS.init({
      duration: '1000',
      disable: 'false',
      easing: 'ease',
      mirror: true
    });
  }

  //Contact Form Validation
  if ($("#contact-form").length) {
    $("#contact-form").validate({
      submitHandler: function (form) {
        var form_btn = $(form).find('button[type="submit"]');
        var form_result_div = '#form-result';
        $(form_result_div).remove();
        form_btn.before('<div id="form-result" class="alert alert-success" role="alert" style="display: none;"></div>');
        var form_btn_old_msg = form_btn.html();
        form_btn.html(form_btn.prop('disabled', true).data("loading-text"));
        $(form).ajaxSubmit({
          dataType: 'json',
          success: function (data) {
            if (data.status = 'true') {
              $(form).find('.form-control').val('');
            }
            form_btn.prop('disabled', false).html(form_btn_old_msg);
            $(form_result_div).html(data.message).fadeIn('slow');
            setTimeout(function () {
              $(form_result_div).fadeOut('slow')
            }, 6000);
          }
        });
      }
    });
  }

  // Animation gsap 
  function title_animation() {
    var tg_var = jQuery('.sec-title-animation');
    if (!tg_var.length) {
      return;
    }
    const quotes = document.querySelectorAll(".sec-title-animation .title-animation");

    quotes.forEach(quote => {

      //Reset if needed
      if (quote.animation) {
        quote.animation.progress(1).kill();
        quote.split.revert();
      }

      var getclass = quote.closest('.sec-title-animation').className;
      var animation = getclass.split('animation-');
      if (animation[1] == "style4") return

      quote.split = new SplitText(quote, {
        type: "lines,words,chars",
        linesClass: "split-line"
      });
      gsap.set(quote, {
        perspective: 400
      });

      if (animation[1] == "style1") {
        gsap.set(quote.split.chars, {
          opacity: 0,
          y: "90%",
          rotateX: "-40deg"
        });
      }
      if (animation[1] == "style2") {
        gsap.set(quote.split.chars, {
          opacity: 0,
          x: "50"
        });
      }
      if (animation[1] == "style3") {
        gsap.set(quote.split.chars, {
          opacity: 0,
        });
      }
      quote.animation = gsap.to(quote.split.chars, {
        scrollTrigger: {
          trigger: quote,
          start: "top 90%",
        },
        x: "0",
        y: "0",
        rotateX: "0",
        opacity: 1,
        duration: 1,
        ease: Back.easeOut,
        stagger: .02
      });
    });
  }
  ScrollTrigger.addEventListener("refresh", title_animation);

  //Accordion Box
  if ($('.accordion-box').length) {
    $(".accordion-box").on('click', '.acc-btn', function () {

      var outerBox = $(this).parents('.accordion-box');
      var target = $(this).parents('.accordion');

      if ($(this).hasClass('active') !== true) {
        $(outerBox).find('.accordion .acc-btn').removeClass('active');
      }

      if ($(this).next('.acc-content').is(':visible')) {
        return false;
      } else {
        $(this).addClass('active');
        $(outerBox).children('.accordion').removeClass('active-block');
        $(outerBox).find('.accordion').children('.acc-content').slideUp(300);
        target.addClass('active-block');
        $(this).next('.acc-content').slideDown(300);
      }
    });
  }

  // window load event
  $(window).on("load", function () {
    fullHeight();
    handlePreloader();
    thmOwlInit();
    projectMasonaryLayout();
    title_animation();

    /*--------------------------------------------------------------
       Fact Counter Style1 Round Text Curved Circle Script
    --------------------------------------------------------------*/
    if ($('.fact-counter-style1__content-round-text').length) {
      $('.fact-counter-style1__content-round-text').circleType({
        position: 'absolute',
        dir: 1,
        radius: 72,
        forceHeight: true,
        forceWidth: true
      });
    }

    /*--------------------------------------------------------------
       Features Style1 Round Text Curved Circle Script
    --------------------------------------------------------------*/
    if ($('.features-style1__content-two-round-text').length) {
      $('.features-style1__content-two-round-text').circleType({
        position: 'absolute',
        dir: 1,
        radius: 72,
        forceHeight: true,
        forceWidth: true
      });
    }

    /*--------------------------------------------------------------
       Testimoial Style1 Round Text Curved Circle Script
    --------------------------------------------------------------*/
    if ($('.testimoial-style1__content-round-text').length) {
      $('.testimoial-style1__content-round-text').circleType({
        position: 'absolute',
        dir: 1,
        radius: -60,
        forceHeight: true,
        forceWidth: true
      });
    }

    /*--------------------------------------------------------------
       Main Slider Style2 Curved Top Script
    --------------------------------------------------------------*/
    if ($('.main-slider-style2__curved-top').length) {
      $('.main-slider-style2__curved-top').circleType({
        position: 'absolute',
        dir: 1,
        radius: 240,
        forceHeight: true,
        forceWidth: true
      });
    }

    /*--------------------------------------------------------------
       Main Slider Style2 Curved Bottom Script
    --------------------------------------------------------------*/
    if ($('.main-slider-style2__curved-bottom').length) {
      $('.main-slider-style2__curved-bottom').circleType({
        position: 'absolute',
        dir: 1,
        radius: -200,
        forceHeight: true,
        forceWidth: true
      });
    }

    /*--------------------------------------------------------------
       Main Slider Style2 Curved Top Script
    --------------------------------------------------------------*/
    if ($('.banner-style1__curved-top').length) {
      $('.banner-style1__curved-top').circleType({
        position: 'absolute',
        dir: 1,
        radius: 240,
        forceHeight: true,
        forceWidth: true
      });
    }

    /*--------------------------------------------------------------
       Main Slider Style2 Curved Bottom Script
    --------------------------------------------------------------*/
    if ($('.banner-style1__curved-bottom').length) {
      $('.banner-style1__curved-bottom').circleType({
        position: 'absolute',
        dir: 1,
        radius: -200,
        forceHeight: true,
        forceWidth: true
      });
    }

  });


  // window scroll event
  $(window).on("scroll", function () {
    handleScrollbar();
    SmoothMenuScroll();
    OnePageMenuScroll();



    //Stricked Menu Fixed
    if ($(".stricked-menu").length) {
      var headerScrollPos = 130;
      var stricky = $(".stricked-menu");
      if ($(window).scrollTop() > headerScrollPos) {
        stricky.addClass("stricky-fixed");
      } else if ($(this).scrollTop() <= headerScrollPos) {
        stricky.removeClass("stricky-fixed");
      }
    }

    //Scroll To Top
    if ($(window).scrollTop() > 200) {
      $('.scroll-top-inner').addClass('visible');
    } else {
      $('.scroll-top-inner').removeClass('visible');
    }



  });

  // Scroll top button
  $('.scroll-top-inner').on("click", function () {
    $('html, body').animate({
      scrollTop: 0
    }, 500);
    return false;
  });




  // Nice Select Activation
  $(document).ready(function () {
    $('select:not(.ignore)').niceSelect();

  });


})(jQuery);