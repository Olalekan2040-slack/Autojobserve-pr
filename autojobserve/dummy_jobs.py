from autojobserve.models import AllJobs
from autojobserve.schemas import AllJobsSchema
from autojobserve.routers import get_db
import random

def create_dummy_jobs():
    job_types = ["remote", "on-site", "hybrid"]
    dummy_jobs = [
        {
            "job_title": "Software Developer",
            "job_salary": "$80,000",
            "job_skill": "Python, JavaScript, SQL",
            "job_location": "New York",
            "job_description": "We are looking for a skilled Software Developer to join our team.",
            "job_requirements": "Requirements:\n- Proficiency in Python, JavaScript, and SQL\n- Bachelor's degree in Computer Science\n- Strong problem-solving skills",
            "company_name": "Tech Solutions Inc.", 
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/", 
        },
        {
            "job_title": "Data Analyst",
            "job_salary": "$72,000",
            "job_skill": "Data Analysis, Excel, Python",
            "job_location": "San Francisco",
            "job_description": "Join our Data Analysis team and make an impact with your analytical skills.",
            "job_requirements": "Requirements:\n- Data analysis experience\n- Proficiency in Excel and Python\n- Strong analytical skills",
            "company_name": "Data Insights Corp.", 
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/aabout/"
        },
        {
            "job_title": "Frontend Developer",
            "job_salary": "$75,000",
            "job_skill": "HTML, CSS, JavaScript",
            "job_location": "Los Angeles",
            "job_description": "Create stunning web interfaces as a Frontend Developer at our creative agency.",
            "job_requirements": "Requirements:\n- Frontend development experience\n- Proficiency in HTML, CSS, and JavaScript\n- Design skills a plus",
            "company_name": "Web Design Pro", 
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/abouts/"
        },
        {
            "job_title": "Backend Engineer",
            "job_salary": "$85,000",
            "job_skill": "Java, Spring Boot, SQL",
            "job_location": "Chicago",
            "job_description": "Join our Backend Engineering team and work on cutting-edge technologies.",
            "job_requirements": "Requirements:\n- Proficiency in Java and Spring Boot\n- Experience with SQL databases\n- Strong coding skills",
            "company_name": "Tech Innovators LLC", 
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/aboutss/"
        },
        {
            "job_title": "UX Designer",
            "job_salary": "$70,000",
            "job_skill": "UI/UX Design, Prototyping",
            "job_location": "Boston",
            "job_description": "Design user-friendly interfaces and create seamless user experiences as a UX Designer.",
            "job_requirements": "Requirements:\n- UI/UX design experience\n- Proficiency in prototyping tools\n- Creative mindset",
            "company_name": "Design Dynamics", 
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/aboutv/"
        },
        {
            "job_title": "Data Scientist",
            "job_salary": "$90,000",
            "job_skill": "Machine Learning, Python, Data Visualization",
            "job_location": "Seattle",
            "job_description": "Join our Data Science team and use machine learning to derive valuable insights.",
            "job_requirements": "Requirements:\n- Machine learning expertise\n- Proficiency in Python\n- Data visualization skills",
            "company_name": "DataTech Solutions", 
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/aboutw/"
        },
        {
            "job_title": "Product Manager",
            "job_salary": "$95,000",
            "job_skill": "Product Management, Agile, Roadmapping",
            "job_location": "Austin",
            "job_description": "Lead product development projects as a Product Manager and drive innovation.",
            "job_requirements": "Requirements:\n- Product management experience\n- Agile methodology knowledge\n- Strong roadmapping skills",
            "company_name": "InnovateX Inc.", 
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/"
        },
        {
            "job_title": "DevOps Engineer",
            "job_salary": "$85,000",
            "job_skill": "Docker, Kubernetes, CI/CD",
            "job_location": "Denver",
            "job_description": "Manage our infrastructure and automate deployment pipelines as a DevOps Engineer.",
            "job_requirements": "Requirements:\n- DevOps experience\n- Proficiency in Docker and Kubernetes\n- CI/CD pipeline expertise",
            "company_name": "CloudSolutions Ltd.", 
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/abo/"
        },
        {
            "job_title": "Network Administrator",
            "job_salary": "$75,000",
            "job_skill": "Network Management, Troubleshooting",
            "job_location": "Miami",
            "job_description": "Ensure the reliability of our network infrastructure as a Network Administrator.",
            "job_requirements": "Requirements:\n- Network management experience\n- Troubleshooting skills\n- Networking certifications a plus",
            "company_name": "NetWorks Inc.", 
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/abouut/"
        },
        {
            "job_title": "Database Administrator",
            "job_salary": "$80,000",
            "job_skill": "Database Management, SQL",
            "job_location": "Phoenix",
            "job_description": "Manage and optimize databases to ensure data integrity as a Database Administrator.",
            "job_requirements": "Requirements:\n- Database management experience\n- Proficiency in SQL\n- Strong data management skills",
            "company_name": "DataMasters Corp.", 
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/aboutbv/"
        },
        {
            "job_title": "Graphic Designer",
            "job_salary": "$60,000",
            "job_skill": "Adobe Creative Suite, Illustration",
            "job_location": "Portland",
            "job_description": "Create visually stunning designs and illustrations as a Graphic Designer.",
            "job_requirements": "Requirements:\n- Proficiency in Adobe Creative Suite\n- Illustration skills\n- Creative flair",
            "company_name": "DesignCraft Studios", 
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/abvout/"
        },
        {
            "job_title": "Marketing Manager",
            "job_salary": "$85,000",
            "job_skill": "Digital Marketing, SEO, Social Media",
            "job_location": "Houston",
            "job_description": "Lead marketing campaigns and strategies as a Marketing Manager to drive business growth.",
            "job_requirements": "Requirements:\n- Digital marketing experience\n- SEO expertise\n- Social media marketing skills",
            "company_name": "MarketBoosters Inc.", 
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/aboutmn/"
        },
        {
            "job_title": "Quality Assurance Engineer",
            "job_salary": "$70,000",
            "job_skill": "Testing, Test Automation, Bug Tracking",
            "job_location": "Detroit",
            "job_description": "Ensure the quality and reliability of our software through thorough testing as a QA Engineer.",
            "job_requirements": "Requirements:\n- Testing experience\n- Test automation skills\n- Bug tracking knowledge",
            "company_name": "QualityTech Solutions",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/aboutnm/"
        },
        {
            "job_title": "Financial Analyst",
            "job_salary": "$75,000",
            "job_skill": "Financial Modeling, Excel, Finance",
            "job_location": "Minneapolis",
            "job_description": "Analyze financial data and provide valuable insights as a Financial Analyst.",
            "job_requirements": "Requirements:\n- Financial modeling experience\n- Proficiency in Excel\n- Financial analysis skills",
            "company_name": "FinanceWise Corp.",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/1/"
        },
        {
            "job_title": "Content Writer",
            "job_salary": "$55,000",
            "job_skill": "Content Creation, Blogging, SEO",
            "job_location": "Philadelphia",
            "job_description": "Create engaging and SEO-friendly content as a Content Writer.",
            "job_requirements": "Requirements:\n- Content creation experience\n- Blogging skills\n- SEO knowledge",
            "company_name": "ContentMasters LLC",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/2/"
        },
        {
            "job_title": "AI Research Scientist",
            "job_salary": "$100,000",
            "job_skill": "Machine Learning, Deep Learning, Python",
            "job_location": "San Jose",
            "job_description": "Conduct groundbreaking research in the field of artificial intelligence as an AI Research Scientist.",
            "job_requirements": "Requirements:\n- Machine learning and deep learning expertise\n- Proficiency in Python\n- Research experience",
            "company_name": "AI Innovations Corp.",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/3",
        },
        {
            "job_title": "Cybersecurity Analyst",
            "job_salary": "$80,000",
            "job_skill": "Cybersecurity, Network Security, Incident Response",
            "job_location": "Washington, D.C.",
            "job_description": "Protect our organization from cyber threats and ensure the security of our network as a Cybersecurity Analyst.",
            "job_requirements": "Requirements:\n- Cybersecurity expertise\n- Network security knowledge\n- Incident response experience",
            "company_name": "SecureNet Solutions",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/4",
        },
        {
            "job_title": "Sales Manager",
            "job_salary": "$90,000",
            "job_skill": "Sales, Relationship Building, CRM",
            "job_location": "Dallas",
            "job_description": "Lead our sales team and drive revenue growth as a Sales Manager through effective sales strategies.",
            "job_requirements": "Requirements:\n- Sales experience\n- Relationship building skills\n- CRM knowledge",
            "company_name": "SalesPro Inc.",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/5",
        },
        {
            "job_title": "Environmental Engineer",
            "job_salary": "$70,000",
            "job_skill": "Environmental Engineering, Sustainability, Environmental Impact Assessment",
            "job_location": "Portland",
            "job_description": "Work on environmental projects and promote sustainability as an Environmental Engineer.",
            "job_requirements": "Requirements:\n- Environmental engineering expertise\n- Sustainability knowledge\n- Impact assessment skills",
            "company_name": "EcoSolutions Ltd.",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/6",
        },
        {
            "job_title": "Healthcare Administrator",
            "job_salary": "$85,000",
            "job_skill": "Healthcare Management, Regulatory Compliance, Leadership",
            "job_location": "Chicago",
            "job_description": "Manage healthcare facilities and ensure compliance with regulations as a Healthcare Administrator.",
            "job_requirements": "Requirements:\n- Healthcare management experience\n- Regulatory compliance knowledge\n- Leadership skills",
            "company_name": "HealthCarePro Inc.",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/7",
        },
        {
            "job_title": "Civil Engineer",
            "job_salary": "$75,000",
            "job_skill": "Civil Engineering, Infrastructure Design, AutoCAD",
            "job_location": "Atlanta",
            "job_description": "Design and oversee infrastructure projects as a Civil Engineer to improve our cities.",
            "job_requirements": "Requirements:\n- Civil engineering expertise\n- Infrastructure design skills\n- AutoCAD proficiency",
            "company_name": "CityBuilders Corp.",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/8",
        },
        {
            "job_title": "HR Specialist",
            "job_salary": "$60,000",
            "job_skill": "Human Resources, Recruitment, Employee Relations",
            "job_location": "New Orleans",
            "job_description": "Manage human resources functions, including recruitment and employee relations, as an HR Specialist.",
            "job_requirements": "Requirements:\n- Human resources experience\n- Recruitment skills\n- Employee relations knowledge",
            "company_name": "HRConnect Solutions",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/88",
        },
        {
            "job_title": "Architect",
            "job_salary": "$80,000",
            "job_skill": "Architectural Design, AutoCAD, Building Codes",
            "job_location": "Denver",
            "job_description": "Design innovative and functional architectural projects as an Architect.",
            "job_requirements": "Requirements:\n- Architectural design expertise\n- AutoCAD proficiency\n- Knowledge of building codes",
            "company_name": "ArchiDesign Studios",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/89",
        },
        {
            "job_title": "Biomedical Engineer",
            "job_salary": "$90,000",
            "job_skill": "Biomedical Engineering, Medical Device Design, FDA Regulations",
            "job_location": "San Diego",
            "job_description": "Innovate in the field of biomedical engineering and contribute to the development of medical devices.",
            "job_requirements": "Requirements:\n- Biomedical engineering expertise\n- Medical device design skills\n- Knowledge of FDA regulations",
            "company_name": "MedTech Innovations",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/90",
        },
        {
            "job_title": "Electrician",
            "job_salary": "$55,000",
            "job_skill": "Electrical Wiring, Troubleshooting, Safety Standards",
            "job_location": "Houston",
            "job_description": "Install and maintain electrical systems and ensure electrical safety as an Electrician.",
            "job_requirements": "Requirements:\n- Electrical wiring expertise\n- Troubleshooting skills\n- Knowledge of safety standards",
            "company_name": "ElecPro Services",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/11",
        },
        {
            "job_title": "Pharmacist",
            "job_salary": "$100,000",
            "job_skill": "Pharmacy, Medication Dispensing, Patient Counseling",
            "job_location": "New York",
            "job_description": "Dispense medications and provide pharmaceutical care as a Pharmacist.",
            "job_requirements": "Requirements:\n- Pharmacy degree and licensure\n- Medication dispensing skills\n- Patient counseling expertise",
            "company_name": "PharmaCare Solutions",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/23",
        },
        {
            "job_title": "Mechanical Engineer",
            "job_salary": "$80,000",
            "job_skill": "Mechanical Engineering, CAD, Product Design",
            "job_location": "Seattle",
            "job_description": "Design and improve mechanical systems and products as a Mechanical Engineer.",
            "job_requirements": "Requirements:\n- Mechanical engineering expertise\n- CAD proficiency\n- Product design skills",
            "company_name": "MechanoWorks Inc.",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/234",
        },
        {
            "job_title": "Veterinarian",
            "job_salary": "$85,000",
            "job_skill": "Veterinary Medicine, Animal Care, Surgery",
            "job_location": "San Francisco",
            "job_description": "Provide medical care to animals and perform surgeries as a Veterinarian.",
            "company_name": "AnimalHealth Clinic",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/566",
        },
        {
            "job_title": "Restaurant Chef",
            "job_salary": "$70,000",
            "job_skill": "Culinary Arts, Menu Planning, Kitchen Management",
            "job_location": "Miami",
            "job_description": "Lead a kitchen team and create exquisite culinary dishes as a Restaurant Chef.",
            "job_requirements": "Requirements:\n- Culinary arts expertise\n- Menu planning skills\n- Kitchen management experience",
            "company_name": "Gourmet Delights Restaurant",
            "job_type": random.choice(job_types),
            "job_permalink": "https://jobs.google.com/about/44",
        },
    ]
    db = next(get_db()) 

    try:
        for job_data in dummy_jobs:
            existing_job = db.query(AllJobs).filter_by(job_permalink=job_data['job_permalink']).first()

            if not existing_job:
                job = AllJobs(**job_data)
                db.add(job)

        db.commit()
    finally:
        db.close()