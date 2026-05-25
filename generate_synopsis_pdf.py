import os
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        pass

    def footer(self):
        if self.page_no() != 1:
            self.set_y(-15)
            self.set_font("Times", "", 12)
            self.cell(0, 10, str(self.page_no()), align="C")

def create_pdf():
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # -----------------------------
    # PAGE 1: COVER PAGE
    # -----------------------------
    pdf.add_page()
    pdf.set_font("Times", "B", 14)
    
    pdf.ln(10)
    pdf.cell(0, 8, "DONBOSCO INSTITUTE OF MANAGEMENT STUDIES AND", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "COMPUTER APPLICATIONS", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(30)
    pdf.set_font("Times", "B", 16)
    pdf.cell(0, 8, "A Project Synopsis", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "ON", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "COMPARE2SAVE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "(2025-2026)", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(30)
    pdf.set_font("Times", "B", 14)
    pdf.cell(0, 8, "BANGALORE UNIVERSITY (JNANABHARATHI)", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(20)
    pdf.set_font("Times", "BU", 14)
    pdf.cell(0, 8, "UNDER THE GUIDANCE OF", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "", 14)
    pdf.cell(0, 8, "K Kerthi Yadav, Asst. professor, Dept. of BCA, DBIMSCA", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(20)
    pdf.set_font("Times", "BU", 14)
    pdf.cell(0, 8, "SUBMITTED BY", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "", 14)
    pdf.cell(0, 8, "MANOJ N (U03CQ23S0025)", align="C", new_x="LMARGIN", new_y="NEXT")
    
    # -----------------------------
    # PAGE 2: TABLE OF CONTENTS
    # -----------------------------
    pdf.add_page()
    pdf.set_font("Times", "B", 14)
    pdf.cell(0, 10, "TABLE OF CONTENTS:", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Table header
    pdf.set_font("Times", "", 12)
    col_width_1 = 30
    col_width_2 = 120
    col_width_3 = 30
    line_height = 10
    
    pdf.cell(col_width_1, line_height, "SERIAL.NO", border=1, align="C")
    pdf.cell(col_width_2, line_height, "CONTENTS", border=1, align="C")
    pdf.cell(col_width_3, line_height, "PG.NO", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
    
    # Table rows
    rows = [
        ("1", "ABSTRACT", "3"),
        ("2", "INTRODUCTION", "3"),
        ("3", "OBJECTIVES", "4"),
        ("4", "EXISTING SYSTEM", "4"),
        ("5", "PROPOSED SYSTEM", "5"),
        ("6", "TECHNOLOGY USED", "5"),
        ("7", "CONCLUSION", "6"),
        ("8", "REFERENCES", "6"),
    ]
    for r in rows:
        pdf.cell(col_width_1, line_height, r[0], border=1, align="C")
        pdf.cell(col_width_2, line_height, r[1], border=1, align="C")
        pdf.cell(col_width_3, line_height, r[2], border=1, align="C", new_x="LMARGIN", new_y="NEXT")

    # -----------------------------
    # PAGE 3: ABSTRACT & INTRODUCTION
    # -----------------------------
    pdf.add_page()
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 10, "ABSTRACT:", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Times", "", 12)
    abstract_text = (
        "The COMPARE2SAVE is a comprehensive, full-stack marketplace and local product discovery application "
        "designed to bridge the gap between neighborhood brick-and-mortar retail stores and modern e-commerce. "
        "The project is designed using Flask for the backend, SQLite for database operations, and modern frontend "
        "technologies with Three.js and Leaflet.js. The platform delivers dedicated dashboards with Role-Based Access Control "
        "(RBAC) for Customers, Shopkeepers, and Owner Admins.\n\n"
        "Traditional shopping methods for local stores rely heavily on physical visits and manual price comparisons, "
        "which lead to high search friction and wasted travel time. The proposed system replaces these outdated routines "
        "with a location-aware digital catalog. Customers can verify securely using Twilio SMS OTP, search for products "
        "nearby, compare prices, and negotiate with shopkeepers via a real-time chat interface.\n\n"
        "A core feature is the integration of Three.js for immersive 3D preview of products and an OpenAI-powered "
        "AI Shopping Assistant. Overall, the project aims to improve local trade and offer cross-platform accessibility "
        "as a PWA and Capacitor-based mobile app."
    )
    pdf.multi_cell(0, 6, abstract_text)
    
    pdf.ln(10)
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 10, "INTRODUCTION:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "", 12)
    intro_text = (
        "In recent years, the retail market has experienced a significant shift towards e-commerce. While large online "
        "retail provides convenience, it lacks instant local fulfillment, and neighborhood shopkeepers face immense "
        "difficulty making inventory visible to nearby consumers. Local consumers who need items immediately often "
        "walk from store to store, which is inefficient.\n\n"
        "Traditional local commerce is fragmented. The COMPARE2SAVE application is developed to overcome these "
        "limitations by introducing a complete web-based solution that automates local marketplace activities.\n\n"
        "The system provides an interactive platform enabling local businesses to catalog products, while giving "
        "neighborhood customers a live search engine to locate items and compare prices nearby."
    )
    pdf.multi_cell(0, 6, intro_text)

    # -----------------------------
    # PAGE 4: OBJECTIVES & EXISTING SYSTEM
    # -----------------------------
    pdf.add_page()
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 10, "OBJECTIVES:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "", 12)
    objectives_text = (
        "- To develop a complete web-based local product discovery system using modern technologies\n"
        "- To automate inventory management for local shopkeepers and reduce search overhead\n"
        "- To implement secure authentication using Twilio SMS-based OTP verification\n"
        "- To integrate 3D product visualization using Three.js\n"
        "- To provide interactive maps using Leaflet.js to locate nearby shops\n"
        "- To embed an OpenAI-powered AI Shopping Assistant for smart recommendations\n"
        "- To establish real-time live chat communication between buyers and sellers\n"
        "- To provide a scalable platform supporting PWA and mobile applications"
    )
    pdf.multi_cell(0, 6, objectives_text)
    
    pdf.ln(10)
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 10, "EXISTING SYSTEM:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "", 12)
    existing_text = (
        "Existing local commerce operates primarily through manual routines. When consumers want to purchase "
        "a product immediately, they must visit local shops physically or make phone calls to inquire about "
        "availability and pricing.\n\n"
        "These systems are difficult to navigate and highly inefficient. They lead to high search costs for "
        "consumers, frequent stock unavailability issues, and lost revenue for local shopkeepers who cannot "
        "publicize their stock.\n\n"
        "Limitations:\n"
        "- Manual store-visiting routines consume significant time and travel effort\n"
        "- Lack of online visibility and digital cataloging tools for small shopkeepers\n"
        "- No mechanism for real-time local product availability and pricing check\n"
        "- Absence of intelligent technologies like AI recommendations and 3D visualization\n"
        "- Inability for customers to chat and negotiate directly with nearby sellers online\n"
        "- High reliance on distant e-commerce fulfillment instead of local immediate delivery"
    )
    pdf.multi_cell(0, 6, existing_text)

    # -----------------------------
    # PAGE 5: PROPOSED SYSTEM & TECHNOLOGY USED
    # -----------------------------
    pdf.add_page()
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 10, "PROPOSED SYSTEM:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "", 12)
    proposed_text = (
        "The proposed COMPARE2SAVE system provides an intelligent and automated solution for local product "
        "discovery and marketplace activities. The system is designed using Python (Flask), SQLite, HTML5, CSS3, "
        "JavaScript, Three.js, and Leaflet.js.\n\n"
        "The application provides centralized dashboards for different roles. Customers can register, locate nearby "
        "products on interactive maps, and use an AI assistant for recommendations.\n\n"
        "Advantages:\n"
        "- Provides secure Twilio OTP authentication and authorization mechanisms\n"
        "- Automates location-based store discovery using Leaflet.js\n"
        "- Enables centralized management of inventory for shopkeepers\n"
        "- Reduces manual searching and wasted travel time\n"
        "- Improves operational efficiency and gives small businesses digital visibility\n"
        "- Supports real-time chat and interactive 3D product previews"
    )
    pdf.multi_cell(0, 6, proposed_text)
    
    pdf.ln(10)
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 10, "TECHNOLOGY USED:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "", 12)
    tech_text = (
        "Frontend:\n"
        "- HTML5, CSS3 (Vanilla)\n"
        "- JavaScript (ES6)\n"
        "- Three.js (3D Viewer)\n"
        "- Leaflet.js (Maps)\n\n"
        "Backend:\n"
        "- Python\n"
        "- Flask, Flask-SQLAlchemy\n\n"
        "Database:\n"
        "- SQLite / PostgreSQL\n\n"
        "Additional Technologies:\n"
        "- Twilio API (SMS Auth)\n"
        "- OpenAI API (Chatbot)\n"
        "- Capacitor (Mobile Wrapper)"
    )
    pdf.multi_cell(0, 6, tech_text)

    # -----------------------------
    # PAGE 6: CONCLUSION & REFERENCES
    # -----------------------------
    pdf.add_page()
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 10, "CONCLUSION:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "", 12)
    conclusion_text = (
        "The COMPARE2SAVE system provides a smart and efficient solution for modern local commerce. "
        "By integrating web technologies with interactive mapping, 3D visualization, and AI capabilities, "
        "the system simplifies product discovery, price comparison, and offline-to-online retail bridge.\n\n"
        "The implementation of secure authentication ensures safety and verified interactions. The use of "
        "modern frameworks such as Flask, Three.js, and Leaflet.js ensures scalability, flexibility, and reliability.\n\n"
        "Overall, the proposed system serves as a practical, scalable, and secure solution for the local retail "
        "ecosystem and can be enhanced in the future with advanced AR shopping experiences and localized delivery logistics."
    )
    pdf.multi_cell(0, 6, conclusion_text)
    
    pdf.ln(10)
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 10, "REFERENCES:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "", 12)
    refs_text = (
        "1. Flask Official Documentation - https://flask.palletsprojects.com/\n"
        "2. Three.js Official Documentation - https://threejs.org/\n"
        "3. Leaflet.js Official Documentation - https://leafletjs.com/\n"
        "4. SQLAlchemy Official Documentation - https://www.sqlalchemy.org/\n"
        "5. OpenAI API Documentation - https://platform.openai.com/docs/\n"
        "6. Twilio API Documentation - https://www.twilio.com/docs/\n"
        "7. Capacitor Official Documentation - https://capacitorjs.com/"
    )
    pdf.multi_cell(0, 6, refs_text)

    pdf.output("final_compare2save_synopsis.pdf")
    print("PDF generated successfully.")

if __name__ == "__main__":
    create_pdf()
