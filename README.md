# 🏨 Red HMS – Hotel Management System
> Final Year Project | Django 4.2 | Reference CSS/JS Framework

---

## 📁 Project Structure

```
Red_HMS/
├── hotel_management/       ← Django settings package
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/               ← Custom User, Profile, Notifications
├── rooms/                  ← Hotel, RoomType, Room, Reviews
├── guests/                 ← Reservations, Bookmarks, Coupons
├── billing/                ← Stripe Payments, Invoices
├── reports/                ← Dashboard, Revenue, Occupancy
├── templates/
│   ├── partials/
│   │   ├── base.html               ← Public navbar/footer (reference framework)
│   │   ├── dashboard_base.html     ← Dashboard header (notification bell, user menu)
│   │   └── dashboard_sidebar.html  ← Sidebar with active-state links
│   ├── hotel/       index, listing, detail, room_type_detail
│   ├── accounts/    login, register, profile, change_password, notifications
│   ├── guests/      selected_rooms, checkout, my_reservations, reservation_detail, wishlist
│   ├── billing/     payment (Stripe), success, failed, invoice (printable)
│   ├── reports/     dashboard, all_bookings, revenue_report, occupancy_report
│   └── email/       booking_confirmed.html + .txt
├── static/
│   ├── css/
│   │   ├── stylesheet.css      ← Main reference theme (U-Listing)
│   │   ├── style.css           ← Color variables
│   │   ├── mmenu.css           ← Mobile menu
│   │   ├── perfect-scrollbar.css
│   │   ├── bootstrap-grid.css
│   │   ├── icons.css
│   │   └── revolutionslider.css
│   └── images/
├── media/
├── manage.py
├── requirements.txt
└── setup.sh
```

---

## ⚡ Quick Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py makemigrations accounts rooms guests billing reports
python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser

# 5. Start server
python manage.py runserver
```

Or simply run `bash setup.sh` for automated setup.

Visit → **http://127.0.0.1:8000/**
Admin → **http://127.0.0.1:8000/admin/**

---

## 🔑 URL Reference

| URL | Description |
|-----|-------------|
| `/` | Homepage – hotel listing |
| `/hotels/` | Browse all hotels |
| `/hotels/<slug>/` | Hotel detail with gallery & reviews |
| `/hotels/<slug>/room/<rt_slug>/` | Room type with availability |
| `/accounts/login/` | Sign in |
| `/accounts/register/` | Create account |
| `/guests/add/` | Add room to session cart |
| `/guests/selected-rooms/` | View cart |
| `/guests/checkout/` | Billing form |
| `/billing/payment/<id>/` | Stripe payment page |
| `/billing/invoice/<id>/` | Printable invoice |
| `/reports/dashboard/` | Staff & Guest dashboard |
| `/reports/revenue/` | Revenue analytics |
| `/reports/occupancy/` | Room occupancy |
| `/admin/` | Jazzmin admin panel |

---

## 💳 Stripe Configuration

1. Sign up at **https://stripe.com** (free test account)
2. Get your keys from the Dashboard
3. Update `hotel_management/settings.py`:

```python
STRIPE_PUBLIC_KEY = 'pk_test_...'
STRIPE_SECRET_KEY = 'sk_test_...'
```

---

## 👤 User Roles

| Role | Access |
|------|--------|
| **Admin** | Full staff dashboard + admin panel |
| **Manager** | Staff dashboard, all reports |
| **Receptionist** | Bookings, check-in/out |
| **Housekeeping** | Room status |
| **Guest** | Own bookings, wishlist |

Set roles in Django Admin → Users.

---

## 🎨 CSS/JS Framework

The frontend uses the **U-Listing** reference theme with these files served from `static/css/`:

- `stylesheet.css` — Complete layout, navigation, listing cards, dashboard panels, booking forms
- `style.css` — Color variables (customised to Red HMS brand)
- `mmenu.css` — Mobile hamburger navigation
- `perfect-scrollbar.css` — Dashboard sidebar scrollbar
- `bootstrap-grid.css` — 12-column grid

External CDN resources loaded in every template:
- **SweetAlert2** — Toast notifications for Django messages
- **DateRangePicker** — Date selection on booking forms
- **Font Awesome 4 & 6** — Icons throughout
- **Bootstrap Icons** — Dashboard icons
- **Boxicons, Remix Icons** — Additional icon sets
- **Google Fonts** — Nunito + Open Sans (matching reference)
- **Stripe.js v3** — Payment processing

---

---

## 🤝 Contributors

| Contributor | Role |
|-------------|------|
| **Aditya Gautam** | Project Author – Full-stack development, UI/UX, Django backend |

---

*Red HMS – Final Year Project*
