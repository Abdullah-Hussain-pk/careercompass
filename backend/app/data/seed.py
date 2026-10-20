"""
CareerCompass – Seed data script.

Creates:
  - Demo accounts (student, counsellor x2, admin, expert)
  - 25+ skills with learning resources
  - 10 degree programs
  - 40+ careers with RIASEC profiles and required skills
  - 48 RIASEC questions (8 per type)
  - 2 counsellors with availability slots
  - Default settings (weights w1/w2/w3)

RIASEC profiles are marked as estimated from O*NET categories.
See docs/architecture.md for details.

Run: python -m app.data.seed
"""
import asyncio
from datetime import datetime, timedelta, timezone
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import hash_password
from app.models.models import (
    User, StudentProfile, Skill, LearningResource, Degree,
    Career, CareerSkill, CareerDegree, RIASECQuestion,
    AvailabilitySlot, Setting
)


async def seed():
    """Run the seed script."""
    # Create tables if not using Alembic
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        existing = await db.get(User, "seed-admin-001")
        if existing:
            print("✅ Database already seeded, skipping.")
            return

        print("🌱 Seeding database...")

        # ── Settings (weights) ─────────────────────────────────────────────
        for key, value, desc in [
            ("w1", "0.5", "Interest (RIASEC cosine similarity) weight – must sum to 1.0 with w2+w3"),
            ("w2", "0.3", "Skill coverage weight"),
            ("w3", "0.2", "Degree eligibility weight"),
            ("degree_penalty", "0.6", "Score penalty when student degree is not eligible for career"),
        ]:
            db.add(Setting(id=f"setting-{key}", key=key, value=value, description=desc))

        # ── Degrees ────────────────────────────────────────────────────────
        degrees = [
            Degree(id="deg-bsse", name="BS Software Engineering", short_name="BSSE"),
            Degree(id="deg-bscs", name="BS Computer Science", short_name="BSCS"),
            Degree(id="deg-bsit", name="BS Information Technology", short_name="BSIT"),
            Degree(id="deg-bsee", name="BS Electrical Engineering", short_name="BSEE"),
            Degree(id="deg-bsce", name="BS Civil Engineering", short_name="BSCE"),
            Degree(id="deg-mbbs", name="MBBS (Bachelor of Medicine)", short_name="MBBS"),
            Degree(id="deg-bba",  name="BBA (Business Administration)", short_name="BBA"),
            Degree(id="deg-bsacc",name="BS Accounting & Finance", short_name="BSAF"),
            Degree(id="deg-bsed", name="BS Education", short_name="BSEd"),
            Degree(id="deg-bsdes",name="BS Graphic Design / Visual Arts", short_name="BSGD"),
            Degree(id="deg-bsds", name="BS Data Science", short_name="BSDS"),
            Degree(id="deg-bscyb",name="BS Cybersecurity", short_name="BSCyb"),
            Degree(id="deg-bsme", name="BS Mechanical Engineering", short_name="BSME"),
        ]
        for d in degrees:
            db.add(d)

        # ── Skills ─────────────────────────────────────────────────────────
        skills_data = [
            ("sk-python",   "Python Programming",        "Programming",   "General-purpose programming language"),
            ("sk-js",       "JavaScript",                "Programming",   "Frontend and backend web development"),
            ("sk-sql",      "SQL & Databases",           "Data",          "Relational database queries"),
            ("sk-ml",       "Machine Learning",          "Data",          "Supervised/unsupervised learning"),
            ("sk-cloud",    "Cloud Computing (AWS/GCP)", "Infrastructure","Deploying and managing cloud services"),
            ("sk-linux",    "Linux / Command Line",      "Infrastructure","Shell scripting and system administration"),
            ("sk-docker",   "Docker & Containers",       "Infrastructure","Containerisation and orchestration"),
            ("sk-net",      "Computer Networking",       "Infrastructure","TCP/IP, routing, firewalls"),
            ("sk-sec",      "Cybersecurity Fundamentals","Security",      "OWASP, threat modelling, penetration testing"),
            ("sk-crypto",   "Cryptography",              "Security",      "Symmetric and asymmetric encryption"),
            ("sk-react",    "React / Frontend Dev",      "Programming",   "Component-based UI development"),
            ("sk-api",      "REST API Design",           "Programming",   "HTTP APIs, OpenAPI"),
            ("sk-git",      "Git / Version Control",     "Tools",         "Branching, merging, pull requests"),
            ("sk-agile",    "Agile / Scrum",             "Soft Skills",   "Sprint planning, retrospectives"),
            ("sk-comm",     "Written Communication",     "Soft Skills",   "Technical writing and documentation"),
            ("sk-pres",     "Presentation Skills",       "Soft Skills",   "Public speaking and slide design"),
            ("sk-lead",     "Leadership",                "Soft Skills",   "Team management and motivation"),
            ("sk-analysis", "Data Analysis",             "Data",          "Pandas, Excel, statistics"),
            ("sk-vis",      "Data Visualisation",        "Data",          "Charts, dashboards, Matplotlib, Power BI"),
            ("sk-excel",    "Microsoft Excel",           "Tools",         "Advanced spreadsheet functions"),
            ("sk-acc",      "Accounting Principles",     "Finance",       "Debits, credits, financial statements"),
            ("sk-audit",    "Auditing",                  "Finance",       "Financial and IT auditing"),
            ("sk-teach",    "Teaching / Instructional",  "Education",     "Lesson planning, pedagogy"),
            ("sk-design",   "Graphic Design",            "Creative",      "Adobe Suite, Figma, typography"),
            ("sk-photo",    "Photography & Media",       "Creative",      "Visual storytelling and editing"),
            ("sk-cad",      "CAD / AutoCAD",             "Engineering",   "2D and 3D structural drawing"),
            ("sk-struct",   "Structural Analysis",       "Engineering",   "Load calculations, beams, columns"),
            ("sk-circuits", "Circuit Design",            "Engineering",   "Analog and digital electronics"),
            ("sk-anatomy",  "Human Anatomy",             "Medical",       "Body systems and pathology"),
            ("sk-pharma",   "Pharmacology",              "Medical",       "Drug mechanisms and dosages"),
        ]

        for (sid, name, cat, desc) in skills_data:
            db.add(Skill(id=sid, name=name, category=cat, description=desc))

        # ── Learning Resources (note: links must be verified, see docs) ───
        resources = [
            # Python
            LearningResource(skill_id="sk-python", title="Python for Everybody – Coursera", url="https://www.coursera.org/specializations/python", provider="University of Michigan", is_free=True),
            LearningResource(skill_id="sk-python", title="Official Python Tutorial", url="https://docs.python.org/3/tutorial/", provider="python.org", is_free=True),
            LearningResource(skill_id="sk-python", title="CS50P: Python – edX", url="https://cs50.harvard.edu/python/", provider="Harvard / edX", is_free=True),
            # SQL
            LearningResource(skill_id="sk-sql", title="SQLZoo Interactive Tutorial", url="https://sqlzoo.net/", provider="SQLZoo", is_free=True),
            LearningResource(skill_id="sk-sql", title="Khan Academy SQL Course", url="https://www.khanacademy.org/computing/computer-programming/sql", provider="Khan Academy", is_free=True),
            # ML
            LearningResource(skill_id="sk-ml", title="Machine Learning Specialisation – Coursera", url="https://www.coursera.org/specializations/machine-learning-introduction", provider="DeepLearning.AI", is_free=True),
            LearningResource(skill_id="sk-ml", title="Scikit-learn User Guide", url="https://scikit-learn.org/stable/user_guide.html", provider="scikit-learn", is_free=True),
            # Cloud
            LearningResource(skill_id="sk-cloud", title="AWS Cloud Practitioner Essentials", url="https://explore.skillbuilder.aws/learn/course/134", provider="AWS", is_free=True),
            LearningResource(skill_id="sk-cloud", title="Google Cloud Skills Boost (Free Tier)", url="https://cloudskillsboost.google/", provider="Google Cloud", is_free=True),
            # Security
            LearningResource(skill_id="sk-sec", title="OWASP Top 10 – Official Guide", url="https://owasp.org/www-project-top-ten/", provider="OWASP", is_free=True),
            LearningResource(skill_id="sk-sec", title="Cybersecurity for Everyone – Coursera", url="https://www.coursera.org/learn/cybersecurity-for-everyone", provider="University of Maryland", is_free=True),
            # React
            LearningResource(skill_id="sk-react", title="React Official Documentation", url="https://react.dev/learn", provider="Meta", is_free=True),
            LearningResource(skill_id="sk-react", title="Full Stack Open (React chapters)", url="https://fullstackopen.com/en/", provider="University of Helsinki", is_free=True),
            # Git
            LearningResource(skill_id="sk-git", title="Pro Git Book (Free)", url="https://git-scm.com/book/en/v2", provider="git-scm.com", is_free=True),
            # Data Analysis
            LearningResource(skill_id="sk-analysis", title="Pandas Documentation", url="https://pandas.pydata.org/docs/getting_started/", provider="pandas", is_free=True),
            LearningResource(skill_id="sk-analysis", title="Data Analysis with Python – FreeCodeCamp", url="https://www.freecodecamp.org/learn/data-analysis-with-python/", provider="freeCodeCamp", is_free=True),
            # Graphic Design
            LearningResource(skill_id="sk-design", title="Canva Design School", url="https://www.canva.com/designschool/", provider="Canva", is_free=True),
            LearningResource(skill_id="sk-design", title="Figma Tutorials (Official)", url="https://help.figma.com/hc/en-us/categories/360002051613", provider="Figma", is_free=True),
            # Teaching
            LearningResource(skill_id="sk-teach", title="Teaching and Learning Toolkit – Education Endowment Foundation", url="https://educationendowmentfoundation.org.uk/education-evidence/teaching-learning-toolkit", provider="EEF", is_free=True),
            # Accounting
            LearningResource(skill_id="sk-acc", title="Accounting Basics – Khan Academy", url="https://www.khanacademy.org/economics-finance-domain/core-finance/accounting-and-financial-statements", provider="Khan Academy", is_free=True),
            # Docker
            LearningResource(skill_id="sk-docker", title="Docker Getting Started", url="https://docs.docker.com/get-started/", provider="Docker", is_free=True),
            # Networking
            LearningResource(skill_id="sk-net", title="Networking Basics – Cisco NetAcad", url="https://www.netacad.com/courses/networking/networking-basics", provider="Cisco", is_free=True),
        ]
        for r in resources:
            db.add(r)

        # ── Users (demo accounts, documented in README) ───────────────────
        users = [
            User(id="seed-admin-001", email="admin@careercompass.pk",
                 hashed_password=hash_password("Admin@1234"), full_name="Admin User", role="admin"),
            User(id="seed-student-001", email="student@careercompass.pk",
                 hashed_password=hash_password("Student@1234"), full_name="Ali Hassan", role="student"),
            User(id="seed-student-002", email="student2@careercompass.pk",
                 hashed_password=hash_password("Student@1234"), full_name="Fatima Khan", role="student"),
            User(id="seed-counsellor-001", email="counsellor@careercompass.pk",
                 hashed_password=hash_password("Counsellor@1234"), full_name="Dr. Sana Mir", role="counsellor"),
            User(id="seed-counsellor-002", email="counsellor2@careercompass.pk",
                 hashed_password=hash_password("Counsellor@1234"), full_name="Mr. Usman Riaz", role="counsellor"),
            User(id="seed-expert-001", email="expert@careercompass.pk",
                 hashed_password=hash_password("Expert@1234"), full_name="Zara Ahmed", role="expert"),
        ]
        for u in users:
            db.add(u)
        await db.flush()

        # Student profiles
        for uid in ["seed-student-001", "seed-student-002"]:
            db.add(StudentProfile(user_id=uid, degree_id="deg-bsse", semester=5, cgpa=3.2))

        # ── RIASEC Questions (48 items, 8 per type) ─────────────────────
        # Original wording adapted for Pakistani students
        questions = [
            # Realistic (R) – hands-on, practical
            ("R", "I enjoy working with tools, machines, or equipment."),
            ("R", "I like outdoor activities that involve physical work."),
            ("R", "I prefer practical, hands-on problems to abstract ones."),
            ("R", "I enjoy building or fixing things."),
            ("R", "I like working with plants or animals."),
            ("R", "I prefer physical activity over sitting at a desk."),
            ("R", "I enjoy tasks that produce a concrete, tangible result."),
            ("R", "I am good at working with my hands."),
            # Investigative (I) – analytical, intellectual
            ("I", "I enjoy solving complex scientific or mathematical problems."),
            ("I", "I like reading scientific journals or research articles."),
            ("I", "I enjoy figuring out how things work."),
            ("I", "I prefer to analyse information before making decisions."),
            ("I", "I enjoy conducting experiments or research."),
            ("I", "I like exploring new ideas even without a practical application."),
            ("I", "I enjoy working independently on intellectual challenges."),
            ("I", "I like asking 'why' and looking for evidence-based answers."),
            # Artistic (A) – creative, expressive
            ("A", "I enjoy creative writing, poetry or storytelling."),
            ("A", "I like drawing, painting or designing things."),
            ("A", "I enjoy music, drama or performing arts."),
            ("A", "I prefer tasks where I can express my individuality."),
            ("A", "I like creating original work rather than following a template."),
            ("A", "I enjoy working in an environment that values creativity."),
            ("A", "I like taking photographs or making videos."),
            ("A", "I enjoy attending cultural events, exhibitions or galleries."),
            # Social (S) – helping, teaching
            ("S", "I enjoy helping others solve their personal problems."),
            ("S", "I like teaching or explaining ideas to others."),
            ("S", "I prefer working in a team over working alone."),
            ("S", "I enjoy volunteering or community service."),
            ("S", "I like interacting with a wide variety of people."),
            ("S", "I enjoy counselling or advising friends on their decisions."),
            ("S", "I prefer careers that make a direct positive impact on people."),
            ("S", "I enjoy listening carefully and empathising with others."),
            # Enterprising (E) – leading, persuading
            ("E", "I enjoy leading a team or managing a project."),
            ("E", "I like persuading others to accept my point of view."),
            ("E", "I enjoy starting new projects or businesses."),
            ("E", "I like making important decisions under pressure."),
            ("E", "I enjoy selling ideas, products or services."),
            ("E", "I like taking charge in ambiguous or uncertain situations."),
            ("E", "I prefer competitive environments where results are rewarded."),
            ("E", "I enjoy public speaking or presenting to large groups."),
            # Conventional (C) – organised, detail-oriented
            ("C", "I enjoy organising information and maintaining records."),
            ("C", "I like following established rules and procedures."),
            ("C", "I prefer tasks that are clearly defined with step-by-step instructions."),
            ("C", "I enjoy working with numbers, spreadsheets or data."),
            ("C", "I like keeping my workspace and files well organised."),
            ("C", "I prefer predictable routines over unpredictable situations."),
            ("C", "I enjoy verifying details and checking for accuracy."),
            ("C", "I like administrative work such as scheduling or bookkeeping."),
        ]

        for idx, (rtype, text) in enumerate(questions, start=1):
            db.add(RIASECQuestion(
                id=f"q-{idx:03d}",
                riasec_type=rtype,
                question_text=text,
                order_index=idx,
            ))

        # ── 40+ Careers with RIASEC profiles ─────────────────────────────
        # All RIASEC profiles are ESTIMATED from O*NET categories.
        # Not official data; must be reviewed by a domain expert.
        # Source: O*NET Online (onetonline.org) – categories mapped to 0-100 scale
        careers_data = [
            # (id, title, desc, R, I, A, S, E, C, roles, salary, source, skills, degrees)
            ("car-se",  "Software Engineer",
             "Design, develop and maintain software applications and systems. Pakistan's fastest-growing professional role with strong demand in local product companies and global outsourcing.",
             30, 80, 40, 40, 60, 60,
             "Junior Developer, Senior Engineer, Tech Lead, Software Architect",
             "PKR 60,000 – 300,000/month (varies with experience and company)",
             "O*NET 15-1252.00 – estimated",
             [("sk-python",4),("sk-js",3),("sk-sql",3),("sk-git",3),("sk-api",3),("sk-agile",2)],
             ["deg-bsse","deg-bscs","deg-bsit"]),

            ("car-da",  "Data Analyst",
             "Collect, clean and interpret large datasets to support business decisions. High demand in banking, telecom and e-commerce sectors in Pakistan.",
             20, 85, 30, 30, 40, 80,
             "Junior Analyst, Data Analyst, Senior Analyst, Analytics Manager",
             "PKR 50,000 – 200,000/month",
             "O*NET 15-2041.00 – estimated",
             [("sk-python",3),("sk-sql",4),("sk-analysis",4),("sk-vis",3),("sk-excel",3)],
             ["deg-bscs","deg-bsds","deg-bsit","deg-bsse","deg-bsacc"]),

            ("car-csa", "Cybersecurity Analyst",
             "Protect organisations from digital threats. Monitor networks, respond to incidents and implement security controls.",
             40, 80, 20, 30, 50, 70,
             "Security Analyst, SOC Analyst, Penetration Tester, CISO",
             "PKR 70,000 – 250,000/month",
             "O*NET 15-1212.00 – estimated",
             [("sk-sec",4),("sk-net",4),("sk-linux",3),("sk-crypto",3),("sk-python",2)],
             ["deg-bscs","deg-bscyb","deg-bsse","deg-bsit"]),

            ("car-cle", "Cloud Engineer",
             "Deploy and manage scalable infrastructure on AWS, GCP or Azure. Critical for Pakistan's growing SaaS and fintech industries.",
             40, 75, 25, 30, 55, 65,
             "Cloud Engineer, DevOps Engineer, Site Reliability Engineer",
             "PKR 80,000 – 350,000/month",
             "O*NET 15-1244.00 – estimated",
             [("sk-cloud",4),("sk-linux",3),("sk-docker",4),("sk-net",3),("sk-python",2)],
             ["deg-bsse","deg-bscs","deg-bsit"]),

            ("car-ml",  "ML Engineer",
             "Build and deploy machine learning models. Bridge between data science and production engineering.",
             30, 90, 30, 25, 50, 60,
             "ML Engineer, AI Engineer, Research Engineer",
             "PKR 80,000 – 400,000/month",
             "O*NET 15-2051.00 – estimated",
             [("sk-python",5),("sk-ml",4),("sk-sql",3),("sk-cloud",3),("sk-analysis",4)],
             ["deg-bscs","deg-bsds","deg-bsse","deg-bsit"]),

            ("car-fe",  "Frontend Developer",
             "Build responsive, accessible web interfaces using React and modern JavaScript.",
             25, 65, 65, 40, 50, 50,
             "UI Developer, Frontend Engineer, Web Developer",
             "PKR 50,000 – 200,000/month",
             "O*NET 15-1254.00 – estimated",
             [("sk-react",4),("sk-js",4),("sk-design",2),("sk-git",3),("sk-api",2)],
             ["deg-bsse","deg-bscs","deg-bsit"]),

            ("car-ce",  "Civil Engineer",
             "Plan, design and oversee construction of infrastructure – roads, bridges, buildings. Highest employment in CPEC-era Pakistan.",
             80, 60, 30, 50, 60, 70,
             "Site Engineer, Structural Engineer, Project Manager (Civil)",
             "PKR 40,000 – 180,000/month",
             "O*NET 17-2051.00 – estimated",
             [("sk-cad",4),("sk-struct",4),("sk-comm",3),("sk-agile",2)],
             ["deg-bsce"]),

            ("car-doc", "Medical Doctor (MBBS)",
             "Diagnose and treat patient illness across specialisations. Requires MBBS and Pakistan Medical Commission registration.",
             40, 70, 25, 85, 60, 55,
             "General Practitioner, Specialist, Surgeon, Hospital Consultant",
             "PKR 60,000 – 500,000/month (varies by specialisation)",
             "O*NET 29-1216.00 – estimated",
             [("sk-anatomy",5),("sk-pharma",4),("sk-comm",4),("sk-lead",3)],
             ["deg-mbbs"]),

            ("car-acc", "Accountant",
             "Prepare financial statements, manage accounts and ensure regulatory compliance. Core function in every Pakistani business.",
             20, 50, 20, 40, 50, 90,
             "Junior Accountant, Senior Accountant, Finance Manager, CFO",
             "PKR 35,000 – 150,000/month",
             "O*NET 13-2011.00 – estimated",
             [("sk-acc",4),("sk-excel",4),("sk-audit",3),("sk-sql",2)],
             ["deg-bsacc","deg-bba"]),

            ("car-teacher","School / College Teacher",
             "Educate students at secondary or tertiary level. Government and private sector positions available across Pakistan.",
             20, 55, 55, 90, 50, 60,
             "Teacher, Lecturer, Professor, Academic Coordinator",
             "PKR 30,000 – 120,000/month",
             "O*NET 25-2031.00 – estimated",
             [("sk-teach",5),("sk-comm",4),("sk-pres",4),("sk-lead",3)],
             ["deg-bsed","deg-bscs","deg-bsce","deg-mbbs","deg-bba"]),

            ("car-gd",  "Graphic Designer",
             "Create visual content for digital and print media. High demand in advertising, media and tech startups.",
             30, 40, 90, 45, 50, 45,
             "Junior Designer, Senior Designer, Art Director, Creative Lead",
             "PKR 35,000 – 150,000/month",
             "O*NET 27-1024.00 – estimated",
             [("sk-design",5),("sk-photo",3),("sk-pres",3),("sk-comm",3)],
             ["deg-bsdes"]),

            ("car-pm",  "Product Manager",
             "Define product strategy, prioritise features and coordinate cross-functional teams.",
             25, 60, 50, 60, 85, 55,
             "Associate PM, Product Manager, Senior PM, Head of Product",
             "PKR 80,000 – 300,000/month",
             "O*NET 11-3021.00 – estimated",
             [("sk-agile",4),("sk-pres",4),("sk-comm",4),("sk-analysis",3),("sk-lead",4)],
             ["deg-bsse","deg-bscs","deg-bba"]),

            ("car-ba",  "Business Analyst",
             "Bridge business requirements and technical solutions. Essential in banking, insurance and enterprise software projects.",
             20, 70, 40, 55, 65, 75,
             "Junior BA, Senior BA, Business Systems Analyst",
             "PKR 50,000 – 180,000/month",
             "O*NET 13-1111.00 – estimated",
             [("sk-analysis",4),("sk-sql",3),("sk-comm",4),("sk-agile",3),("sk-pres",3)],
             ["deg-bba","deg-bsse","deg-bscs","deg-bsit"]),

            ("car-net", "Network Engineer",
             "Design and manage enterprise networks, routers, switches and WAN/LAN infrastructure.",
             55, 70, 20, 35, 55, 70,
             "Network Engineer, Network Admin, NOC Engineer",
             "PKR 45,000 – 180,000/month",
             "O*NET 15-1241.00 – estimated",
             [("sk-net",5),("sk-linux",3),("sk-sec",2),("sk-cloud",2)],
             ["deg-bscs","deg-bsit","deg-bsse"]),

            ("car-dba", "Database Administrator",
             "Install, configure and maintain database systems. Optimise query performance and manage backup/recovery.",
             30, 75, 20, 35, 45, 85,
             "DBA, Senior DBA, Data Engineer",
             "PKR 55,000 – 200,000/month",
             "O*NET 15-1242.00 – estimated",
             [("sk-sql",5),("sk-linux",3),("sk-python",2),("sk-cloud",2)],
             ["deg-bscs","deg-bsit","deg-bsse"]),

            ("car-devops","DevOps Engineer",
             "Automate software delivery pipelines and manage infrastructure as code.",
             40, 75, 30, 35, 60, 65,
             "DevOps Engineer, Platform Engineer, SRE",
             "PKR 80,000 – 300,000/month",
             "O*NET 15-1244.00 – estimated",
             [("sk-docker",4),("sk-linux",4),("sk-cloud",4),("sk-git",4),("sk-python",3)],
             ["deg-bsse","deg-bscs","deg-bsit"]),

            ("car-ux",  "UX / UI Designer",
             "Research user needs and design intuitive interfaces. Growing demand in Pakistani product companies.",
             25, 55, 85, 60, 50, 45,
             "UI/UX Designer, Product Designer, UX Researcher",
             "PKR 40,000 – 180,000/month",
             "O*NET 15-1255.00 – estimated",
             [("sk-design",5),("sk-react",2),("sk-comm",3),("sk-pres",4)],
             ["deg-bsdes","deg-bsse","deg-bscs"]),

            ("car-fin", "Financial Analyst",
             "Analyse financial data to support investment and corporate finance decisions.",
             15, 70, 20, 40, 65, 85,
             "Financial Analyst, Investment Analyst, Equity Research Analyst",
             "PKR 55,000 – 220,000/month",
             "O*NET 13-2051.00 – estimated",
             [("sk-excel",5),("sk-acc",4),("sk-analysis",4),("sk-vis",3),("sk-comm",3)],
             ["deg-bba","deg-bsacc"]),

            ("car-hr",  "HR Manager",
             "Recruit, develop and retain talent. Manage employee relations and HR policies.",
             20, 45, 40, 80, 65, 65,
             "HR Executive, HR Manager, HR Business Partner, CHRO",
             "PKR 40,000 – 160,000/month",
             "O*NET 11-3121.00 – estimated",
             [("sk-comm",4),("sk-lead",4),("sk-pres",3),("sk-excel",2)],
             ["deg-bba"]),

            ("car-mkt", "Digital Marketer",
             "Plan and execute online marketing campaigns (SEO, SEM, social media, email).",
             20, 50, 65, 55, 80, 55,
             "Digital Marketing Executive, SEO Specialist, Marketing Manager",
             "PKR 35,000 – 150,000/month",
             "O*NET 11-2021.00 – estimated",
             [("sk-comm",4),("sk-design",3),("sk-analysis",3),("sk-pres",3)],
             ["deg-bba"]),

            ("car-ee",  "Electrical Engineer",
             "Design and test electrical systems for power generation, distribution and electronics.",
             75, 70, 30, 35, 55, 65,
             "Electrical Engineer, Power Systems Engineer, Electronics Engineer",
             "PKR 45,000 – 180,000/month",
             "O*NET 17-2071.00 – estimated",
             [("sk-circuits",4),("sk-cad",3),("sk-linux",2),("sk-analysis",3)],
             ["deg-bsee"]),

            ("car-me",  "Mechanical Engineer",
             "Design and manufacture mechanical systems, machines and thermal systems.",
             80, 65, 30, 35, 55, 60,
             "Mechanical Engineer, Design Engineer, Manufacturing Engineer",
             "PKR 40,000 – 160,000/month",
             "O*NET 17-2141.00 – estimated",
             [("sk-cad",5),("sk-struct",3),("sk-analysis",3)],
             ["deg-bsme"]),

            ("car-pharma","Pharmacist",
             "Dispense medications, counsel patients and review prescriptions. Required in hospitals, retail pharmacies.",
             30, 65, 25, 75, 40, 70,
             "Retail Pharmacist, Hospital Pharmacist, Clinical Pharmacist",
             "PKR 40,000 – 120,000/month",
             "O*NET 29-1051.00 – estimated",
             [("sk-pharma",5),("sk-comm",4),("sk-anatomy",3)],
             ["deg-mbbs"]),

            ("car-jour","Journalist / Content Writer",
             "Research and write news articles, features and digital content.",
             20, 55, 85, 60, 60, 40,
             "Reporter, Content Writer, Editor, Feature Writer",
             "PKR 25,000 – 100,000/month",
             "O*NET 27-3023.00 – estimated",
             [("sk-comm",5),("sk-pres",3),("sk-photo",3)],
             ["deg-bsed","deg-bba"]),

            ("car-audit","Internal / IT Auditor",
             "Review financial and IT controls to ensure compliance with regulations and standards.",
             25, 70, 20, 40, 50, 90,
             "Internal Auditor, IT Auditor, Compliance Officer",
             "PKR 50,000 – 180,000/month",
             "O*NET 13-2011.01 – estimated",
             [("sk-audit",5),("sk-acc",4),("sk-sql",3),("sk-sec",2)],
             ["deg-bsacc","deg-bba","deg-bscs"]),

            ("car-archi","Software Architect",
             "Define high-level software structure, select technologies and guide development teams.",
             30, 85, 40, 45, 70, 65,
             "Software Architect, Solutions Architect, Principal Engineer",
             "PKR 150,000 – 500,000/month",
             "O*NET 15-1299.08 – estimated",
             [("sk-python",4),("sk-api",5),("sk-cloud",4),("sk-docker",4),("sk-agile",4),("sk-lead",4)],
             ["deg-bsse","deg-bscs"]),

            ("car-qae", "QA Engineer",
             "Ensure software quality through manual and automated testing strategies.",
             30, 70, 30, 40, 45, 75,
             "QA Engineer, Test Engineer, SDET",
             "PKR 40,000 – 150,000/month",
             "O*NET 15-1253.00 – estimated",
             [("sk-python",3),("sk-api",3),("sk-sql",2),("sk-comm",3),("sk-agile",3)],
             ["deg-bsse","deg-bscs","deg-bsit"]),

            ("car-emb", "Embedded Systems Engineer",
             "Develop firmware and low-level software for microcontrollers and hardware devices.",
             80, 80, 25, 30, 50, 65,
             "Firmware Engineer, Embedded Developer, IoT Engineer",
             "PKR 60,000 – 250,000/month",
             "O*NET 17-2061.00 – estimated",
             [("sk-circuits",4),("sk-linux",3),("sk-python",3),("sk-net",2)],
             ["deg-bsee","deg-bscs","deg-bsse"]),

            ("car-bio", "Biomedical Engineer",
             "Apply engineering principles to medical equipment design and healthcare technology.",
             70, 75, 35, 55, 50, 60,
             "Biomedical Engineer, Medical Device Engineer",
             "PKR 45,000 – 160,000/month",
             "O*NET 17-2031.00 – estimated",
             [("sk-circuits",3),("sk-analysis",3),("sk-anatomy",3),("sk-cad",2)],
             ["deg-bsee","deg-bsme","deg-mbbs"]),

            ("car-econ","Economist",
             "Research economic trends and advise on policy, business and investment decisions.",
             15, 85, 30, 50, 65, 75,
             "Economic Analyst, Research Economist, Policy Analyst",
             "PKR 50,000 – 200,000/month",
             "O*NET 19-3011.00 – estimated",
             [("sk-analysis",5),("sk-excel",4),("sk-comm",4),("sk-vis",3)],
             ["deg-bba","deg-bsacc"]),

            ("car-stat","Statistician / Data Scientist",
             "Apply statistical methods to analyse data and draw insights. Growing field in Pakistan's fintech and health sectors.",
             20, 90, 30, 35, 50, 75,
             "Statistician, Data Scientist, Research Analyst",
             "PKR 60,000 – 300,000/month",
             "O*NET 15-2041.00 – estimated",
             [("sk-python",4),("sk-ml",4),("sk-analysis",5),("sk-sql",3),("sk-vis",4)],
             ["deg-bsds","deg-bscs","deg-bsse"]),

            ("car-env", "Environmental Engineer",
             "Develop solutions to environmental problems such as pollution, water supply and waste management.",
             75, 70, 40, 60, 55, 60,
             "Environmental Engineer, Environmental Consultant",
             "PKR 40,000 – 130,000/month",
             "O*NET 17-2081.00 – estimated",
             [("sk-cad",3),("sk-analysis",3),("sk-comm",3),("sk-struct",2)],
             ["deg-bsce","deg-bsme"]),

            ("car-sc",  "Supply Chain Manager",
             "Oversee procurement, logistics and inventory management for manufacturing or retail.",
             40, 55, 25, 55, 75, 70,
             "Supply Chain Analyst, Logistics Manager, Procurement Officer",
             "PKR 50,000 – 180,000/month",
             "O*NET 11-3071.00 – estimated",
             [("sk-excel",4),("sk-analysis",3),("sk-comm",3),("sk-agile",3)],
             ["deg-bba"]),

            ("car-pub", "Public Relations Officer",
             "Manage the public image and communications of organisations.",
             20, 45, 65, 75, 75, 45,
             "PR Executive, Communications Officer, PR Manager",
             "PKR 35,000 – 120,000/month",
             "O*NET 27-3031.00 – estimated",
             [("sk-comm",5),("sk-pres",4),("sk-design",2)],
             ["deg-bba"]),

            ("car-swe2","Full-Stack Developer",
             "Build both frontend and backend components of web applications.",
             30, 75, 45, 40, 60, 60,
             "Full-Stack Developer, Web Developer, Software Engineer",
             "PKR 60,000 – 280,000/month",
             "O*NET 15-1252.00 – estimated",
             [("sk-react",4),("sk-python",4),("sk-sql",3),("sk-api",4),("sk-docker",3),("sk-git",3)],
             ["deg-bsse","deg-bscs","deg-bsit"]),

            ("car-mob", "Mobile App Developer",
             "Develop iOS and Android applications using Flutter, React Native or native SDKs.",
             30, 70, 50, 40, 60, 55,
             "Mobile Developer, App Engineer, React Native Developer",
             "PKR 55,000 – 250,000/month",
             "O*NET 15-1252.00 – estimated",
             [("sk-js",4),("sk-react",3),("sk-api",3),("sk-git",3),("sk-agile",2)],
             ["deg-bsse","deg-bscs","deg-bsit"]),

            ("car-proj","Project Manager (IT)",
             "Lead software and technology projects from inception to delivery.",
             25, 60, 35, 60, 85, 65,
             "Project Manager, IT PM, Scrum Master",
             "PKR 70,000 – 250,000/month",
             "O*NET 15-1299.09 – estimated",
             [("sk-agile",5),("sk-comm",4),("sk-lead",5),("sk-pres",4),("sk-analysis",3)],
             ["deg-bsse","deg-bscs","deg-bba"]),

            ("car-phys","Physicist / Research Scientist",
             "Conduct fundamental or applied physics research in academia or industry.",
             50, 95, 50, 50, 60, 65,
             "Research Scientist, Lab Physicist, Nuclear Technician",
             "PKR 50,000 – 200,000/month",
             "O*NET 19-2012.00 – estimated",
             [("sk-analysis",5),("sk-python",3),("sk-vis",3),("sk-comm",4)],
             ["deg-bsee","deg-bsme"]),

            ("car-chef","Game Developer",
             "Design and develop video games for PC, mobile or console platforms.",
             40, 70, 80, 40, 60, 50,
             "Game Developer, Unity Developer, Game Designer",
             "PKR 50,000 – 200,000/month",
             "O*NET 15-1252.00 – estimated",
             [("sk-python",3),("sk-js",3),("sk-design",3),("sk-agile",2)],
             ["deg-bsse","deg-bscs"]),

            ("car-consul","IT Consultant",
             "Advise organisations on technology strategy, system selection and digital transformation.",
             25, 70, 35, 60, 80, 60,
             "IT Consultant, Technology Advisor, Management Consultant",
             "PKR 80,000 – 350,000/month",
             "O*NET 15-1299.00 – estimated",
             [("sk-comm",5),("sk-pres",5),("sk-analysis",4),("sk-agile",3),("sk-cloud",2)],
             ["deg-bsse","deg-bscs","deg-bba"]),

            ("car-iot", "IoT Engineer",
             "Design connected devices and IoT systems for smart homes, industry and healthcare.",
             70, 80, 30, 30, 55, 60,
             "IoT Engineer, Embedded Engineer, IoT Architect",
             "PKR 55,000 – 220,000/month",
             "O*NET 17-2061.00 – estimated",
             [("sk-circuits",4),("sk-net",3),("sk-python",3),("sk-cloud",3),("sk-linux",3)],
             ["deg-bsee","deg-bsse","deg-bscs"]),

            ("car-taxc","Tax Consultant",
             "Advise individuals and businesses on tax planning and compliance under Pakistani tax law.",
             15, 60, 20, 45, 60, 90,
             "Tax Consultant, Tax Adviser, Tax Manager",
             "PKR 40,000 – 150,000/month",
             "O*NET 13-2082.00 – estimated",
             [("sk-acc",5),("sk-excel",4),("sk-audit",4),("sk-comm",3)],
             ["deg-bsacc","deg-bba"]),
        ]

        for cdata in careers_data:
            (cid, title, desc, R, I, A, S, E, C,
             roles, salary, source, skill_reqs, degree_ids) = cdata

            career = Career(
                id=cid, title=title, description=desc,
                r_score=float(R), i_score=float(I), a_score=float(A),
                s_score=float(S), e_score=float(E), c_score=float(C),
                typical_roles=roles, salary_range=salary, source=source,
            )
            db.add(career)
            await db.flush()

            for (skill_id, req_level) in skill_reqs:
                db.add(CareerSkill(career_id=cid, skill_id=skill_id, required_level=req_level))

            for deg_id in degree_ids:
                db.add(CareerDegree(career_id=cid, degree_id=deg_id))

        # ── Counsellor Availability Slots ──────────────────────────────────
        # Create 5 future slots for each of the two counsellors
        base_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        for i in range(1, 6):
            slot_time = base_time + timedelta(days=i, hours=9)
            db.add(AvailabilitySlot(
                counsellor_id="seed-counsellor-001",
                start_time=slot_time,
                end_time=slot_time + timedelta(minutes=30),
            ))
        for i in range(1, 6):
            slot_time = base_time + timedelta(days=i, hours=14)
            db.add(AvailabilitySlot(
                counsellor_id="seed-counsellor-002",
                start_time=slot_time,
                end_time=slot_time + timedelta(minutes=30),
            ))

        await db.commit()
        print("✅ Seed complete!")
        print("\nDemo accounts:")
        print("  Admin:      admin@careercompass.pk     / Admin@1234")
        print("  Student:    student@careercompass.pk   / Student@1234")
        print("  Student 2:  student2@careercompass.pk  / Student@1234")
        print("  Counsellor: counsellor@careercompass.pk / Counsellor@1234")
        print("  Counsellor2:counsellor2@careercompass.pk / Counsellor@1234")
        print("  Expert:     expert@careercompass.pk    / Expert@1234")


if __name__ == "__main__":
    asyncio.run(seed())
