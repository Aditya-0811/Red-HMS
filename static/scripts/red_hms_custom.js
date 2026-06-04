/*
 * Red HMS – Custom JavaScript
 * Adapts all reference interactions to Red HMS URL structure.
 * Requires: jQuery, SweetAlert2
 */

$(document).ready(function () {

    // preloader is handled in base.html inline JS

    // ══════════════════════════════════════════
    // BACK TO TOP
    // ══════════════════════════════════════════
    $(window).scroll(function () {
        if ($(this).scrollTop() > 300) {
            $('#bottom_backto_top').addClass('visible');
        } else {
            $('#bottom_backto_top').removeClass('visible');
        }
    });
    $('#bottom_backto_top a').on('click', function (e) {
        e.preventDefault();
        $('html, body').animate({ scrollTop: 0 }, 500);
    });

    // ══════════════════════════════════════════
    // STICKY HEADER ON SCROLL
    // ══════════════════════════════════════════
    $(window).scroll(function () {
        if ($(this).scrollTop() > 80) {
            $('#header_part').addClass('cloned-class');
        } else {
            $('#header_part').removeClass('cloned-class');
        }
    });

    // ══════════════════════════════════════════
    // MOBILE NAV TOGGLE
    // ══════════════════════════════════════════
    $('.utfbutton_collapse').on('click', function () {
        $('body').toggleClass('mmenu-open');
    });

    // ══════════════════════════════════════════
    // DASHBOARD RESPONSIVE SIDEBAR
    // ══════════════════════════════════════════
    $(document).on('click', '.utf_dashboard_nav_responsive', function (e) {
        e.preventDefault();
        $('.utf_dashboard_navigation').slideToggle(250);
    });

    // ══════════════════════════════════════════
    // NOTIFICATION DROPDOWN
    // ══════════════════════════════════════════
    $(document).on('click', '.js-item-menu', function (e) {
        e.stopPropagation();
        $(this).find('.js-dropdown').toggleClass('active');
    });
    $(document).on('click', function () {
        $('.js-dropdown').removeClass('active');
    });

    // ══════════════════════════════════════════
    // ROOM COUNT BADGE – update navbar count
    // ══════════════════════════════════════════
    function refreshRoomCount() {
        $.ajax({
            url: '/accounts/cart-count/',
            success: function (res) {
                if (res && res.count !== undefined) {
                    $('.room-count').text(res.count);
                }
            }
        });
    }
    refreshRoomCount();

    // ══════════════════════════════════════════
    // ADD TO SELECTION – handled by native POST
    // form in room_type_detail.html; Django view
    // redirects to HTTP_REFERER and shows toast.
    // ══════════════════════════════════════════

    // ══════════════════════════════════════════
    // REMOVE FROM SELECTION (AJAX)
    // Template uses class "delete-item" with data-item=<room_pk_key>
    // View: GET /booking/delete_selection/?id=<key>
    // ══════════════════════════════════════════
    $(document).on('click', '.delete-item', function (e) {
        e.preventDefault();
        var btn  = $(this);
        var key  = btn.data('item');

        $.ajax({
            url   : '/booking/delete_selection/',
            method: 'GET',
            data  : { id: key },
            success: function (res) {
                btn.closest('li').fadeOut(300, function () { $(this).remove(); });
                var count = res.total_selected_items || 0;
                $('.room-count').text(count);
                Swal.mixin({
                    toast: true, position: 'top-end',
                    showConfirmButton: false, timer: 1200
                }).fire({ icon: 'success', title: 'Room removed.' });
            },
            error: function () {
                window.location.href = '/booking/delete_session/';
            }
        });
    });

    // ══════════════════════════════════════════
    // BOOKMARK / WISHLIST TOGGLE (AJAX)
    // ══════════════════════════════════════════
    $(document).on('click', '#add-to-bookmark, .bookmark-toggle', function (e) {
        e.preventDefault();
        var btn   = $(this);
        var slug  = btn.data('hotel') || btn.data('slug');
        var icon  = btn.find('i');

        btn.html('<i class="fas fa-spinner fa-spin" style="color:gray;"></i>');

        $.ajax({
            url: '/guests/bookmark/' + slug + '/',
            method: 'GET',
            success: function (res) {
                // After redirect Django shows message via SweetAlert in template
                // We update the icon optimistically
                if (res && res.bookmarked !== undefined) {
                    if (res.bookmarked) {
                        btn.html('<i class="fa fa-heart" style="color:#c0392b;"></i> Saved');
                    } else {
                        btn.html('<i class="fa fa-heart" style="color:#aaa;"></i> Save');
                    }
                } else {
                    // Full page refresh fallback
                    window.location.reload();
                }
            },
            error: function () {
                window.location.href = '/guests/bookmark/' + slug + '/';
            }
        });
    });

    // ══════════════════════════════════════════
    // REVIEW SUBMIT (via magnific popup)
    // ══════════════════════════════════════════
    $(document).on('click', '#review-btn', function () {
        var btn    = $(this);
        var hotelId = btn.data('hotel');
        var review  = $('#review-input').val();
        var rating  = $('#rating-input').val();
        var csrfToken = $('[name=csrfmiddlewaretoken]').val();

        if (!review.trim()) {
            Swal.fire({ icon: 'warning', title: 'Please write a review first.' });
            return;
        }

        btn.html('<i class="fas fa-spinner fa-spin"></i> Submitting...');

        $.ajax({
            url: '/rooms/hotels/' + btn.data('slug') + '/review/',
            method: 'POST',
            data: {
                csrfmiddlewaretoken: csrfToken,
                review: review,
                rating: rating,
            },
            success: function () {
                Swal.mixin({
                    toast: true, position: 'top-end',
                    showConfirmButton: false, timer: 2000
                }).fire({ icon: 'success', title: 'Review submitted!' });
                $('#add-review-button').hide();
                $('#review_div').html(
                    '<p style="color:#27ae60;"><i class="fa fa-check-circle"></i> ' +
                    'Your review has been submitted successfully.</p>'
                );
                $.magnificPopup.close();
            },
            error: function () {
                btn.closest('form').submit();
            }
        });
    });

    // ══════════════════════════════════════════
    // SHARE / CLIPBOARD
    // ══════════════════════════════════════════
    $(document).on('click', '#clipboard', function (e) {
        e.preventDefault();
        var tmp = $('<input>');
        $('body').append(tmp);
        tmp.val(window.location.href).select();
        document.execCommand('copy');
        tmp.remove();
        $(this).html('<i class="fa fa-check-circle"></i> URL Copied!');
        var self = this;
        setTimeout(function () {
            $(self).html('<i class="fa fa-share"></i> Share');
        }, 2000);
    });

    // ══════════════════════════════════════════
    // NOTIFICATION DISMISSAL
    // ══════════════════════════════════════════
    $(document).on('click', '.mark-noti-as-seen', function (e) {
        e.preventDefault();
        var btn  = $(this);
        var id   = btn.data('index');
        var csrfToken = $('[name=csrfmiddlewaretoken]').val() || '';

        $.ajax({
            url: '/accounts/notifications/mark-seen/',
            data: { id: id, csrfmiddlewaretoken: csrfToken },
            success: function () {
                $('.noti-div-' + id).fadeOut(200);
                Swal.mixin({
                    toast: true, position: 'top-end',
                    showConfirmButton: false, timer: 1000
                }).fire({ icon: 'success', title: 'Notification dismissed.' });
            },
            error: function () {
                $('.noti-div-' + id).fadeOut(200);
            }
        });
    });

    // ══════════════════════════════════════════
    // AUTO-DISMISS FLASH MESSAGES (fallback)
    // ══════════════════════════════════════════
    setTimeout(function () {
        $('.notification.closeable').fadeOut(500);
    }, 4500);

    $(document).on('click', '.notification .close', function (e) {
        e.preventDefault();
        $(this).closest('.notification').fadeOut(300);
    });

    // ══════════════════════════════════════════
    // DATE VALIDATION: checkout after checkin
    // ══════════════════════════════════════════
    $(document).on('change', 'input[name="checkin"], #checkin-input', function () {
        var minDate = $(this).val();
        $('input[name="checkout"], #checkout-input').attr('min', minDate);
        var checkoutVal = $('input[name="checkout"], #checkout-input').val();
        if (checkoutVal && checkoutVal <= minDate) {
            $('input[name="checkout"], #checkout-input').val('');
        }
    });

    // Set today as minimum for all date inputs
    var todayISO = new Date().toISOString().split('T')[0];
    $('input[type="date"][name="checkin"], input[type="date"][name="checkout"]')
        .attr('min', todayISO);

    // ══════════════════════════════════════════
    // MAGNIFIC POPUP – Review dialog
    // ══════════════════════════════════════════
    if ($.fn.magnificPopup) {
        $('.popup-with-zoom-anim').magnificPopup({
            type: 'inline',
            fixedContentPos: false,
            fixedBgPos: true,
            overflowY: 'auto',
            closeBtnInside: true,
            preloader: false,
            midClick: true,
            removalDelay: 300,
            mainClass: 'my-mfp-zoom-in'
        });
    }

    // ══════════════════════════════════════════
    // SLICK CAROUSEL – Hotel cards on index
    // ══════════════════════════════════════════
    if ($.fn.slick && $('.slick-hotel-cards').length) {
        $('.slick-hotel-cards').slick({
            slidesToShow: 3,
            slidesToScroll: 1,
            autoplay: true,
            autoplaySpeed: 3500,
            dots: true,
            arrows: true,
            responsive: [
                { breakpoint: 1024, settings: { slidesToShow: 2 } },
                { breakpoint: 640,  settings: { slidesToShow: 1 } }
            ]
        });
    }

    // ══════════════════════════════════════════
    // PERFECT SCROLLBAR – dashboard sidebar
    // ══════════════════════════════════════════
    try {
        if (typeof PerfectScrollbar !== 'undefined' && $('.js-scrollbar').length) {
            new PerfectScrollbar('.js-scrollbar');
        }
    } catch (e) {
        console.log('PerfectScrollbar not available:', e);
    }

    // ══════════════════════════════════════════
    // CHOSEN SELECT – dropdowns
    // ══════════════════════════════════════════
    if ($.fn.chosen) {
        $('select.utf_chosen_select_single').chosen({ disable_search_threshold: 8 });
    }

    // ══════════════════════════════════════════
    // TOOLTIPS
    // ══════════════════════════════════════════
    if ($.fn.tooltip) {
        $('[data-toggle="tooltip"]').tooltip();
    }

    // ══════════════════════════════════════════
    // QUANTITY BUTTONS (adult/children selectors)
    // ══════════════════════════════════════════
    $(document).on('click', '.qtyBtn', function () {
        var input  = $(this).siblings('input[type="number"]');
        var val    = parseInt(input.val()) || 0;
        var isPlus = $(this).hasClass('qtyPlus');
        var min    = parseInt(input.attr('min') || 0);
        if (isPlus) {
            input.val(val + 1);
        } else if (val > min) {
            input.val(val - 1);
        }
    });

    // ══════════════════════════════════════════
    // ROOM STATUS PING (every 60s like reference)
    // ══════════════════════════════════════════
    function pingRoomStatus() {
        $.ajax({
            url: '/billing/update-room-status/',
            type: 'GET',
            success: function () { console.log('[RedHMS] Room status refreshed'); },
            error:   function () { /* silent */ }
        });
    }
    setInterval(pingRoomStatus, 60000);

    // ══════════════════════════════════════════
    // STAR RATING DISPLAY
    // Converts data-rating attributes into
    // visual star spans matching reference
    // ══════════════════════════════════════════
    function renderStars() {
        $('.utf_star_rating_section').each(function () {
            var rating = parseFloat($(this).data('rating')) || 0;
            var stars  = '';
            for (var i = 1; i <= 5; i++) {
                if (i <= Math.round(rating)) {
                    stars += '<i class="fa fa-star" style="color:#c0392b;font-size:.85rem;"></i>';
                } else {
                    stars += '<i class="fa fa-star-o" style="color:#ddd;font-size:.85rem;"></i>';
                }
            }
            var counter = $(this).find('.utf_counter_star_rating');
            if (counter.length) {
                counter.before('<div class="utf_star_rating_stars">' + stars + '</div>');
            }
        });
    }
    renderStars();

    // ══════════════════════════════════════════
    // PRINT INVOICE BUTTON
    // ══════════════════════════════════════════
    $(document).on('click', '#printButton', function () {
        window.print();
    });

    // ══════════════════════════════════════════
    // PROFILE IMAGE PREVIEW
    // ══════════════════════════════════════════
    window.loadFile = function (event) {
        var output = document.getElementById('profile-preview');
        if (output && event.target.files[0]) {
            output.src = URL.createObjectURL(event.target.files[0]);
        }
    };

    // ══════════════════════════════════════════
    // TABLE ROW HOVER HIGHLIGHT
    // ══════════════════════════════════════════
    $(document).on('mouseenter', '.table tbody tr', function () {
        $(this).css('background', '#fef9f9');
    }).on('mouseleave', '.table tbody tr', function () {
        $(this).css('background', '');
    });

});
