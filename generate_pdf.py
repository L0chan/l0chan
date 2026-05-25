import os
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        # We don't want a header on the first page
        if self.page_no() != 1:
            pass

    def footer(self):
        # We don't want a footer on the first page
        if self.page_no() != 1:
            self.set_y(-15)
            self.set_font("Times", "I", 10)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

def create_pdf():
    pdf = PDF()
    
    # -----------------------------
    # PAGE 1: COVER PAGE
    # -----------------------------
    pdf.add_page()
    pdf.set_font("Times", "B", 16)
    
    pdf.ln(20)
    pdf.cell(0, 10, "DONBOSCO INSTITUTE OF MANAGEMENT STUDIES AND", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "COMPUTER APPLICATIONS", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Times", "", 14)
    pdf.cell(0, 10, "Kumbalagodu, Mysore Road, Bengaluru-560074", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(30)
    pdf.set_font("Times", "B", 20)
    pdf.cell(0, 10, "A Project Synopsis", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(10)
    pdf.set_font("Times", "B", 16)
    pdf.cell(0, 10, "ON", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Times", "B", 22)
    pdf.cell(0, 10, "COMPARE2SAVE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font("Times", "B", 16)
    pdf.cell(0, 10, "(2025-2026)", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(30)
    pdf.set_font("Times", "B", 16)
    pdf.cell(0, 10, "BANGALORE UNIVERSITY (JNANABHARATHI)", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(20)
    pdf.set_font("Times", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "UNDER THE GUIDANCE OF", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.set_font("Times", "B", 14)
    pdf.set_text_color(255, 0, 0)
    pdf.cell(0, 10, "Ms. K Keerthi Yadav Asst. professor,", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "Dept. of BCA, DBIMSCA.", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(20)
    pdf.set_text_color(0, 0, 128)
    pdf.set_font("Times", "B", 14)
    pdf.cell(0, 10, "SUBMITTED BY", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.set_font("Times", "B", 16)
    pdf.cell(0, 10, "MANOJ N", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "(U03CQ23S0025)", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_text_color(0, 0, 0)

    # Helper function for adding sections
    def add_section(title, text):
        pdf.add_page()
        pdf.set_font("Times", "B", 16)
        pdf.cell(0, 10, title, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        pdf.set_font("Times", "", 12)
        pdf.multi_cell(0, 8, text)
    
    # -----------------------------
    # PAGE 2: ABSTRACT
    # -----------------------------
    abstract_text = (
        "The COMPARE2SAVE is a comprehensive, full-stack marketplace and local product discovery application "
        "designed to bridge the gap between neighborhood brick-and-mortar retail stores and modern e-commerce. "
        "The project is designed with a Flask-based backend in Python, using Flask-SQLAlchemy for database operations "
        "and structured SQLite/PostgreSQL databases. The frontend is built using HTML5, Vanilla CSS, and modern "
        "JavaScript (ES6) with specific integration of Three.js for an interactive 3D product visualizer and Leaflet.js "
        "for geolocation-based store mapping. The platform delivers dedicated dashboards with Role-Based Access Control "
        "(RBAC) for Customers, Shopkeepers, and Owner Admins.\n\n"
        "Traditional shopping methods for local stores rely heavily on physical visits and manual price comparisons, "
        "which lead to high search friction, wasted travel time, and operational inefficiencies for both buyers and sellers. "
        "The proposed system replaces these outdated, manual routines with a location-aware digital catalog and direct "
        "chat platform. Customers can register, verify their mobile numbers securely using Twilio SMS OTP, search for "
        "products near their current coordinates, compare prices, and negotiate with shopkeepers via a real-time chat interface.\n\n"
        "A core feature of the system is the integration of Three.js to provide an immersive 360-degree 3D preview of products, "
        "giving local shops an interactive edge similar to high-end e-commerce applications. Furthermore, the incorporation of "
        "an OpenAI-powered AI Shopping Assistant provides immediate recommendations and handles natural-language product "
        "discovery queries. Overall, the project aims to improve local trade, reduce consumer search overhead, and offer "
        "cross-platform installation as a Progressive Web App (PWA) and Capacitor-based mobile application."
    )
    add_section("ABSTRACT", abstract_text)

    # -----------------------------
    # PAGE 3: INTRODUCTION
    # -----------------------------
    intro_text = (
        "In recent years, the retail market has experienced a significant shift towards large e-commerce platforms. "
        "While national-scale online retail provides convenience, it lacks instant local fulfillment, and neighborhood "
        "shopkeepers face immense difficulty in making their inventory visible to nearby consumers. Conversely, local "
        "consumers who need items immediately often walk from store to store checking stock and comparing prices, which "
        "is highly inefficient.\n\n"
        "Traditional local commerce is highly fragmented and lacks a unified platform where inventory and pricing are transparent. "
        "Small shopkeepers often do not have the technical skills or budget to maintain individual online portals, making them "
        "invisible in the digital economy.\n\n"
        "The COMPARE2SAVE application is developed to overcome these challenges. By offering a unified marketplace, the platform "
        "enables local businesses to catalog their products easily, while giving neighborhood customers a live search engine to "
        "locate items and compare prices nearby. This system provides interactive 3D rendering, live geographical maps, role-based "
        "controls, and direct seller-to-buyer messaging, providing an immediate online-to-offline retail bridge."
    )
    add_section("INTRODUCTION", intro_text)

    # -----------------------------
    # PAGE 4: OBJECTIVES OF THE PROJECT
    # -----------------------------
    objectives_text = (
        "The primary objectives of the COMPARE2SAVE system are as follows:\n\n"
        "- To develop a complete web-based local product discovery and marketplace system using modern technologies.\n"
        "- To automate inventory management for local shopkeepers and reduce search overhead for consumers.\n"
        "- To implement secure, role-based user authentication using JWT and Twilio SMS-based OTP verification.\n"
        "- To integrate an interactive 3D product viewer using Three.js for 360-degree item visualization.\n"
        "- To incorporate Leaflet.js interactive maps to locate nearby shops and track orders geographically.\n"
        "- To embed an OpenAI-powered AI Shopping Assistant for natural-language product search and recommendations.\n"
        "- To establish real-time live chat communication between customers and shopkeepers.\n"
        "- To provide a scalable platform that supports desktop installation (.exe), PWA capabilities, and mobile builds."
    )
    add_section("OBJECTIVES OF THE PROJECT", objectives_text)

    # -----------------------------
    # PAGE 5: MODULES OF THE PROJECT
    # -----------------------------
    modules_text = (
        "The COMPARE2SAVE application consists of multiple interconnected modules designed to provide a comprehensive local marketplace:\n\n"
        "1. User Authentication Module: Handles secure registration, Twilio SMS OTP verification, and secure login with Role-Based "
        "Access Control for Customers, Shopkeepers, and Admins.\n\n"
        "2. Location & Mapping Module: Integrates Leaflet.js to pinpoint shop locations, track current user coordinates, and compute "
        "distances between buyers and sellers dynamically.\n\n"
        "3. Product Discovery & Comparison Module: A core engine that allows users to search products, sort them by price or distance, "
        "and visually inspect them. It bridges the offline-to-online gap.\n\n"
        "4. 3D Visualization Module: Uses Three.js to provide customers an interactive 360-degree preview of select products, "
        "enhancing the decision-making process before physical visits.\n\n"
        "5. AI Shopping Assistant Module: Integrates the OpenAI GPT engine to interpret natural language queries, providing immediate "
        "product suggestions and smart recommendations.\n\n"
        "6. Live Communication Module: Offers a real-time chat interface connecting buyers directly to sellers for price negotiations, "
        "stock confirmations, or general inquiries.\n\n"
        "7. Shopkeeper & Admin Dashboard Modules: Provides shopkeepers tools to manage their digital catalogs seamlessly. Admins monitor "
        "transactions, user activities, and platform integrity."
    )
    add_section("MODULES OF THE PROJECT", modules_text)

    # -----------------------------
    # PAGE 6: EXISTING AND PROPOSED SYSTEM
    # -----------------------------
    system_text = (
        "EXISTING SYSTEM\n"
        "Existing local commerce operates primarily through manual routines. When consumers want to purchase a product immediately, "
        "they must visit local shops physically or make phone calls to inquire about availability and pricing. Global e-commerce "
        "platforms cannot fulfill orders instantly and lack neighborhood-level store discovery. Limitations include high search costs, "
        "frequent stock unavailability issues, lack of online visibility for small sellers, and no interactive or live negotiation platform.\n\n"
        "PROPOSED SYSTEM\n"
        "The proposed COMPARE2SAVE system provides an automated, location-aware, and highly interactive marketplace solution. "
        "Built using a robust Flask backend and a modern HTML5/CSS Vanilla UI, it incorporates real-time geolocation mapping, "
        "3D item visualization, and AI assistant capabilities. The system seamlessly handles digital product cataloging and enables "
        "location-based store discovery with direct seller-to-buyer interactions, significantly improving the local retail experience."
    )
    add_section("EXISTING AND PROPOSED SYSTEM", system_text)

    # -----------------------------
    # PAGE 7: SOFTWARE AND HARDWARE REQUIREMENTS
    # -----------------------------
    requirements_text = (
        "SOFTWARE REQUIREMENTS\n"
        "- Operating System: Windows 10/11, Linux, or macOS.\n"
        "- Frontend Technologies: HTML5, CSS3 (Vanilla), JavaScript (ES6), Three.js, Leaflet.js.\n"
        "- Backend Technologies: Python 3.10+, Flask, Flask-SQLAlchemy, Flask-Login.\n"
        "- Database: SQLite (Development) or PostgreSQL (Production).\n"
        "- Additional APIs & Tools: Twilio SMS API, OpenAI API, WebSockets, PyInstaller, Capacitor.\n"
        "- Browser: Google Chrome, Mozilla Firefox, or Microsoft Edge.\n\n"
        "HARDWARE REQUIREMENTS\n"
        "- Processor: Intel Core i3 or equivalent (or higher).\n"
        "- RAM: 4GB minimum (8GB recommended for concurrent services).\n"
        "- Storage: At least 5GB of free space for project dependencies and localized databases.\n"
        "- Internet Connection: Stable connection required for AI API, mapping, and OTP features.\n"
        "- Peripherals: Standard monitor, keyboard, mouse. Mobile devices for testing the Capacitor app."
    )
    add_section("SOFTWARE & HARDWARE REQUIREMENTS", requirements_text)

    # -----------------------------
    # PAGE 8: CONCLUSION
    # -----------------------------
    conclusion_text = (
        "The COMPARE2SAVE project presents a highly interactive and scalable solution that digitizes local commerce. "
        "By combining Flask backend capabilities with advanced frontend tools like Three.js and Leaflet.js, it creates "
        "a powerful platform that connects offline retail with online consumers in real-time. The implementation of Twilio "
        "OTP ensures a secure and verifiable authentication flow, while the AI assistant handles search queries intuitively. "
        "With compilation options ranging from PWAs to standalone executables and mobile packages, the platform achieves "
        "high accessibility and user convenience.\n\n"
        "Ultimately, the application supports local economies by redirecting online consumers to nearby physical shops, "
        "laying down a stable foundation for future enhancements like augmented reality shopping experiences and automated "
        "route optimization for hyperlocal deliveries."
    )
    add_section("CONCLUSION", conclusion_text)

    # -----------------------------
    # PAGE 9: REFERENCES
    # -----------------------------
    references_text = (
        "1. Flask Documentation - https://flask.palletsprojects.com/\n"
        "2. Three.js Documentation - https://threejs.org/\n"
        "3. Leaflet.js Documentation - https://leafletjs.com/\n"
        "4. SQLAlchemy Documentation - https://www.sqlalchemy.org/\n"
        "5. OpenAI API Documentation - https://platform.openai.com/docs/\n"
        "6. Twilio API Documentation - https://www.twilio.com/docs/\n"
        "7. Capacitor Documentation - https://capacitorjs.com/\n"
        "8. SQLite Documentation - https://sqlite.org/docs.html\n"
        "9. Mozilla Developer Network (MDN) Web Docs - https://developer.mozilla.org/"
    )
    add_section("REFERENCES", references_text)

    pdf.output("COMPARE2SAVE_Synopsis.pdf")
    print("PDF generated successfully.")

if __name__ == "__main__":
    create_pdf()
