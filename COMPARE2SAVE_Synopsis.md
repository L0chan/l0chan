# COMPARE2SAVE - Project Synopsis (2025-2026)

This document contains the complete project synopsis for **COMPARE2SAVE**, formatted in accordance with the academic structure of the reference synopsis.

---

### Cover Page Details
* **Institution**: DONBOSCO INSTITUTE OF MANAGEMENT STUDIES AND COMPUTER APPLICATIONS
* **Affiliation**: BANGALORE UNIVERSITY (JNANABHARATHI)
* **Title**: A Project Synopsis ON COMPARE2SAVE (2025-2026)
* **Under the Guidance of**: K Kerthi Yadav, Asst. professor, Dept. of BCA, DBIMSCA
* **Submitted by**: MANOJ N (U03CQ23S0025)

---

## TABLE OF CONTENTS

| Serial No. | Contents | Page No. |
| :--- | :--- | :--- |
| 1 | ABSTRACT | 3 |
| 2 | INTRODUCTION | 3 |
| 3 | OBJECTIVES | 4 |
| 4 | EXISTING SYSTEM | 4 |
| 5 | PROPOSED SYSTEM | 5 |
| 6 | TECHNOLOGY USED | 5 |
| 7 | CONCLUSION | 6 |
| 8 | REFERENCES | 6 |

---

## 1. ABSTRACT

The **COMPARE2SAVE** is a comprehensive, full-stack marketplace and local product discovery application designed to bridge the gap between neighborhood brick-and-mortar retail stores and modern e-commerce. The project is designed with a Flask-based backend in Python, using Flask-SQLAlchemy for database operations and structured SQLite/PostgreSQL databases. The frontend is built using HTML5, Vanilla CSS, and modern JavaScript (ES6) with specific integration of **Three.js** for an interactive 3D product visualizer and **Leaflet.js** for geolocation-based store mapping. The platform delivers dedicated dashboards with Role-Based Access Control (RBAC) for Customers, Shopkeepers, and Owner Admins.

Traditional shopping methods for local stores rely heavily on physical visits and manual price comparisons, which lead to high search friction, wasted travel time, and operational inefficiencies for both buyers and sellers. The proposed system replaces these outdated, manual routines with a location-aware digital catalog and direct chat platform. Customers can register, verify their mobile numbers securely using Twilio SMS OTP, search for products near their current coordinates, compare prices, and negotiate with shopkeepers via a real-time chat interface.

A core feature of the system is the integration of Three.js to provide an immersive 360-degree 3D preview of products, giving local shops an interactive edge similar to high-end e-commerce applications. Furthermore, the incorporation of an OpenAI-powered AI Shopping Assistant provides immediate recommendations and handles natural-language product discovery queries. Overall, the project aims to improve local trade, reduce consumer search overhead, and offer cross-platform installation as a Progressive Web App (PWA) and Capacitor-based mobile application.

---

## 2. INTRODUCTION

In recent years, the retail market has experienced a significant shift towards large e-commerce platforms. While national-scale online retail provides convenience, it lacks instant local fulfillment, and neighborhood shopkeepers face immense difficulty in making their inventory visible to nearby consumers. Conversely, local consumers who need items immediately often walk from store to store checking stock and comparing prices, which is highly inefficient.

Traditional local commerce is highly fragmented and lacks a unified platform where inventory and pricing are transparent. Small shopkeepers often do not have the technical skills or budget to maintain individual online portals, making them invisible in the digital economy.

The **COMPARE2SAVE** application is developed to overcome these challenges. By offering a unified marketplace, the platform enables local businesses to catalog their products easily, while giving neighborhood customers a live search engine to locate items and compare prices nearby. This system provides interactive 3D rendering, live geographical maps, role-based controls, and direct seller-to-buyer messaging, providing an immediate online-to-offline retail bridge.

---

## 3. OBJECTIVES

* To develop a complete web-based local product discovery and marketplace system using modern technologies.
* To automate inventory management for local shopkeepers and reduce search overhead for consumers.
* To implement secure, role-based user authentication using JWT and Twilio SMS-based OTP verification.
* To integrate an interactive 3D product viewer using Three.js for 360-degree item visualization.
* To incorporate Leaflet.js interactive maps to locate nearby shops and track orders geographically.
* To embed an OpenAI-powered AI Shopping Assistant for natural-language product search and recommendations.
* To establish real-time live chat communication between customers and shopkeepers.
* To provide a scalable platform that supports desktop installation (.exe), PWA capabilities, and mobile builds (using Capacitor).

---

## 4. EXISTING SYSTEM

Existing local commerce operates primarily through manual routines. When consumers want to purchase a product immediately, they must visit local shops physically or make phone calls to inquire about availability and pricing. While global e-commerce platforms (like Amazon or Flipkart) provide online catalogs, they cannot fulfill orders instantly (taking 1–3 days) and do not support local neighborhood-level store discovery.

These manual and disconnected systems lead to high search costs for consumers, frequent stock unavailability issues, and lost revenue for local shopkeepers who cannot publicize their stock.

### Limitations:
* Manual store-visiting routines consume significant time and travel effort.
* Lack of online visibility and digital cataloging tools for small-scale local shopkeepers.
* No mechanism for real-time local product availability and pricing check.
* Absence of interactive 3D visualization to preview physical products.
* Inability for customers to chat and negotiate directly with nearby sellers online.
* Poor local search capabilities, leading to consumer reliance on distant e-commerce fulfillment.

---

## 5. PROPOSED SYSTEM

The proposed **COMPARE2SAVE** system provides an automated, location-aware, and highly interactive marketplace solution. Built using a robust Flask backend and a clean, responsive HTML5/CSS Vanilla UI, it incorporates real-time geolocation mapping, 3D item visualization, and AI assistant capabilities.

The system divides access into three specific roles: Customers can browse stores on a map, inspect items in 3D, chat with sellers, and talk to an AI assistant; Shopkeepers can manage product catalogs, update stocks, and track sales; Admins manage users, verify shops, and monitor transactions.

### Advantages:
* Provides secure OTP-based login and role-based authorization mechanisms.
* Automates product cataloging and price updates for local shopkeepers.
* Enables location-based store discovery and interactive distance routing using Leaflet.js.
* Offers 360-degree product previewing using Three.js.
* Incorporates a GPT-based AI assistant for immediate buyer query assistance.
* Reduces paper records and manual searching via a digital product index.
* Features cross-platform availability, including installable PWAs, Windows EXE packaging, and Capacitor mobile wrappers.

---

## 6. TECHNOLOGY USED

### Frontend:
* **HTML5 & CSS3**: Core application structure and Vanilla CSS styling (clean dark theme).
* **JavaScript (ES6)**: Dynamic interface components and API integrations.
* **Three.js**: Interactive 3D product visualization.
* **Leaflet.js**: Live maps, store locations, and routing.

### Backend:
* **Python (Flask)**: Backend logic and routes.
* **Flask-SQLAlchemy**: Object-Relational Mapping (ORM) for database interactions.
* **Flask-Login**: Session and authentication state management.

### Database:
* **SQLite**: Local database storage (development).
* **PostgreSQL**: Production-ready relational database.

### Additional Technologies:
* **Twilio SMS API**: OTP verification.
* **OpenAI API (GPT)**: Natural language AI Shopping Assistant.
* **WebSockets / HTTP Long-Polling**: Real-time customer-to-shopkeeper chat.
* **Capacitor**: Offline-first mobile app compilation (Android & iOS).
* **PyInstaller**: Standalone Windows packaging (.exe).

---

## 7. CONCLUSION

The **COMPARE2SAVE** project presents a highly interactive and scalable solution that digitizes local commerce. By combining Flask backend capabilities with advanced frontend tools like Three.js and Leaflet.js, it creates a powerful platform that connects offline retail with online consumers in real-time. 

The implementation of Twilio OTP ensures a secure and verifiable authentication flow, while the AI assistant handles search queries intuitively. With compilation options ranging from PWAs to standalone executables and mobile packages, the platform achieves high accessibility and user convenience.

Ultimately, the application supports local economies by redirecting online consumers to nearby physical shops, laying down a stable foundation for future enhancements like AR shopping and automatic route optimization for local deliveries.

---

## 8. REFERENCES

1. **Flask Documentation** – [flask.palletsprojects.com](https://flask.palletsprojects.com/)
2. **Three.js Documentation** – [threejs.org](https://threejs.org/)
3. **Leaflet.js Documentation** – [leafletjs.com](https://leafletjs.com/)
4. **SQLAlchemy Documentation** – [sqlalchemy.org](https://www.sqlalchemy.org/)
5. **OpenAI API Documentation** – [platform.openai.com/docs](https://platform.openai.com/docs/)
6. **Twilio API Documentation** – [twilio.com/docs](https://www.twilio.com/docs/)
7. **Capacitor Documentation** – [capacitorjs.com](https://capacitorjs.com/)
